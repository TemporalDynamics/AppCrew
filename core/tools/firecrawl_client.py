from __future__ import annotations

from typing import Any

MOCK_COMPANIES = [
    {
        "company": "TechMex",
        "signal": "Ronda Serie B por $12M — expansión de equipo",
        "source": "crunchbase",
        "source_type": "mock_fallback",
        "detail": "TechMex anunció cierre de Serie B. Buscan CTO y 5 ingenieros senior.",
        "url": "",
        "score": 92,
        "confidence": "alta",
    },
    {
        "company": "FinTechMX",
        "signal": "Nuevo head de RH — señal de crecimiento",
        "source": "linkedin",
        "source_type": "mock_fallback",
        "detail": "FinTechMX acaba de contratar Directora de Talento. Históricamente precede contrataciones masivas.",
        "url": "",
        "score": 85,
        "confidence": "alta",
    },
    {
        "company": "SoftCloud LATAM",
        "signal": "Expansión a 3 nuevos mercados",
        "source": "google_news",
        "source_type": "mock_fallback",
        "detail": "SoftCloud abre operaciones en Colombia, Perú y Chile.",
        "url": "",
        "score": 78,
        "confidence": "media",
    },
]

MOCK_COMPANY_CONTEXT: dict[str, dict] = {
    "TechMex": {
        "timeline": [
            {"year": "2018", "event": "Fundación", "source": "Crunchbase"},
            {"year": "2020", "event": "Serie A — $5M liderado por Kaszek Ventures", "source": "Crunchbase"},
            {"year": "2021", "event": "Serie B — $15M, expansión a 3 países", "source": "Crunchbase"},
            {"year": "2022", "event": "Apertura operaciones en Colombia y Perú", "source": "Prensa"},
            {"year": "2023", "event": "Cambio de CEO — fundador pasa a chairman", "source": "LinkedIn News"},
            {"year": "2024", "event": "Recorte del 15% del equipo, consolidación regional", "source": "Prensa"},
        ],
        "signals": ["crecimiento acelerado 2020-2022", "cambio de liderazgo 2023", "consolidación con recorte 2024"],
        "confidence": "alta",
        "source_type": "mock_fallback",
    },
    "FinTechMX": {
        "timeline": [
            {"year": "2019", "event": "Fundación, equipo fundador de 4 personas", "source": "Crunchbase"},
            {"year": "2021", "event": "Seed round — $2M", "source": "Crunchbase"},
            {"year": "2022", "event": "Serie A — $10M liderado por monashees", "source": "Crunchbase"},
            {"year": "2023", "event": "Reestructuración interna, cambio de CTO", "source": "LinkedIn News"},
            {"year": "2024", "event": "Adquirida por vertical de banco regional", "source": "Prensa"},
        ],
        "signals": ["startup en fase de escalamiento", "reestructuración técnica 2023", "salida por adquisición 2024"],
        "confidence": "alta",
        "source_type": "mock_fallback",
    },
    "SoftCloud_LATAM": {
        "timeline": [
            {"year": "2015", "event": "Fundación", "source": "Crunchbase"},
            {"year": "2018", "event": "Serie B — $20M", "source": "Crunchbase"},
            {"year": "2020", "event": "Expansión regional a 5 países LATAM", "source": "Prensa"},
            {"year": "2022", "event": "IPO en BIVA — valoración $400M", "source": "Prensa"},
            {"year": "2023", "event": "Crisis de retención, rotación del 30% en equipos técnicos", "source": "Prensa / Glassdoor"},
        ],
        "signals": ["crecimiento sostenido pre-IPO", "salida a bolsa 2022", "crisis de retención post-IPO"],
        "confidence": "alta",
        "source_type": "mock_fallback",
    },
    "Nubank": {
        "timeline": [
            {"year": "2013", "event": "Fundación en Brasil", "source": "Crunchbase"},
            {"year": "2019", "event": "Serie F — $400M, valoración $10B", "source": "Crunchbase"},
            {"year": "2021", "event": "IPO en NYSE — valoración $45B", "source": "Prensa"},
            {"year": "2022", "event": "Expansión a Colombia y México acelerada", "source": "Prensa"},
            {"year": "2023", "event": "Primer trimestre rentable como público", "source": "Prensa"},
            {"year": "2024", "event": "Nuevos productos: crypto, cuentas de alto rendimiento", "source": "Prensa"},
        ],
        "signals": ["crecimiento explosivo 2019-2021", "madurez como empresa pública 2022+", "diversificación de producto"],
        "confidence": "alta",
        "source_type": "mock_fallback",
    },
}


class FirecrawlClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._real_available = bool(api_key)
        self._app = None

    @property
    def is_real_available(self) -> bool:
        return self._real_available

    async def _get_app(self):
        if self._app is None and self._real_available:
            from firecrawl import AsyncFirecrawlApp
            self._app = AsyncFirecrawlApp(api_key=self.api_key)
        return self._app

    async def scan_opportunities(self, query: str = "", limit: int = 5) -> list[dict]:
        if not self._real_available:
            return self._mock_opportunities()

        try:
            return await self._real_scan(query, limit)
        except Exception:
            return self._mock_opportunities()

    async def get_company_context(self, company_name: str) -> dict | None:
        mock = self._mock_company_context(company_name)

        if not self._real_available:
            return mock

        try:
            real = await self._real_company_context(company_name)
            if real and real.get("timeline"):
                return real
        except Exception:
            pass

        return mock

    async def test_connection(self) -> dict:
        if not self._real_available:
            return {"status": "mock", "message": "API key no configurada, usando fallback mock"}
        try:
            app = await self._get_app()
            result = await app.search(query="test", limit=1)
            items = []
            if hasattr(result, "web") and result.web:
                items = result.web
            elif isinstance(result, dict):
                web_data = result.get("web") or result.get("data") or []
                items = web_data if isinstance(web_data, list) else []
            if items:
                return {"status": "ok", "message": "Firecrawl conectado correctamente"}
            return {"status": "ok", "message": "Firecrawl conectado, sin resultados"}
        except Exception as e:
            return {"status": "error", "message": str(e)}

    async def scrape_url(self, url: str) -> dict | None:
        if not self._real_available:
            return None
        try:
            app = await self._get_app()
            result = await app.scrape(url)
            if hasattr(result, "model_dump"):
                return result.model_dump()
            if isinstance(result, dict):
                return result
            return None
        except Exception:
            return None

    async def _extract_items(self, result) -> list:
        if hasattr(result, "web") and result.web:
            return result.web
        if hasattr(result, "data") and result.data:
            return result.data
        if isinstance(result, dict):
            for key in ("web", "news", "data"):
                items = result.get(key, [])
                if items and isinstance(items, list):
                    return items
        return []

    def _item_val(self, item, key: str, default: str = "") -> str:
        if hasattr(item, key):
            return getattr(item, key) or default
        if isinstance(item, dict):
            return item.get(key, default)
        return default

    async def _real_scan(self, query: str, limit: int) -> list[dict]:
        app = await self._get_app()
        result = await app.search(query=query or "empresas contratando talento expansión México LATAM 2026", limit=limit)
        items = await self._extract_items(result)
        ops = []
        for item in items:
            title = self._item_val(item, "title", "Unknown")
            desc = self._item_val(item, "description", "")
            url = self._item_val(item, "url", "")
            ops.append({
                "company": title.split(" - ")[0][:60],
                "signal": "expansión / contratación",
                "source": "firecrawl",
                "source_type": "real",
                "detail": desc[:200],
                "url": url,
                "score": 75,
                "confidence": "media",
            })
        return ops if ops else self._mock_opportunities()

    async def _real_company_context(self, company_name: str) -> dict | None:
        app = await self._get_app()
        result = await app.search(query=f"{company_name} empresa historia noticias 2024 2025", limit=5)
        items = await self._extract_items(result)
        if not items:
            return None
        timeline = []
        for item in items[:5]:
            title = self._item_val(item, "title", "")
            desc = self._item_val(item, "description", "")
            url = self._item_val(item, "url", "")
            timeline.append({
                "year": title[:4],
                "event": desc[:150],
                "source": url,
            })
        return {
            "timeline": timeline,
            "signals": [self._item_val(item, "description", "")[:100] for item in items[:3]],
            "confidence": "media",
            "source_type": "real",
        }

    def _mock_opportunities(self) -> list[dict]:
        return [dict(c) for c in MOCK_COMPANIES]

    def _mock_company_context(self, company_name: str) -> dict | None:
        ctx = MOCK_COMPANY_CONTEXT.get(company_name)
        if ctx is None:
            return None
        return dict(ctx)
