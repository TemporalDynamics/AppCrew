from agents.base import BaseAgent
from contracts import AgentAction, ActionType


class EvidenceAgent(BaseAgent):
    id = "evidence"
    name = "Evidence"
    icon = "📎"
    description = "Genera audit trail de qué keywords dispararon qué señales"
    read_only = True
    never_sends = True

    def _init_contract(self):
        self.contract = {
            "authority": "auditor",
            "tools": {},
            "invariants": [
                "No modifica datos — solo reporta",
                "Cada señal debe tener keyword que la originó",
            ],
            "context": ["run_id actual", "candidatos con signal_evidence en payload"],
        }

    async def work(self) -> list[AgentAction]:
        actions = []
        for action in self.pending_actions:
            if action.action_type not in ("candidate", "signal"):
                continue
            payload = action.payload or {}
            signal_evidence = payload.get("signal_evidence", {})
            if not signal_evidence:
                continue
            name = payload.get("name", action.target)
            lines = []
            for signal_name, keyword in signal_evidence.items():
                lines.append(f"  • {signal_name}: {keyword}")
            audit = "\n".join(lines)
            actions.append(AgentAction(
                agent_id=self.id,
                action_type=ActionType.NOTE.value,
                target=f"evidence:{name}",
                reason=f"{len(signal_evidence)} señal(es) registrada(s) para {name}",
                payload={
                    "candidate": name,
                    "evidence_count": len(signal_evidence),
                    "audit_trail": audit,
                    "raw_evidence": signal_evidence,
                },
                score=0,
            ))
        return actions
