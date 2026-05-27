from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATE_DIR = DATA_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = STATE_DIR / "ge_state.db"
RUNS_FILE = STATE_DIR / "runs.json"
ACTIONS_FILE = STATE_DIR / "actions.json"
AGENTS_FILE = STATE_DIR / "agent_states.json"


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_tables():
    with _get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS runs (
                run_id TEXT PRIMARY KEY,
                agent_id TEXT NOT NULL,
                actions_created INTEGER DEFAULT 0,
                actions_skipped INTEGER DEFAULT 0,
                errors TEXT DEFAULT '[]',
                started_at TEXT,
                finished_at TEXT
            );
            CREATE TABLE IF NOT EXISTS actions (
                action_id TEXT PRIMARY KEY,
                run_id TEXT DEFAULT '',
                agent_id TEXT NOT NULL,
                action_type TEXT NOT NULL,
                target TEXT DEFAULT '',
                reason TEXT DEFAULT '',
                payload TEXT DEFAULT '{}',
                score INTEGER DEFAULT 0,
                state TEXT DEFAULT 'pending_review',
                created_at TEXT,
                reviewed_at TEXT,
                review_comment TEXT DEFAULT ''
            );
            CREATE INDEX IF NOT EXISTS idx_actions_agent ON actions(agent_id);
            CREATE INDEX IF NOT EXISTS idx_actions_state ON actions(state);
            CREATE INDEX IF NOT EXISTS idx_actions_run ON actions(run_id);
            CREATE TABLE IF NOT EXISTS agent_states (
                agent_id TEXT PRIMARY KEY,
                data TEXT NOT NULL
            );
            CREATE TABLE IF NOT EXISTS cached_sources (
                url TEXT PRIMARY KEY,
                source_type TEXT NOT NULL DEFAULT 'web',
                content TEXT,
                title TEXT,
                fetched_at TEXT NOT NULL,
                ttl_seconds INTEGER DEFAULT 86400
            );
        """)


def _migrate_from_json():
    if DB_PATH.exists():
        return
    _ensure_tables()
    migrated = 0

    if RUNS_FILE.exists():
        try:
            with open(RUNS_FILE) as f:
                runs = json.load(f)
            if isinstance(runs, list):
                with _get_db() as conn:
                    for r in runs:
                        if r.get("run_id"):
                            conn.execute(
                                """INSERT OR IGNORE INTO runs
                                (run_id, agent_id, actions_created, actions_skipped, errors, started_at, finished_at)
                                VALUES (?,?,?,?,?,?,?)""",
                                (r["run_id"], r.get("agent_id", ""), r.get("actions_created", 0),
                                 r.get("actions_skipped", 0), json.dumps(r.get("errors", [])),
                                 r.get("started_at", ""), r.get("finished_at", "")),
                            )
                            migrated += 1
        except Exception:
            pass

    if ACTIONS_FILE.exists():
        try:
            with open(ACTIONS_FILE) as f:
                actions = json.load(f)
            if isinstance(actions, list):
                with _get_db() as conn:
                    for a in actions:
                        if a.get("action_id"):
                            conn.execute(
                                """INSERT OR IGNORE INTO actions
                                (action_id, run_id, agent_id, action_type, target, reason, payload, score, state, created_at, reviewed_at, review_comment)
                                VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                                (a["action_id"], a.get("run_id", ""), a.get("agent_id", ""),
                                 a.get("action_type", ""), a.get("target", ""), a.get("reason", ""),
                                 json.dumps(a.get("payload", {})), a.get("score", 0),
                                 a.get("state", "pending_review"), a.get("created_at", ""),
                                 a.get("reviewed_at"), a.get("review_comment", "")),
                            )
                            migrated += 1
        except Exception:
            pass

    if AGENTS_FILE.exists():
        try:
            with open(AGENTS_FILE) as f:
                agents = json.load(f)
            if isinstance(agents, dict):
                with _get_db() as conn:
                    for aid, data in agents.items():
                        conn.execute(
                            "INSERT OR REPLACE INTO agent_states (agent_id, data) VALUES (?,?)",
                            (aid, json.dumps(data if isinstance(data, dict) else {})),
                        )
                        migrated += 1
        except Exception:
            pass

    return migrated


# ── Public API (drop-in replacement for old StateStore) ──


