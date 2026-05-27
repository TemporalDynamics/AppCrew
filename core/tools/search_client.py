from __future__ import annotations

from typing import Any

import httpx

MOCK_RESULTS = [
    {
        "title": "TechMex cierra ronda Serie B por $12M",
        "url": "https://techcrunch.com/example/techmex-series-b",
        "description": "TechMex anunció el cierre de su Serie B liderada por Kaszek. Buscan CTO y 5 ingenieros senior para expansión regional.",
    },
    {
        "title": "FinTechMX contrata Directora de Talento",
        "url": "https://example.com/fintechmx-hiring",
        "description": "FinTechMX acaba de contratar una Directora de Talento. Históricamente esta señal precede contrataciones masivas.",
    },
    {
        "title": "SoftCloud LATAM expande operaciones a 3 países",
        "url": "https://example.com/softcloud-expansion",
        "description": "SoftCloud LATAM abre oficinas en Colombia, Perú y Chile durante 2026.",
    },
]


class SearchClient:
    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._base_url = "https://api.search.brave.com/res/v1/web/search"

    @property
    def is_real_available(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, count: int = 5) -> list[dict]:
        if not self.api_key:
            return self._mock_results()

        try:
            return await self._real_search(query, count)
        except Exception:
            return self._mock_results()

    async def search_company_news(self, company: str, count: int = 5) -> list[dict]:
        return await self.search(f"{company} noticias expansión contratación 2026", count)

    async def _real_search(self, query: str, count: int) -> list[dict]:
        headers = {
            "Accept": "application/json",
            "Accept-Encoding": "gzip",
            "X-Subscription-Token": self.api_key,
        }
        params = {"q": query, "count": min(count, 10)}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.get(self._base_url, headers=headers, params=params)
            r.raise_for_status()
            data = r.json()
        results = []
        for item in data.get("web", {}).get("results", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("url", ""),
                "description": item.get("description", ""),
            })
        return results if results else self._mock_results()

    def _mock_results(self) -> list[dict]:
        return [dict(r) for r in MOCK_RESULTS]
