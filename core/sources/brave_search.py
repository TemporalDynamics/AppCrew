from __future__ import annotations

import os
from datetime import datetime, timezone

from contracts.talent import CandidateEvidence, CandidateSignal
from core.sources.base import TalentSourceConnector
from core.tools.search_client import SearchClient


_PROFILE_DOMAINS = (
    "torre.co/",
    "linkedin.com/in/",
    "getonbrd.com/",
    "computrabajo.com",
    "bumeran.com",
    "trabajando.com",
    "indeed.com/r/",
    "curriculum.es",
)


class BraveSearchConnector(TalentSourceConnector):
    source_name = "serper_search"
    source_url = "https://google.serper.dev"
    compliance_notes = "Google Search via Serper.dev. Only public profile pages. No login scraping."
    requires_key = True

    def __init__(self, api_key: str = ""):
        from core.config import settings as _s
        key = api_key or os.getenv("SERPER_API_KEY", "") or _s.serper_api_key or os.getenv("BRAVE_SEARCH_API_KEY", "") or _s.brave_search_api_key
        self._client = SearchClient(api_key=key)

    @property
    def is_available(self) -> bool:
        return self._client.is_real_available

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        if not self.is_available:
            return []

        role = criteria.get("role_target", "")
        markets = criteria.get("markets", ["LATAM"])
        limit = min(criteria.get("limit", 10), 20)

        location_str = markets[0] if markets else "LATAM"
        queries = self._build_queries(role, location_str)

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        for query in queries:
            per_page = min(10, limit - len(results) + 3)
            raw = await self._client.search(query, count=per_page)
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
        r = role.strip()
        return [
            f'site:torre.co "{r}"',
            f'site:linkedin.com/in "{r}" {location}',
            f'site:getonbrd.com "{r}"',
            f'"{r}" {location} curriculum vitae OR CV OR perfil profesional',
            f'"{r}" {location} "open to work" OR "abierto a oportunidades" site:linkedin.com',
        ]

    @staticmethod
    def _normalize(item: dict, role_hint: str) -> CandidateSignal | None:
        title = item.get("title", "").strip()
        url = item.get("url", "").strip()
        desc = item.get("description", "").strip()

        if not url or not title:
            return None

        # Only accept profile-like URLs — reject social posts, news, jobs listings
        url_lower = url.lower()
        skip_domains = ("instagram.com", "facebook.com", "reddit.com", "twitter.com",
                        "x.com", "youtube.com", "tiktok.com", "pinterest.com",
                        "/jobs/", "/ofertas/", "/vacantes/", "/empleo-")
        if any(d in url_lower for d in skip_domains):
            return None

        is_profile = any(d in url_lower for d in _PROFILE_DOMAINS)

        # Reject obvious job listings / news pages
        skip_title_kw = ["empleos de", "ofertas de trabajo", "se busca", "buscamos",
                         "vacante", "job opening", "empresas", " s.a.", " s.r.l."]
        if any(k in title.lower() for k in skip_title_kw):
            return None

        # Reject article/blog titles by pattern before extracting name
        title_lower = title.lower()
        skip_title_kw = [
            "empleos de", "ofertas de trabajo", "se busca", "buscamos", "vacante",
            "job opening", "empresas", " s.a.", " s.r.l.", "platform with",
            "remote jobs", "job board", "¿cómo", "¿qué", "¿cuál", "how to",
            "the largest", "best ", "top ", "lista de", "guía", "artículo",
        ]
        if any(k in title_lower for k in skip_title_kw):
            return None

        # Extract name: first segment before " - " or " | "
        name = title.split(" - ")[0].split(" | ")[0].split(" – ")[0].strip()[:80]
        parts = name.split()
        # Names: 2-4 words, at least 2 capitalized, no digits anywhere in the segment
        if len(parts) < 2 or len(parts) > 5:
            return None
        if any(ch.isdigit() for ch in name):
            return None
        capitalized = sum(1 for p in parts if p and p[0].isupper())
        if capitalized < 2:
            return None

        source = "serper_search"
        if "torre.co" in url_lower:
            source = "torre"
        elif "getonbrd.com" in url_lower:
            source = "getonboard"
        elif "computrabajo" in url_lower:
            source = "computrabajo"
        elif "linkedin.com" in url_lower:
            source = "linkedin"

        evidence = [
            CandidateEvidence(label="Fuente web", value=desc[:150] or title, url=url)
        ]

        return CandidateSignal(
            name=name,
            current_role=role_hint.split("/")[0].strip(),
            company="Por confirmar",
            location="LATAM",
            source=source,
            source_url=url,
            availability_signal="inferred_from_profile" if is_profile else "unknown",
            evidence=evidence,
            raw_score=0.0,
            confidence="low" if not is_profile else "medium",
            last_seen_at=datetime.now(timezone.utc).isoformat(),
        )
