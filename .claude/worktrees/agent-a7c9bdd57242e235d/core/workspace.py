from __future__ import annotations

import yaml
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
WORKSPACES_FILE = ROOT / "data" / "workspaces.yaml"


class WorkspaceManager:
    @staticmethod
    def load() -> list[dict]:
        """Load all workspaces from YAML."""
        if not WORKSPACES_FILE.exists():
            return []
        with open(WORKSPACES_FILE, "r", encoding="utf-8") as f:
            data = yaml.safe_load(f)
        return data.get("workspaces", []) if data else []

    @staticmethod
    def get_by_token(token: str) -> dict | None:
        """Return workspace config for given token, or None if invalid."""
        if not token:
            return None
        for ws in WorkspaceManager.load():
            if ws.get("token") == token:
                return ws
        return None

    @staticmethod
    def get_default() -> dict:
        """Return default dev workspace (no token required)."""
        for ws in WorkspaceManager.load():
            if ws.get("id") == "default":
                return ws
        # Fallback if YAML is missing or malformed
        return {
            "id": "default",
            "name": "Dev Local",
            "token": "",
            "owner": "dev",
            "status": "active",
        }
