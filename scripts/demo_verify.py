#!/usr/bin/env python3
"""Verifica la integridad del hash chain del ledger MCP demo.

Exit 0 = cadena íntegra. Exit 1 = tamper detectado.
"""
from __future__ import annotations

import hashlib
import json
import os
import sqlite3
import sys
from pathlib import Path


ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))


def _ledger_db_path() -> Path:
    data_dir = os.getenv("VMCP_DATA_DIR")
    if data_dir:
        return Path(data_dir) / "memory.db"
    return ROOT / "data/state/verifiable-memory-mcp/memory.db"


def _sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()


def _canonical(content_hash: str, prev_hash: str | None, created_at: str) -> str:
    return json.dumps(
        {"contentHash": content_hash, "prevHash": prev_hash, "createdAt": created_at},
        separators=(",", ":"),
    )


def verify_chain(db_path: Path) -> tuple[bool, str]:
    if not db_path.exists():
        return False, f"Ledger no encontrado: {db_path}"

    conn = sqlite3.connect(str(db_path))
    rows = conn.execute(
        "SELECT id, created_at, content, content_hash, prev_hash, entry_hash "
        "FROM entries ORDER BY created_epoch ASC"
    ).fetchall()
    conn.close()

    if not rows:
        return True, "Ledger vacío — sin entradas que verificar."

    for idx, (entry_id, created_at, content, stored_content_hash, prev_hash, stored_entry_hash) in enumerate(rows):
        actual_content_hash = _sha256(content)
        if actual_content_hash != stored_content_hash:
            return (
                False,
                f"TAMPER DETECTADO en entrada #{idx + 1} ({entry_id})\n"
                f"  content_hash almacenado : {stored_content_hash[:16]}...\n"
                f"  content_hash calculado  : {actual_content_hash[:16]}...\n"
                f"  → El contenido fue modificado después de registrarse.",
            )

        actual_entry_hash = _sha256(_canonical(actual_content_hash, prev_hash, created_at))
        if actual_entry_hash != stored_entry_hash:
            return (
                False,
                f"TAMPER DETECTADO en entry_hash de entrada #{idx + 1} ({entry_id})\n"
                f"  entry_hash almacenado : {stored_entry_hash[:16]}...\n"
                f"  entry_hash calculado  : {actual_entry_hash[:16]}...\n"
                f"  → La huella de la entrada fue alterada.",
            )

    return True, f"Cadena verificada. {len(rows)} entradas íntegras."


def main() -> None:
    db_path = _ledger_db_path()
    ok, message = verify_chain(db_path)

    if ok:
        print(f"[VERIFY OK] {message}")
        sys.exit(0)
    else:
        print(f"\n[VERIFY FAIL] {message}\n")
        try:
            from core.demo_notifiers import safe_notify_telegram
            safe_notify_telegram(
                "🚨 ALERTA: Tamper detectado en el ledger",
                f"{message}\n\nEl sistema detectó una modificación no autorizada. "
                "Ninguna acción puede ejecutarse hasta que el ledger sea restaurado.",
            )
        except Exception:
            print("[TELEGRAM MOCK] 🚨 ALERTA: Tamper detectado en el ledger")
        sys.exit(1)


if __name__ == "__main__":
    main()
