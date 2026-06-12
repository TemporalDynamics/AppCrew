import os
import re
from datetime import datetime, timezone
from contracts.talent import CandidateSignal, CandidateEvidence
from core.sources.base import TalentSourceConnector
from core.tools.search_client import SearchClient
from core.tools.pdf_parser import download_and_extract_pdf


_SKILL_KEYWORDS = [
    "python", "javascript", "typescript", "java", "go", "rust", "c++",
    "react", "angular", "vue", "node", "django", "flask", "fastapi",
    "aws", "gcp", "azure", "docker", "kubernetes", "terraform",
    "sql", "postgresql", "mysql", "mongodb", "redis",
    "machine learning", "data science", "nlp", "computer vision",
    "agile", "scrum", "kanban", "leadership", "management",
    "fintech", "saas", "b2b", "b2c",
]


class OpenSignalConnector(TalentSourceConnector):
    source_name = "open_signal"
    source_url = "https://api.search.brave.com"
    compliance_notes = "Finds publicly hosted PDF profiles via open web signals."
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
        limit = min(criteria.get("limit", 5), 10)

        primary_role = role.split("/")[0].strip()
        location_str = " OR ".join(markets[:2])
        query = f'filetype:pdf (CV OR "curriculum vitae") "{primary_role}" {location_str}'

        raw_results = await self._client.search(query, count=limit * 2)

        results: list[CandidateSignal] = []
        seen: set[str] = set()

        for item in raw_results:
            url = item.get("url", "")
            title = item.get("title", "")
            desc = item.get("description", "")

            if not url.lower().endswith(".pdf"):
                continue

            name = self._guess_name(title)
            if not name:
                continue

            pdf_text = await download_and_extract_pdf(url)

            evidence = [
                CandidateEvidence(label="Open Signal", value=desc[:150], url=url),
            ]
            if pdf_text:
                evidence.append(
                    CandidateEvidence(label="pdf_extracted_text", value=pdf_text[:3000], url=url)
                )

            skills = self._extract_skills(pdf_text) if pdf_text else []

            c = CandidateSignal(
                name=name,
                current_role=primary_role,
                company="Unknown",
                location=markets[0] if markets else "LATAM",
                source="open_signal",
                source_url=url,
                availability_signal="open_web",
                evidence=evidence,
                skills=skills,
                raw_score=0.0,
                confidence="low",
                last_seen_at=datetime.now(timezone.utc).isoformat(),
            )

            key = c.dedup_key()
            if key not in seen:
                seen.add(key)
                results.append(c)

            if len(results) >= limit:
                break

        return results

    @staticmethod
    def _guess_name(title: str) -> str:
        t = title.lower()
        t = t.replace("cv", "").replace("curriculum", "").replace("vitae", "").replace(".pdf", "")
        t = t.replace("-", " ").replace("_", " ")
        words = [w.capitalize() for w in t.split() if len(w) > 2]
        if 1 <= len(words) <= 4:
            return " ".join(words)
        return title[:30].strip()

    @staticmethod
    def _extract_skills(text: str) -> list[str]:
        found = []
        text_lower = text.lower()
        for skill in _SKILL_KEYWORDS:
            if skill in text_lower:
                found.append(skill)
        return found[:10]
