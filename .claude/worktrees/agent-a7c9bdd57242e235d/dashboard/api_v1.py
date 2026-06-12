from __future__ import annotations

import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

from fastapi import APIRouter, Depends, Request
from fastapi.responses import JSONResponse

from core.workspace import WorkspaceManager
from core.state import StateStore

router = APIRouter()


# ── Health ────────────────────────────────────────────────────────────────────

@router.get("/health")
async def health():
    return {"status": "ok", "product": "Cerno", "version": "0.1"}


# ── Searches ──────────────────────────────────────────────────────────────────

@router.get("/searches")
async def get_searches():
    """Return the last 20 runs from StateStore."""
    runs = StateStore.load_runs()
    return {"searches": runs[:20]}


# ── Workspace ─────────────────────────────────────────────────────────────────

@router.get("/workspace")
async def get_workspace_info():
    """Return default workspace info (no token required for this endpoint)."""
    ws = WorkspaceManager.get_default()
    safe = {k: v for k, v in ws.items() if k != "token"}
    return safe


# ── Pool ──────────────────────────────────────────────────────────────────────

@router.get("/pool/size")
async def pool_size():
    """Return the number of candidates in the talent pool."""
    try:
        from core.talent_pool import TalentPool
        size = TalentPool.get_pool_size()
        return {"size": size, "status": "ok"}
    except Exception:
        return JSONResponse(
            status_code=503,
            content={"size": 0, "status": "not_initialized"},
        )


@router.get("/pool/candidates")
async def pool_candidates(request: Request):
    """Return a basic list of candidates from the talent pool, filtered by workspace token."""
    token = request.headers.get("X-Workspace-Token", "").strip()
    if not token:
        token = request.query_params.get("token", "").strip()
    workspace_id = "default"
    if token:
        ws = WorkspaceManager.get_by_token(token)
        if ws:
            workspace_id = ws.get("id", "default")

    try:
        from core.talent_pool import TalentPool
        import sqlite3

        db_path = ROOT / "data" / "state" / "talent_pool.db"
        if not db_path.exists():
            return {"candidates": [], "total": 0, "status": "empty"}

        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        where_clause = ""
        params: list = []
        if workspace_id != "default":
            where_clause = "WHERE c.workspace_id = ?"
            params.append(workspace_id)
        rows = conn.execute(
            f"""SELECT c.dedup_key, c.source, c.source_url, c.confidence,
                       c.first_seen_at, c.status,
                       ci.name, ci.current_role, ci.company, ci.location
                FROM candidates c
                LEFT JOIN candidate_identities ci ON c.dedup_key = ci.dedup_key
                {where_clause}
                ORDER BY c.first_seen_at DESC
                LIMIT 100""",
            params,
        ).fetchall()
        conn.close()

        candidates = [dict(r) for r in rows]
        return {"candidates": candidates, "total": len(candidates), "status": "ok", "workspace_id": workspace_id}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"candidates": [], "total": 0, "status": "not_initialized", "detail": str(exc)},
        )


# ── Pool Review ───────────────────────────────────────────────────────────────

@router.post("/pool/review/{dedup_key}")
async def pool_review(dedup_key: str):
    """Register a review event for a candidate (stub)."""
    try:
        from core.talent_pool import TalentPool
        TalentPool.record_review(
            dedup_key,
            action="reviewed",
            reviewer="api_v1",
            stage="api",
        )
        return {"success": True, "dedup_key": dedup_key}
    except Exception as exc:
        return JSONResponse(
            status_code=503,
            content={"success": False, "dedup_key": dedup_key, "detail": str(exc)},
        )
