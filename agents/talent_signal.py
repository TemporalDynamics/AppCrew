from agents.base import BaseAgent
from contracts import AgentAction, ActionType


class TalentSignalAgent(BaseAgent):
    id = "talent_signal"
    name = "Talent Signal"
    icon = "🔍"
    description = "Detecta señales humanas, narrativas y contextuales que un score tradicional no ve"
    read_only = True
    never_sends = True

    def __init__(self, config: dict):
        super().__init__(config)
        self._doctrine_keeper = None

    def bind_doctrine(self, keeper) -> None:
        self._doctrine_keeper = keeper

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": True, "notes": "solo lectura de perfiles públicos"},
                "browser": {"permitted": True, "notes": "solo lectura"},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "escritura, namespace `memory/talent_signal/*`"},
                "doctrine": {"permitted": True, "notes": "lectura de principios desde Doctrine Keeper"},
            },
            "context": ["run_id actual", "candidatos con score (desde Fit Scoring)", "doctrina de la firma (desde Doctrine Keeper)"],
            "memory": {
                "namespace": "memory/talent_signal/*",
                "can_remember": ["señales ya detectadas por candidato", "hipótesis previas"],
                "cannot_remember": ["datos personales sensibles", "decisiones de contratación"],
            },
            "invariants": [
                "Nunca diagnostica personalidad ni salud mental",
                "Nunca usa categorías sensibles",
                "Nunca descarta candidatos automáticamente",
                "Toda hipótesis ligada a evidencia observable del perfil",
                "Toda señal incluye pregunta de validación humana",
                "Nunca recomienda contratar o rechazar — solo informa y sugiere",
            ],
            "failure_modes": [
                "Sin candidatos para analizar: reportar 'no data'",
                "Doctrina no disponible: operar con defaults conservadores",
            ],
            "escalation": [
                "Señales de riesgo crítico → escalar para revisión humana",
                "Hipótesis sin evidencia suficiente → marcar como baja confianza",
            ],
            "tests": [
                "import OK", "run produce signals con hipótesis y preguntas",
                "no produce diagnósticos de personalidad",
                "no descarta candidatos automáticamente",
                "toda señal tiene evidencia y pregunta de validación",
            ],
            "authority": "analyst",
        }

    def _get_mock_candidates(self) -> list[dict]:
        return [
            {
                "name": "Luis Mendoza",
                "role": "Growth Lead",
                "trayectoria": "Expansión regional en 3 países, roles operativos y comerciales, perfil de LinkedIn poco cuantificado, sin logros numéricos visibles.",
                "seniority": "senior",
                "skills_score": 75,
                "experience_score": 70,
            },
            {
                "name": "Ana Torres",
                "role": "HR Director",
                "trayectoria": "10+ años en RH, cambios de industria cada 3 años, logros descriptivos sin métricas, perfil bien armado pero genérico.",
                "seniority": "director",
                "skills_score": 80,
                "experience_score": 85,
            },
            {
                "name": "Carlos Ruiz",
                "role": "CTO",
                "trayectoria": "CTO en 2 startups, salió antes de serie B ambas veces, cargo alto pero equipos chicos (< 5 personas), narrativa centrada en tecnología no en negocio.",
                "seniority": "c-level",
                "skills_score": 88,
                "experience_score": 85,
            },
        ]

    def _analyze_candidate(self, candidate: dict, principles: list[dict], signals: dict) -> AgentAction:
        name = candidate["name"]
        role = candidate.get("role", "—")
        trayectoria = candidate.get("trayectoria", "")
        principles_text = "; ".join(p["statement"] for p in principles[:3])

        # Mock analysis based on candidate data
        analysis = self._mock_analysis(name, trayectoria, principles, signals)

        return AgentAction(
            agent_id=self.id,
            action_type=ActionType.SIGNAL.value,
            target=f"{name} — {role}",
            reason=f"Señales: {analysis['signal_count']} potencial, {analysis['risk_count']} riesgo. Hipótesis: {analysis['hypothesis']}",
            payload={
                "candidate_name": name,
                "candidate_role": role,
                "trayectoria": trayectoria,
                "observable_signals": analysis["observable_signals"],
                "hypothesis": analysis["hypothesis"],
                "risks": analysis["risks"],
                "validation_questions": analysis["validation_questions"],
                "recommendation": analysis["recommendation"],
                "confidence": analysis["confidence"],
                "principles_applied": [p["id"] for p in principles[:3]],
            },
            score=analysis.get("score", 70),
        )

    def _mock_analysis(self, name: str, trayectoria: str, principles: list[dict], signals: dict) -> dict:
        analyses = {
            "Luis Mendoza": {
                "observable_signals": [
                    "Expansión regional en 3 países muestra capacidad de adaptación",
                    "Perfil sin logros cuantificados — posible subcomunicación",
                    "Roles operativos y comerciales combinados",
                ],
                "hypothesis": "Perfil con alta capacidad práctica pero baja autopresentación. Puede estar subposicionado respecto a su impacto real.",
                "risks": [
                    "Podría ser subvalorado si se evalúa solo por LinkedIn",
                    "Sin métricas visibles, difícil validar alcance real",
                ],
                "validation_questions": [
                    "¿Qué mercados abriste y cuál fue el más complejo?",
                    "¿Qué decisiones tomabas sin supervisión?",
                    "¿Cómo median el éxito de tu gestión?",
                ],
                "recommendation": "No descartar. Requiere entrevista exploratoria para validar alcance real.",
                "confidence": "media-alta",
                "signal_count": 3,
                "risk_count": 1,
                "score": 78,
            },
            "Ana Torres": {
                "observable_signals": [
                    "Trayectoria diversa en RH con cambios de industria",
                    "Perfil bien armado pero genérico — logros sin cuantificar",
                    "Narrativa consistente que no cambia entre roles",
                ],
                "hypothesis": "Perfil sólido pero con narrativa estandarizada. Puede estar ocultando profundidad tras un storytelling genérico.",
                "risks": [
                    "Riesgo de que sea más generalista que especialista",
                    "Cambios frecuentes de industria sin hilo conductor claro",
                ],
                "validation_questions": [
                    "¿Cuál fue el proyecto de RH más complejo que lideraste?",
                    "¿Cómo mediste el impacto de una iniciativa de talento?",
                    "¿Qué aprendiste de cada industria y cómo lo aplicaste?",
                ],
                "recommendation": "Validar profundidad técnica en entrevista. No descartar por formato genérico.",
                "confidence": "media",
                "signal_count": 2,
                "risk_count": 1,
                "score": 72,
            },
        }

        default = {
            "observable_signals": [
                f"Trayectoria en {trayectoria[:50]}...",
                "Perfil requiere análisis más profundo",
            ],
            "hypothesis": "Señales mixtas. Requiere más datos para formular hipótesis sólida.",
            "risks": [
                "Información insuficiente para evaluación completa",
            ],
            "validation_questions": [
                "¿Cuál fue tu mayor logro medible en tu rol actual?",
                "¿Qué problemas resolviste que otros no pudieron?",
            ],
            "recommendation": "Requiere más información antes de determinar.",
            "confidence": "baja",
            "signal_count": 1,
            "risk_count": 0,
            "score": 60,
        }

        return analyses.get(name, default)

    async def work(self) -> list[AgentAction]:
        # Load doctrine principles for this agent
        principles = []
        signals = {"potential": [], "risk": []}
        if self._doctrine_keeper:
            principles = self._doctrine_keeper.principles_for_agent(self.id)
            signals = self._doctrine_keeper.get_signals()

        candidates = self._get_mock_candidates()
        actions = []
        for c in candidates:
            action = self._analyze_candidate(c, principles, signals)
            actions.append(action)

        return actions
