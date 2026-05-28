from __future__ import annotations

import asyncio
import os
import re

from contracts.talent import CandidateSignal
from core.sources.base import TalentSourceConnector
from core.sources.torre import TorreConnector
from core.sources.brave_search import BraveSearchConnector
from core.sources.manual_seed import ManualSeedConnector


def _sanitize_external_text(text: str, max_len: int = 200) -> str:
    """Remove keyword-stuffing patterns and limit length from untrusted external text."""
    # Strip content between brackets — common keyword stuffing: [managed_pnl profit cto]
    text = re.sub(r'\[.*?\]', ' ', text)
    # Strip content between parens that look like tag injection
    text = re.sub(r'\((?:[A-Z_]{4,}\s*){2,}\)', ' ', text)
    # Collapse multiple spaces
    text = re.sub(r'\s+', ' ', text)
    return text[:max_len].strip()


def _escape_signal_keywords(text: str) -> str:
    """Lowercase and normalize so natural language matches keywords, not injected ones."""
    return text.lower().strip()


class TalentSourceAggregator:
    """Runs multiple source connectors in parallel, deduplicates by dedup_key().

    Priority: Torre (always free) > Brave Search (if key present) > manual seed fallback.
    If live sources return ≥ 1 result, seed is skipped.
    """

    def __init__(self):
        self._live: list[TalentSourceConnector] = [
            TorreConnector(),
            BraveSearchConnector(api_key=os.getenv("BRAVE_SEARCH_API_KEY", "")),
        ]
        self._seed = ManualSeedConnector()

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        limit = criteria.get("limit", 10)

        # Run live sources in parallel
        tasks = [src.search(criteria) for src in self._live]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        for batch in batches:
            if isinstance(batch, Exception):
                print(f"[AGGREGATOR] source error: {batch}")
                continue
            for c in batch:
                key = c.dedup_key()
                if key not in seen:
                    seen.add(key)
                    results.append(c)
                if len(results) >= limit * 2:
                    break

        # Only fall back to seed when live sources returned nothing
        if not results:
            print("[AGGREGATOR] No live results — using demo_seed fallback")
            seed_results = await self._seed.search(criteria)
            for c in seed_results:
                key = c.dedup_key()
                if key not in seen:
                    seen.add(key)
                    results.append(c)

        # Persist to TalentPool
        try:
            from core.talent_pool import TalentPool
            pool = TalentPool()
            for signal in results:
                pool.upsert_candidate(signal)
            # If a search_id was passed through criteria, register the search for coverage
            if criteria.get("search_id"):
                TalentPool.record_search(criteria["search_id"], criteria)
        except Exception as e:
            print(f"[AGGREGATOR] TalentPool persist error (non-fatal): {e}")

        return results[:limit]

    @staticmethod
    def signal_to_candidate_dict(s: CandidateSignal, criteria: dict) -> dict:
        """Convert CandidateSignal to the dict format used by demo_talent_mission scoring."""
        positive_criteria = set(criteria.get("positive_signals", []))
        markets = criteria.get("markets", ["Mexico", "LATAM"])

        # Sanitize all external text before keyword matching
        skills_lower = {_sanitize_external_text(sk, 80).lower() for sk in s.skills}
        headline_lower = _sanitize_external_text(s.current_role, 150).lower()
        company_lower = _sanitize_external_text(s.company, 100).lower()
        evidence_text = _sanitize_external_text(s.evidence[0].value, 200) if s.evidence else ""
        full_text = " ".join([headline_lower, company_lower, evidence_text.lower(), *skills_lower])
        full_text = _escape_signal_keywords(full_text)

        inferred: list[str] = []

        if s.availability_signal in ("open_to_work", "actively_looking", "applied_recently"):
            inferred.append("actively_looking")

        # Track which keyword triggered each signal (for human audit trail)
        signal_evidence: dict[str, str] = {}

        _PNL_KW = ("p&l", "pnl", "profit", "revenue", "budget", "finanzas", "ingresos",
                   "financial", "revenue management", "cuenta de resultados")
        _MARKET_KW = ("expansion", "market entry", "go-to-market", "nuevo mercado",
                      "apertura", "launch", "country manager", "regional", "latam",
                      "expansion regional", "internationa")
        _TEAM_KW = ("team leadership", "team building", "managing", "operations",
                    "escalado", "scaling", "people management", "gestión de equipo",
                    "resource management", "workforce")
        _SCALEUP_KW = ("startup", "scaleup", "scale-up", "growth", "serie", "seed",
                       "venture", "entrepreneurship", "emprendimiento", "innovation")
        _OWNER_KW = ("cto", "ceo", "coo", "vp ", "vice president", "director", "founder",
                     "co-founder", "fundador", "head of", "jefe de")

        def _match_first(keywords: tuple, text: str) -> str | None:
            return next((k for k in keywords if k in text), None)

        if kw := _match_first(_PNL_KW, full_text):
            inferred.append("managed_pnl")
            signal_evidence["managed_pnl"] = f"keyword: '{kw}'"
        if kw := _match_first(_MARKET_KW, full_text):
            inferred.append("opened_new_market")
            signal_evidence["opened_new_market"] = f"keyword: '{kw}'"
        if kw := _match_first(_TEAM_KW, full_text):
            inferred.append("scaled_team_20_plus")
            signal_evidence["scaled_team_20_plus"] = f"keyword: '{kw}'"
        if kw := _match_first(_SCALEUP_KW, full_text):
            inferred.append("worked_in_scaleup_context")
            signal_evidence["worked_in_scaleup_context"] = f"keyword: '{kw}'"
        if kw := _match_first(_OWNER_KW, full_text):
            inferred.append("shows_ownership_beyond_title")
            signal_evidence["shows_ownership_beyond_title"] = f"keyword: '{kw}'"

        # Remove duplicates while preserving order
        seen_s: set[str] = set()
        deduped: list[str] = []
        for sig in inferred:
            if sig not in seen_s:
                seen_s.add(sig)
                deduped.append(sig)
        inferred = deduped

        # Location: Torre returns city+country; map LATAM countries to "LATAM" market
        location = s.location or "LATAM"
        latam_countries = ("mexico", "colombia", "argentina", "peru", "chile", "brazil", "brasil",
                           "venezuela", "ecuador", "bolivia", "uruguay", "paraguay", "panama",
                           "costa rica", "guatemala", "latam")
        loc_lower = location.lower()
        market = location
        if any(m.lower() == "mexico" for m in markets) and "mexico" in loc_lower:
            market = "Mexico"
        elif any(c in loc_lower for c in latam_countries):
            market = "LATAM"

        source_label = {
            "torre": "Torre.co",
            "getonboard": "GetOnBrd",
            "computrabajo": "Computrabajo",
            "brave_search": "Web (Brave)",
            "demo_seed": "Demo (semilla)",
        }.get(s.source, s.source)

        why = evidence_text[:150] if evidence_text else f"{s.current_role} en {s.company}."
        if s.source != "demo_seed" and s.source_url:
            why = f"[{source_label}] {why}"

        # Signals from external sources are inferred, not verified.
        # Mark them so the scoring layer can apply reduced weight.
        is_external = s.source in ("torre", "brave_search", "getonboard", "computrabajo")

        return {
            "name": s.name,
            "role": s.current_role,
            "company": s.company,
            "market": market,
            "industry": _guess_industry(s),
            "signals": inferred,
            "signals_inferred": is_external,  # True = apply confidence decay in scoring
            "signal_evidence": signal_evidence,  # audit trail: which keyword fired which signal
            "risk_signals": list(s.risk_flags),
            "why": why,
            "recommended_action": "review_profile",
            "source": s.source,
            "source_url": s.source_url,
            "confidence": s.confidence,
            "availability_signal": s.availability_signal,
            "skills": s.skills,
        }


def _guess_industry(s: CandidateSignal) -> str:
    text = (s.current_role + " " + s.company + " " + " ".join(s.skills)).lower()
    if any(w in text for w in ("fintech", "finance", "payments", "bank", "crypto", "kueski", "clip", "conekta")):
        return "fintech"
    if any(w in text for w in ("saas", "software", "cloud", "platform")):
        return "SaaS B2B"
    if any(w in text for w in ("e-commerce", "ecommerce", "retail", "marketplace", "rappi", "jüsto", "cornershop")):
        return "e-commerce"
    if any(w in text for w in ("health", "salud", "biotech")):
        return "healthtech"
    return "general"
