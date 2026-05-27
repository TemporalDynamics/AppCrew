import json
import subprocess
import sys
import re
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml
import uvicorn
from fastapi import FastAPI, Request
from fastapi import Header, HTTPException
from fastapi.responses import HTMLResponse
from jinja2 import Environment, FileSystemLoader

from core.orchestrator import Orchestrator
from core.heartbeat import HeartbeatStore
from core.config import settings

app = FastAPI()
orch = Orchestrator()

HERE = Path(__file__).parent
templates = Environment(loader=FileSystemLoader(HERE / "templates"))


def _require_api_token(authorization: str | None, x_api_key: str | None) -> None:
    expected = settings.dashboard_api_token
    if not expected:
        return
    bearer = ""
    if authorization:
        parts = authorization.strip().split(" ", 1)
        if len(parts) == 2 and parts[0].lower() == "bearer":
            bearer = parts[1].strip()
    token = bearer or (x_api_key or "").strip()
    if token != expected:
        raise HTTPException(status_code=401, detail="unauthorized")


def _build_brief(status: dict, pending: list[dict]) -> dict:
    agents = status.get("agents", {})
    total_pending = len(pending)
    total_history = status.get("total_history", 0)
    last_runs = status.get("last_runs", [])
    high_priority = [p for p in pending if p.get("score", 0) >= 80]

    # ── Agent state analysis ──
    errors = []
    blocked = []
    working = []
    pending_review = []
    idle = []
    for aid, a in agents.items():
        s = a.get("state", "")
        if s == "error": errors.append(a.get("name", aid))
        elif s in ("pending_review",): pending_review.append(a.get("name", aid))
        elif s == "working": working.append(a.get("name", aid))
        elif s == "idle": idle.append(a.get("name", aid))

    # ── Risks ──
    risks = []
    for p in pending:
        payload_str = str(p.get("payload", {}))
        if "mock" in payload_str.lower():
            risks.append({"item": p.get("target", ""), "risk": "datos mock/demo"})
        if p.get("action_type") == "inmail":
            risks.append({"item": p.get("target", ""), "risk": "requiere aprobación humana"})

    # ── QA issues ──
    qa_agent = orch.agents.get("qa")
    qa_issues = len([a for a in qa_agent.history if a.action_type == "quality_issue"]) if qa_agent else 0
    qa_pending = len([a for a in qa_agent.pending_actions if a.action_type == "quality_issue"]) if qa_agent else 0

    # ── Action-type breakdown ──
    by_type = {}
    for p in pending:
        at = p.get("action_type", "unknown")
        by_type[at] = by_type.get(at, 0) + 1

    # ── Brief text ──
    brief_parts = []

    if errors:
        brief_parts.append(f"⚠️ <strong>{' y '.join(errors)}</strong> en estado de error. Revisar antes de continuar.")

    if qa_pending > 0:
        brief_parts.append(f"🔍 <strong>QA</strong> detectó <strong>{qa_issues} incidencias</strong> de calidad ({qa_pending} sin revisar).")
    elif qa_issues > 0:
        brief_parts.append(f"✅ <strong>QA</strong> inspeccionó todo — {qa_issues} incidencias ya revisadas.")

    if risks:
        risk_items = [r["risk"] for r in risks[:2]]
        brief_parts.append(f"⚠️ Riesgos activos: {' y '.join(risk_items)}.")

    if by_type.get("inmail", 0) > 0:
        brief_parts.append(f"✉️ <strong>{by_type['inmail']} draft(s)</strong> de Outreach listos para aprobación.")
    if by_type.get("candidate", 0) > 0:
        brief_parts.append(f"🎯 <strong>{by_type['candidate']} candidato(s)</strong> nuevos por revisar.")
    if by_type.get("quality_issue", 0) > 0:
        brief_parts.append(f"🔧 <strong>{by_type['quality_issue']} issue(s)</strong> de calidad pendientes.")

    if total_history > 0 and not brief_parts:
        brief_parts.append(f"📊 Último run produjo <strong>{total_history} acciones</strong>. Todas revisadas.")
    if not total_history > 0:
        brief_parts.append("💤 Sistema en estado inicial. No hay ejecuciones registradas.")

    if total_pending == 0 and not errors:
        brief_parts.append("✅ No hay decisiones pendientes ni riesgos activos.")

    brief = " ".join(brief_parts) if brief_parts else "Sistema operativo nominal."

    # ── Recommendation ──
    if errors:
        recommendation = f"Revisar agentes en error: {', '.join(errors)}."
    elif high_priority:
        types_high = {}
        for p in high_priority:
            at = p.get("action_type", "")
            types_high[at] = types_high.get(at, 0) + 1
        detail = ", ".join(f"{v} {k}" for k, v in types_high.items())
        recommendation = f"Revisar Decision Inbox: {detail} de alta prioridad."
    elif pending_review and total_pending > 0:
        recommendation = f"Revisar los {total_pending} items pendientes en Decision Inbox."
    else:
        recommendation = "Ejecutar un nuevo run o asignar una tarea al CEO."

    kpi_data = [
        {"label": "Pendientes", "value": total_pending, "color": "var(--warning)"},
        {"label": "Historial", "value": total_history, "color": "var(--text-primary)"},
        {"label": "Agentes", "value": len(agents), "color": "var(--accent)"},
        {"label": "Runs", "value": status.get("total_runs", 0), "color": "var(--success)"},
    ]
    for at, count in by_type.items():
        icons = {"inmail": "✉️", "candidate": "🎯", "opportunity": "📡", "quality_issue": "🔧", "score": "📊", "qa_summary": "📋", "folder_structure": "📁", "context_signal": "🏢"}
        kpi_data.append({"label": icons.get(at, "•") + " " + at, "value": count, "color": "var(--text-secondary)"})

    return {
        "brief": brief,
        "recommendation": recommendation,
        "pending_high": len(high_priority),
        "risks": risks[:5],
        "qa_issues": qa_issues,
        "qa_pending": qa_pending,
        "by_type": by_type,
        "kpi_data": kpi_data,
    }


