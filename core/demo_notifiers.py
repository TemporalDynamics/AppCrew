from __future__ import annotations

import hashlib
import json
import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


def _utc_now() -> str:
    return datetime.now(timezone.utc).isoformat()


def safe_notify_telegram(title: str, body: str) -> dict[str, Any]:
    """Send Telegram when configured; otherwise print the exact demo message."""
    message = f"{title}\n\n{body}"
    try:
        from core.telegram_notifier import TelegramNotifier

        notifier = TelegramNotifier()
        if notifier.enabled:
            ok = notifier.send_raw_message(message)
            return {"provider": "telegram", "sent": ok, "message": message}
    except Exception as exc:
        print(f"[TELEGRAM MOCK] Telegram unavailable: {exc}")

    print(f"\n[TELEGRAM MOCK]\n{message}\n")
    return {"provider": "mock", "sent": False, "message": message}


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(content_hash: str, prev_hash: str | None, created_at: str) -> str:
    return json.dumps(
        {"contentHash": content_hash, "prevHash": prev_hash, "createdAt": created_at},
        separators=(",", ":"),
    )


def _ledger_db_path() -> Path:
    data_dir = os.getenv("VMCP_DATA_DIR")
    if data_dir:
        return Path(data_dir) / "memory.db"
    return Path("data/state/verifiable-memory-mcp/memory.db")


def safe_record_ledger(
    event_type: str,
    summary: str,
    evidence: dict[str, Any] | None = None,
    tags: list[str] | None = None,
) -> dict[str, Any]:
    """Record a demo event in the verifiable-memory compatible SQLite ledger.

    Falls back to JSONL if SQLite is unavailable, so the demo never blocks on infra.
    """
    evidence = evidence or {}
    tags = tags or []
    content = json.dumps(
        {
            "event_type": event_type,
            "summary": summary,
            "evidence": evidence,
            "created_at": _utc_now(),
        },
        ensure_ascii=False,
        sort_keys=True,
    )

    try:
        db_path = _ledger_db_path()
        db_path.parent.mkdir(parents=True, exist_ok=True)
        conn = sqlite3.connect(str(db_path))
        conn.execute(
            """
            CREATE TABLE IF NOT EXISTS entries (
              id TEXT PRIMARY KEY,
              created_at TEXT NOT NULL,
              content TEXT NOT NULL,
              tags TEXT NOT NULL DEFAULT '[]',
              content_hash TEXT NOT NULL,
              prev_hash TEXT,
              entry_hash TEXT NOT NULL UNIQUE,
              created_epoch INTEGER NOT NULL
            )
            """
        )
        row = conn.execute(
            "SELECT entry_hash FROM entries ORDER BY created_epoch DESC LIMIT 1"
        ).fetchone()
        prev_hash = row[0] if row else None
        created_at = _utc_now()
        content_hash = _sha256(content)
        entry_hash = _sha256(_canonical(content_hash, prev_hash, created_at))
        entry_id = f"mem_ge_{uuid4().hex[:12]}"
        created_epoch = int(datetime.now(timezone.utc).timestamp() * 1000)
        ledger_tags = sorted(set(["global_executive", "crew", event_type, *tags]))

        conn.execute(
            """
            INSERT INTO entries (
                id, created_at, content, tags, content_hash, prev_hash, entry_hash, created_epoch
            ) VALUES (?, ?, ?, ?, ?, ?, ?, ?)
            """,
            (
                entry_id,
                created_at,
                content,
                json.dumps(ledger_tags, ensure_ascii=False),
                content_hash,
                prev_hash,
                entry_hash,
                created_epoch,
            ),
        )
        conn.commit()
        conn.close()
        print(f"[MCP LEDGER] {event_type} -> {entry_id} ({entry_hash[:12]})")
        return {
            "provider": "verifiable-memory-compatible-sqlite",
            "recorded": True,
            "id": entry_id,
            "entry_hash": entry_hash,
        }
    except Exception as exc:
        fallback = Path("data/state/demo_ledger_fallback.jsonl")
        fallback.parent.mkdir(parents=True, exist_ok=True)
        record = {
            "event_type": event_type,
            "summary": summary,
            "evidence": evidence,
            "tags": tags,
            "created_at": _utc_now(),
            "error": str(exc),
        }
        with fallback.open("a", encoding="utf-8") as f:
            f.write(json.dumps(record, ensure_ascii=False) + "\n")
        print(f"[MCP MOCK] {event_type} -> fallback {fallback} ({exc})")
        return {"provider": "jsonl-fallback", "recorded": False, "path": str(fallback)}
