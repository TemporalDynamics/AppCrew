from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _default_state_dir() -> Path:
    override = os.getenv("APP_CREW_STATE_DIR", "").strip()
    if override:
        return Path(override)
    root = Path(__file__).resolve().parents[2]
    return root / ".appcrew" / "state"


class AgentRuns:
    def __init__(self, state_dir: Path | None = None) -> None:
        self._state_dir = state_dir or _default_state_dir()
        self._state_path = self._state_dir / "agent_runs.json"
        self._data = self._load()

    def _load(self) -> dict[str, Any]:
        if self._state_path.exists():
            try:
                return json.loads(self._state_path.read_text(encoding="utf-8"))
            except Exception:
                pass
        return {"runs": {}, "subject_index": {}, "current_run_id": ""}

    def _persist(self) -> None:
        self._state_path.parent.mkdir(parents=True, exist_ok=True)
        self._state_path.write_text(json.dumps(self._data, indent=2), encoding="utf-8")

    def create_run(self, subject_id: str, kind: str = "mission") -> dict[str, Any]:
        ts = datetime.now(timezone.utc)
        run_id = f"run_{ts.strftime('%Y%m%d%H%M%S%f')}_{kind}_{subject_id}_{uuid4().hex[:6]}"
        run = {
            "run_id": run_id,
            "subject_id": subject_id,
            "kind": kind,
            "status": "READY",
            "started_at": "",
            "ended_at": "",
            "stop_reason": "",
            "technical_detail": "",
            "evidence_path": "",
        }
        self._data["runs"][run_id] = run
        self._data["subject_index"][subject_id] = run_id
        self._data["current_run_id"] = run_id
        self._persist()
        return dict(run)

    def update_run(self, run_id: str, **kwargs: Any) -> dict[str, Any]:
        run = self._data["runs"].setdefault(run_id, {"run_id": run_id})
        run.update(kwargs)
        if subject_id := run.get("subject_id", ""):
            self._data["subject_index"][subject_id] = run_id
        self._data["current_run_id"] = run_id
        self._persist()
        return dict(run)

    def get_run(self, run_id: str) -> dict[str, Any]:
        return dict(self._data.get("runs", {}).get(run_id, {}))

    def get_current_run(self, subject_id: str = "") -> dict[str, Any]:
        if subject_id:
            run_id = self._data.get("subject_index", {}).get(subject_id, "")
            return self.get_run(run_id) if run_id else {}
        current = self._data.get("current_run_id", "")
        return self.get_run(current) if current else {}

    def clear(self) -> None:
        self._data = {"runs": {}, "subject_index": {}, "current_run_id": ""}
        self._persist()