@app.get("/", response_class=HTMLResponse)
async def landing():
    template = templates.get_template("landing.html")
    return template.render()


@app.get("/shortlist", response_class=HTMLResponse)
async def shortlist_view():
    cache_path = ROOT / "data" / "shortlist_cache.json"
    data: dict = {}
    if cache_path.exists():
        try:
            data = json.loads(cache_path.read_text(encoding="utf-8"))
        except Exception:
            data = {}
    template = templates.get_template("shortlist.html")
    return template.render(
        shortlist=data.get("shortlist", []),
        golden_calibration=data.get("golden_calibration", []),
        golden_total=data.get("golden_total", 0),
        brief=data.get("brief", {}),
        cells=data.get("cells", []),
    )


@app.get("/ops", response_class=HTMLResponse)
async def dashboard(request: Request):
    presentation = request.query_params.get("mode", "") == "presentation"
    status = orch.get_status()
    pending = orch.get_pending_actions()
    brief = _build_brief(status, pending)

    ceo = orch.agents.get("ceo")
    ceo_history = ceo.get_conversation()[-6:] if ceo else []

    timeline = []
    for r in status.get("last_runs", []):
        timeline.append({
            "run_id": r.get("run_id", ""),
            "agent_id": r.get("agent_id", ""),
            "actions": r.get("actions_created", 0),
            "time": r.get("started_at", "")[11:19] if r.get("started_at") else "",
        })

    template = templates.get_template("command_room.html")
    return template.render(
        status=status,
        pending=pending,
        brief=brief,
        ceo_history=ceo_history,
        timeline=timeline,
        presentation=presentation,
    )


@app.get("/ceo", response_class=HTMLResponse)
async def ceo_page():
    ceo = orch.agents.get("ceo")
    status = orch.get_status()
    template = templates.get_template("ceo.html")
    return template.render(
        status=status,
        conversation=ceo.get_conversation() if ceo else [],
    )


