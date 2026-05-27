from agents.base import BaseAgent
from contracts import AgentAction, ActionType


class TalentSourcingAgent(BaseAgent):
    id = "talent_sourcing"
    name = "Talent Sourcing"
    icon = "🎯"
    description = "Busca talento por rol, industria, seniority y país"
    read_only = True
    never_sends = True

    def __init__(self, config: dict):
        super().__init__(config)
        self.max_results = config.get("agents", {}).get("talent_sourcing", {}).get("max_results", 10)

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": True, "notes": "LinkedIn Search"},
                "browser": {"permitted": True, "notes": "solo lectura, sesión autenticada"},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "escritura, namespace `memory/talent_sourcing/*`"},
            },
            "context": ["run_id actual", "criterios de búsqueda (rol, ubicación)", "sesión de LinkedIn", "max_results"],
            "memory": {
                "namespace": "memory/talent_sourcing/*",
                "can_remember": ["candidatos ya vistos", "búsquedas recientes para evitar repetir"],
                "cannot_remember": ["datos fuera de su búsqueda", "decisiones de contratación"],
            },
            "invariants": [
                "Solo lectura: nunca escribe en LinkedIn",
                "No comparte datos fuera del sistema",
                "Respeto de tasa (delays 2-7s entre acciones)",
                "Cada candidato tiene ubicación",
                "Toda acción tiene run_id y dedup_key",
            ],
            "failure_modes": [
                "LinkedIn bloquea: rotar sesión, esperar, reintentar",
                "Sin sesión: cae a mock data",
                "Sin resultados: reportar 'no encontrados'",
            ],
            "escalation": [
                "Sin resultados después de 3 intentos → escalar al CEO",
                "LinkedIn pide verificación → escalar al humano",
            ],
            "tests": [
                "import OK", "run genera acciones válidas", "run_id obligatorio",
                "dedup funciona", "no viola tools prohibidas",
            ],
            "authority": "researcher",
        }

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        for a in actions:
            assert a.target, "Candidato sin nombre"
            loc = a.payload.get("location", "")
            assert loc, f"Candidato {a.target} sin ubicación"

    async def work(self) -> list[AgentAction]:
        candidates = self._search_linkedin_mock()
        return [
            AgentAction(
                agent_id=self.id,
                action_type=ActionType.CANDIDATE.value,
                target=c["name"],
                reason=f"{c['role']} en {c['company']} — {c.get('summary', '')[:60]}",
                payload={
                    "name": c["name"], "role": c["role"], "company": c["company"],
                    "location": c["location"], "linkedin_url": c.get("linkedin_url", ""),
                    "summary": c.get("summary", ""),
                },
                score=c.get("score", 70),
            )
            for c in candidates
        ]

    def _search_linkedin_mock(self) -> list[dict]:
        return [
            {"name": "María García", "role": "CTO", "company": "TechMex", "location": "CDMX", "score": 88, "summary": "Ex-Google, 12 años en tech lead. En transición."},
            {"name": "Pedro López", "role": "VP Engineering", "company": "FinTechMX", "location": "CDMX", "score": 85, "summary": "Ha escalado equipos de 5 a 50 personas."},
            {"name": "Ana Torres", "role": "HR Director", "company": "SoftCloud", "location": "Monterrey", "score": 82, "summary": "Especialista en hiring masivo LATAM."},
            {"name": "Luis Mendoza", "role": "Growth Lead", "company": "StartupMX", "location": "Guadalajara", "score": 79, "summary": "Ha lanzado 3 expansiones regionales."},
            {"name": "Carla Ruiz", "role": "CFO", "company": "MexVentures", "location": "CDMX", "score": 76, "summary": "Experiencia en startups Serie A y B."},
        ]
