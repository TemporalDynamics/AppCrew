from __future__ import annotations

from dataclasses import asdict, dataclass


@dataclass
class AgentRun:
    run_id: str
    subject_id: str
    kind: str
    status: str
    started_at: str = ""
    ended_at: str = ""
    stop_reason: str = ""
    technical_detail: str = ""
    evidence_path: str = ""

    def to_dict(self) -> dict:
        return asdict(self)

