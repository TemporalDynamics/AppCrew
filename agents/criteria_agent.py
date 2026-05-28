import yaml
from pathlib import Path

from agents.base import BaseAgent
from contracts import AgentAction, ActionType


ROOT = Path(__file__).resolve().parent.parent
CRITERIA_PATH = ROOT / "data" / "demo_rodri_criteria.yaml"


class CriteriaAgent(BaseAgent):
    id = "criteria"
    name = "Criteria"
    icon = "📋"
    description = "Lee y expone los criterios de búsqueda activos para cada run"
    read_only = True
    never_sends = True

    def _init_contract(self):
        self.contract = {
            "authority": "reader",
            "tools": {"filesystem": {"permitted": True, "notes": "solo lectura de criteria file"}},
            "invariants": ["Nunca modifica el archivo de criterios"],
            "context": ["run_id actual", "ruta del criteria file: data/demo_rodri_criteria.yaml"],
        }

    async def work(self) -> list[AgentAction]:
        try:
            with open(CRITERIA_PATH) as f:
                criteria = yaml.safe_load(f)
        except Exception as e:
            return [AgentAction(
                agent_id=self.id,
                action_type=ActionType.NOTE.value,
                target="criteria_load_error",
                reason=f"No se pudo cargar criteria: {e}",
                payload={"error": str(e)},
                score=0,
            )]

        return [AgentAction(
            agent_id=self.id,
            action_type=ActionType.NOTE.value,
            target="criteria_snapshot",
            reason=f"Criterios activos: {criteria.get('role_target', '—')} en {', '.join(criteria.get('markets', []))}",
            payload={
                "role_target": criteria.get("role_target", ""),
                "markets": criteria.get("markets", []),
                "industries": criteria.get("industries", []),
                "positive_signals": criteria.get("positive_signals", []),
                "negative_signals": criteria.get("negative_signals", []),
                "preferred_background": criteria.get("preferred_background", ""),
                "outreach_tone": criteria.get("outreach_tone", ""),
                "hard_filters": criteria.get("hard_filters", []),
                "human_approval_required": criteria.get("human_approval_required", True),
            },
            score=0,
        )]
