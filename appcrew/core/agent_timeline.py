from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path


def _default_state_dir() -> Path:
    override = os.getenv("APP_CREW_STATE_DIR", "").strip()
    if override:
        return Path(override)
    root = Path(__file__).resolve().parents[2]
    return root / ".appcrew" / "state"


class AgentTimeline:
    def __init__(self, state_dir: Path | None = None) -> None:
        self._state_dir = state_dir or _default_state_dir()
        self._timeline_path = self._state_dir / "agent_timeline.json"
        self._events = self._load()

    def _load(self) -> list[dict]:
        if self._timeline_path.exists():
            try:
                return json.loads(self._timeline_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return []

    def _persist(self) -> None:
        self._timeline_path.parent.mkdir(parents=True, exist_ok=True)
        self._timeline_path.write_text(json.dumps(self._events[-500:], indent=2), encoding="utf-8")

    def append(
        self,
        *,
        run_id: str,
        subject_id: str,
        event_type: str,
        title: str,
        message: str,
        technical_detail: str = "",
        meta: dict | None = None,
    ) -> dict:
        event = {
            "event_id": f"evt_{datetime.now(timezone.utc).strftime('%Y%m%d%H%M%S%f')}",
            "run_id": run_id,
            "subject_id": subject_id,
            "type": event_type,
            "title": title,
            "message": message,
            "technical_detail": technical_detail,
            "meta": meta or {},
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
        self._events.append(event)
        self._persist()
        return dict(event)

    def list_for_run(self, run_id: str, limit: int = 50) -> list[dict]:
        return [event for event in self._events if event.get("run_id") == run_id][-limit:]

    def list_for_subject(self, subject_id: str, limit: int = 50) -> list[dict]:
        return [event for event in self._events if event.get("subject_id") == subject_id][-limit:]

    def clear(self) -> None:
        self._events = []
        self._persist()

