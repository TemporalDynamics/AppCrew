from __future__ import annotations

from dataclasses import asdict, dataclass, field


@dataclass
class AgentEvent:
    event_id: str
    run_id: str
    subject_id: str
    type: str
    title: str
    message: str
    technical_detail: str = ""
    timestamp: str = ""
    meta: dict = field(default_factory=dict)

    def to_dict(self) -> dict:
        return asdict(self)

