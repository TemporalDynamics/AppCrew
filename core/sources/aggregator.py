from __future__ import annotations

import asyncio
import os
import re
import traceback

from contracts.talent import CandidateSignal
from core.logger import get_logger
from core.sources.base import TalentSourceConnector

logger = get_logger("core.sources.aggregator")
from core.sources.torre import TorreConnector
from core.sources.brave_search import BraveSearchConnector
from core.sources.dork_connector import OpenSignalConnector
from core.sources.google_dork_engine import GoogleDorkEngine
from core.sources.github_search import GitHubSearchConnector
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


def _signal_text(signal: CandidateSignal) -> str:
    return (signal.current_role + " " + signal.company + " " +
            " ".join(signal.skills) + " " +
            " ".join(e.value for e in signal.evidence)).lower()


_SIGNAL_KEYWORDS: dict[str, tuple[str, ...]] = {
    "scaleup": ("startup", "scaleup", "scale-up", "growth", "serie", "venture",
                "entrepreneurship", "innovation", "scaling", "escalado"),
    "P&L": ("p&l", "pnl", "profit", "revenue", "budget", "finanzas",
            "ingresos", "financial", "cuenta de resultados"),
    "regional expansion": ("expansion", "market entry", "go-to-market", "nuevo mercado",
                           "apertura", "launch", "country manager", "regional", "latam",
                           "expansion regional", "internationa"),
    "team scaling": ("team leadership", "team building", "managing", "operations",
                     "escalado", "scaling", "people management", "gestión de equipo",
                     "resource management", "workforce"),
    "ownership": ("cto", "ceo", "coo", "vp ", "vice president", "director", "founder",
                  "co-founder", "fundador", "head of", "jefe de"),
}


def _preliminary_score(signal: CandidateSignal, criteria: dict) -> int:
    """Compute a preliminary match score (0-100) based on evidence overlap with positive signals."""
    pos = criteria.get("positive_signals", [])
    if not pos:
        return 50
    text = _signal_text(signal)
    matched = 0
    for kw in pos:
        keywords = _SIGNAL_KEYWORDS.get(kw, (kw.lower(),))
        if any(kw_text in text for kw_text in keywords):
            matched += 1
    return min(100, int((matched / len(pos)) * 100))


def _matched_signals(signal: CandidateSignal, criteria: dict) -> list[str]:
    """Return which positive_signals from criteria are hinted by signal evidence."""
    pos = criteria.get("positive_signals", [])
    if not pos:
        return []
    text = _signal_text(signal)
    result = []
    for kw in pos:
        keywords = _SIGNAL_KEYWORDS.get(kw, (kw.lower(),))
        if any(kw_text in text for kw_text in keywords):
            result.append(kw)
    return result


