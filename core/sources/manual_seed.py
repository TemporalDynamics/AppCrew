from __future__ import annotations

from datetime import datetime, timezone

from contracts.talent import CandidateEvidence, CandidateSignal
from core.sources.base import TalentSourceConnector

# Labeled demo calibration set — clearly marked source="demo_seed"
# Used as fallback when no live API is available, or as golden calibration anchors.
_SEED: list[dict] = [
    {
        "name": "Jorge Martínez",
        "current_role": "VP Operations",
        "company": "Kueski",
        "location": "Mexico",
        "url": "https://www.linkedin.com/in/jorge-martinez-kueski",
        "headline": "VP Operations at Kueski — scaled ops 12→55 people, opened Monterrey hub, P&L of underwriting & collections.",
        "skills": ["operations", "P&L", "team scaling", "fintech", "LATAM expansion"],
        "availability": "open_to_work",
    },
    {
        "name": "Sofía Herrera",
        "current_role": "Country Manager",
        "company": "Pagali",
        "location": "LATAM",
        "url": "https://torre.co/sofia-herrera-pagali",
        "headline": "Country Manager at Pagali — opened Colombia and Peru from zero. USD 4M P&L.",
        "skills": ["market expansion", "P&L", "fintech", "country management"],
        "availability": "open_to_work",
    },
    {
        "name": "Carlos Mendoza",
        "current_role": "VP Digital",
        "company": "Banorte",
        "location": "Mexico",
        "url": "https://www.linkedin.com/in/carlos-mendoza-banorte",
        "headline": "VP Digital Transformation at Banorte — led retail banking digital with team of 40+.",
        "skills": ["digital transformation", "banking", "team leadership"],
        "availability": "unknown",
    },
    {
        "name": "Andrés Torres",
        "current_role": "Director of Growth",
        "company": "Jüsto",
        "location": "LATAM",
        "url": "https://www.linkedin.com/in/andres-torres-growth",
        "headline": "Director of Growth at Jüsto — prev Rappi, Cornershop, NotCo. Fast mover.",
        "skills": ["growth", "e-commerce", "market expansion", "retail"],
        "availability": "inferred_from_job_board",
    },
]


class ManualSeedConnector(TalentSourceConnector):
    source_name = "demo_seed"
    source_url = ""
    compliance_notes = "Calibration seed profiles for demo/testing. Not real scraped data."
    requires_key = False

    async def search(self, criteria: dict) -> list[CandidateSignal]:
        limit = min(criteria.get("limit", 10), len(_SEED))
        now = datetime.now(timezone.utc).isoformat()
        results = []
        for p in _SEED[:limit]:
            evidence = [CandidateEvidence(label="Perfil demo", value=p["headline"], url=p["url"])]
            results.append(
                CandidateSignal(
                    name=p["name"],
                    current_role=p["current_role"],
                    company=p["company"],
                    location=p["location"],
                    source="demo_seed",
                    source_url=p["url"],
                    availability_signal=p["availability"],
                    skills=p["skills"],
                    evidence=evidence,
                    raw_score=0.0,
                    confidence="demo_seed",
                    last_seen_at=now,
                )
            )
        return results
