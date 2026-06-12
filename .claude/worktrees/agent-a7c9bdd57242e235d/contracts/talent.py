from __future__ import annotations

from dataclasses import dataclass, field
from typing import Literal


AvailabilitySignal = Literal[
    "actively_looking",
    "open_to_work",
    "applied_recently",
    "inferred_from_job_board",
    "unknown",
    "demo_seed",
]

SourceConfidence = Literal["high", "medium", "low", "demo_seed"]


@dataclass
class CandidateEvidence:
    label: str
    value: str
    url: str = ""


@dataclass
class CandidateSignal:
    name: str
    current_role: str
    company: str
    location: str
    source: str                    # "torre" | "brave_search" | "firecrawl" | "manual" | "demo_seed"
    source_url: str                # REQUIRED — no URL = no candidate
    availability_signal: AvailabilitySignal = "unknown"
    skills: list[str] = field(default_factory=list)
    evidence: list[CandidateEvidence] = field(default_factory=list)
    raw_score: float = 0.0
    risk_flags: list[str] = field(default_factory=list)
    last_seen_at: str | None = None
    confidence: SourceConfidence = "medium"
    workspace_id: str = "default"

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "current_role": self.current_role,
            "company": self.company,
            "location": self.location,
            "source": self.source,
            "source_url": self.source_url,
            "availability_signal": self.availability_signal,
            "skills": self.skills,
            "evidence": [{"label": e.label, "value": e.value, "url": e.url} for e in self.evidence],
            "raw_score": self.raw_score,
            "risk_flags": self.risk_flags,
            "last_seen_at": self.last_seen_at,
            "confidence": self.confidence,
            "workspace_id": self.workspace_id,
        }

    def dedup_key(self) -> str:
        name_slug = self.name.lower().replace(" ", "_")
        url_slug = self.source_url.split("/")[-1] if self.source_url else ""
        return f"{name_slug}|{url_slug}"
