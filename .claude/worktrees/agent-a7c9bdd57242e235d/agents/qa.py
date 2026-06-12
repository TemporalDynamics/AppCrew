from datetime import datetime, timezone
from pathlib import Path

from agents.base import BaseAgent
from contracts import AgentAction, ActionType, InvariantViolation, AgentState


class QAAgent(BaseAgent):
    id = "qa"
    name = "Delivery QA"
    icon = "✅"
    description = "Control de calidad — solo lee, nunca modifica datos"
    read_only = True
    never_sends = True

    INVARIANT_READ_ONLY = "QA solo inspecciona y reporta. Nunca modifica datos."

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": False},
                "browser": {"permitted": False},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura, nunca escribe"},
                "context7": {"permitted": False},
                "memory": {"permitted": False},
            },
            "context": ["run_id actual", "datos del sistema a inspeccionar"],
            "memory": {
                "namespace": "N/A (cada inspección es fresca)",
                "can_remember": [],
                "cannot_remember": [],
            },
            "invariants": [
                "Solo lectura (read_only = True)",
                "Nunca modifica datos",
                "Siempre produce reporte (mínimo QA_SUMMARY)",
                "Issue siempre tiene severidad",
                "Accionable (cada issue incluye qué hacer)",
                "No bloqueante",
                "Toda acción tiene run_id y dedup_key",
            ],
            "failure_modes": [
                "Datos no disponibles: reporta 'no data to inspect'",
                "Permisos de lectura: error, escala",
            ],
            "escalation": [
                "Issues críticos (severidad > 80): destacar en reporte",
                "No puede leer datos: escala al CEO",
            ],
            "agent_state_on_findings": "idle",
            "tests": [
                "import OK", "run siempre produce al menos QA_SUMMARY", "read_only = True",
                "run_id obligatorio", "dedup funciona", "state = idle cuando encuentra issues",
            ],
            "authority": "inspector",
        }

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        if not actions:
            raise RuntimeError("QA siempre debe producir al menos 1 acción (summary)")

    async def run(self, run_id: str) -> list[AgentAction]:
        """QA override: no pasa a PENDING_REVIEW, siempre termina en IDLE.
        Las issues requieren ack/resolve/escalate, no aprobación.
        Solo agrega a pending_actions, no duplica en history."""
        self.state = AgentState.WORKING
        self.last_run_id = run_id

        violations = self._check_preconditions()
        if violations:
            self.state = AgentState.ERROR
            self.last_action = f"Invariante violada: {violations[0].invariant}"
            return []

        try:
            actions = await self.work()
            deduped = self._deduplicate(actions)
            self._check_postconditions(deduped)

            for idx, a in enumerate(deduped):
                a.run_id = run_id
                raw = f"{a.agent_id}|{run_id}|{a.action_type}|{a.target}|{idx}"
                h = abs(hash(raw))
                a.action_id = f"{a.agent_id}_{run_id[:12]}_{h % 10**12:012d}"
                self.pending_actions.append(a)

            self.state = AgentState.IDLE
            self.last_run = datetime.now(timezone.utc).isoformat()
            skipped = len(actions) - len(deduped)
            self.last_action = f"{len(deduped)} acciones ({skipped} duplicadas omitidas)"
            return deduped
        except Exception as e:
            self.state = AgentState.ERROR
            self.last_action = f"Error: {e}"
            return []

    async def work(self) -> list[AgentAction]:
        actions = []
        for issue in self._run_checks():
            actions.append(AgentAction(
                agent_id=self.id,
                action_type=ActionType.QUALITY_ISSUE.value,
                target=issue["scope"],
                reason=issue["detail"],
                payload=issue,
                score=issue.get("severity", 50),
            ))
        actions.append(AgentAction(
            agent_id=self.id,
            action_type=ActionType.QA_SUMMARY.value,
            target="all",
            reason=f"{len(actions)} issues encontrados" if actions else "Todo en orden",
            payload={
                "checks_run": len(actions) + 1,
                "issues_found": len([a for a in actions if a.action_type != ActionType.QA_SUMMARY.value]),
                "status": "PASS" if not [a for a in actions if a.action_type != ActionType.QA_SUMMARY.value] else "ISSUES_FOUND",
            },
            score=100 if not [a for a in actions if a.action_type != ActionType.QA_SUMMARY.value] else 60,
        ))
        return actions

    def _run_checks(self) -> list[dict]:
        issues = []
        for account_dir in Path("data/knowledge").iterdir():
            if not account_dir.is_dir():
                continue
            for folder in account_dir.iterdir():
                if folder.is_dir() and not any(folder.iterdir()):
                    issues.append({
                        "scope": f"{account_dir.name}/{folder.name}",
                        "type": "empty_folder",
                        "detail": f"Carpeta {folder.name} en {account_dir.name} está vacía",
                        "severity": 40,
                    })
        return issues
