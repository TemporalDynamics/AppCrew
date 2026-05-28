from __future__ import annotations

import json
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from contracts.talent import CandidateSignal

ROOT = Path(__file__).resolve().parent.parent
DATA_DIR = ROOT / "data"
STATE_DIR = DATA_DIR / "state"
STATE_DIR.mkdir(parents=True, exist_ok=True)

DB_PATH = STATE_DIR / "talent_pool.db"


def _get_db() -> sqlite3.Connection:
    conn = sqlite3.connect(str(DB_PATH))
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA journal_mode=WAL")
    conn.execute("PRAGMA foreign_keys=ON")
    return conn


def _ensure_tables() -> None:
    with _get_db() as conn:
        conn.executescript("""
            CREATE TABLE IF NOT EXISTS candidates (
                dedup_key TEXT PRIMARY KEY,
                source TEXT NOT NULL,
                source_url TEXT NOT NULL,
                confidence TEXT DEFAULT 'low',
                availability_signal TEXT DEFAULT 'unknown',
                first_seen_at TEXT NOT NULL,
                last_seen_at TEXT NOT NULL,
                times_surfaced INTEGER DEFAULT 1,
                status TEXT DEFAULT 'new',
                workspace_id TEXT DEFAULT 'default'
            );

            CREATE TABLE IF NOT EXISTS candidate_identities (
                dedup_key TEXT PRIMARY KEY,
                name TEXT NOT NULL,
                current_role TEXT DEFAULT '',
                company TEXT DEFAULT '',
                location TEXT DEFAULT '',
                skills TEXT DEFAULT '[]',
                FOREIGN KEY (dedup_key) REFERENCES candidates(dedup_key)
            );

            CREATE TABLE IF NOT EXISTS candidate_snapshots (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dedup_key TEXT NOT NULL,
                run_id TEXT DEFAULT '',
                raw_score REAL DEFAULT 0.0,
                inferred_signals TEXT DEFAULT '[]',
                signal_evidence TEXT DEFAULT '{}',
                signals_inferred INTEGER DEFAULT 0,
                captured_at TEXT NOT NULL,
                FOREIGN KEY (dedup_key) REFERENCES candidates(dedup_key)
            );

            CREATE TABLE IF NOT EXISTS candidate_evidence (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dedup_key TEXT NOT NULL,
                label TEXT DEFAULT '',
                value TEXT DEFAULT '',
                url TEXT DEFAULT '',
                added_at TEXT NOT NULL,
                FOREIGN KEY (dedup_key) REFERENCES candidates(dedup_key)
            );

            CREATE TABLE IF NOT EXISTS search_requests (
                search_id TEXT PRIMARY KEY,
                criteria TEXT NOT NULL,
                role_target TEXT DEFAULT '',
                markets TEXT DEFAULT '[]',
                created_at TEXT NOT NULL,
                status TEXT DEFAULT 'running'
            );

            CREATE TABLE IF NOT EXISTS search_matches (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                search_id TEXT NOT NULL,
                dedup_key TEXT NOT NULL,
                score INTEGER DEFAULT 0,
                criteria_match TEXT DEFAULT '0/0',
                band TEXT DEFAULT 'review_needed',
                matched_criteria TEXT DEFAULT '[]',
                risks TEXT DEFAULT '[]',
                FOREIGN KEY (search_id) REFERENCES search_requests(search_id),
                FOREIGN KEY (dedup_key) REFERENCES candidates(dedup_key)
            );

            CREATE TABLE IF NOT EXISTS review_events (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                dedup_key TEXT NOT NULL,
                search_id TEXT DEFAULT '',
                decision TEXT NOT NULL,
                comment TEXT DEFAULT '',
                reviewer TEXT DEFAULT 'human',
                decided_at TEXT NOT NULL,
                FOREIGN KEY (dedup_key) REFERENCES candidates(dedup_key)
            );

            CREATE INDEX IF NOT EXISTS idx_candidates_status ON candidates(status);
            CREATE INDEX IF NOT EXISTS idx_candidates_source ON candidates(source);
            CREATE INDEX IF NOT EXISTS idx_snapshots_dedup ON candidate_snapshots(dedup_key);
            CREATE INDEX IF NOT EXISTS idx_matches_search ON search_matches(search_id);
            CREATE INDEX IF NOT EXISTS idx_matches_dedup ON search_matches(dedup_key);
        """)


