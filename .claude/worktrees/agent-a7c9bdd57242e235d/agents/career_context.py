from agents.base import BaseAgent
from contracts import AgentAction, ActionType
from core.tools.firecrawl_client import FirecrawlClient


class CareerContextAgent(BaseAgent):
    id = "career_context"
    name = "Career Context"
    icon = "🏢"
    description = "Reconstruye el contexto público de las empresas donde trabajó un candidato para interpretar mejor su trayectoria"
    read_only = True
    never_sends = True

    def __init__(self, config: dict):
        super().__init__(config)
        self._doctrine_keeper = None
        firecrawl_key = config.get("firecrawl", {}).get("api_key", "")
        self._firecrawl = FirecrawlClient(firecrawl_key)
        self._fallback_used = True
        self._last_companies = []
        self._last_risk = "baja"

    def bind_doctrine(self, keeper) -> None:
        self._doctrine_keeper = keeper

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": True, "notes": "búsqueda de noticias y eventos públicos"},
                "browser": {"permitted": True, "notes": "solo lectura, navegar fuentes públicas"},
                "crunchbase": {"permitted": True, "notes": "solo lectura, datos de inversión/liderazgo"},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "escritura, namespace `memory/career_context/*`"},
                "doctrine": {"permitted": True, "notes": "lectura de principios y límites desde Doctrine Keeper"},
            },
            "context": ["run_id actual", "perfil del candidato (empresas, cargos, fechas)", "rol y seniority objetivo", "doctrina de la firma (límites éticos sobre inferencias)"],
            "memory": {
                "namespace": "memory/career_context/*",
                "can_remember": ["contexto de empresa ya consultado", "eventos previamente confirmados", "fuentes validadas como confiables"],
                "cannot_remember": ["información no pública", "datos personales del candidato fuera del contexto de empresa", "rumores o fuentes no verificadas"],
            },
            "invariants": [
                "Nunca atribuye eventos de empresa al candidato sin evidencia directa",
                "Nunca penaliza por industria, momento de empresa o crisis externa",
                "Nunca usa rumores ni fuentes no verificables",
                "Toda acción incluye risk_of_noise con nivel de confianza explícito",
                "Toda señal incluye validation_questions para separar contexto de contribución",
                "Toda acción lista sources consultadas",
                "Nunca recomienda contratar, descartar ni priorizar candidatos",
            ],
            "failure_modes": [
                "Empresa sin presencia pública: reportar 'sin datos'",
                "Fuentes contradictorias: reportar ambas versiones",
            ],
            "escalation": [
                "Evidencia de crisis severa durante permanencia del candidato → escalar para revisión humana",
                "Más de 2 empresas sin contexto recuperable → escalar para criterio alternativo",
            ],
            "tests": [
                "import OK", "run produce context_signal con timeline y señales",
                "toda acción tiene risk_of_noise",
                "toda acción tiene validation_questions",
                "no produce juicios sobre el candidato",
                "empresa sin fuentes reporta 'sin datos'",
            ],
            "authority": "analyst",
        }

    def _get_mock_candidates_with_companies(self) -> list[dict]:
        return [
            {
                "name": "Luis Mendoza",
                "role": "Growth Lead",
                "search_role": "VP Growth",
                "seniority": "senior",
                "industry": "fintech",
                "companies": [
                    {"company": "TechMex", "role": "Growth Lead", "start_date": "2021", "end_date": "2024", "is_current": False},
                    {"company": "FinTechMX", "role": "Sr. Analyst", "start_date": "2019", "end_date": "2021", "is_current": False},
                ],
            },
            {
                "name": "Ana Torres",
                "role": "HR Director",
                "search_role": "CHRO",
                "seniority": "director",
                "industry": "technology",
                "companies": [
                    {"company": "SoftCloud_LATAM", "role": "HR Director", "start_date": "2020", "end_date": "2024", "is_current": True},
                    {"company": "TechMex", "role": "HRBP Sr.", "start_date": "2017", "end_date": "2020", "is_current": False},
                ],
            },
            {
                "name": "Carlos Ruiz",
                "role": "CTO",
                "search_role": "CTO / VP Engineering",
                "seniority": "c-level",
                "industry": "fintech",
                "companies": [
                    {"company": "FinTechMX", "role": "CTO", "start_date": "2022", "end_date": "2024", "is_current": False},
                    {"company": "Nubank", "role": "Engineering Manager", "start_date": "2019", "end_date": "2022", "is_current": False},
                ],
            },
        ]

    async def _analyze_candidate(self, candidate: dict, limits: list[str]) -> AgentAction:
        name = candidate["name"]
        role = candidate.get("role", "—")
        search_role = candidate.get("search_role", role)
        companies_data = candidate.get("companies", [])

        companies_analyzed = []
        total_confidence = "alta"
        companies_without_data = 0
        all_sources = set()
        any_real = False

        for c in companies_data:
            cname = c["company"]
            ctx = await self._firecrawl.get_company_context(cname)
            if ctx is None:
                companies_without_data += 1
                companies_analyzed.append({
                    "company": cname,
                    "role": c["role"],
                    "period": f"{c['start_date']}–{c['end_date']}",
                    "status": "sin fuentes públicas suficientes",
                    "timeline": [],
                    "signals": [],
                    "confidence": "baja",
                    "source_type": "mock_fallback",
                })
                continue

            source_type = ctx.get("source_type", "mock_fallback")
            if source_type == "real":
                any_real = True
            for ev in ctx.get("timeline", []):
                src = ev.get("source", "")
                if src:
                    all_sources.add(src)

            companies_analyzed.append({
                "company": cname,
                "role": c["role"],
                "period": f"{c['start_date']}–{c['end_date']}",
                "status": "contexto recuperado",
                "timeline": ctx.get("timeline", []),
                "signals": ctx.get("signals", []),
                "confidence": ctx.get("confidence", "media"),
                "source_type": source_type,
            })

        self._fallback_used = not any_real
        self._last_companies = companies_analyzed

        if companies_without_data > 0:
            total_confidence = "media"

        self._last_risk = (
            "baja" if total_confidence == "alta" and companies_without_data == 0
            else "media" if total_confidence == "media"
            else "alta"
        )

        validation_questions = []
        for c in companies_analyzed:
            if c["signals"]:
                validation_questions.append(
                    f"Durante tu etapa en {c['company']} ({c['period']}), "
                    f"la empresa atravesó: {'; '.join(c['signals'][:2])}. "
                    f"¿Qué parte de ese contexto te tocó liderar o gestionar directamente?"
                )
                validation_questions.append(
                    f"En {c['company']}, ¿hubo alguna decisión crítica que tomaras "
                    f"durante ese periodo sin supervisión directa?"
                )

        context_summary = "; ".join(
            f"{c['company']}: {', '.join(c['signals'][:2]) if c['signals'] else 'sin datos'}"
            for c in companies_analyzed
        )

        hypothesis = (
            f"El candidato estuvo en {len(companies_analyzed)} empresas durante periodos con "
            f"contextos públicos relevantes. "
        )
        for c in companies_analyzed:
            if c["signals"]:
                hypothesis += (
                    f"En {c['company']} ({c['period']}) se detectaron: "
                    f"{'; '.join(c['signals'][:2])}. "
                )
        hypothesis += (
            f"Estos contextos pueden haber influido en su experiencia, "
            f"pero no hay evidencia pública de su rol directo en esos eventos. "
            f"Validation_questions permitirán separar contexto de contribución real."
        )

        return AgentAction(
            agent_id=self.id,
            action_type=ActionType.CONTEXT_SIGNAL.value,
            target=f"{name} — {role}",
            reason=f"Contexto: {len(companies_analyzed)} empresas analizadas. "
                   f"Confianza: {total_confidence}. Señales: {context_summary[:100]}",
            payload={
                "candidate_name": name,
                "candidate_role": role,
                "search_role": search_role,
                "seniority": candidate.get("seniority", ""),
                "industry": candidate.get("industry", ""),
                "companies_analyzed": companies_analyzed,
                "hypothesis": hypothesis.strip(),
                "risk_of_noise": self._last_risk,
                "validation_questions": validation_questions,
                "sources": sorted(all_sources) if all_sources else ["sin fuentes disponibles"],
                "companies_without_data": companies_without_data,
                "total_companies": len(companies_data),
                "source_type": "real" if any_real else "mock_fallback",
            },
            score=85 if total_confidence == "alta" else 70 if total_confidence == "media" else 50,
        )

    async def work(self) -> list[AgentAction]:
        limits = []
        if self._doctrine_keeper:
            limits = self._doctrine_keeper.get_limits()

        candidates = self._get_mock_candidates_with_companies()
        actions = []
        for c in candidates:
            action = await self._analyze_candidate(c, limits)
            actions.append(action)

        return actions
