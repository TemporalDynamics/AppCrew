from __future__ import annotations

import os
from datetime import datetime, timezone

from contracts.talent import CandidateEvidence, CandidateSignal
from core.sources.base import TalentSourceConnector
from core.tools.search_client import SearchClient


_TALENT_SITES = [
    "site:torre.co",
    "site:getonbrd.com",
    "site:linkedin.com/in",
    "site:computrabajo.com.mx",
]


class BraveSearchConnector(TalentSourceConnector):
    source_name = "brave_search"
    source_url = "https://api.search.brave.com"
    compliance_notes = "Web search API. Only public profile pages. No login scraping."
    requires_key = True

    def __init__(self, api_key: str = ""):
        self._client = SearchClient(api_key=api_key or os.getenv("BRAVE_SEARCH_API_KEY", ""))

    @property
    def is_available(self) -> bool:
        return self._client.is_real_available

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        if not self.is_available:
            return []

        role = criteria.get("role_target", "CTO")
        markets = criteria.get("markets", ["Mexico"])
        limit = min(criteria.get("limit", 8), 15)

        location_str = " OR ".join(markets[:2])
        queries = self._build_queries(role, location_str)

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        for query in queries:
            raw = await self._client.search(query, count=min(5, limit - len(results)))
            for item in raw:
                c = self._normalize(item, role)
                if c:
                    key = c.dedup_key()
                    if key not in seen:
                        seen.add(key)
                        results.append(c)
            if len(results) >= limit:
                break

        return results[:limit]

    @staticmethod
    def _build_queries(role: str, location: str) -> list[str]:
        primary_role = role.split("/")[0].strip()
        return [
            f'"{primary_role}" "{location}" (torre.co OR getonbrd.com) buscando trabajo',
            f'"{primary_role}" open to work OR "abierto a oportunidades" {location}',
            f'site:torre.co "{primary_role}" {location}',
        ]

    @staticmethod
    def _normalize(item: dict, role_hint: str) -> CandidateSignal | None:
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        desc = item.get("description", "").strip()

        if not url or not title:
            return None

        # Skip obvious non-profile pages
        skip_keywords = ["empresa", "company", "vacante", "job opening", "trabajo para"]
        if any(k in title.lower() for k in skip_keywords):
            return None

        name = title.split(" - ")[0].split(" | ")[0].strip()[:80]
        if not name or len(name.split()) < 2:
            return None

        source = "brave_search"
        if "torre.co" in url:
            source = "torre"
        elif "getonbrd.com" in url:
            source = "getonboard"
        elif "computrabajo" in url:
            source = "computrabajo"

        evidence = [
            CandidateEvidence(label="Fuente web", value=desc[:120] or title, url=url)
        ]

        return CandidateSignal(
            name=name,
            current_role=role_hint.split("/")[0].strip(),
            company="Por confirmar",
            location="LATAM",
            source=source,
            source_url=url,
            availability_signal="inferred_from_job_board",
            evidence=evidence,
            raw_score=0.0,
            confidence="low",
            last_seen_at=datetime.now(timezone.utc).isoformat(),
        )
