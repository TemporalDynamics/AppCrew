from agents.base import BaseAgent
from contracts import AgentAction, ActionType


class IntakeAgent(BaseAgent):
    id = "intake"
    name = "Intake"
    icon = "📥"
    description = "Valida y normaliza candidatos entrantes antes del pipeline"
    read_only = True
    never_sends = True

    def _init_contract(self):
        self.contract = {
            "authority": "validator",
            "tools": {},
            "invariants": ["Solo acepta candidatos con name y source_url"],
            "context": ["run_id actual", "candidatos raw desde sourcing"],
        }

    async def work(self) -> list[AgentAction]:
        return []
