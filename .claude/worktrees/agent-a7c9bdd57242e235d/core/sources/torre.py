from __future__ import annotations

from datetime import datetime, timezone

import httpx

from contracts.talent import CandidateEvidence, CandidateSignal
from core.sources.base import TalentSourceConnector

_TORRE_SEARCH = "https://search.torre.co/people/_search"
_TORRE_PROFILE = "https://torre.co/{username}"


class TorreConnector(TalentSourceConnector):
    source_name = "torre"
    source_url = "https://torre.co"
    compliance_notes = "Public profiles only. No login. Torre ToS allows public access."
    requires_key = False

    # Map criteria roles to Torre search terms
    _ROLE_MAP = {
        "cto": "CTO",
        "vp engineering": "VP Engineering",
        "vp eng": "VP Engineering",
        "country manager": "Country Manager",
        "head of product": "Head of Product",
        "coo": "COO",
        "cfo": "CFO",
        "head of growth": "Head of Growth",
        "vp product": "VP Product",
        "director of operations": "Director of Operations",
    }

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        role_raw = criteria.get("role_target", "CTO / VP Engineering")
        markets = criteria.get("markets", ["Mexico"])
        limit = min(criteria.get("limit", 10), 20)

        roles = self._parse_roles(role_raw)
        country = self._primary_country(markets)

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        for role in roles:
            batch = await self._search_role(role, country, limit)
            for c in batch:
                key = c.dedup_key()
                if key not in seen:
                    seen.add(key)
                    results.append(c)
            if len(results) >= limit:
                break

        return results[:limit]

    async def _search_role(self, role: str, country: str, limit: int) -> list[CandidateSignal]:
        body = {
            "and": [
                {"skill/role": {"text": role, "experience": "potential-to-develop"}},
                {"location/country": {"term": country}},
            ],
            "size": limit,
            "offset": 0,
        }
        headers = {
            "Content-Type": "application/json",
            "User-Agent": "Mozilla/5.0 (X11; Linux x86_64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/124.0.0.0 Safari/537.36",
            "Accept": "application/json, text/plain, */*",
            "Origin": "https://torre.co",
            "Referer": "https://torre.co/",
        }
        try:
            async with httpx.AsyncClient(timeout=12) as client:
                r = await client.post(_TORRE_SEARCH, json=body, headers=headers)
                r.raise_for_status()
                data = r.json()
        except Exception as exc:
            print(f"[TORRE] Error: {exc}")
            return []

        profiles = data.get("results", [])
        signals = []
        for p in profiles:
            c = self._normalize(p)
            if c:
                signals.append(c)
        return signals

    def _normalize(self, p: dict) -> CandidateSignal | None:
        name = p.get("name", "").strip()
        username = p.get("username", "")
        if not name or not username:
            return None

        headline = p.get("professionalHeadline", "")
        location = p.get("locationName", p.get("location", {}).get("name", "")) if isinstance(p.get("location"), dict) else p.get("location", "")
        pic = p.get("pictureThumbnail", "")

        # Parse role from headline
        role, company = self._split_headline(headline)

        skills = [s.get("name", s) if isinstance(s, dict) else str(s) for s in p.get("skills", [])[:8]]

        profile_url = _TORRE_PROFILE.format(username=username)

        # Torre profiles are explicitly people open to opportunities
        availability = "open_to_work"

        evidence = [
            CandidateEvidence(
                label="Perfil Torre",
                value=headline or role,
                url=profile_url,
            )
        ]
        if location:
            evidence.append(CandidateEvidence(label="Ubicación", value=location, url=""))

        return CandidateSignal(
            name=name,
            current_role=role or headline[:60],
            company=company or "Por confirmar",
            location=location or "LATAM",
            source="torre",
            source_url=profile_url,
            availability_signal=availability,
            skills=skills,
            evidence=evidence,
            raw_score=0.0,
            confidence="medium",
            last_seen_at=datetime.now(timezone.utc).isoformat(),
        )

    @staticmethod
    def _split_headline(headline: str) -> tuple[str, str]:
        """Extract role and company from 'Role at Company' headline."""
        for sep in (" at ", " en ", " @ ", " - ", " | "):
            if sep in headline:
                parts = headline.split(sep, 1)
                return parts[0].strip()[:80], parts[1].strip()[:80]
        return headline[:80], ""

    @staticmethod
    def _parse_roles(role_raw: str) -> list[str]:
        parts = [r.strip() for r in role_raw.replace("/", "|").replace(",", "|").split("|")]
        return [r for r in parts if r][:3]

    @staticmethod
    def _primary_country(markets: list[str]) -> str:
        priority = {"Mexico": "Mexico", "México": "Mexico", "Colombia": "Colombia", "Argentina": "Argentina"}
        for m in markets:
            if m in priority:
                return priority[m]
        return markets[0] if markets else "Mexico"