@app.post("/api/ceo/task")
async def api_ceo_task(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    body = await request.json()
    result = await orch.run_task(body.get("task", ""))
    return result


@app.get("/api/status")
async def api_status():
    return orch.get_status()


@app.get("/api/pending")
async def api_pending():
    return {"pending": orch.get_pending_actions()}


@app.post("/api/approve/{action_id}")
async def api_approve(
    action_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    body = await request.json()
    result = orch.approve_action(action_id, body.get("comment", ""))
    return {"success": result is not None, "action": result}


@app.post("/api/reject/{action_id}")
async def api_reject(
    action_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    body = await request.json()
    result = orch.reject_action(action_id, body.get("comment", ""))
    return {"success": result is not None, "action": result}


@app.post("/api/review/{action_id}")
async def api_review(
    action_id: str,
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    body = await request.json()
    result = orch.review_action(action_id, body.get("action", "acknowledged"), body.get("comment", ""))
    return {"success": result is not None, "action": result}


@app.get("/api/review-options/{action_id}")
async def api_review_options(action_id: str):
    for agent in orch.agents.values():
        for action in agent.pending_actions:
            if action.action_id == action_id:
                return {"action_id": action_id, "action_type": action.action_type, "options": action.get_available_reviews()}
        for action in agent.history:
            if action.action_id == action_id:
                return {"action_id": action_id, "action_type": action.action_type, "options": action.get_available_reviews()}
    return {"error": "action not found", "options": ["approved", "rejected"]}


@app.post("/api/run/{agent_id}")
async def api_run_agent(
    agent_id: str,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    import asyncio
    actions = await orch.run_agent(agent_id)
    return {"actions": len(actions), "agent": orch.agents[agent_id].to_dict()}


@app.post("/api/run-all")
async def api_run_all(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    import asyncio
    results = await orch.run_all()
    return {k: len(v) for k, v in results.items()}


@app.get("/api/agent/{agent_id}")
async def api_agent_detail(agent_id: str):
    detail = orch.get_agent_detail(agent_id)
    return detail or {"error": "agent not found"}


@app.post("/api/load-demo")
async def api_load_demo(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    """Clears state, runs all agents, saves — ready for demo.
    The tester runs sub-agents internally, so run_all() returns 0 for them.
    We report actual pending actions from each agent."""
    orch.clear_state()
    await orch.run_all()
    orch.save_state()
    pending_by_agent = {
        aid: len(orch.agents[aid].pending_actions)
        for aid in orch.agents
        if len(orch.agents[aid].pending_actions) > 0
    }
    total = sum(pending_by_agent.values())
    return {
        "success": True,
        "total_actions": total,
        "by_agent": pending_by_agent,
    }


@app.get("/api/tester-results")
async def api_tester_results():
    tester = orch.agents.get("tester")
    if not tester:
        return {"error": "tester not found"}
    return tester.get_summary()


@app.get("/api/heartbeats")
async def api_heartbeats():
    return HeartbeatStore.get_all()


@app.get("/api/heartbeat/{agent_id}")
async def api_heartbeat(agent_id: str):
    hb = HeartbeatStore.get(agent_id)
    if not hb:
        return {"error": f"no heartbeat for agent {agent_id}"}
    return hb


@app.get("/api/sources/firecrawl/test")
async def api_firecrawl_test(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    from core.tools.firecrawl_client import FirecrawlClient
    client = FirecrawlClient(orch.config.get("firecrawl", {}).get("api_key", ""))
    return await client.test_connection()


@app.post("/api/sources/firecrawl/scrape")
async def api_firecrawl_scrape(
    request: Request,
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    from core.tools.firecrawl_client import FirecrawlClient

    body = await request.json()
    url = (body.get("url") or "").strip()
    if not url:
        return {"success": False, "error": "missing_url"}
    if not (url.startswith("http://") or url.startswith("https://")):
        return {"success": False, "error": "invalid_url"}

    client = FirecrawlClient(orch.config.get("firecrawl", {}).get("api_key", ""))
    if not client.is_real_available:
        return {
            "success": False,
            "error": "firecrawl_api_key_missing",
            "message": "Configura firecrawl.api_key o FIRECRAWL_API_KEY para scrape real.",
        }

    raw = await client.scrape_url(url)
    if not raw:
        return {"success": False, "error": "scrape_failed_or_blocked"}

    text_sources = []
    for key in ("markdown", "content", "rawHtml", "html"):
        val = raw.get(key)
        if isinstance(val, str) and val.strip():
            text_sources.append(val)
    joined = "\n".join(text_sources)

    # Heurística ligera para perfiles públicos de Instagram.
    username_match = re.search(r"instagram\.com/([A-Za-z0-9._]+)/?", url)
    username = username_match.group(1) if username_match else ""
    bio_match = re.search(r"Bio[:\s]+(.{1,240})", joined, flags=re.IGNORECASE)
    followers_match = re.search(r"([0-9][0-9.,]*)\s+followers", joined, flags=re.IGNORECASE)
    following_match = re.search(r"([0-9][0-9.,]*)\s+following", joined, flags=re.IGNORECASE)
    posts_match = re.search(r"([0-9][0-9.,]*)\s+posts", joined, flags=re.IGNORECASE)

    return {
        "success": True,
        "url": url,
        "source_type": "real",
        "public_profile": {
            "username": username,
            "bio_guess": bio_match.group(1).strip() if bio_match else "",
            "followers_guess": followers_match.group(1) if followers_match else "",
            "following_guess": following_match.group(1) if following_match else "",
            "posts_guess": posts_match.group(1) if posts_match else "",
        },
        "raw": raw,
    }


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080, reload=False, log_level="info")
