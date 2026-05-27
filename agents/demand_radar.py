from agents.base import BaseAgent
from contracts import AgentAction, ActionType, InvariantViolation
from core.tools.firecrawl_client import FirecrawlClient
from core.tools.search_client import SearchClient


class DemandRadarAgent(BaseAgent):
    id = "demand_radar"
    name = "Demand Radar"
    icon = "🛰️"
    description = "Detecta empresas con señales de contratación futura"
    read_only = True
    never_sends = True

    def __init__(self, config: dict):
        super().__init__(config)
        self.sources = config.get("agents", {}).get("demand_radar", {}).get("sources", [])
        firecrawl_key = config.get("firecrawl", {}).get("api_key", "")
        search_key = config.get("search", {}).get("api_key", "")
        self._firecrawl = FirecrawlClient(firecrawl_key)
        self._search = SearchClient(search_key)
        self._source_type = "mock_fallback"
        self.invariants = [
            {"name": "solo_lectura", "rule": "Nunca escribe en LinkedIn ni contacta empresas"},
            {"name": "toda_oportunidad_tiene_score", "rule": "Cada oportunidad tiene score 0-100"},
            {"name": "deduplicacion_empresa", "rule": "No duplicar empresa en mismo ciclo"},
        ]

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": True, "notes": "brave search + firecrawl"},
                "browser": {"permitted": True, "notes": "solo lectura"},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "escritura, namespace `memory/demand_radar/*`"},
            },
            "context": ["run_id actual", "fuentes configuradas", "API key de Firecrawl (opcional)", "API key de Search (opcional)", "región de interés (desde CEO)"],
            "memory": {
                "namespace": "memory/demand_radar/*",
                "can_remember": ["empresas ya vistas (para no repetir)", "fuentes confiables / no confiables"],
                "cannot_remember": ["datos de candidatos (no es su dominio)", "decisiones de aprobación humanas"],
            },
            "invariants": [
                "Solo lectura: nunca escribe en LinkedIn ni contacta empresas",
                "Toda oportunidad tiene score entre 0-100",
                "Deduplicación por empresa en mismo ciclo",
                "Toda acción tiene source_type (real | mock_fallback)",
                "Toda acción tiene run_id",
                "Toda acción tiene dedup_key (agent_id + action_type + target)",
            ],
            "failure_modes": [
                "Search API sin key: cae a mock",
                "Firecrawl sin key: usa solo Search + mock",
                "Sin fuentes configuradas: warning, usa mock",
            ],
            "escalation": [
                "Score bajo (< 50): incluir en reporte pero no forzar revisión",
                "Contradicción entre fuentes: marcar como 'pendiente de verificación'",
            ],
            "tests": [
                "import OK", "run genera acciones válidas", "run_id obligatorio",
                "dedup funciona", "source_type siempre presente",
            ],
            "authority": "scanner",
        }

    def _check_preconditions(self) -> list[InvariantViolation]:
        v = []
        if not self.sources:
            v.append(InvariantViolation(
                agent_id=self.id, invariant="fuentes_configuradas",
                detail="No hay fuentes configuradas en config.yaml",
                severity="warning",
            ))
        return v

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        companies = set()
        for a in actions:
            assert 0 <= a.score <= 100, f"Score fuera de rango: {a.score}"
            company = a.payload.get("company", "")
            assert company not in companies, f"Empresa duplicada: {company}"
            companies.add(company)
            assert a.payload.get("source_type", "") in ("real", "mock_fallback"), \
                f"source_type inválido: {a.payload.get('source_type')}"

    async def work(self) -> list[AgentAction]:
        has_real_source = self._firecrawl.is_real_available or self._search.is_real_available
        self._source_type = "real" if has_real_source else "mock_fallback"

        opportunities = await self._pipeline_search_scrape()

        if not opportunities:
            opportunities = self._firecrawl._mock_opportunities()

        return [
            AgentAction(
                agent_id=self.id,
                action_type=ActionType.OPPORTUNITY.value,
                target=opp["company"],
                reason=opp["signal"],
                payload={
                    "company": opp["company"],
                    "signal": opp["signal"],
                    "source": opp.get("source", opp.get("source_type", self._source_type)),
                    "source_type": opp.get("source_type", self._source_type),
                    "detail": opp["detail"],
                    "url": opp.get("url", ""),
                    "confidence": opp.get("confidence", "media"),
                },
                score=opp.get("score", 70),
            )
            for opp in opportunities
        ]

    async def _pipeline_search_scrape(self) -> list[dict]:
        results = await self._search.search("empresas contratando talento expansión México LATAM 2026", count=10)
        if not results:
            return []

        opportunities = []
        for r in results[:5]:
            company = r.get("title", "Unknown").split(" - ")[0].split(":")[0][:60]
            url = r.get("url", "")
            detail = r.get("description", "")[:200]

            scraped = None
            if url and self._firecrawl.is_real_available:
                scraped = await self._firecrawl.scrape_url(url)

            opportunities.append({
                "company": company,
                "signal": "señal de mercado detectada",
                "source": "brave_search" if not scraped else "firecrawl",
                "source_type": "real",
                "detail": detail,
                "url": url,
                "score": 75,
                "confidence": "media",
            })

        return opportunities
