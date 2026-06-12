from __future__ import annotations

from datetime import datetime, timezone

import httpx

from contracts.talent import CandidateEvidence, CandidateSignal
from core.logger import get_logger
from core.sources.base import TalentSourceConnector

logger = get_logger("core.sources.torre")

_TORRE_SEARCH = "https://search.torre.co/people/_search"
_TORRE_PROFILE = "https://torre.co/{username}"


class TorreConnector(TalentSourceConnector):
    source_name = "torre"
    source_url = "https://torre.co"
    compliance_notes = "Public profiles only. No login. Torre ToS allows public access."
    requires_key = False

    # Map criteria roles to Torre search terms
    # Scoped to the 5 target industries: Finanzas, Ventas/Marketing, RRHH, Logística, Ingeniería
    _ROLE_MAP = {
        # Ingeniería
        "cto": "CTO",
        "vp engineering": "VP Engineering",
        "vp eng": "VP Engineering",
        "engineering manager": "Engineering Manager",
        "head of engineering": "Head of Engineering",
        "tech lead": "Tech Lead",
        "vp product": "VP Product",
        "head of product": "Head of Product",
        # Finanzas & Banking
        "cfo": "CFO",
        "finance director": "Finance Director",
        "director de finanzas": "Director de Finanzas",
        "gerente de finanzas": "Gerente de Finanzas",
        "controller": "Financial Controller",
        "tesorero": "Tesorero",
        "treasury manager": "Treasury Manager",
        "credit manager": "Credit Manager",
        "risk manager": "Risk Manager",
        "gerente de riesgos": "Gerente de Riesgos",
        # Ventas & Marketing
        "vp sales": "VP Sales",
        "director de ventas": "Director de Ventas",
        "gerente de ventas": "Gerente de Ventas",
        "sales director": "Sales Director",
        "head of sales": "Head of Sales",
        "cmo": "CMO",
        "marketing director": "Marketing Director",
        "director de marketing": "Director de Marketing",
        "head of growth": "Head of Growth",
        "growth manager": "Growth Manager",
        "head of marketing": "Head of Marketing",
        # Recursos Humanos
        "chro": "CHRO",
        "hr director": "HR Director",
        "director de rrhh": "Director de RRHH",
        "gerente de rrhh": "Gerente de RRHH",
        "head of people": "Head of People",
        "talent acquisition manager": "Talent Acquisition Manager",
        "people manager": "People Manager",
        # Logística
        "director de logística": "Director de Logística",
        "logistics director": "Logistics Director",
        "supply chain director": "Supply Chain Director",
        "gerente de logística": "Gerente de Logística",
        "gerente de operaciones": "Gerente de Operaciones",
        "operations manager": "Operations Manager",
        "warehouse manager": "Warehouse Manager",
        # Ejecutivos generales
        "coo": "COO",
        "country manager": "Country Manager",
        "director of operations": "Director of Operations",
        "vp operations": "VP Operations",
    }

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        role_raw = criteria.get("role_target", "CTO / VP Engineering")
        markets = criteria.get("markets", ["Mexico"])
        limit = min(criteria.get("limit", 10), 20)

        roles = self._parse_roles(role_raw)
        
        countries = []
        for m in markets:
            mapped = self._map_country(m)
            if mapped not in countries:
                countries.append(mapped)
        if not countries:
            countries = ["Mexico"]

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        for country in countries:
            for role in roles:
                batch = await self._search_role(role, country, limit)
                for c in batch:
                    key = c.dedup_key()
                    if key not in seen:
                        seen.add(key)
                        results.append(c)
                if len(results) >= limit:
                    break
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
            logger.error("[TORRE] Error: %s", exc)
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
    def _map_country(market: str) -> str:
        mapping = {
            "Mexico": "Mexico", "México": "Mexico", 
            "Colombia": "Colombia", 
            "Argentina": "Argentina", 
            "Uruguay": "Uruguay", 
            "Peru": "Peru", "Perú": "Peru", 
            "Chile": "Chile",
            "Brasil": "Brazil", "Brazil": "Brazil"
        }
        return mapping.get(market, market)
