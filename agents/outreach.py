from agents.base import BaseAgent
from contracts import AgentAction, ActionType, InvariantViolation


class OutreachAgent(BaseAgent):
    id = "outreach"
    name = "Outreach"
    icon = "✉️"
    description = "Genera borradores — NUNCA envía sin aprobación humana"
    never_sends = True
    needs_approval = True

    INVARIANT_NEVER_SENDS = "NUNCA ejecuta el envío. Solo prepara drafts. El humano autoriza."

    def __init__(self, config: dict):
        super().__init__(config)
        self.require_approval = config.get("agents", {}).get("outreach", {}).get("require_approval", True)

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": False},
                "browser": {"permitted": False, "notes": "el envío lo ejecuta el orquestador después de aprobación"},
                "email": {"permitted": False, "notes": "prohibido absolutamente"},
                "filesystem": {"permitted": True, "notes": "solo lectura"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "escritura, namespace `memory/outreach/*`"},
            },
            "context": ["run_id actual", "targets con contexto", "tono configurado", "require_approval (debe ser True)"],
            "memory": {
                "namespace": "memory/outreach/*",
                "can_remember": ["mensajes ya enviados (para no repetir)", "targets contactados recientemente"],
                "cannot_remember": ["contraseñas, tokens, datos sensibles"],
            },
            "invariants": [
                "NUNCA envía — solo prepara drafts (regla más importante)",
                "Si require_approval = False, no arranca (critical precondition)",
                "Mensaje no se modifica después de aprobado",
                "Trazabilidad completa (action_id único)",
                "Máximo 1 mensaje por target por día",
                "Toda acción tiene run_id y dedup_key",
            ],
            "failure_modes": [
                "require_approval en false: no arranca, error crítico",
                "Target sin datos suficientes: no genera draft, reporta",
            ],
            "escalation": [
                "require_approval desactivado: error al orquestador, no escala al humano",
                "Contenido sensible detectado: escala al CEO para revisión manual",
            ],
            "tests": [
                "import OK", "run genera borradores", "run_id obligatorio", "dedup funciona",
                "never_sends = True", "needs_approval = True",
                "precondition crítica si require_approval = False",
            ],
            "authority": "draft-only",
        }

    def _check_preconditions(self) -> list[InvariantViolation]:
        if not self.require_approval:
            return [InvariantViolation(
                agent_id=self.id, invariant="requiere_aprobacion",
                detail="require_approval está en false. Outreach nunca debe enviar sin aprobación.",
                severity="critical",
            )]
        return []

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        for a in actions:
            assert a.state == AgentState.PENDING_REVIEW.value, \
                f"Acción {a.action_id} no está en PENDING_REVIEW"

    async def work(self) -> list[AgentAction]:
        return self._prepare_outreach()

    def _prepare_outreach(self) -> list[AgentAction]:
        return [
            AgentAction(
                agent_id=self.id,
                action_type=ActionType.INMAIL.value,
                target="Carlos Méndez — CEO TechMex",
                reason="TechMex en expansión Serie B — oportunidad de alto score (92)",
                payload={
                    "subject": "Expansión TechMex — talento clave",
                    "message": (
                        "Hola Carlos,\n\n"
                        "Vi que TechMex está en un momento de expansión importante "
                        "con la Serie B. En Cerno hemos ayudado a "
                        "empresas en etapa similar a encontrar talento clave "
                        "para sostener ese crecimiento.\n\n"
                        "¿Te parece si agendamos 15 min la semana que viene?\n\n"
                        "Saludos,\nManu"
                    ),
                    "channel": "linkedin_inmail",
                    "requires_approval": True,
                },
                score=92,
            ),
            AgentAction(
                agent_id=self.id,
                action_type=ActionType.INMAIL.value,
                target="Ana López — HR Director FinTechMX",
                reason="Nueva Directora de Talento en FinTechMX — señal de contrataciones entrantes",
                payload={
                    "subject": "Talento para expansión FinTechMX",
                    "message": (
                        "Hola Ana,\n\n"
                        "Vi tu nuevo rol como Directora de Talento en FinTechMX. "
                        "Tenemos un pipeline de perfiles que podrían encajar "
                        "con la etapa de crecimiento que están viviendo.\n\n"
                        "¿Te interesaría ver algunos perfiles la próxima semana?\n\n"
                        "Saludos,\nManu"
                    ),
                    "channel": "linkedin_inmail",
                    "requires_approval": True,
                },
                score=87,
            ),
        ]


from contracts import AgentState
AgentState.PENDING_REVIEW  # ensure import
