from __future__ import annotations

from abc import ABC, abstractmethod

from contracts.talent import CandidateSignal


class TalentSourceConnector(ABC):
    source_name: str = ""
    source_url: str = ""
    compliance_notes: str = ""
    requires_key: bool = False

    @property
    def is_available(self) -> bool:
        return True

    @abstractmethod
    async def search(self, criteria: dict) -> list[CandidateSignal]:
        """Search for candidates matching the criteria dict.

        criteria keys used (all optional):
          role_target   str   — e.g. "CTO / VP Engineering"
          markets       list  — e.g. ["Mexico", "LATAM"]
          industries    list  — e.g. ["fintech", "SaaS B2B"]
          positive_signals list
          limit         int   — max results (default 10)
        """
        ...