def _migrate_add_workspace_id() -> None:
    """Add workspace_id column to candidates table if missing."""
    try:
        with _get_db() as conn:
            conn.execute("ALTER TABLE candidates ADD COLUMN workspace_id TEXT DEFAULT 'default'")
    except sqlite3.OperationalError:
        pass  # column already exists


# Ensure tables exist on import
_ensure_tables()
_migrate_add_workspace_id()


class TalentPool:

    BAND_RULES = [
        ("priority_1", 75),
        ("priority_2", 55),
        ("review_needed", 35),
    ]

    @staticmethod
    def band_from_score(score: int) -> str:
        for band, threshold in TalentPool.BAND_RULES:
            if score >= threshold:
                return band
        return "discard"

    @staticmethod
    def upsert_candidate(signal: "CandidateSignal", run_id: str = "") -> str:
        """Insert or update a candidate from a CandidateSignal. Returns dedup_key."""
        from contracts.talent import CandidateSignal as _CS  # noqa: F401

        key = signal.dedup_key()
        now = datetime.now(timezone.utc).isoformat()

        with _get_db() as conn:
            existing = conn.execute(
                "SELECT dedup_key FROM candidates WHERE dedup_key = ?",
                (key,),
            ).fetchone()

            if existing:
                # Bump surface counter and freshen availability/confidence
                conn.execute(
                    """UPDATE candidates
                       SET times_surfaced = times_surfaced + 1,
                           last_seen_at = ?,
                           availability_signal = ?,
                           confidence = ?
                       WHERE dedup_key = ?""",
                    (now, signal.availability_signal, signal.confidence, key),
                )
                # Refresh identity fields (role/company may have changed)
                conn.execute(
                    """UPDATE candidate_identities
                       SET current_role = ?,
                           company = ?,
                           location = ?,
                           skills = ?
                       WHERE dedup_key = ?""",
                    (
                        signal.current_role,
                        signal.company,
                        signal.location,
                        json.dumps(signal.skills),
                        key,
                    ),
                )
            else:
                # New candidate
                conn.execute(
                    """INSERT INTO candidates
                       (dedup_key, source, source_url, confidence, availability_signal,
                        first_seen_at, last_seen_at, times_surfaced, status, workspace_id)
                       VALUES (?,?,?,?,?,?,?,1,'new',?)""",
                    (
                        key,
                        signal.source,
                        signal.source_url,
                        signal.confidence,
                        signal.availability_signal,
                        now,
                        now,
                        signal.workspace_id,
                    ),
                )
                conn.execute(
                    """INSERT INTO candidate_identities
                       (dedup_key, name, current_role, company, location, skills)
                       VALUES (?,?,?,?,?,?)""",
                    (
                        key,
                        signal.name,
                        signal.current_role,
                        signal.company,
                        signal.location,
                        json.dumps(signal.skills),
                    ),
                )

            # Always record a new snapshot
            conn.execute(
                """INSERT INTO candidate_snapshots
                   (dedup_key, run_id, raw_score, inferred_signals, signal_evidence,
                    signals_inferred, captured_at)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    key,
                    run_id,
                    signal.raw_score,
                    json.dumps([]),   # filled by scoring layer later
                    json.dumps({}),   # filled by scoring layer later
                    0,
                    now,
                ),
            )

            # Insert evidence entries
            for ev in signal.evidence:
                conn.execute(
                    """INSERT INTO candidate_evidence
                       (dedup_key, label, value, url, added_at)
                       VALUES (?,?,?,?,?)""",
                    (key, ev.label, ev.value, ev.url, now),
                )

        return key

    @staticmethod
    def get_candidate(dedup_key: str) -> dict | None:
        """Return full candidate data including identity and latest snapshot signals."""
        with _get_db() as conn:
            row = conn.execute(
                """SELECT c.dedup_key, c.source, c.source_url, c.confidence,
                          c.availability_signal, c.first_seen_at, c.last_seen_at,
                          c.times_surfaced, c.status,
                          ci.name, ci.current_role, ci.company, ci.location, ci.skills
                   FROM candidates c
                   JOIN candidate_identities ci ON c.dedup_key = ci.dedup_key
                   WHERE c.dedup_key = ?""",
                (dedup_key,),
            ).fetchone()
            if row is None:
                return None

            d = dict(row)
            try:
                d["skills"] = json.loads(d.get("skills") or "[]")
            except (json.JSONDecodeError, TypeError):
                d["skills"] = []

            # Latest snapshot
            snap = conn.execute(
                """SELECT raw_score, inferred_signals, signal_evidence, signals_inferred
                   FROM candidate_snapshots
                   WHERE dedup_key = ?
                   ORDER BY id DESC LIMIT 1""",
                (dedup_key,),
            ).fetchone()
            if snap:
                d["raw_score"] = snap["raw_score"]
                try:
                    d["inferred_signals"] = json.loads(snap["inferred_signals"] or "[]")
                except (json.JSONDecodeError, TypeError):
                    d["inferred_signals"] = []
                try:
                    d["signal_evidence"] = json.loads(snap["signal_evidence"] or "{}")
                except (json.JSONDecodeError, TypeError):
                    d["signal_evidence"] = {}
                d["signals_inferred"] = bool(snap["signals_inferred"])
            else:
                d["raw_score"] = 0.0
                d["inferred_signals"] = []
                d["signal_evidence"] = {}
                d["signals_inferred"] = False

        return d

    @staticmethod
    def get_candidate_blind(dedup_key: str) -> dict:
        """Return candidate with PII masked for blind review stage."""
        d = TalentPool.get_candidate(dedup_key)
        if d is None:
            return {}

        # Deterministic blind ID from dedup_key hash
        blind_id = f"Candidato #{abs(hash(dedup_key)) % 9999:04d}"
        d["name"] = blind_id
        d["source_url"] = ""
        d["company"] = "Empresa confidencial"
        # Keep: signals, score, skills (no links), location, availability_signal
        return d

    @staticmethod
    def record_search(search_id: str, criteria: dict) -> None:
        """Persist a search request record."""
        now = datetime.now(timezone.utc).isoformat()
        role_target = criteria.get("role_target", criteria.get("role", ""))
        markets = criteria.get("markets", [])

        with _get_db() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO search_requests
                   (search_id, criteria, role_target, markets, created_at, status)
                   VALUES (?,?,?,?,?,?)""",
                (
                    search_id,
                    json.dumps(criteria, default=str),
                    role_target,
                    json.dumps(markets),
                    now,
                    "running",
                ),
            )

    @staticmethod
    def record_match(
        search_id: str,
        dedup_key: str,
        score: int,
        band: str | None = None,
        criteria_match: str = "0/0",
        matched_criteria: list | None = None,
        risks: list | None = None,
    ) -> None:
        """Record that a candidate matched a given search. Band auto-calculated from score if not provided."""
        if band is None:
            band = TalentPool.band_from_score(score)
        with _get_db() as conn:
            conn.execute(
                """INSERT INTO search_matches
                   (search_id, dedup_key, score, criteria_match, band, matched_criteria, risks)
                   VALUES (?,?,?,?,?,?,?)""",
                (
                    search_id,
                    dedup_key,
                    score,
                    criteria_match,
                    band,
                    json.dumps(matched_criteria or []),
                    json.dumps(risks or []),
                ),
            )

    @staticmethod
    def record_review(
        dedup_key: str,
        decision: str,
        search_id: str = "",
        comment: str = "",
        reviewer: str = "human",
    ) -> None:
        """Record a human review and update candidate status accordingly."""
        now = datetime.now(timezone.utc).isoformat()

        status_map = {
            "approved": "approved",
            "rejected": "rejected",
            "shortlisted": "shortlisted",
            "contacted": "contacted",
            "on_hold": "on_hold",
        }
        new_status = status_map.get(decision, "reviewed")

        with _get_db() as conn:
            conn.execute(
                """INSERT INTO review_events
                   (dedup_key, search_id, decision, comment, reviewer, decided_at)
                   VALUES (?,?,?,?,?,?)""",
                (dedup_key, search_id, decision, comment, reviewer, now),
            )
            conn.execute(
                "UPDATE candidates SET status = ? WHERE dedup_key = ?",
                (new_status, dedup_key),
            )

    @staticmethod
    def get_search_coverage(search_id: str, workspace_id: str = "default") -> dict:
        """Return coverage stats for a given search_id, optionally filtered by workspace."""
        with _get_db() as conn:
            workspace_join = ""
            workspace_param: list = []
            if workspace_id != "default":
                workspace_join = "JOIN candidates c ON sm.dedup_key = c.dedup_key AND c.workspace_id = ?"
                workspace_param.append(workspace_id)

            total_row = conn.execute(
                f"""SELECT COUNT(*) as cnt
                    FROM search_matches sm
                    {workspace_join}
                    WHERE sm.search_id = ?""",
                workspace_param + [search_id],
            ).fetchone()
            total_matches = total_row["cnt"] if total_row else 0

            # By band
            band_rows = conn.execute(
                f"""SELECT sm.band, COUNT(*) as cnt
                    FROM search_matches sm
                    {workspace_join}
                    WHERE sm.search_id = ?
                    GROUP BY sm.band""",
                workspace_param + [search_id],
            ).fetchall()
            by_band: dict[str, int] = {
                "priority_1": 0,
                "priority_2": 0,
                "review_needed": 0,
                "discard": 0,
            }
            for r in band_rows:
                by_band[r["band"]] = r["cnt"]

            # By source — join through candidates
            source_rows = conn.execute(
                f"""SELECT c.source, COUNT(*) as cnt
                    FROM search_matches sm
                    JOIN candidates c ON sm.dedup_key = c.dedup_key
                    {workspace_join}
                    WHERE sm.search_id = ?
                    GROUP BY c.source""",
                workspace_param + [search_id],
            ).fetchall()
            by_source: dict[str, int] = {r["source"]: r["cnt"] for r in source_rows}

            # By candidate status — join through candidates
            status_rows = conn.execute(
                f"""SELECT c.status, COUNT(*) as cnt
                    FROM search_matches sm
                    JOIN candidates c ON sm.dedup_key = c.dedup_key
                    {workspace_join}
                    WHERE sm.search_id = ?
                    GROUP BY c.status""",
                workspace_param + [search_id],
            ).fetchall()
            by_status: dict[str, int] = {r["status"]: r["cnt"] for r in status_rows}

        return {
            "search_id": search_id,
            "total_matches": total_matches,
            "by_band": by_band,
            "by_source": by_source,
            "by_status": by_status,
        }

    @staticmethod
    def _get_candidates_with_evidence(workspace_id: str = "default") -> list[dict]:
        """Return candidates formatted for blind review, filtered by workspace."""
        with _get_db() as conn:
            where_clause = ""
            params: list = []
            if workspace_id != "default":
                where_clause = "WHERE c.workspace_id = ?"
                params.append(workspace_id)

            rows = conn.execute(
                f"""SELECT c.dedup_key, c.source, c.source_url, c.confidence,
                           c.availability_signal, c.first_seen_at, c.status,
                           ci.name, ci.current_role, ci.company, ci.location, ci.skills
                    FROM candidates c
                    JOIN candidate_identities ci ON c.dedup_key = ci.dedup_key
                    {where_clause}
                    ORDER BY c.first_seen_at DESC
                    LIMIT 100""",
                params,
            ).fetchall()

        results = []
        for row in rows:
            d = dict(row)
            try:
                d["skills"] = json.loads(d.get("skills") or "[]")
            except (json.JSONDecodeError, TypeError):
                d["skills"] = []

            blind_id = f"cand_{abs(hash(d['dedup_key'])) % 99999:05d}"
            results.append({
                "candidate_id": blind_id,
                "dedup_key": d["dedup_key"],
                "full_name": d["name"],
                "current_role": d.get("current_role", ""),
                "company": d.get("company", ""),
                "source_url": d.get("source_url", ""),
                "source": d.get("source", ""),
                "source_label": d.get("source", "").replace("_", " ").title(),
                "band": "medium",
                "band_label": "Review needed",
                "skills": d.get("skills", []),
                "evidence": [],
                "reason": "",
                "revealed": False,
            })
        return results

    @staticmethod
    def get_pool_size(workspace_id: str = "default") -> int:
        """Return total number of candidates in the pool, optionally filtered by workspace."""
        with _get_db() as conn:
            if workspace_id != "default":
                row = conn.execute(
                    "SELECT COUNT(*) as cnt FROM candidates WHERE workspace_id = ?",
                    (workspace_id,),
                ).fetchone()
            else:
                row = conn.execute("SELECT COUNT(*) as cnt FROM candidates").fetchone()
            return row["cnt"] if row else 0

    @staticmethod
    def get_full_candidate(dedup_key: str) -> dict | None:
        """Alias for get_candidate — returns full unmasked data."""
        return TalentPool.get_candidate(dedup_key)

    @staticmethod
    def seed_selectahr() -> dict:
        """No-op stub — workspace seeding handled by WorkspaceManager."""
        return {}

    @staticmethod
    def get_workspace(name: str) -> dict | None:
        """Look up workspace config by name via WorkspaceManager."""
        from core.workspace import WorkspaceManager
        workspaces = WorkspaceManager.load()
        return next((w for w in workspaces if w.get("name") == name), None)

    @staticmethod
    def get_users(workspace_id: str) -> list[dict]:
        """Return users for a workspace (stub — returns empty list until user table exists)."""
        return []
