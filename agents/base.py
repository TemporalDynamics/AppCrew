from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from contracts import AgentAction, AgentState, InvariantViolation
from core.logger import get_logger

logger = get_logger("agents.base")


class BaseAgent:
    id: str = ""
    name: str = ""
    icon: str = ""
    description: str = ""
    state: AgentState = AgentState.IDLE
    last_action: str = ""
    last_run: str | None = None
    last_run_id: str | None = None
    pending_actions: list[AgentAction] = []
    history: list[AgentAction] = []

    invariants: list[dict] = []
    read_only: bool = False
    never_sends: bool = True
    needs_approval: bool = True

    contract: dict = {}

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._init_contract()

    def _init_contract(self):
        self.contract = {
            "tools": {},
            "context": [],
            "memory": {"namespace": "N/A", "can_remember": [], "cannot_remember": []},
            "invariants": [],
            "failure_modes": [],
            "escalation": [],
            "tests": [],
            "authority": "worker",
        }

    def resolve_context(self) -> dict:
        workspace_id = self.config.get("workspace_id", "default")
        logger.info("[%s HOOK] 1. resolve_context: Resolving context for workspace '%s'", self.id.upper(), workspace_id)
        
        # Load workspace settings (demo_mode)
        import yaml
        from pathlib import Path
        ROOT = Path(__file__).resolve().parent.parent
        settings_path = ROOT / "data" / "criteria" / f"settings_{workspace_id}.yaml"
        demo_mode = True
        if settings_path.exists():
            try:
                with open(settings_path, "r", encoding="utf-8") as f:
                    s_data = yaml.safe_load(f) or {}
                    demo_mode = s_data.get("demo_mode", True)
            except Exception:
                logger.warning("[%s HOOK] Could not load settings for workspace '%s'", self.id.upper(), workspace_id)
                
        # Load active criteria / mission
        if workspace_id == "default":
            criteria_path = ROOT / "data" / "demo_rodri_criteria.yaml"
        else:
            criteria_path = ROOT / "data" / "criteria" / f"{workspace_id}.yaml"
            
        criteria = {}
        if criteria_path.exists():
            try:
                with open(criteria_path, "r", encoding="utf-8") as f:
                    criteria = yaml.safe_load(f) or {}
            except Exception:
                logger.warning("[%s HOOK] Could not load criteria from '%s'", self.id.upper(), criteria_path)
                
        role_target = criteria.get("role_target", criteria.get("role", "Candidato Talo"))
        
        # Fail closed check: if workspace_id is empty, fail immediately
        if not workspace_id:
            raise ValueError(f"Freno de seguridad [Fail-Closed]: Workspace ID no resuelto en el agente {self.id}.")
            
        self.config["workspace_id"] = workspace_id
        self.config["demo_mode"] = demo_mode
        self.config["criteria"] = criteria
        
        logger.info("[%s HOOK] Context resolved: Mode=%s, Role='%s'", self.id.upper(), "Demo" if demo_mode else "Real", role_target)
        return {
            "workspace_id": workspace_id,
            "demo_mode": demo_mode,
            "role_target": role_target,
            "criteria": criteria
        }

    def verify_memory_scope(self) -> None:
        logger.info("[%s HOOK] 2. verify_memory_scope: Checking memory integrity (ledger)...", self.id.upper())
        try:
            from scripts.demo_verify import verify_chain, _ledger_db_path
            db_path = _ledger_db_path()
            if db_path.exists():
                ok, message = verify_chain(db_path)
                if not ok:
                    logger.error("[%s HOOK] MEMORY INTEGRITY FAILURE: %s", self.id.upper(), message)
                    raise ValueError(f"Freno de seguridad: Tamper detectado en el ledger de memoria de Talo. {message}")
                else:
                    logger.info("[%s HOOK] Memory integrity OK: %s", self.id.upper(), message)
            else:
                logger.info("[%s HOOK] Memory ledger not found at %s. Skipping verification.", self.id.upper(), db_path)
        except ImportError:
            logger.warning("[%s HOOK] demo_verify script not importable. Skipping verification.", self.id.upper())

    def load_recent_audit_context(self) -> list:
        logger.info("[%s HOOK] 3. load_recent_audit_context: Loading recent relevant entries from ledger...", self.id.upper())
        import sqlite3
        import json
        from pathlib import Path
        ROOT = Path(__file__).resolve().parent.parent
        entries = []
        try:
            from scripts.demo_verify import _ledger_db_path
            db_path = _ledger_db_path()
            if db_path.exists():
                conn = sqlite3.connect(str(db_path))
                rows = conn.execute(
                    "SELECT id, created_at, content, tags FROM entries ORDER BY created_epoch DESC"
                ).fetchall()
                conn.close()
                
                for r in rows:
                    entry_id, created_at, content, tags_json = r
                    try:
                        tags = json.loads(tags_json)
                    except Exception:
                        tags = []
                    # Filter: relevant if tag matches agent_id or general system events
                    if not tags or self.id in tags or "startup" in tags:
                        entries.append({
                            "id": entry_id,
                            "created_at": created_at,
                            "content": json.loads(content) if content.startswith("{") else content,
                            "tags": tags
                        })
                    if len(entries) >= 5:
                        break
                logger.info("[%s HOOK] Loaded %d relevant audit entries.", self.id.upper(), len(entries))
        except Exception as e:
            logger.warning("[%s HOOK] Could not load audit context: %s", self.id.upper(), e)
        return entries

    def append_task_start(self, run_id: str) -> None:
        logger.info("[%s HOOK] 4. append_task_start: Registering task start in ledger...", self.id.upper())
        try:
            from core.demo_notifiers import safe_record_ledger
            safe_record_ledger(
                event_type="agent_run_started",
                summary=f"El agente {self.name or self.id} inició la ejecución",
                evidence={
                    "agent_id": self.id,
                    "run_id": run_id,
                    "timestamp": datetime.now(timezone.utc).isoformat()
                },
                tags=["startup", self.id]
            )
        except Exception as e:
            logger.warning("[%s HOOK] safe_record_ledger failed: %s", self.id.upper(), e)

    def reset_state(self):
        self.pending_actions = []
        self.history = []
        self.state = AgentState.IDLE
        self.last_action = ""
        self.last_run = None
        self.last_run_id = None

    async def run(self, run_id: str) -> list[AgentAction]:
        self.state = AgentState.WORKING
        self.last_run_id = run_id

        # Run startup hooks
        self.resolve_context()
        try:
            self.verify_memory_scope()
        except ValueError as e:
            self.state = AgentState.ERROR
            self.last_action = str(e)
            logger.error("[%s RUN] Stopped due to memory verification failure: %s", self.id.upper(), e)
            raise

        self.load_recent_audit_context()
        self.append_task_start(run_id)

        violations = self._check_preconditions()
        if violations:
            self.state = AgentState.ERROR
            self.last_action = f"Invariante violada: {violations[0].invariant}"
            return []

        try:
            actions = await self.work()
            deduped = self._deduplicate(actions)
            self._check_postconditions(actions)

            for idx, a in enumerate(deduped):
                a.run_id = run_id
                raw = f"{a.agent_id}|{run_id}|{a.action_type}|{a.target}|{idx}"
                h = abs(hash(raw))
                a.action_id = f"{a.agent_id}_{run_id[:12]}_{h % 10**12:012d}"
                self.pending_actions.append(a)

            if deduped:
                self.state = AgentState.PENDING_REVIEW
            else:
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
        raise NotImplementedError

    def _check_preconditions(self) -> list[InvariantViolation]:
        return []

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        pass

    def _deduplicate(self, actions: list[AgentAction]) -> list[AgentAction]:
        existing = {a.dedup_key() for a in self.pending_actions}
        historical = {a.dedup_key() for a in self.history}
        all_seen = existing | historical
        return [a for a in actions if a.dedup_key() not in all_seen]

    def to_dict(self) -> dict:
        tools_list = sorted(
            k for k, v in self.contract.get("tools", {}).items() if v.get("permitted")
        )
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "state": self.state.value if hasattr(self.state, "value") else str(self.state),
            "last_action": self.last_action,
            "last_run": self.last_run,
            "last_run_id": self.last_run_id,
            "pending_count": len(self.pending_actions),
            "history_count": len(self.history),
            "contract_summary": {
                "tools": tools_list,
                "tools_count": len(tools_list),
                "invariant_count": len(self.contract.get("invariants", [])),
                "authority": self.contract.get("authority", "worker"),
                "memory_namespace": self.contract.get("memory", {}).get("namespace", "N/A"),
                "failure_modes": len(self.contract.get("failure_modes", [])),
                "escalation_rules": len(self.contract.get("escalation", [])),
                "tests": len(self.contract.get("tests", [])),
            },
        }

    def get_contract(self) -> dict:
        return self.contract

    def get_pending_actions(self) -> list[dict]:
        return [a.to_dict() for a in self.pending_actions]