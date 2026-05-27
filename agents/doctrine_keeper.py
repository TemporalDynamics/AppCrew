from pathlib import Path

from agents.base import BaseAgent
from contracts import AgentAction, ActionType

DOCTRINE_PATH = Path(__file__).resolve().parent.parent / "doctrine" / "philosophy.yaml"


class DoctrineKeeperAgent(BaseAgent):
    id = "doctrine_keeper"
    name = "Doctrine Keeper"
    icon = "📜"
    description = "Custodia la filosofía de talento de la firma. No evalúa candidatos — solo mantiene el criterio experto."
    read_only = True
    never_sends = True

    def __init__(self, config: dict):
        super().__init__(config)
        self.doctrine = self._load_doctrine()

    def _load_doctrine(self) -> dict:
        try:
            import yaml
            if DOCTRINE_PATH.exists():
                with open(DOCTRINE_PATH) as f:
                    return yaml.safe_load(f) or {}
        except Exception:
            pass
        return {
            "firm": "Global Executive",
            "version": 0,
            "principles": [],
            "signals": {"potential": [], "risk": []},
            "limits": [],
            "onboarding_philosophy": [],
        }

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": False},
                "browser": {"permitted": False},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura de doctrine/philosophy.yaml"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "escritura, namespace `memory/doctrine/*`"},
            },
            "context": ["run_id actual", "doctrine/philosophy.yaml"],
            "memory": {
                "namespace": "memory/doctrine/*",
                "can_remember": ["principios activos", "contradicciones detectadas"],
                "cannot_remember": ["datos de candidatos", "información de clientes"],
            },
            "invariants": [
                "Nunca modifica doctrina sin aprobación humana",
                "No expone doctrina sin autenticación",
                "Toda respuesta incluye el principio exacto que aplica",
                "No generaliza doctrina entre firmas",
            ],
            "failure_modes": [
                "Doctrina no disponible: reportar 'modo conservador'",
                "Archivo YAML corrupto: recovery a defaults",
            ],
            "escalation": [
                "Sin doctrina cargada → escalar para carga inicial",
                "Contradicción entre decisión y doctrina → escalar",
            ],
            "tests": [
                "import OK", "carga doctrina desde YAML", "no produce acciones de talento",
                "fallback a defaults si YAML no existe",
            ],
            "authority": "custodian",
        }

    def get_principle(self, principle_id: str) -> dict | None:
        for p in self.doctrine.get("principles", []):
            if p.get("id") == principle_id:
                return p
        return None

    def principles_for_agent(self, agent_id: str) -> list[dict]:
        return [p for p in self.doctrine.get("principles", []) if agent_id in p.get("applies_to", [])]

    def get_signals(self) -> dict:
        return self.doctrine.get("signals", {"potential": [], "risk": []})

    def get_limits(self) -> list[str]:
        return self.doctrine.get("limits", [])

    def get_onboarding_philosophy(self) -> list[str]:
        return self.doctrine.get("onboarding_philosophy", [])

    async def work(self) -> list[AgentAction]:
        principles_count = len(self.doctrine.get("principles", []))
        return [
            AgentAction(
                agent_id=self.id,
                action_type=ActionType.DOCTRINE_SNAPSHOT.value,
                target="all",
                reason=f"{principles_count} principios activos, {len(self.get_signals().get('potential', []))} señales de potencial, {len(self.get_limits())} límites",
                payload={
                    "firm": self.doctrine.get("firm", ""),
                    "version": self.doctrine.get("version", 0),
                    "principles_count": principles_count,
                    "signals_potential_count": len(self.get_signals().get("potential", [])),
                    "signals_risk_count": len(self.get_signals().get("risk", [])),
                    "limits_count": len(self.get_limits()),
                },
                score=100,
            )
        ]
