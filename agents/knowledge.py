from pathlib import Path

from agents.base import BaseAgent
from contracts import AgentAction, ActionType, InvariantViolation


class KnowledgeAgent(BaseAgent):
    id = "knowledge"
    name = "Knowledge"
    icon = "🗂️"
    description = "Organiza memoria operativa — solo crea estructura, nunca elimina"
    read_only = False
    never_sends = True

    def __init__(self, config: dict):
        super().__init__(config)
        self.data_dir = Path("data/knowledge")
        self.data_dir.mkdir(parents=True, exist_ok=True)

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": False},
                "browser": {"permitted": False},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "escritura controlada, solo crear carpetas, nunca borrar"},
                "context7": {"permitted": False},
                "memory": {"permitted": False},
            },
            "context": ["run_id actual", "lista de cuentas", "estructura de carpetas"],
            "memory": {
                "namespace": "N/A (idempotente, no necesita memoria)",
                "can_remember": [],
                "cannot_remember": [],
            },
            "invariants": [
                "Nunca elimina datos",
                "Estructura uniforme (todas las cuentas igual)",
                "Idempotente (N ejecuciones = 1 ejecución)",
                "Sin contenido generado (solo carpetas)",
                "Toda acción tiene run_id y dedup_key",
            ],
            "failure_modes": [
                "Permisos de filesystem: error, reporta",
                "Disco lleno: error, escala",
            ],
            "escalation": [
                "Error de permisos: escala al CEO",
                "Las cuentas no se pre-crean automáticamente si hay error",
            ],
            "tests": [
                "import OK", "run genera acciones", "carpetas existen después del run",
                "run_id obligatorio", "idempotente (segundo run no duplica)",
            ],
            "authority": "memory",
        }

    def _check_preconditions(self) -> list[InvariantViolation]:
        return []

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        for a in actions:
            path = Path(a.payload.get("path", ""))
            assert path.is_dir(), f"Directorio no creado: {path}"

    async def work(self) -> list[AgentAction]:
        folders = [
            "01_Mercado", "02_Oportunidades", "03_Candidatos",
            "04_Contactos_y_Seguimiento", "05_Insights_Semanales", "06_Riesgos_y_Bloqueos",
        ]
        accounts = ["TechMex", "FinTechMX", "SoftCloud_LATAM"]
        actions = []

        for account in accounts:
            account_dir = self.data_dir / account
            account_dir.mkdir(exist_ok=True)
            created = []
            for folder in folders:
                fp = account_dir / folder
                if not fp.exists():
                    fp.mkdir()
                    created.append(folder)

            actions.append(AgentAction(
                agent_id=self.id,
                action_type=ActionType.FOLDER_STRUCTURE.value,
                target=account,
                reason=f"{len(created)} carpetas creadas de {len(folders)}",
                payload={
                    "account": account,
                    "folders": folders,
                    "created": created,
                    "path": str(account_dir),
                },
                score=100,
            ))

        return actions
