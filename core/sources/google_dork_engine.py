from __future__ import annotations

import asyncio
from datetime import datetime, timezone

from contracts.talent import CandidateEvidence, CandidateSignal
from core.logger import get_logger
from core.sources.base import TalentSourceConnector
from core.tools.search_client import SearchClient

logger = get_logger("core.sources.google_dork")

_DORK_QUERIES_TEMPLATE = [
    'site:linkedin.com/in "{role}" "{location}" (CTO | VP | Director | Head | Manager)',
    'site:linkedin.com/in "{role}" "{location}" (startup | fintech | SaaS | scaleup)',
    'site:github.com "{role}" location:"{location}"',
    'site:github.com "{role}" (CEO | CTO | founder | engineer) location:"{location}"',
    'site:angel.co "{role}" "{location}" (CTO | VP | Director | Head)',
    'intitle:"curriculum vitae" "{role}" filetype:pdf "{location}"',
    'site:about.me "{role}" "{location}"',
    'site:crunchbase.com/person "{role}" "{location}"',
    'site:medium.com "{role}" "{location}" (CTO | VP | Director | Head | founder)',
    'site:stackoverflow.com/users "{role}" "{location}"',
    '"{role}" "{location}" ("open to work" | "buscando trabajo" | "open to opportunities" | "looking for")',
    'inurl:team "{role}" "{location}" (startup | company | corp)',
]


class GoogleDorkEngine(TalentSourceConnector):
    source_name = "google_dork"
    source_url = "https://google.serper.dev/search"
    compliance_notes = "Public search results only. Uses Serper.dev API (Google search). Respects robots.txt indirectly via Google index."
    requires_key = True

    def __init__(self, api_key: str = ""):
        self._client = SearchClient(api_key=api_key)

    @property
    def is_available(self) -> bool:
        return self._client.is_real_available

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        role_raw = criteria.get("role_target", "CTO / VP Engineering")
        markets = criteria.get("markets", ["Mexico", "LATAM"])
        limit = min(criteria.get("limit", 10), 30)

        roles = self._parse_roles(role_raw)
        location = self._primary_location(markets)

        queries = self._build_queries(roles, location)
        tasks = [self._search_query(q, count=4) for q in queries]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        for batch in batches:
            if isinstance(batch, Exception):
                continue
            for c in batch:
                key = c.dedup_key()
                if key not in seen:
                    seen.add(key)
                    results.append(c)
                    if len(results) >= limit:
                        return results[:limit]

        return results

    def _build_queries(self, roles: list[str], location: str) -> list[str]:
        queries = []
        for role in roles:
            for tmpl in _DORK_QUERIES_TEMPLATE:
                q = tmpl.replace("{role}", role).replace("{location}", location)
                queries.append(q)
        return queries

    async def _search_query(self, query: str, count: int = 4) -> list[CandidateSignal]:
        try:
            raw = await self._client.search(query, count=count)
        except Exception as exc:
            logger.error("[DORK] query error '%s': %s", query[:60], exc)
            return []

        results: list[CandidateSignal] = []
        for item in raw:
            url = item.get("url", "")
            if not url:
                continue
            title = item.get("title", "")
            desc = item.get("description", "")
            name = self._extract_name(title, url)
            if not name:
                continue
            role = self._guess_role(title, desc) or title[:60]
            domain = self._domain(url)
            evidence = [
                CandidateEvidence(label=f"Perfil {domain}", value=desc or title, url=url),
            ]
            results.append(CandidateSignal(
                name=name,
                current_role=role[:80],
                company="",
                location=self._guess_location(title, desc),
                source="google_dork",
                source_url=url,
                availability_signal="unknown",
                skills=[],
                evidence=evidence,
                raw_score=0.0,
                confidence="low",
                last_seen_at=datetime.now(timezone.utc).isoformat(),
            ))
        return results

    @staticmethod
    def _parse_roles(role_raw: str) -> list[str]:
        parts = [r.strip() for r in role_raw.replace("/", "|").replace(",", "|").split("|")]
        return [r for r in parts if r][:3]

    @staticmethod
    def _primary_location(markets: list[str]) -> str:
        loc_map = {
            "Mexico": "México",
            "México": "México",
            "Colombia": "Colombia",
            "Argentina": "Argentina",
            "Chile": "Chile",
            "Peru": "Perú",
            "Perú": "Perú",
            "Brazil": "Brasil",
            "Brasil": "Brasil",
            "Uruguay": "Uruguay",
        }
        for m in markets:
            if m in loc_map:
                return loc_map[m]
        return markets[0] if markets else "LATAM"

    @staticmethod
    def _extract_name(title: str, url: str) -> str:
        url_lower = url.lower()
        if "linkedin.com/in/" in url_lower:
            slug = url.split("/in/")[-1].split("/")[0].split("?")[0]
            return slug.replace("-", " ").replace("_", " ").title().strip()
        if "angel.co" in url_lower or "wellfound.com" in url_lower:
            slug = url.split(".co/")[-1] if "angel.co" in url_lower else url.split("wellfound.com/")[-1]
            slug = slug.split("/")[0].split("?")[0]
            return slug.replace("-", " ").replace("_", " ").title().strip()
        name = title.split(" - ")[0].split(" | ")[0].split(" — ")[0].split(" ·")[0].strip()
        name = name.replace("Profile | ", "").replace("CV | ", "").strip()
        if len(name) > 40:
            return ""
        return name

    @staticmethod
    def _guess_role(title: str, desc: str) -> str:
        combined = f"{title} {desc}"
        patterns = ["CTO", "VP", "Director", "Head of", "Manager", "CEO", "COO",
                    "CFO", "CMO", "CHRO", "Tech Lead", "Engineering", "Founder",
                    "Co-founder"]
        for p in patterns:
            if p.lower() in combined.lower():
                idx = combined.lower().find(p.lower())
                return combined[idx:idx + 40].split(".")[0].split(",")[0].strip()
        return ""

    @staticmethod
    def _guess_location(title: str, desc: str) -> str:
        combined = f"{title} {desc}"
        locs = ["México", "Mexico", "Colombia", "Argentina", "Chile", "Perú",
                "Peru", "Brasil", "Brazil", "Uruguay", "LATAM", "Latam"]
        for loc in locs:
            if loc.lower() in combined.lower():
                return loc
        return "LATAM"

    @staticmethod
    def _domain(url: str) -> str:
        from urllib.parse import urlparse
        try:
            netloc = urlparse(url).netloc
            return netloc.replace("www.", "").split(".")[0].capitalize()
        except Exception:
            return "Web"
