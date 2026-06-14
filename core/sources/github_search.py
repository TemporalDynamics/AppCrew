from __future__ import annotations

from datetime import datetime, timezone

import httpx

from contracts.talent import CandidateEvidence, CandidateSignal
from core.logger import get_logger
from core.sources.base import TalentSourceConnector

logger = get_logger("core.sources.github")

_GITHUB_SEARCH_USERS = "https://api.github.com/search/users"
_GITHUB_USER = "https://api.github.com/users/{username}"


class GitHubSearchConnector(TalentSourceConnector):
    source_name = "github"
    source_url = "https://github.com"
    compliance_notes = "Public GitHub profiles. GitHub ToS allows automated access with rate limits (5000 req/h authed, 60 req/h unauthed)."
    requires_key = False

    def __init__(self, token: str = ""):
        self._token = token

    def _headers(self) -> dict:
        h = {
            "Accept": "application/vnd.github.v3+json",
            "User-Agent": "Talo/1.0",
        }
        if self._token:
            h["Authorization"] = f"Bearer {self._token}"
        return h

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        role_raw = criteria.get("role_target", "CTO / VP Engineering")
        markets = criteria.get("markets", ["Mexico", "LATAM"])
        limit = min(criteria.get("limit", 10), 30)

        roles = self._parse_roles(role_raw)
        location = self._primary_location(markets)
        queries = self._build_queries(roles, location)

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        for q in queries:
            if len(results) >= limit:
                break
            batch = await self._search_users(q, limit)
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
            queries.append(f"{role} location:{location}")
            queries.append(f"{role} location:{location} repos:>5")
            queries.append(f'"{role}" location:{location}')
            queries.append(f'"{role}" location:{location} followers:>10')
        return queries

    async def _search_users(self, query: str, limit: int) -> list[CandidateSignal]:
        params = {"q": query, "per_page": min(limit, 30), "sort": "followers"}
        try:
            async with httpx.AsyncClient(timeout=10) as client:
                r = await client.get(_GITHUB_SEARCH_USERS, params=params, headers=self._headers())
                r.raise_for_status()
                data = r.json()
        except Exception as exc:
            logger.error("[GITHUB] search error '%s': %s", query[:40], exc)
            return []

        items = data.get("items", [])
        tasks = [self._enrich_user(u["login"]) for u in items[:limit]]
        if not tasks:
            return []

        import asyncio
        profiles = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[CandidateSignal] = []
        for p in profiles:
            if isinstance(p, Exception) or p is None:
                continue
            results.append(p)
        return results

    async def _enrich_user(self, username: str) -> CandidateSignal | None:
        try:
            async with httpx.AsyncClient(timeout=8) as client:
                r = await client.get(_GITHUB_USER.format(username=username), headers=self._headers())
                r.raise_for_status()
                u = r.json()
        except Exception as exc:
            logger.debug("[GITHUB] enrich error for %s: %s", username, exc)
            return None

        name = u.get("name") or username
        bio = u.get("bio") or ""
        company = u.get("company") or ""
        location = u.get("location") or "LATAM"
        blog = u.get("blog") or ""

        skills = [u.get("language", "unknown").lower()] if u.get("language") else []
        skills.extend(["python", "javascript", "go", "rust", "typescript"])

        role = self._extract_role(bio) or bio[:60] if bio else f"Developer ({username})"
        profile_url = u.get("html_url", f"https://github.com/{username}")

        evidence = [
            CandidateEvidence(label="Bio GitHub", value=bio[:200] if bio else role, url=profile_url),
        ]
        if company:
            evidence.append(CandidateEvidence(label="Compañía", value=company[:80], url=""))
        if blog:
            evidence.append(CandidateEvidence(label="Blog/Web", value=blog[:80], url=blog))

        return CandidateSignal(
            name=name[:80],
            current_role=role,
            company=company[:80] if company else "",
            location=location[:80],
            source="github",
            source_url=profile_url,
            availability_signal="unknown",
            skills=skills,
            evidence=evidence,
            raw_score=0.0,
            confidence="low",
            last_seen_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _extract_role(bio: str) -> str:
        patterns = ["CTO", "VP", "Director", "Head of", "Manager", "CEO", "COO",
                    "CFO", "CMO", "CHRO", "Tech Lead", "Engineering", "Founder",
                    "Co-founder", "Lead Engineer", "Staff Engineer", "Principal",
                    "Architect", "DevOps", "Platform", "Data"]
        for p in patterns:
            if p.lower() in bio.lower():
                idx = bio.lower().find(p.lower())
                return bio[idx:idx + 50].split(".")[0].split(",")[0].split("|")[0].strip()
        return ""

    @staticmethod
    def _parse_roles(role_raw: str) -> list[str]:
        parts = [r.strip() for r in role_raw.replace("/", "|").replace(",", "|").split("|")]
        return [r for r in parts if r][:3]

    @staticmethod
    def _primary_location(markets: list[str]) -> str:
        loc_map = {
            "Mexico": "Mexico", "México": "Mexico",
            "Colombia": "Colombia",
            "Argentina": "Argentina",
            "Chile": "Chile",
            "Peru": "Peru", "Perú": "Peru",
            "Brazil": "Brazil", "Brasil": "Brazil",
            "Uruguay": "Uruguay",
        }
        for m in markets:
            if m in loc_map:
                return loc_map[m]
        return markets[0] if markets else "LATAM"