class TalentSourceAggregator:
    """Runs multiple source connectors in parallel, deduplicates by dedup_key().

    Priority: Torre (always free) > Brave Search (if key present) > manual seed fallback.
    If live sources return ≥ 1 result, seed is skipped.
    """

    def __init__(self):
        # Prefer SERPER_API_KEY; fall back to BRAVE_SEARCH_API_KEY (legacy)
        _search_key = os.getenv("SERPER_API_KEY", "") or os.getenv("BRAVE_SEARCH_API_KEY", "")
        _github_token = os.getenv("GITHUB_TOKEN", "")
        self._live: list[TalentSourceConnector] = [
            TorreConnector(),
            BraveSearchConnector(api_key=_search_key),
            OpenSignalConnector(api_key=_search_key),
            GoogleDorkEngine(api_key=_search_key),
            GitHubSearchConnector(token=_github_token),
        ]
        self._seed = ManualSeedConnector()

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        limit = criteria.get("limit", 10)

        # Run live sources in parallel
        tasks = [src.search(criteria) for src in self._live]
        batches = await asyncio.gather(*tasks, return_exceptions=True)

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        # Import TalentPool locally to avoid circular dependencies if any, and fetch status
        from core.talent_pool import TalentPool

        for batch in batches:
            if isinstance(batch, Exception):
                logger.error("[AGGREGATOR] source error: %s", batch)
                continue
            for c in batch:
                key = c.dedup_key()
                if key not in seen:
                    # Filter out candidates that were explicitly rejected or dismissed previously
                    db_candidate = TalentPool.get_candidate(key)
                    if db_candidate and db_candidate.get("status") in ("dismissed", "rejected"):
                        continue

                    seen.add(key)
                    results.append(c)
                if len(results) >= limit * 2:
                    break

        # We no longer fall back to demo_seed silently. If there are no results,
        # we return an empty list so the agent can correctly report the lack of candidates.

        # Persist to TalentPool
        try:
            from core.talent_pool import TalentPool
            pool = TalentPool()
            workspace_id = criteria.get("workspace_id", "default")
            search_id = criteria.get("search_id", "")
            if search_id:
                TalentPool.record_search(search_id, criteria)
            for signal in results:
                signal.workspace_id = workspace_id
                pool.upsert_candidate(signal, run_id=search_id)
                if search_id:
                    dedup_key = signal.dedup_key()
                    score = _preliminary_score(signal, criteria)
                    matched = _matched_signals(signal, criteria)
                    TalentPool.record_match(
                        search_id, dedup_key,
                        score=score,
                        matched_criteria=matched,
                        risks=list(signal.risk_flags),
                    )
        except Exception as e:
            logger.error("[AGGREGATOR] TalentPool persist error (non-fatal): %s", e, exc_info=True)

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

        # Use full PDF extracted text when available, fall back to short evidence
        evidence_text = ""
        if s.evidence:
            pdf_ev = next((e for e in s.evidence if e.label == "pdf_extracted_text"), None)
            if pdf_ev:
                evidence_text = _sanitize_external_text(pdf_ev.value, 3000)
            else:
                evidence_text = _sanitize_external_text(s.evidence[0].value, 200)
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
            "google_dork": "Google Dork",
            "github": "GitHub",
            "demo_seed": "Demo (semilla)",
        }.get(s.source, s.source)

        why = evidence_text[:150] if evidence_text else f"{s.current_role} en {s.company}."
        if s.source != "demo_seed" and s.source_url:
            why = f"[{source_label}] {why}"

        # Signals from external sources are inferred, not verified.
        # Mark them so the scoring layer can apply reduced weight.
        is_external = s.source in ("torre", "brave_search", "google_dork", "github", "getonboard", "computrabajo")

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
    if any(w in text for w in (
        "finanzas", "finance", "fintech", "banking", "banco", "bank", "tesorería", "treasury",
        "contabilidad", "accounting", "auditor", "crédito", "credit", "riesgo financiero",
        "payments", "kueski", "clip", "conekta", "mercado pago", "nubank",
    )):
        return "FINANZAS & BANKING"
    if any(w in text for w in (
        "ventas", "sales", "marketing", "comercial", "growth", "revenue", "cmo", "gtm",
        "go-to-market", "demand generation", "account executive", "business development",
        "quota", "pipeline", "crm", "hubspot", "salesforce",
    )):
        return "VENTAS & MARKETING"
    if any(w in text for w in (
        "recursos humanos", "rrhh", "hr ", "people", "talent", "talento", "chro",
        "reclutamiento", "recruiting", "onboarding", "cultura organizacional",
        "employee experience", "compensaciones", "nómina", "payroll",
    )):
        return "RECURSOS HUMANOS"
    if any(w in text for w in (
        "logística", "logistics", "supply chain", "cadena de suministro", "almacén",
        "warehouse", "distribución", "distribution", "flota", "fleet", "transporte",
        "inventario", "inventory", "last mile", "última milla", "fulfillment",
    )):
        return "LOGÍSTICA"
    if any(w in text for w in (
        "ingeniería", "engineering", "software", "cto", "tech lead", "developer",
        "desarrollador", "infraestructura", "cloud", "devops", "data engineer",
        "machine learning", "platform", "arquitecto", "architect", "saas",
    )):
        return "INGENIERÍA"
    return "general"
