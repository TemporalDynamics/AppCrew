from __future__ import annotations

from typing import Any

import httpx

MOCK_RESULTS = [
    {
        "title": "Alejandro Ríos — CTO @ TechMex LATAM",
        "url": "https://torre.co/alejandro-rios",
        "description": "CTO con 12 años liderando equipos de producto en startups LATAM. Actualmente en modo apertura.",
    },
    {
        "title": "Valentina Morales — VP Engineering @ Shippify",
        "url": "https://linkedin.com/in/valentina-morales",
        "description": "VP of Engineering con foco en escalabilidad y entregas. Open to new challenges.",
    },
    {
        "title": "Carlos Medina — Head of Product @ Kushki",
        "url": "https://torre.co/carlos-medina",
        "description": "Head de producto fintech. Pasó por Rappi y Kushki. Busca próximo desafío.",
    },
]


class SearchClient:
    """Web search client — uses Serper.dev when SERPER_API_KEY is available, mock otherwise."""

    def __init__(self, api_key: str = ""):
        self.api_key = api_key
        self._base_url = "https://google.serper.dev/search"

    @property
    def is_real_available(self) -> bool:
        return bool(self.api_key)

    async def search(self, query: str, count: int = 5) -> list[dict]:
        if not self.api_key:
            return self._mock_results()
        try:
            return await self._real_search(query, count)
        except Exception:
            return []  # don't inject mocks on API error — connector aggregates multiple queries

    async def search_company_news(self, company: str, count: int = 5) -> list[dict]:
        return await self.search(f"{company} noticias expansión contratación 2026", count)

    async def _real_search(self, query: str, count: int) -> list[dict]:
        headers = {
            "X-API-KEY": self.api_key,
            "Content-Type": "application/json",
        }
        payload = {"q": query, "num": min(count, 10)}
        async with httpx.AsyncClient(timeout=15) as client:
            r = await client.post(self._base_url, headers=headers, json=payload)
            r.raise_for_status()
            data = r.json()
        results = []
        for item in data.get("organic", []):
            results.append({
                "title": item.get("title", ""),
                "url": item.get("link", ""),
                "description": item.get("snippet", ""),
            })
        return results

    def _mock_results(self) -> list[dict]:
        return [dict(r) for r in MOCK_RESULTS]
