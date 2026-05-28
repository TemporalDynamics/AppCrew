from __future__ import annotations

from dataclasses import dataclass, field, asdict
from datetime import datetime, timezone
from enum import Enum
from typing import Any


class AgentState(str, Enum):
    IDLE = "idle"
    WORKING = "working"
    PENDING_REVIEW = "pending_review"
    APPROVED = "approved"
    REJECTED = "rejected"
    NEEDS_REVISION = "needs_revision"
    ERROR = "error"
    ACKNOWLEDGED = "acknowledged"
    SHORTLISTED = "shortlisted"
    QUALIFIED = "qualified"
    DISMISSED = "dismissed"
    ESCALATED = "escalated"
    IGNORED = "ignored"
    RESOLVED = "resolved"
    VALIDATED_SIGNAL = "validated_signal"
    NEEDS_HUMAN_REVIEW = "needs_human_review"
    WEAK_SIGNAL = "weak_signal"

    # ── Human review actions (mapping) ──
    @staticmethod
    def reviews_for(action_type: str) -> list[str]:
        return ReviewPolicy.allowed_states(action_type)


class ActionType(str, Enum):
    OPPORTUNITY = "opportunity"
    CANDIDATE = "candidate"
    SCORE = "score"
    INMAIL = "inmail"
    EMAIL = "email"
    CONNECTION_REQUEST = "connection_request"
    FOLDER_STRUCTURE = "folder_structure"
    QUALITY_ISSUE = "quality_issue"
    QA_SUMMARY = "qa_summary"
    SIGNAL = "signal"
    CONTEXT_SIGNAL = "context_signal"
    DOCTRINE_SNAPSHOT = "doctrine_snapshot"
    NOTE = "note"


class ReviewPolicy:
    """Central authority for per-action-type review states."""

    _MAPPING: dict[str, list[str]] = {
        ActionType.QUALITY_ISSUE.value: ["acknowledged", "dismissed", "resolved", "escalated"],
        ActionType.INMAIL.value: ["approved", "rejected", "needs_revision"],
        ActionType.CANDIDATE.value: ["shortlisted", "dismissed", "escalated"],
        ActionType.SCORE.value: ["acknowledged", "dismissed"],
        ActionType.OPPORTUNITY.value: ["qualified", "dismissed", "escalated"],
        ActionType.QA_SUMMARY.value: ["acknowledged"],
        ActionType.FOLDER_STRUCTURE.value: ["approved", "rejected"],
        ActionType.SIGNAL.value: ["validated_signal", "needs_human_review", "weak_signal", "escalated"],
        ActionType.CONTEXT_SIGNAL.value: ["acknowledged", "needs_human_review", "dismissed", "escalated"],
        ActionType.DOCTRINE_SNAPSHOT.value: ["acknowledged"],
        ActionType.NOTE.value: ["acknowledged"],
    }

    @staticmethod
    def allowed_states(action_type: str) -> list[str]:
        return ReviewPolicy._MAPPING.get(action_type, ["acknowledged", "dismissed"])


class Channel(str, Enum):
    LINKEDIN_INMAIL = "linkedin_inmail"
    EMAIL = "email"
    LINKEDIN_CONNECT = "linkedin_connect"


class TaskIntent(str, Enum):
    OPORTUNIDADES = "deteccion_oportunidades"
    TALENTO = "busqueda_talento"
    CONTACTO = "contacto_cliente"
    CALIDAD = "control_calidad"
    CONOCIMIENTO = "organizacion_conocimiento"
    GENERAL = "analisis_general"


# ── Core Contracts ──────────────────────────────

@dataclass
class AgentAction:
    action_id: str = ""
    run_id: str = ""
    agent_id: str = ""
    action_type: str = ""
    target: str = ""
    reason: str = ""
    payload: dict = field(default_factory=dict)
    score: int = 0
    state: str = AgentState.PENDING_REVIEW.value
    created_at: str = ""
    reviewed_at: str | None = None
    review_comment: str = ""

    def __post_init__(self):
        if not self.action_id:
            ts = datetime.now(timezone.utc).timestamp()
            raw = f"{self.agent_id}|{self.action_type}|{self.target}|{ts}"
            h = abs(hash(raw))
            self.action_id = f"{self.agent_id}_{int(ts) % 10**6:06d}_{h % 10**12:012d}"
        if not self.created_at:
            self.created_at = datetime.now(timezone.utc).isoformat()

    def dedup_key(self) -> str:
        scope = self.payload.get("decision_scope", "") if isinstance(self.payload, dict) else ""
        return f"{self.agent_id}|{self.action_type}|{self.target}|{scope}"

    def to_dict(self) -> dict:
        return asdict(self)

    @classmethod
    def from_dict(cls, d: dict) -> AgentAction:
        return cls(**d)

    def get_available_reviews(self) -> list[str]:
        return AgentState.reviews_for(self.action_type)

    def review(self, action: str, comment: str = ""):
        available = self.get_available_reviews()
        if action not in available:
            raise ValueError(f"'{action}' no es válido para {self.action_type}. Válidos: {available}")
        self.state = action
        self.reviewed_at = datetime.now(timezone.utc).isoformat()
        self.review_comment = comment

    def approve(self, comment: str = ""):
        self.review("approved", comment)

    def reject(self, comment: str = ""):
        self.review("rejected", comment)


@dataclass
class AgentInfo:
    agent_id: str = ""
    name: str = ""
    icon: str = ""
    description: str = ""
    state: str = AgentState.IDLE.value
    last_action: str = ""
    last_run: str | None = None
    pending_count: int = 0
    history_count: int = 0

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class SystemStatus:
    orchestrator: str = ""
    agents: dict[str, dict] = field(default_factory=dict)
    pending_count: int = 0
    total_history: int = 0
    timestamp: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


# ── CEO Contracts ───────────────────────────────

@dataclass
class HumanTask:
    text: str
    context: dict | None = None
    reply_to: str | None = None


@dataclass
class AgentOrder:
    agent_id: str
    params: dict
    parent_task: str


@dataclass
class CEOResponse:
    task: str = ""
    summary: str = ""
    plan: dict | None = None
    results: dict | None = None
    pending_actions: list[dict] = field(default_factory=list)
    timestamp: str = ""
    errors: list[str] = field(default_factory=list)

    def to_dict(self) -> dict:
        return asdict(self)


# ── Run / Invariant Contracts ────────────────────

@dataclass
class RunRecord:
    run_id: str = ""
    agent_id: str = ""
    actions_created: int = 0
    actions_skipped: int = 0
    errors: list[str] = field(default_factory=list)
    started_at: str = ""
    finished_at: str = ""

    def to_dict(self) -> dict:
        return asdict(self)


@dataclass
class InvariantViolation:
    agent_id: str
    invariant: str
    detail: str
    severity: str = "warning"  # "warning" | "critical"

    def to_dict(self) -> dict:
        return asdict(self)


# ── Tester Contracts ────────────────────────────

class TestVerdict(str, Enum):
    PASS = "PASS"
    SOFT_FAIL = "SOFT_FAIL"
    HARD_FAIL = "HARD_FAIL"
    SKIP = "SKIP"


@dataclass
class TestResult:
    test_name: str
    verdict: TestVerdict
    detail: str = ""
    fix_applied: str | None = None
    attempts: int = 1

    def to_dict(self) -> dict:
        return asdict(self)