class StateStore:
    @staticmethod
    def save_runs(runs: list[dict]) -> None:
        _ensure_tables()
        with _get_db() as conn:
            for r in runs:
                conn.execute(
                    """INSERT OR REPLACE INTO runs
                    (run_id, agent_id, actions_created, actions_skipped, errors, started_at, finished_at)
                    VALUES (?,?,?,?,?,?,?)""",
                    (r.get("run_id", ""), r.get("agent_id", ""), r.get("actions_created", 0),
                     r.get("actions_skipped", 0), json.dumps(r.get("errors", [])),
                     r.get("started_at", ""), r.get("finished_at", "")),
                )

    @staticmethod
    def load_runs() -> list[dict]:
        _ensure_tables()
        with _get_db() as conn:
            rows = conn.execute("SELECT * FROM runs ORDER BY started_at DESC").fetchall()
        return [dict(r) for r in rows]

    @staticmethod
    def save_actions(actions: list[dict]) -> None:
        _ensure_tables()
        with _get_db() as conn:
            for a in actions:
                conn.execute(
                    """INSERT OR REPLACE INTO actions
                    (action_id, run_id, agent_id, action_type, target, reason, payload, score, state, created_at, reviewed_at, review_comment)
                    VALUES (?,?,?,?,?,?,?,?,?,?,?,?)""",
                    (a.get("action_id", ""), a.get("run_id", ""), a.get("agent_id", ""),
                     a.get("action_type", ""), a.get("target", ""), a.get("reason", ""),
                     json.dumps(a.get("payload", {})), a.get("score", 0),
                     a.get("state", "pending_review"), a.get("created_at", ""),
                     a.get("reviewed_at"), a.get("review_comment", "")),
                )

    @staticmethod
    def load_actions() -> list[dict]:
        _ensure_tables()
        with _get_db() as conn:
            rows = conn.execute("SELECT * FROM actions ORDER BY created_at DESC").fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["payload"] = json.loads(d.get("payload", "{}"))
            except (json.JSONDecodeError, TypeError):
                d["payload"] = {}
            try:
                d["errors"] = json.loads(d.get("errors", "[]"))
            except (json.JSONDecodeError, TypeError):
                d["errors"] = []
            result.append(d)
        return result

    @staticmethod
    def save_agent_states(agent_states: dict[str, dict]) -> None:
        _ensure_tables()
        with _get_db() as conn:
            for aid, data in agent_states.items():
                d = data if isinstance(data, dict) else data.to_dict() if hasattr(data, "to_dict") else {}
                conn.execute(
                    "INSERT OR REPLACE INTO agent_states (agent_id, data) VALUES (?,?)",
                    (aid, json.dumps(d)),
                )

    @staticmethod
    def load_agent_states() -> dict:
        _ensure_tables()
        with _get_db() as conn:
            rows = conn.execute("SELECT * FROM agent_states").fetchall()
        result = {}
        for r in rows:
            try:
                result[r["agent_id"]] = json.loads(r["data"])
            except (json.JSONDecodeError, TypeError):
                result[r["agent_id"]] = {}
        return result

    @staticmethod
    def load_actions_by_agent(agent_id: str) -> list[dict]:
        _ensure_tables()
        with _get_db() as conn:
            rows = conn.execute(
                "SELECT * FROM actions WHERE agent_id = ? ORDER BY created_at DESC", (agent_id,)
            ).fetchall()
        result = []
        for r in rows:
            d = dict(r)
            try:
                d["payload"] = json.loads(d.get("payload", "{}"))
            except (json.JSONDecodeError, TypeError):
                d["payload"] = {}
            result.append(d)
        return result

    @staticmethod
    def get_pending_count() -> int:
        _ensure_tables()
        with _get_db() as conn:
            row = conn.execute(
                "SELECT COUNT(*) as cnt FROM actions WHERE state = 'pending_review'"
            ).fetchone()
            return row["cnt"] if row else 0

    @staticmethod
    def snapshot(orchestrator) -> dict:
        return {
            "runs": StateStore.load_runs(),
            "actions": StateStore.load_actions(),
            "agent_states": StateStore.load_agent_states(),
            "snapshot_at": datetime.now(timezone.utc).isoformat(),
        }

    @staticmethod
    def restore(orchestrator) -> dict:
        _ensure_tables()
        runs = StateStore.load_runs()
        agents = StateStore.load_agent_states()
        actions = StateStore.load_actions()

        if hasattr(orchestrator, "runs") and runs:
            from contracts import RunRecord
            orchestrator.runs = [RunRecord(**r) for r in runs if r]

        from contracts import AgentState, AgentAction
        restored = 0
        pending_by_agent: dict[str, list] = {aid: [] for aid in orchestrator.agents}
        history_by_agent: dict[str, list] = {aid: [] for aid in orchestrator.agents}

        for a in actions:
            aid = a.get("agent_id", "")
            state_val = a.get("state", "")
            if state_val in ("pending_review",):
                pending_by_agent.setdefault(aid, []).append(AgentAction(**a))
            else:
                history_by_agent.setdefault(aid, []).append(AgentAction(**a))

        if hasattr(orchestrator, "agents") and agents:
            for aid, state in agents.items():
                if aid in orchestrator.agents:
                    agent = orchestrator.agents[aid]
                    state_val = state.get("state", "idle")
                    try:
                        agent.state = AgentState(state_val)
                    except ValueError:
                        agent.state = AgentState.IDLE
                    agent.last_action = state.get("last_action", "")
                    agent.last_run = state.get("last_run")
                    agent.last_run_id = state.get("last_run_id")
                    agent.pending_actions = pending_by_agent.get(aid, [])
                    agent.history = history_by_agent.get(aid, [])
                    restored += 1

        return {"runs_restored": len(runs), "agents_restored": restored, "actions_restored": len(actions)}

    @staticmethod
    def clear() -> None:
        with _get_db() as conn:
            conn.executescript("DELETE FROM runs; DELETE FROM actions; DELETE FROM agent_states;")
        for f in [RUNS_FILE, ACTIONS_FILE, AGENTS_FILE]:
            if f.exists():
                f.unlink()

    @staticmethod
    def cache_source(url: str, source_type: str, content: str, title: str = "", ttl: int = 86400) -> None:
        _ensure_tables()
        with _get_db() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO cached_sources (url, source_type, content, title, fetched_at, ttl_seconds)
                VALUES (?,?,?,?,?,?)""",
                (url, source_type, content, title, datetime.now(timezone.utc).isoformat(), ttl),
            )

    @staticmethod
    def get_cached_source(url: str) -> dict | None:
        _ensure_tables()
        with _get_db() as conn:
            row = conn.execute(
                "SELECT * FROM cached_sources WHERE url = ?", (url,)
            ).fetchone()
        if row is None:
            return None
        d = dict(row)
        return d


# Migrate existing JSON data on import
_migrate_from_json()
