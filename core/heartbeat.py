from __future__ import annotations

from datetime import datetime, timezone
from typing import Any


class HeartbeatStore:
    _heartbeats: dict[str, dict[str, Any]] = {}

    @classmethod
    def record(cls, agent_id: str, heartbeat: dict[str, Any]) -> None:
        heartbeat["recorded_at"] = datetime.now(timezone.utc).isoformat()
        cls._heartbeats[agent_id] = heartbeat

    @classmethod
    def get(cls, agent_id: str) -> dict[str, Any] | None:
        return cls._heartbeats.get(agent_id)

    @classmethod
    def get_all(cls) -> dict[str, dict[str, Any]]:
        return dict(cls._heartbeats)

    @classmethod
    def clear(cls) -> None:
        cls._heartbeats.clear()


def build_heartbeat(agent, actions_created: int = 0, **extra) -> dict[str, Any]:
    return {
        "agent_id": agent.id,
        "state": agent.state.value if hasattr(agent.state, "value") else str(agent.state),
        "last_action": agent.last_action,
        "last_run_at": agent.last_run or "",
        "last_run_id": agent.last_run_id or "",
        "pending_actions": len(agent.pending_actions),
        "actions_created": actions_created or len(agent.history),
        "errors": [],
        "blocked": agent.state.value in ("error",) if hasattr(agent.state, "value") else False,
        "blocked_reason": "",
        "source_type": "internal",
        "confidence": "high",
        **extra,
    }
