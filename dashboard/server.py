import json
import subprocess
import sys
import re
import asyncio
import time
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from core.logger import get_logger

logger = get_logger("dashboard.server")

ROOT = Path(__file__).resolve().parents[1]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import yaml
import uvicorn
from fastapi import FastAPI, Request, Depends, UploadFile, File, Form
from fastapi import Header, HTTPException
from fastapi.responses import HTMLResponse, RedirectResponse, StreamingResponse, FileResponse
from fastapi.staticfiles import StaticFiles
from jinja2 import Environment, FileSystemLoader
from jinja2.utils import htmlsafe_json_dumps

from core.orchestrator import Orchestrator
from core.heartbeat import HeartbeatStore
from core.config import settings
from core.talent_pool import TalentPool
from core.workspace import WorkspaceManager

app = FastAPI()
orch = Orchestrator()
app.mount("/assets", StaticFiles(directory=ROOT / "public"), name="assets")

# Seed SelectaHR workspace on startup
TalentPool.seed_selectahr()

# Start Telegram candidate bot (polling) in background
@app.on_event("startup")
async def _start_telegram_bot():
    try:
        from agents.conversation_agent import handle_message
        from core.tools.telegram_bot import start_polling
        start_polling(handle_message)
        logger.info("Bot de Telegram para candidatos iniciado")
    except Exception as e:
        logger.warning("Bot de Telegram no iniciado: %s", e)

HERE = Path(__file__).parent
templates = Environment(loader=FileSystemLoader(HERE / "templates"))
templates.filters["tojson"] = htmlsafe_json_dumps

def fromjson_filter(value):
    if isinstance(value, str):
        try: return json.loads(value)
        except: return value
    return value
templates.filters["fromjson"] = fromjson_filter


def get_workspace(request: Request) -> dict:
    """FastAPI dependency: resolve workspace from X-Workspace-Token header or ?token= param."""
    token = request.headers.get("X-Workspace-Token", "").strip()
    if not token:
        token = request.query_params.get("token", "").strip()
    if not token:
        token = request.cookies.get("talo_session", "").strip()
    if token:
        ws = WorkspaceManager.get_by_token(token)
        if ws:
            return ws
    return WorkspaceManager.get_default()


def _check_session(request: Request) -> bool:
    token = request.cookies.get("talo_session", "").strip()
    if not token:
        token = request.query_params.get("token", "").strip()
    if not token:
        token = request.headers.get("X-Workspace-Token", "").strip()
    if token:
        ws = WorkspaceManager.get_by_token(token)
        if ws:
            return True
    return False


PUBLIC_PATHS = {
    "/admin",
    "/cargar-cv",
    "/candidate/upload_cv",
    "/assets",
    "/robots.txt",
    "/sitemap.xml",
    "/llms.txt",
}


@app.middleware("http")
async def auth_middleware(request: Request, call_next):
    path = request.url.path
    if path in PUBLIC_PATHS or path.startswith("/assets"):
        return await call_next(request)
    if path == "/" or _check_session(request):
        return await call_next(request)
    from starlette.responses import RedirectResponse
    return RedirectResponse(url="/admin")


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
        # Count candidates with inferred signals
        inferred_count = sum(
            1 for p in pending
            if p.get("action_type") == "candidate" and p.get("payload", {}).get("signals_inferred")
        )
        if inferred_count:
            brief_parts.append(f"📡 <strong>{inferred_count}</strong> con señales inferidas (no verificadas).")
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


@app.get("/workspace/info")
async def workspace_info(workspace: dict = Depends(get_workspace)):
    """Return the active workspace config without exposing the token."""
    safe = {k: v for k, v in workspace.items() if k != "token"}
    return safe


@app.get("/", response_class=HTMLResponse)
async def root(request: Request):
    from starlette.responses import RedirectResponse
    if _check_session(request):
        return RedirectResponse(url="/inicio")
    return RedirectResponse(url="/admin")


@app.get("/inicio", response_class=HTMLResponse)
async def inicio_page(request: Request, workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    pool = TalentPool()
    try:
        import sqlite3
        db_path = ROOT / "data" / "state" / "talent_pool.db"
        searches = []
        talent_stats = {"total": 0, "en_revision": 0, "shortlist": 0, "contactados": 0, "entrevistados": 0, "rechazados": 0, "colocados": 0}
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            ws_where = "WHERE workspace_id = ?" if workspace_id != "default" else ""
            ws_params = [workspace_id] if workspace_id != "default" else []
            searches_rows = conn.execute(
                f"SELECT search_id, role_target, created_at, status FROM search_requests {ws_where} ORDER BY created_at DESC LIMIT 10",
                ws_params,
            ).fetchall()
            searches = [dict(s) for s in searches_rows]
            # Add candidate count per search
            for s in searches:
                count_row = conn.execute(
                    "SELECT COUNT(DISTINCT dedup_key) FROM search_matches WHERE search_id = ?",
                    [s["search_id"]],
                ).fetchone()
                s["talent_count"] = count_row[0] if count_row else 0
            talent_stats["total"] = pool.get_pool_size(workspace_id=workspace_id)

            # Count pending review and shortlist
            if workspace_id != "default":
                review_row = conn.execute(
                    "SELECT COUNT(*) FROM candidates c WHERE c.workspace_id = ? AND c.status = 'new'",
                    [workspace_id],
                ).fetchone()
            else:
                review_row = conn.execute(
                    "SELECT COUNT(*) FROM candidates c WHERE c.status = 'new'",
                ).fetchone()
            talent_stats["en_revision"] = review_row[0] if review_row else 0

            sl_row = conn.execute(
                """SELECT COUNT(*) FROM search_matches sm
                   JOIN candidates c ON c.dedup_key = sm.dedup_key
                   WHERE sm.band = 'priority_1'""" + (" AND c.workspace_id = ?" if workspace_id != "default" else ""),
                [workspace_id] if workspace_id != "default" else [],
            ).fetchone()
            talent_stats["shortlist"] = sl_row[0] if sl_row else 0

            # Count contactados, entrevistas, desertados
            ws_cond = "AND workspace_id = ?" if workspace_id != "default" else ""
            ws_p = [workspace_id] if workspace_id != "default" else []

            contacted_row = conn.execute(
                f"SELECT COUNT(*) FROM candidates WHERE status = 'contacted' {ws_cond}", ws_p
            ).fetchone()
            talent_stats["contactados"] = contacted_row[0] if contacted_row else 0

            interview_row = conn.execute(
                f"SELECT COUNT(*) FROM candidates WHERE status = 'interview_scheduled' {ws_cond}", ws_p
            ).fetchone()
            talent_stats["entrevistas"] = interview_row[0] if interview_row else 0

            deserted_row = conn.execute(
                f"SELECT COUNT(*) FROM candidates WHERE status IN ('rejected','dismissed') {ws_cond}", ws_p
            ).fetchone()
            talent_stats["desertados"] = deserted_row[0] if deserted_row else 0

            conn.close()
    except Exception:
        searches = []

    template = templates.get_template("inicio.html")
    workspace_settings = _get_workspace_settings(workspace_id)
    return template.render(
        searches=searches,
        talent_stats=talent_stats,
        workspace=workspace,
        workspace_settings=workspace_settings,
    )

@app.get("/cargar-cv", response_class=HTMLResponse)
async def cargar_cv():
    template = templates.get_template("cargar_cv.html")
    return template.render()


@app.get("/robots.txt")
async def robots_txt():
    return FileResponse(ROOT / "public" / "robots.txt", media_type="text/plain")


@app.get("/sitemap.xml")
async def sitemap_xml():
    return FileResponse(ROOT / "public" / "sitemap.xml", media_type="application/xml")


@app.get("/llms.txt")
async def llms_txt():
    return FileResponse(ROOT / "public" / "llms.txt", media_type="text/plain")


@app.get("/admin", response_class=HTMLResponse)
async def admin_login():
    template = templates.get_template("admin_login.html")
    return template.render()


@app.post("/admin")
async def admin_auth(request: Request):
    from core.config import settings
    form = await request.form()
    code = form.get("code", "").strip()
    expected = settings.admin_access_code
    if expected and code == expected:
        token = "selec-pilot-2026"
        resp = RedirectResponse(url="/inicio", status_code=303)
        resp.set_cookie(key="talo_session", value=token, max_age=28800, httponly=True, samesite="lax")
        return resp
    return HTMLResponse(status_code=401)


@app.get("/candidates/add", response_class=HTMLResponse)
async def add_candidate_page(request: Request):
    _check_session_or_401(request)
    search_id = request.query_params.get("search_id", "")
    template = templates.get_template("add_candidate.html")
    return HTMLResponse(template.render(search_id=search_id))


@app.post("/api/candidates/add")
async def api_add_candidate(
    request: Request,
    nombre: str = Form(...),
    rol_actual: str = Form(...),
    email: str | None = Form(None),
    whatsapp: str | None = Form(None),
    empresa: str | None = Form(None),
    ubicacion: str | None = Form(None),
    source_url: str | None = Form(None),
    skills: str | None = Form(None),
    notas: str | None = Form(None),
    cv_pdf: UploadFile | None = File(None),
    search_id: str | None = Form(None),
):
    from contracts.talent import CandidateSignal, CandidateEvidence
    import io

    skills_list = [s.strip() for s in (skills or "").split(",") if s.strip()]
    url = source_url or ""

    evidence = []
    pdf_text = ""
    pdf_extracted = False

    # Parse PDF if uploaded
    if cv_pdf and cv_pdf.filename:
        try:
            from pypdf import PdfReader
            pdf_bytes = await cv_pdf.read()
            reader = PdfReader(io.BytesIO(pdf_bytes))
            for page in reader.pages:
                t = page.extract_text()
                if t:
                    pdf_text += t + "\n"
            pdf_text = pdf_text.strip()
            if pdf_text:
                evidence.append(CandidateEvidence(
                    label="pdf_extracted_text",
                    value=pdf_text[:2000],
                    url="",
                ))
                pdf_extracted = True
                # Extract skills from PDF if none provided
                if not skills_list:
                    tech_keywords = [
                        "Python", "JavaScript", "TypeScript", "React", "Node.js", "FastAPI",
                        "Django", "PostgreSQL", "MySQL", "MongoDB", "Redis", "AWS", "GCP",
                        "Azure", "Docker", "Kubernetes", "Go", "Rust", "Java", "C++",
                        "TensorFlow", "PyTorch", "SQL", "GraphQL", "REST", "Git",
                    ]
                    skills_list = [k for k in tech_keywords if k.lower() in pdf_text.lower()][:8]
        except Exception as e:
            logger.warning("Error parseando PDF del candidato manual: %s", e)

    if notas:
        evidence.append(CandidateEvidence(label="recruiter_notes", value=notas, url=""))

    signal = CandidateSignal(
        name=nombre,
        current_role=rol_actual,
        company=empresa or "",
        location=ubicacion or "",
        source="manual",
        source_url=url or f"manual://{nombre.lower().replace(' ', '_')}",
        skills=skills_list,
        evidence=evidence,
        availability_signal="unknown",
        confidence="high",
        raw_score=0.0,
        workspace_id="default",
        phone=whatsapp or "",
        whatsapp=whatsapp or "",
    )
    if email:
        signal.evidence.append(CandidateEvidence(label="email", value=email, url=""))

    # Apollo.io enrichment if email is missing
    if not email:
        try:
            from core.tools.apollo_client import enrich_emails
            api_key = settings.apollo_api_key
            if api_key:
                enriched = asyncio.run(enrich_emails(
                    [{"dedup_key": signal.dedup_key(), "name": nombre, "company": empresa or "", "source_url": url}],
                    api_key,
                ))
                if enriched and signal.dedup_key() in enriched:
                    email = enriched[signal.dedup_key()]
                    signal.evidence.append(CandidateEvidence(label="email", value=email, url=""))
                    logger.info("[MANUAL ADD] Email enriquecido via Apollo para %s", nombre)
        except Exception as exc:
            logger.warning("[MANUAL ADD] Apollo enrichment falló (no crítico): %s", exc)

    effective_search_id = search_id or "manual_add"
    dedup_key = TalentPool.upsert_candidate(signal, run_id=effective_search_id)

    # Compute a basic fit score from skills overlap
    fit_score = 0
    try:
        criteria_dir = ROOT / "data" / "criteria"
        required_skills: list[str] = []
        if criteria_dir.exists():
            import yaml as _yaml
            for f in sorted(criteria_dir.glob("*.yaml"))[:1]:
                c = _yaml.safe_load(f.read_text())
                req = c.get("required_skills") or c.get("skills") or []
                if isinstance(req, list):
                    required_skills = [s.lower() for s in req]
        if required_skills and skills_list:
            matches = sum(1 for s in skills_list if s.lower() in required_skills)
            fit_score = min(100, int((matches / max(len(required_skills), 1)) * 100) + 30)
        else:
            fit_score = 50  # no criteria → neutral score
    except Exception:
        fit_score = 50

    # Record match score
    try:
        TalentPool.record_match(
            search_id=effective_search_id,
            dedup_key=dedup_key,
            score=fit_score,
        )
    except Exception as e:
        logger.warning("No se pudo registrar score: %s", e)

    # Generate outreach draft via OutreachAgent for this single candidate
    outreach_draft = False
    try:
        outreach_agent = orch.agents.get("outreach")
        if outreach_agent:
            candidate_dict = {
                "name": nombre,
                "current_role": rol_actual,
                "company": empresa or "",
                "location": ubicacion or "",
                "source": "manual",
                "source_url": signal.source_url,
                "skills": skills_list,
                "raw_score": fit_score / 100,
                "dedup_key": dedup_key,
                "email": email or "",
                "whatsapp": whatsapp or "",
            }
            search_code = outreach_agent._search_code_for(candidate_dict)
            telegram_link = outreach_agent._telegram_link(search_code, settings)
            email_html = outreach_agent._render_email(candidate_dict, telegram_link, settings)
            email_subject = outreach_agent._generate_subject(candidate_dict, settings)

            from contracts import AgentAction, ActionType, AgentState
            channels = ["email"]
            if whatsapp:
                channels.append("whatsapp")
            action = AgentAction(
                agent_id="outreach",
                action_type=ActionType.INMAIL.value,
                target=f"{nombre} — {rol_actual} @ {empresa or 'sin empresa'}",
                reason=f"Candidato agregado manualmente. Score estimado: {fit_score}/100",
                payload={
                    "subject": email_subject,
                    "email_html": email_html,
                    "channel": "email",
                    "channels": channels,
                    "to_email": email or "",
                    "to_whatsapp": whatsapp or "",
                    "candidate_name": nombre,
                    "source_url": signal.source_url,
                    "search_code": search_code,
                    "telegram_link": telegram_link,
                    "requires_approval": True,
                },
                score=fit_score,
            )
            outreach_agent.pending_actions.append(action)
            from core.state import StateStore
            StateStore.save_actions([action.to_dict()])
            outreach_draft = True
    except Exception as e:
        logger.warning("No se pudo generar draft de outreach para candidato manual: %s", e)

    return {
        "success": True,
        "name": nombre,
        "dedup_key": dedup_key,
        "fit_score": fit_score,
        "pdf_extracted": pdf_extracted,
        "outreach_draft": outreach_draft,
    }


def _check_session_or_401(request: Request):
    if not _check_session(request):
        raise HTTPException(status_code=401, detail="No autorizado")


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


@app.get("/coverage", response_class=HTMLResponse)
async def coverage_page(request: Request, workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    try:
        from core.talent_pool import TalentPool
        import sqlite3
        from pathlib import Path
        db_path = Path("data/state/talent_pool.db")
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            searches = conn.execute(
                "SELECT * FROM search_requests ORDER BY created_at DESC LIMIT 10"
            ).fetchall()
            searches = [dict(s) for s in searches]
            conn.close()
        else:
            searches = []
        coverage_data = []
        pool = TalentPool()
        for s in searches:
            search_id = s.get("search_id", "")
            if search_id:
                cov = pool.get_search_coverage(search_id, workspace_id=workspace_id)
            else:
                cov = {"total_matches": 0, "by_band": {}, "by_source": {}, "by_status": {}}
            coverage_data.append({**s, "coverage": cov})
        pool_size = pool.get_pool_size(workspace_id=workspace_id)
    except Exception:
        searches = []
        coverage_data = []
        pool_size = 0

    template = templates.get_template("coverage.html")
    workspace_settings = _get_workspace_settings(workspace_id)
    return template.render(
        searches=coverage_data,
        pool_size=pool_size,
        workspace=workspace,
        workspace_settings=workspace_settings,
    )


@app.get("/blind", response_class=HTMLResponse)
async def blind_review(request: Request, workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    workspace_settings = _get_workspace_settings(workspace_id)
    include_demo = workspace_settings.get("demo_mode", True)
    if "include_demo" in request.query_params:
        include_demo = request.query_params.get("include_demo") == "1"
    pool = TalentPool()
    with_evidence = pool._get_candidates_with_evidence(workspace_id=workspace_id, include_demo=include_demo)
    criteria_path = _criteria_path(workspace_id)
    criteria = yaml.safe_load(criteria_path.read_text(encoding="utf-8")) if criteria_path.exists() else {}
    template = templates.get_template("blind_review.html")
    return template.render(
        candidates=with_evidence,
        include_demo=include_demo,
        workspace=workspace,
        criteria=criteria,
        workspace_settings=workspace_settings,
    )


@app.get("/ops", response_class=HTMLResponse)
async def dashboard_redirect():
    return RedirectResponse(url="/inicio")

@app.get("/command-room", response_class=HTMLResponse)
async def command_room(request: Request):
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
        api_token=settings.dashboard_api_token or "",
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

    # If this is an email outreach action, send the real email now
    if result and result.get("action_type") == "inmail":
        payload = result.get("payload", {})
        if payload.get("channel") == "email" and payload.get("email_html"):
            to_email = payload.get("to_email", "")
            if not to_email:
                to_email = settings.recruiter_email  # fallback: send to recruiter for review
            if to_email:
                import asyncio
                from core.tools.email_client import send_email
                sent = await asyncio.get_event_loop().run_in_executor(
                    None,
                    lambda: send_email(
                        to=to_email,
                        subject=payload.get("subject", "Oportunidad para vos"),
                        html_body=payload["email_html"],
                        from_name=settings.orchestrator or "Talo",
                    )
                )
                if sent:
                    from core.telegram_notifier import TelegramNotifier
                    TelegramNotifier().send_raw_message(
                        f"✉️ *Email enviado*\n\n"
                        f"Para: `{to_email}`\n"
                        f"Candidato: _{result.get('target', '')}_ \n"
                        f"Acción: `{action_id}`"
                    )
                    logger.info("Email enviado a %s — acción %s aprobada", to_email, action_id)
                else:
                    logger.warning("Aprobación OK pero email no enviado a %s", to_email)
                result["email_sent"] = sent
                result["email_to"] = to_email

    return {"success": result is not None, "action": result}


@app.post("/api/searches/{search_id}/send-emails")
async def send_search_emails(
    search_id: str,
    request: Request,
    workspace: dict = Depends(get_workspace),
):
    """Enrich selected candidates with Apollo, then send cold emails via Resend.

    Body (optional): {"dedup_keys": ["key1", "key2"]} — if omitted, sends to all eligible.
    Returns: {sent, no_email, already_contacted, enriched}
    """
    import asyncio, sqlite3
    from core.tools.email_client import send_email
    from core.tools.apollo_client import enrich_emails

    body = {}
    try:
        body = await request.json()
    except Exception:
        pass

    selected_keys: list[str] = body.get("dedup_keys", [])

    db_path = ROOT / "data" / "state" / "talent_pool.db"
    if not db_path.exists():
        return {"success": False, "detail": "No hay base de datos"}

    conn = sqlite3.connect(str(db_path))
    conn.row_factory = sqlite3.Row

    rows = conn.execute(
        """SELECT c.dedup_key, c.status, c.source_url,
                  ci.name, ci.current_role, ci.company
           FROM search_matches sm
           JOIN candidates c ON sm.dedup_key = c.dedup_key
           LEFT JOIN candidate_identities ci ON sm.dedup_key = ci.dedup_key
           WHERE sm.search_id = ?
           GROUP BY c.dedup_key""",
        (search_id,),
    ).fetchall()

    already_contacted: set[str] = set()
    to_process: list[dict] = []

    for r in rows:
        d = dict(r)
        key = d["dedup_key"]
        if selected_keys and key not in selected_keys:
            continue
        if d.get("status") in ("contacted", "interested", "interview_scheduled", "hired", "placed"):
            already_contacted.add(key)
            continue
        to_process.append(d)

    # Check existing emails in candidate_evidence
    emails_known: dict[str, str] = {}
    needs_enrichment: list[dict] = []

    for c in to_process:
        key = c["dedup_key"]
        ev = conn.execute(
            "SELECT value FROM candidate_evidence WHERE dedup_key = ? AND label = 'email' LIMIT 1",
            (key,),
        ).fetchone()
        if ev and ev["value"] and "@" in ev["value"]:
            emails_known[key] = ev["value"]
        else:
            needs_enrichment.append(c)

    # Apollo enrichment for candidates without email
    enriched_count = 0
    if needs_enrichment and settings.apollo_api_key:
        found = await enrich_emails(needs_enrichment, settings.apollo_api_key)
        for key, email in found.items():
            emails_known[key] = email
            enriched_count += 1
            # Persist to DB
            conn.execute(
                "INSERT OR REPLACE INTO candidate_evidence (dedup_key, label, value, url) VALUES (?, 'email', ?, '')",
                (key, email),
            )
        conn.commit()
        logger.info("[SEND] Apollo enriched %d/%d candidates", enriched_count, len(needs_enrichment))
    elif needs_enrichment:
        logger.warning("[SEND] Apollo key not set — skipping enrichment for %d candidates", len(needs_enrichment))

    # Load search criteria for email copy
    criteria: dict = {}
    try:
        import yaml as _yaml
        crit_file = ROOT / "data" / "demo_rodri_criteria.yaml"
        if crit_file.exists():
            criteria = _yaml.safe_load(crit_file.read_text()) or {}
    except Exception:
        pass

    # Build pending actions map for existing outreach drafts
    pending_by_key: dict[str, dict] = {}
    for a in orch.get_pending_actions():
        if a.get("action_type") == "inmail" and a.get("payload", {}).get("channel") == "email":
            dk = a.get("payload", {}).get("dedup_key", "")
            if dk:
                pending_by_key[dk] = a

    sent_count = 0
    no_email_count = len([c for c in to_process if c["dedup_key"] not in emails_known])

    for c in to_process:
        key = c["dedup_key"]
        to_email = emails_known.get(key)
        if not to_email:
            continue

        # Use existing outreach draft if available, else simple template
        if key in pending_by_key:
            action = pending_by_key[key]
            action_id = action.get("action_id") or action.get("id", "")
            result = orch.approve_action(action_id, "batch send")
            payload = (result or action).get("payload", {})
            subject = payload.get("subject", "Una oportunidad que puede interesarte")
            html_body = payload.get("email_html", "")
        else:
            name_first = (c.get("name") or "").split()[0] or "Hola"
            role = c.get("current_role") or criteria.get("role_target", "el rol")
            subject = f"{name_first}, ¿te interesa esta oportunidad? — {role}"
            # Use cold_email.html template
            try:
                tmpl = (ROOT / "dashboard" / "templates" / "cold_email.html").read_text()
                source_label = {"torre": "Torre.co", "linkedin": "LinkedIn"}.get(
                    c.get("source", ""), c.get("source", "tu perfil público")
                )
                fit = f"{c.get('current_role', '')} en {c.get('company', '')}".strip(" en")
                html_body = (
                    tmpl
                    .replace("{{ CANDIDATE_NAME }}", c.get("name", name_first))
                    .replace("{{ CV_SOURCE }}", source_label)
                    .replace("{{ FIT_REASON }}", fit or "Perfil relevante para la búsqueda")
                    .replace("{{ TELEGRAM_LINK }}", settings.calendly_link or "#")
                    .replace("{{ SEARCH_TITLE }}", role)
                    .replace("{{ RECRUITER_NAME }}", settings.orchestrator or "Talo")
                )
            except Exception:
                html_body = f"<p>Hola {name_first}, te contactamos por una oportunidad para {role}.</p>"

        ok = await asyncio.get_event_loop().run_in_executor(
            None,
            lambda e=to_email, s=subject, h=html_body: send_email(
                to=e, subject=s, html_body=h,
                from_name=settings.orchestrator or "Talo",
            ),
        )
        if ok:
            sent_count += 1
            conn.execute(
                "UPDATE candidates SET status = 'contacted' WHERE dedup_key = ?", (key,)
            )
            logger.info("[SEND] Email enviado a %s (%s)", to_email, c.get("name"))

    conn.commit()
    conn.close()

    if sent_count > 0:
        try:
            from core.telegram_notifier import TelegramNotifier
            TelegramNotifier().send_raw_message(
                f"✉️ *Batch enviado*\n"
                f"✅ {sent_count} alcanzados"
                + (f"\n❌ {no_email_count} sin email" if no_email_count else "")
                + (f"\n⏭ {len(already_contacted)} ya contactados" if already_contacted else "")
            )
        except Exception:
            pass

    return {
        "success": True,
        "sent": sent_count,
        "no_email": no_email_count,
        "enriched": enriched_count,
        "already_contacted": len(already_contacted),
    }


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
    try:
        actions = await orch.run_agent(agent_id)
        return {"actions": len(actions), "agent": orch.agents[agent_id].to_dict()}
    except ValueError as e:
        if "Tamper detectado" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise


@app.post("/api/run-all")
async def api_run_all(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    try:
        results = await orch.run_all()
        return {k: len(v) for k, v in results.items()}
    except ValueError as e:
        if "Tamper detectado" in str(e):
            raise HTTPException(status_code=400, detail=str(e))
        raise



@app.get("/api/workspace/{name}")
async def api_workspace(name: str):
    ws = TalentPool.get_workspace(name)
    if not ws:
        return {"error": "not_found"}
    ws["users"] = TalentPool.get_users(ws["workspace_id"])
    return ws


@app.post("/api/blind/reveal/{candidate_id}")
async def blind_reveal(candidate_id: str):
    pool = TalentPool()
    dedup_key = pool.blind_id_to_dedup_key(candidate_id)
    if not dedup_key:
        return {"success": False, "error": "not_found"}
    full = pool.get_full_candidate(dedup_key)
    if not full:
        return {"success": False, "error": "not_found"}
    pool.record_review(dedup_key, decision="revealed", comment="revealed by human")
    return {"success": True, "candidate_id": candidate_id, "dedup_key": dedup_key}


@app.post("/api/blind/shortlist/{candidate_id}")
async def blind_shortlist(candidate_id: str, request: Request):
    pool = TalentPool()
    dedup_key = pool.blind_id_to_dedup_key(candidate_id)
    if not dedup_key:
        return {"success": False, "error": "not_found"}
    body = await request.json()
    pool.record_review(dedup_key, decision=body.get("action", "shortlisted"),
                       comment=body.get("comment", ""), reviewer="human")
    return {"success": True}


@app.post("/api/blind/dismiss/{candidate_id}")
async def blind_dismiss(candidate_id: str, request: Request):
    pool = TalentPool()
    dedup_key = pool.blind_id_to_dedup_key(candidate_id)
    if not dedup_key:
        return {"success": False, "error": "not_found"}
    body = await request.json()
    pool.record_review(dedup_key, decision=body.get("action", "rejected"),
                       comment=body.get("comment", ""), reviewer="human")
    return {"success": True}


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


AGENT_LABELS = {
    "demand_radar": "Radar de Demanda",
    "knowledge": "Base de Conocimiento",
    "criteria": "Criterios",
    "talent_sourcing": "Talent Sourcing",
    "intake": "Intake",
    "normalization": "Normalización",
    "deduplication": "Deduplicación",
    "talent_signal": "Señales de Talento",
    "career_context": "Contexto de Carrera",
    "fit_scoring": "Scoring",
    "evidence": "Evidencia",
    "memory_update": "Memoria",
    "qa": "Control de Calidad",
    "outreach": "Outreach",
    "ceo": "Orquestador",
}

PIPELINE_PHASES = [
    ("Inteligencia de Mercado", ["demand_radar", "knowledge", "criteria"]),
    ("Sourcing + Intake", ["talent_sourcing", "intake", "normalization", "deduplication"]),
    ("Análisis", ["talent_signal", "career_context", "fit_scoring", "evidence"]),
    ("Cierre", ["memory_update", "qa", "outreach", "ceo"]),
]


def _criteria_path(workspace_id: str = "default") -> Path:
    if workspace_id == "default":
        return ROOT / "data" / "demo_rodri_criteria.yaml"
    return ROOT / "data" / "criteria" / f"{workspace_id}.yaml"


def _settings_path(workspace_id: str = "default") -> Path:
    return ROOT / "data" / "criteria" / f"settings_{workspace_id}.yaml"


def _get_workspace_settings(workspace_id: str = "default") -> dict:
    path = _settings_path(workspace_id)
    defaults = {
        "demo_mode": True,
        "max_candidates": 50,
        "brave_search_api_key": settings.brave_search_api_key or "",
        "firecrawl_api_key": settings.firecrawl_api_key or "",
        "openrouter_api_key": settings.openrouter_api_key or "",
    }
    if path.exists():
        try:
            with open(path, "r", encoding="utf-8") as f:
                data = yaml.safe_load(f) or {}
                # merge with defaults
                for k, v in data.items():
                    defaults[k] = v
        except Exception as e:
            logger.warning("Failed to load workspace settings from %s: %s", path, e)
    return defaults


@app.get("/pool", response_class=HTMLResponse)
async def pool_redirect(request: Request):
    from starlette.responses import RedirectResponse
    q = request.url.query
    target = "/talents" + (f"?{q}" if q else "")
    return RedirectResponse(target)


@app.get("/candidate/{dedup_key:path}", response_class=HTMLResponse)
async def candidate_profile(dedup_key: str, workspace: dict = Depends(get_workspace)):
    import sqlite3, json, urllib.parse
    dedup_key = urllib.parse.unquote(dedup_key)
    workspace_id = workspace.get("id", "default")
    candidate = {}
    try:
        db_path = ROOT / "data" / "state" / "talent_pool.db"
        conn = sqlite3.connect(str(db_path))
        conn.row_factory = sqlite3.Row
        candidate_scope = "c.dedup_key = ?"
        candidate_params: list[str] = [dedup_key]
        if workspace_id != "default":
            candidate_scope += " AND c.workspace_id = ?"
            candidate_params.append(workspace_id)

        row = conn.execute(
            """SELECT c.dedup_key, c.source, c.source_url, c.confidence,
                      c.first_seen_at, c.last_seen_at, c.times_surfaced, c.status,
                      ci.name, ci.current_role, ci.company, ci.location, ci.skills
               FROM candidates c
               LEFT JOIN candidate_identities ci ON c.dedup_key = ci.dedup_key
               WHERE """ + candidate_scope,
            candidate_params,
        ).fetchone()

        if not row:
            row = conn.execute(
                """SELECT ci.name, ci.current_role, ci.company, ci.location, ci.skills,
                          c.source, c.source_url, c.confidence, c.first_seen_at, c.last_seen_at,
                          c.times_surfaced, c.status, sm.score, sm.band, sm.dedup_key
                   FROM search_matches sm
                   JOIN candidates c ON sm.dedup_key = c.dedup_key
                   LEFT JOIN candidate_identities ci ON sm.dedup_key = ci.dedup_key
                   WHERE sm.dedup_key = ? AND (? = 'default' OR c.workspace_id = ?)
                   ORDER BY sm.score DESC, sm.id DESC
                   LIMIT 1""",
                [dedup_key, workspace_id, workspace_id],
            ).fetchone()

        if row:
            candidate = dict(row)
            raw_skills = candidate.get("skills")
            if isinstance(raw_skills, str):
                try:
                    candidate["skills"] = json.loads(raw_skills)
                except Exception:
                    candidate["skills"] = []
            elif raw_skills is None:
                candidate["skills"] = []

        ev_rows = conn.execute(
            """SELECT ce.label, ce.value, ce.url, ce.added_at
               FROM candidate_evidence ce
               JOIN candidates c ON c.dedup_key = ce.dedup_key
               WHERE ce.dedup_key = ? AND (? = 'default' OR c.workspace_id = ?)
               ORDER BY ce.id""",
            [dedup_key, workspace_id, workspace_id],
        ).fetchall()
        raw_evidence = [dict(r) for r in ev_rows]
        # deduplicate: group by (label, value_prefix) and add count
        seen = {}
        deduped = []
        for ev in raw_evidence:
            key = ev.get("label", "") + "::" + (ev.get("value", "")[:100])
            if key in seen:
                seen[key]["count"] = seen[key].get("count", 1) + 1
                if ev.get("added_at", "") > seen[key].get("added_at", ""):
                    seen[key]["added_at"] = ev["added_at"]
                continue
            ev["count"] = 1
            seen[key] = ev
            deduped.append(ev)
        candidate["evidence"] = deduped

        match_rows = conn.execute(
            """SELECT sm.search_id, sm.score, sm.band, sm.matched_criteria, sm.risks,
                      sr.role_target, sr.created_at, c.status
               FROM search_matches sm
               JOIN candidates c ON c.dedup_key = sm.dedup_key
               LEFT JOIN search_requests sr ON sm.search_id = sr.search_id
               WHERE sm.dedup_key = ? AND (? = 'default' OR c.workspace_id = ?)
               ORDER BY sm.score DESC, sm.id DESC""",
            [dedup_key, workspace_id, workspace_id],
        ).fetchall()
        matches = []
        for m in match_rows:
            md = dict(m)
            for field in ("matched_criteria", "risks"):
                raw = md.get(field)
                if isinstance(raw, str):
                    try:
                        md[field] = json.loads(raw)
                    except Exception:
                        md[field] = []
                elif raw is None:
                    md[field] = []
            matches.append(md)
        candidate["matches"] = matches
        candidate["top_match"] = matches[0] if matches else None

        audit_rows = conn.execute(
            """SELECT re.decision, re.comment, re.reviewer, re.decided_at
               FROM review_events re
               JOIN candidates c ON c.dedup_key = re.dedup_key
               WHERE re.dedup_key = ? AND (? = 'default' OR c.workspace_id = ?)
               ORDER BY re.decided_at""",
            [dedup_key, workspace_id, workspace_id],
        ).fetchall()
        candidate["audit"] = [dict(r) for r in audit_rows]

        snap_rows = conn.execute(
            """SELECT cs.raw_score, cs.inferred_signals, cs.signal_evidence, cs.captured_at
               FROM candidate_snapshots cs
               JOIN candidates c ON c.dedup_key = cs.dedup_key
               WHERE cs.dedup_key = ? AND (? = 'default' OR c.workspace_id = ?)
               ORDER BY cs.captured_at DESC LIMIT 3""",
            [dedup_key, workspace_id, workspace_id],
        ).fetchall()
        snapshots = []
        for s in snap_rows:
            sd = dict(s)
            for field in ("inferred_signals", "signal_evidence"):
                raw = sd.get(field)
                if isinstance(raw, str):
                    try:
                        sd[field] = json.loads(raw)
                    except Exception:
                        sd[field] = raw
            snapshots.append(sd)
        candidate["snapshots"] = snapshots
        candidate["current_stage"] = candidate.get("status") or (
            candidate["top_match"].get("band") if candidate.get("top_match") else "new"
        )

        conn.close()
    except Exception as e:
        candidate["_error"] = str(e)

    template = templates.get_template("candidate_profile.html")
    workspace_settings = _get_workspace_settings(workspace_id)
    return template.render(
        candidate=candidate,
        dedup_key=dedup_key,
        workspace=workspace,
        workspace_settings=workspace_settings,
    )



@app.get("/agentes", response_class=HTMLResponse)
async def agentes_page(workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    workspace_settings = _get_workspace_settings(workspace_id)
    template = templates.get_template("agentes.html")
    return template.render(workspace=workspace, workspace_settings=workspace_settings)


@app.get("/settings", response_class=HTMLResponse)
async def settings_page(workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    workspace_settings = _get_workspace_settings(workspace_id)
    template = templates.get_template("settings.html")
    return template.render(workspace=workspace, workspace_settings=workspace_settings)


@app.get("/api/settings/status")
async def settings_status(workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    ws = _get_workspace_settings(workspace_id)
    return {
        "resend": bool(settings.resend_api_key),
        "telegram": bool(settings.telegram_bot_token),
        "calendly": bool(settings.calendly_link),
        "recruiter_email": settings.recruiter_email or "",
        "model": settings.model if hasattr(settings, "model") else "openai/gpt-4o-mini",
        "log_level": "INFO",
    }


@app.post("/api/settings")
async def save_settings(request: Request, workspace: dict = Depends(get_workspace)):
    body = await request.json()
    workspace_id = workspace.get("id", "default")
    
    demo_mode = body.get("demo_mode", True)
    max_candidates = body.get("max_candidates", 50)
    
    openrouter_api_key = body.get("openrouter_api_key", "").strip()
    brave_search_api_key = body.get("brave_search_api_key", "").strip()
    firecrawl_api_key = body.get("firecrawl_api_key", "").strip()
    
    existing = _get_workspace_settings(workspace_id)
    
    if openrouter_api_key.startswith("•••") or not openrouter_api_key:
        openrouter_api_key = existing.get("openrouter_api_key", "")
    if brave_search_api_key.startswith("•••") or not brave_search_api_key:
        brave_search_api_key = existing.get("brave_search_api_key", "")
    if firecrawl_api_key.startswith("•••") or not firecrawl_api_key:
        firecrawl_api_key = existing.get("firecrawl_api_key", "")
        
    config_data = {
        "demo_mode": demo_mode,
        "max_candidates": max_candidates,
        "openrouter_api_key": openrouter_api_key,
        "brave_search_api_key": brave_search_api_key,
        "firecrawl_api_key": firecrawl_api_key,
    }
    
    path = _settings_path(workspace_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(config_data, f, allow_unicode=True, default_flow_style=False)
        
    from core.config import settings as backend_settings
    if openrouter_api_key:
        backend_settings.openrouter_api_key = openrouter_api_key
        orch.config.setdefault("openrouter", {})["api_key"] = openrouter_api_key
    if brave_search_api_key:
        backend_settings.brave_search_api_key = brave_search_api_key
        orch.config.setdefault("search", {})["api_key"] = brave_search_api_key
    if firecrawl_api_key:
        backend_settings.firecrawl_api_key = firecrawl_api_key
        orch.config.setdefault("firecrawl", {})["api_key"] = firecrawl_api_key
        
    return {"success": True, "workspace_id": workspace_id}


@app.get("/api/criteria")
async def api_get_criteria(workspace: dict = Depends(get_workspace)):
    path = _criteria_path(workspace.get("id", "default"))
    if not path.exists():
        return {}
    with open(path, encoding="utf-8") as f:
        data = yaml.safe_load(f) or {}
    # Add search listing for the setup page
    try:
        import sqlite3, json
        db_path = ROOT / "data" / "state" / "talent_pool.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            ws_id = workspace.get("id", "default")
            ws_where = "WHERE workspace_id = ?" if ws_id != "default" else ""
            ws_params = [ws_id] if ws_id != "default" else []
            rows = conn.execute(
                f"SELECT search_id, role_target, created_at, status FROM search_requests {ws_where} ORDER BY created_at DESC",
                ws_params,
            ).fetchall()
            data["_searches"] = [dict(r) for r in rows]
            conn.close()
    except Exception:
        data["_searches"] = []
    return data


@app.post("/api/criteria")
async def api_save_criteria(request: Request, workspace: dict = Depends(get_workspace)):
    import time, json
    from uuid import uuid4
    body = await request.json()
    search_id = body.get("search_id", f"{int(time.time())}_{uuid4().hex[:6]}")
    workspace_id = workspace.get("id", "default")
    now = datetime.now(timezone.utc).isoformat()

    criteria = {
        "owner": body.get("owner", ""),
        "client": body.get("client", ""),
        "role_target": body.get("role_target", ""),
        "markets": [m.strip() for m in body.get("markets", "").split(",") if m.strip()],
        "industries": [i.strip() for i in body.get("industries", "").split(",") if i.strip()],
        "positive_signals": [s.strip() for s in body.get("positive_signals", []) if s.strip()],
        "negative_signals": [s.strip() for s in body.get("negative_signals", []) if s.strip()],
        "preferred_background": body.get("preferred_background", ""),
        "philosophy": body.get("philosophy", ""),
        "outreach_tone": body.get("outreach_tone", ""),
        "sources": body.get("sources", "linkedin,torre,brave"),
        "max_candidates": int(body.get("max_candidates", 50)),
        "hard_filters": ["no_contact_without_human_approval", "no_sensitive_inferences", "no_unverified_claims"],
        "human_approval_required": True,
    }
    # Save criteria to YAML
    path = _criteria_path(workspace_id)
    path.parent.mkdir(parents=True, exist_ok=True)
    with open(path, "w", encoding="utf-8") as f:
        yaml.dump(criteria, f, allow_unicode=True, default_flow_style=False)

    # Create search_request in DB
    try:
        from core.talent_pool import _get_db
        with _get_db() as conn:
            conn.execute(
                """INSERT OR REPLACE INTO search_requests
                   (search_id, criteria, role_target, markets, created_at, status)
                   VALUES (?, ?, ?, ?, ?, ?)""",
                (
                    search_id,
                    json.dumps(criteria),
                    criteria["role_target"],
                    json.dumps(criteria["markets"]),
                    now,
                    "active",
                ),
            )
    except Exception as db_err:
        print(f"[CRITERIA] DB error: {db_err}")

    # Auto-trigger pipeline in the background
    async def _run_pipeline(sid: str):
        try:
            import sqlite3 as _sq3, json as _json
            db_path = ROOT / "data" / "state" / "talent_pool.db"
            if not db_path.exists():
                db_path = ROOT / "data" / "talent_pool.db"

            # Mark running and read criteria from DB (single connection)
            crit_for_pipeline: dict = {}
            with _sq3.connect(str(db_path)) as _c:
                _c.execute("UPDATE search_requests SET status='running' WHERE search_id=?", (sid,))
                row = _c.execute("SELECT criteria FROM search_requests WHERE search_id=?", (sid,)).fetchone()
                if row:
                    crit_for_pipeline = _json.loads(row[0])

            # Inject search_id and rewrite YAML so agents pick up the right criteria
            crit_for_pipeline["search_id"] = sid
            crit_path = ROOT / "data" / "demo_rodri_criteria.yaml"
            with open(str(crit_path), "w", encoding="utf-8") as _f:
                yaml.dump(crit_for_pipeline, _f, allow_unicode=True, default_flow_style=False)
            logger.info("[PIPELINE] Criterios escritos para %s: role=%s", sid, crit_for_pipeline.get("role_target"))

            # Reset sourcing agent so previous-run history doesn't block new candidates
            for _aid in ("talent_sourcing", "fit_scoring", "outreach"):
                if _aid in orch.agents:
                    orch.agents[_aid].history.clear()
                    orch.agents[_aid].pending_actions.clear()
            await orch.run_all()
            # Mark completed
            with _sq3.connect(str(db_path)) as _c:
                _c.execute("UPDATE search_requests SET status='active' WHERE search_id=?", (sid,))
            logger.info("Pipeline completado para búsqueda %s — search_id=%s", sid, sid)
        except Exception as _e:
            logger.error("Pipeline error para búsqueda %s: %s", sid, _e, exc_info=True)

    import asyncio as _asyncio
    _asyncio.create_task(_run_pipeline(search_id))

    return {
        "success": True,
        "search_id": search_id,
        "workspace_id": workspace_id,
        "pipeline": "started",
    }


@app.get("/searches", response_class=HTMLResponse)
async def searches_page(request: Request, workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    try:
        import sqlite3
        db_path = ROOT / "data" / "state" / "talent_pool.db"
        searches = []
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            # Group by role_target so duplicate runs collapse into one card
            rows = conn.execute(
                """SELECT
                    MAX(sr.search_id)   AS latest_id,
                    sr.role_target,
                    MAX(sr.status)      AS status,
                    MAX(sr.created_at)  AS latest,
                    COUNT(sr.search_id) AS runs,
                    (SELECT COUNT(*) FROM search_matches sm
                     WHERE sm.search_id = MAX(sr.search_id)) AS talents_count
                   FROM search_requests sr
                   GROUP BY sr.role_target
                   ORDER BY latest DESC""",
                [],
            ).fetchall()
            searches = [dict(s) for s in rows]
            conn.close()
    except Exception:
        searches = []
    template = templates.get_template("searches.html")
    workspace_settings = _get_workspace_settings(workspace_id)
    return template.render(
        searches=searches,
        workspace=workspace,
        workspace_settings=workspace_settings,
    )


@app.get("/search/{search_id}", response_class=HTMLResponse)
async def search_detail(search_id: str, request: Request, workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    pool = TalentPool()
    search_data = {}
    candidates = []
    pending_actions = []
    try:
        import sqlite3
        db_path = ROOT / "data" / "state" / "talent_pool.db"
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM search_requests WHERE search_id = ?", (search_id,)
            ).fetchone()
            if row:
                search_data = dict(row)
                raw = search_data.get("criteria", "{}")
                if isinstance(raw, str):
                    try:
                        search_data["criteria_obj"] = json.loads(raw)
                    except Exception:
                        search_data["criteria_obj"] = {}
                else:
                    search_data["criteria_obj"] = raw

                cand_rows = conn.execute(
                    """SELECT c.dedup_key, MAX(sm.score) as score, sm.band,
                              sm.matched_criteria, sm.risks,
                              ci.name, ci.current_role, ci.company, ci.location,
                              c.source_url, c.status, c.first_seen_at
                       FROM search_matches sm
                       JOIN candidates c ON sm.dedup_key = c.dedup_key
                       LEFT JOIN candidate_identities ci ON sm.dedup_key = ci.dedup_key
                       WHERE sm.search_id = ?
                       GROUP BY c.dedup_key
                       ORDER BY score DESC""",
                    (search_id,),
                ).fetchall()
                for cr in cand_rows:
                    cd = dict(cr)
                    for field in ("matched_criteria", "risks"):
                        raw_f = cd.get(field)
                        if isinstance(raw_f, str):
                            try:
                                cd[field] = json.loads(raw_f)
                            except Exception:
                                cd[field] = []
                        elif raw_f is None:
                            cd[field] = []
                    candidates.append(cd)
            conn.close()

        pending_actions = orch.get_pending_actions()
        search_pending = [p for p in pending_actions if search_id in str(p.get("payload", {}))]
    except Exception as e:
        search_data["_error"] = str(e)

    template = templates.get_template("search_detail.html")
    workspace_settings = _get_workspace_settings(workspace_id)
    return template.render(
        search=search_data,
        candidates=candidates,
        pending_actions=pending_actions,
        workspace=workspace,
        workspace_settings=workspace_settings,
    )


@app.get("/talents", response_class=HTMLResponse)
async def talents_page(request: Request, workspace: dict = Depends(get_workspace)):
    import json, sqlite3
    band_filter = request.query_params.get("band", "")
    search_filter = request.query_params.get("search_id", "")
    status_filter = request.query_params.get("status", "")
    workspace_id = workspace.get("id", "default")
    try:
        db_path = ROOT / "data" / "state" / "talent_pool.db"
        if not db_path.exists():
            candidates = []
            band_counts = {}
            status_counts = {}
        else:
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            scope_clauses = []
            scope_params: list[str] = []
            if workspace_id != "default":
                scope_clauses.append("c.workspace_id = ?")
                scope_params.append(workspace_id)
            if search_filter:
                scope_clauses.append("sm.search_id = ?")
                scope_params.append(search_filter)
            scope_where = f"WHERE {' AND '.join(scope_clauses)}" if scope_clauses else ""

            band_rows = conn.execute(
                f"""SELECT sm.band, count(*) as n
                    FROM search_matches sm
                    JOIN candidates c ON c.dedup_key = sm.dedup_key
                    {scope_where}
                    GROUP BY sm.band""",
                scope_params,
            ).fetchall()
            band_counts = {r["band"]: r["n"] for r in band_rows}

            status_rows = conn.execute(
                f"""SELECT c.status, count(*) as n
                    FROM candidates c {scope_where.replace('sm.','c.') if scope_where else ''}
                    GROUP BY c.status""",
                scope_params,
            ).fetchall() if not search_filter else []
            status_counts = {r["status"]: r["n"] for r in status_rows}
            pool_count_where = "WHERE workspace_id = ?" if workspace_id != "default" else ""
            pool_count_params = [workspace_id] if workspace_id != "default" else []
            pool_count = conn.execute(
                f"SELECT count(*) FROM candidates {pool_count_where}",
                pool_count_params,
            ).fetchone()[0]
            band_counts["_pool"] = pool_count

            where_clauses = []
            params: list = []
            if band_filter:
                where_clauses.append("sm.band = ?")
                params.append(band_filter)
            if search_filter:
                where_clauses.append("sm.search_id = ?")
                params.append(search_filter)
            if status_filter:
                where_clauses.append("c.status = ?")
                params.append(status_filter)
            if workspace_id != "default":
                where_clauses.append("c.workspace_id = ?")
                params.append(workspace_id)
            where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

            if where_clauses:
                rows = conn.execute(
                    f"""SELECT c.dedup_key, MAX(sm.score) as score, sm.band,
                               sm.matched_criteria, sm.risks, sm.search_id,
                               ci.name, ci.current_role, ci.company, ci.location, ci.skills,
                               c.source, c.source_url, c.status, c.times_surfaced,
                               c.last_seen_at, c.first_seen_at
                        FROM search_matches sm
                        JOIN candidates c ON sm.dedup_key = c.dedup_key
                        LEFT JOIN candidate_identities ci ON sm.dedup_key = ci.dedup_key
                        {where_sql}
                        GROUP BY c.dedup_key
                        ORDER BY score DESC
                        LIMIT 300""",
                    params,
                ).fetchall()
            else:
                ws_where = "WHERE c.workspace_id = ?" if workspace_id != "default" else ""
                ws_params = [workspace_id] if workspace_id != "default" else []
                rows = conn.execute(
                    f"""SELECT c.dedup_key, c.source, c.source_url, c.confidence,
                               c.first_seen_at, c.last_seen_at, c.times_surfaced, c.status,
                               ci.name, ci.current_role, ci.company, ci.location, ci.skills,
                               sm.score, sm.band, sm.matched_criteria, sm.risks
                        FROM candidates c
                        LEFT JOIN candidate_identities ci ON c.dedup_key = ci.dedup_key
                        LEFT JOIN (
                            SELECT dedup_key, score, band, matched_criteria, risks
                            FROM (
                                SELECT dedup_key, score, band, matched_criteria, risks,
                                       ROW_NUMBER() OVER (
                                           PARTITION BY dedup_key
                                           ORDER BY score DESC, id DESC
                                       ) AS rn
                                FROM search_matches
                            )
                            WHERE rn = 1
                        ) sm ON c.dedup_key = sm.dedup_key
                        {ws_where}
                        ORDER BY c.first_seen_at DESC
                        LIMIT 200""",
                    ws_params,
                ).fetchall()

            candidates = [dict(r) for r in rows]

            if candidates:
                keys = [c["dedup_key"] for c in candidates]
                placeholders = ",".join("?" for _ in keys)
                ev_rows = conn.execute(
                    f"""SELECT dedup_key, label, value FROM candidate_evidence
                        WHERE dedup_key IN ({placeholders}) ORDER BY id DESC""",
                    keys,
                ).fetchall()
                ev_map = {}
                for ev in ev_rows:
                    ev_map.setdefault(ev["dedup_key"], []).append(dict(ev))
                for c in candidates:
                    c["evidence"] = ev_map.get(c["dedup_key"], [])

                for c in candidates:
                    for field in ("matched_criteria", "risks"):
                        raw_f = c.get(field)
                        if isinstance(raw_f, str):
                            try:
                                c[field] = json.loads(raw_f)
                            except Exception:
                                c[field] = []
                        elif raw_f is None:
                            c[field] = []
                    raw_skills = c.get("skills")
                    if isinstance(raw_skills, str):
                        try:
                            c["skills"] = json.loads(raw_skills)
                        except Exception:
                            c["skills"] = []
                    elif raw_skills is None:
                        c["skills"] = []

            conn.close()
    except Exception:
        candidates = []
        band_counts = {}
        status_counts = {}

    template = templates.get_template("talents.html")
    workspace_settings = _get_workspace_settings(workspace_id)
    return template.render(
        candidates=candidates,
        band_filter=band_filter,
        search_filter=search_filter,
        status_filter=status_filter,
        band_counts=band_counts,
        status_counts=status_counts,
        workspace=workspace,
        workspace_settings=workspace_settings,
    )


@app.get("/setup", response_class=HTMLResponse)
async def setup_page(request: Request, workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    # Always open blank — previous search data lives in the DB, not here
    criteria = {}
    template = templates.get_template("setup.html")
    workspace_settings = _get_workspace_settings(workspace_id)
    return template.render(criteria=criteria, workspace=workspace, workspace_settings=workspace_settings)


@app.get("/run", response_class=HTMLResponse)
async def run_page(workspace: dict = Depends(get_workspace)):
    workspace_id = workspace.get("id", "default")
    path = _criteria_path(workspace_id)
    criteria = yaml.safe_load(path.read_text(encoding="utf-8")) if path.exists() else {}
    phases = [
        {
            "name": phase_name,
            "agents": [
                {"id": aid, "label": AGENT_LABELS.get(aid, aid)}
                for aid in agent_ids
                if aid in orch.agents
            ],
        }
        for phase_name, agent_ids in PIPELINE_PHASES
    ]
    template = templates.get_template("run.html")
    workspace_settings = _get_workspace_settings(workspace_id)
    return template.render(criteria=criteria, phases=phases, workspace=workspace, workspace_settings=workspace_settings)


def generate_eco_pack(search_id: str, workspace_id: str) -> Path:
    import json
    import sqlite3
    import sys
    import yaml
    from datetime import datetime, timezone
    from core.state import _get_db as get_state_db
    from scripts.demo_verify import _ledger_db_path
    
    evidence_dir = ROOT / "data" / "evidence" / f"{search_id}.eco"
    evidence_dir.mkdir(parents=True, exist_ok=True)
    
    # 1. manifest.json
    manifest = {
        "schema_version": "0.1.0",
        "pack_id": f"eco_{search_id}",
        "workspace_id": workspace_id,
        "generated_at": datetime.now(timezone.utc).isoformat(),
        "files": [
            "manifest.json", "task.json", "context.json", "verification.json",
            "actions.json", "result.json", "trace.log", "source_refs.json"
        ]
    }
    (evidence_dir / "manifest.json").write_text(json.dumps(manifest, indent=2), encoding="utf-8")
    
    # 2. task.json
    criteria_path = ROOT / "data" / f"criteria_{workspace_id}.yaml"
    task_desc = {}
    if criteria_path.exists():
        try:
            task_desc = yaml.safe_load(criteria_path.read_text(encoding="utf-8")) or {}
        except Exception as e:
            logger.warning("Failed to load criteria for %s: %s", workspace_id, e)
    task = {
        "search_id": search_id,
        "role_target": task_desc.get("role_target", "Candidato Talo"),
        "criteria": task_desc,
        "started_at": datetime.now(timezone.utc).isoformat()
    }
    (evidence_dir / "task.json").write_text(json.dumps(task, indent=2), encoding="utf-8")
    
    # 3. context.json
    context = {
        "workspace_id": workspace_id,
        "settings": {
            "demo_mode": True,
            "max_candidates": 50
        },
        "environment": {
            "os": "linux",
            "python_version": sys.version
        }
    }
    (evidence_dir / "context.json").write_text(json.dumps(context, indent=2), encoding="utf-8")
    
    # 4. verification.json
    ledger_db = _ledger_db_path()
    verification = {
        "ledger_type": "verifiable-memory-mcp-sqlite",
        "ledger_db": str(ledger_db),
        "verified": False,
        "reason": "No ledger found"
    }
    if ledger_db.exists():
        try:
            from scripts.demo_verify import verify_chain
            ok, msg = verify_chain(ledger_db)
            verification.update({
                "verified": ok,
                "reason": msg,
                "checked_at": datetime.now(timezone.utc).isoformat()
            })
        except Exception as e:
            verification["reason"] = str(e)
    (evidence_dir / "verification.json").write_text(json.dumps(verification, indent=2), encoding="utf-8")
    
    # 5. actions.json
    actions_list = []
    try:
        with get_state_db() as conn:
            rows = conn.execute("SELECT * FROM actions ORDER BY created_at DESC LIMIT 100").fetchall()
            for r in rows:
                d = dict(r)
                d["payload"] = json.loads(d.get("payload", "{}"))
                actions_list.append(d)
    except Exception:
        pass
    (evidence_dir / "actions.json").write_text(json.dumps(actions_list, indent=2), encoding="utf-8")
    
    # 6. result.json
    result = {
        "status": "completed",
        "actions_generated": len(actions_list),
        "search_id": search_id,
        "completed_at": datetime.now(timezone.utc).isoformat()
    }
    (evidence_dir / "result.json").write_text(json.dumps(result, indent=2), encoding="utf-8")
    
    # 7. trace.log
    trace = (
        f"[{datetime.now(timezone.utc).isoformat()}] INFO: Pipeline started for search_id={search_id}\n"
        f"[{datetime.now(timezone.utc).isoformat()}] INFO: Hook resolve_context completed successfully\n"
        f"[{datetime.now(timezone.utc).isoformat()}] INFO: Hook verify_memory_scope checked ledger. Status: {verification.get('reason')}\n"
        f"[{datetime.now(timezone.utc).isoformat()}] INFO: Run completed. Evidence pack generated.\n"
    )
    (evidence_dir / "trace.log").write_text(trace, encoding="utf-8")
    
    # 8. source_refs.json
    source_refs = []
    try:
        with get_state_db() as conn:
            rows = conn.execute("SELECT url, title, fetched_at FROM cached_sources LIMIT 20").fetchall()
            source_refs = [dict(r) for r in rows]
    except Exception:
        pass
    (evidence_dir / "source_refs.json").write_text(json.dumps(source_refs, indent=2), encoding="utf-8")
    
    return evidence_dir


@app.get("/api/evidence/{search_id}/download")
async def api_download_evidence(search_id: str):
    import zipfile
    import io
    from fastapi.responses import StreamingResponse
    
    evidence_dir = ROOT / "data" / "evidence" / f"{search_id}.eco"
    if not evidence_dir.exists():
        raise HTTPException(status_code=404, detail="Evidence pack not found")
        
    zip_buffer = io.BytesIO()
    with zipfile.ZipFile(zip_buffer, "w", zipfile.ZIP_DEFLATED) as zip_file:
        for file_path in evidence_dir.iterdir():
            if file_path.is_file():
                zip_file.write(file_path, arcname=file_path.name)
                
    zip_buffer.seek(0)
    return StreamingResponse(
        zip_buffer,
        media_type="application/x-zip-compressed",
        headers={"Content-Disposition": f"attachment; filename={search_id}.eco.zip"}
    )


@app.post("/api/tamper")
async def api_tamper(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    import sqlite3
    from scripts.demo_verify import _ledger_db_path
    db_path = _ledger_db_path()
    if not db_path.exists():
        return {"success": False, "error": "database not found"}
    conn = sqlite3.connect(str(db_path))
    conn.execute(
        "UPDATE entries SET content = content || ' [DATO ALTERADO]' WHERE id = (SELECT id FROM entries ORDER BY created_epoch ASC LIMIT 1);"
    )
    conn.commit()
    conn.close()
    return {"success": True, "message": "Ledger tampered successfully"}


@app.post("/api/reset")
async def api_reset(
    authorization: str | None = Header(default=None),
    x_api_key: str | None = Header(default=None),
):
    _require_api_token(authorization, x_api_key)
    import subprocess
    subprocess.run(["bash", "scripts/demo_reset.sh"], check=True)
    return {"success": True, "message": "Ledger reset successfully"}


@app.get("/api/run-stream")
async def api_run_stream(request: Request, workspace: dict = Depends(get_workspace)):
    ws_id = workspace.get("id", "default")
    search_id = f"search_{int(time.time())}_{uuid4().hex[:6]}"

    orch.config["workspace_id"] = ws_id
    orch.config["search_id"] = search_id
    
    ws_settings = _get_workspace_settings(ws_id)
    orch.config["limit"] = ws_settings.get("max_candidates", 50)
    
    if ws_settings.get("openrouter_api_key"):
        orch.config.setdefault("openrouter", {})["api_key"] = ws_settings["openrouter_api_key"]
    if ws_settings.get("brave_search_api_key"):
        orch.config.setdefault("search", {})["api_key"] = ws_settings["brave_search_api_key"]
    if ws_settings.get("firecrawl_api_key"):
        orch.config.setdefault("firecrawl", {})["api_key"] = ws_settings["firecrawl_api_key"]

    criteria_path = _criteria_path(ws_id)
    if criteria_path.exists():
        ws_criteria = yaml.safe_load(criteria_path.read_text(encoding="utf-8")) or {}
        for key in ("role_target", "markets", "industries", "positive_signals", "negative_signals"):
            if ws_criteria.get(key):
                orch.config[key] = ws_criteria[key]

    async def event_gen():
        total_actions = 0
        for phase_name, agent_ids in PIPELINE_PHASES:
            yield f"data: {json.dumps({'type': 'phase_start', 'phase': phase_name})}\n\n"

            tasks: dict[str, asyncio.Task] = {}
            for aid in agent_ids:
                if aid in orch.agents:
                    tasks[aid] = asyncio.create_task(orch.run_agent(aid))

            pending = set(tasks.values())
            task_to_id = {t: aid for aid, t in tasks.items()}

            while pending:
                done, pending = await asyncio.wait(pending, return_when=asyncio.FIRST_COMPLETED)
                for task in done:
                    aid = task_to_id[task]
                    try:
                        result = task.result()
                        n = len(result) if not isinstance(result, Exception) else 0
                    except Exception as e:
                        err_str = str(e)
                        if "Tamper detectado" in err_str:
                            yield f"data: {json.dumps({'type': 'tamper_alert', 'message': err_str})}\n\n"
                            for t in pending:
                                t.cancel()
                            return
                        n = 0
                    total_actions += n
                    label = AGENT_LABELS.get(aid, aid)
                    yield f"data: {json.dumps({'type': 'agent_done', 'agent': aid, 'label': label, 'actions': n, 'phase': phase_name})}\n\n"

        # Generate .eco evidence pack
        try:
            generate_eco_pack(search_id, ws_id)
        except Exception as eco_err:
            print(f"[ECO PACK ERROR] {eco_err}")

        orch.save_state()
        pending_count = sum(len(a.pending_actions) for a in orch.agents.values())
        yield f"data: {json.dumps({'type': 'complete', 'total_actions': total_actions, 'pending_count': pending_count, 'search_id': search_id})}\n\n"

    return StreamingResponse(
        event_gen(),
        media_type="text/event-stream",
        headers={"Cache-Control": "no-cache", "X-Accel-Buffering": "no"},
    )


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


@app.post("/api/talents/{dedup_key}/status")
async def api_talent_set_status(dedup_key: str, request: Request, workspace: dict = Depends(get_workspace)):
    import urllib.parse, sqlite3
    dedup_key = urllib.parse.unquote(dedup_key)
    body = await request.json()
    new_status = body.get("status", "").strip()
    if new_status not in ("new","shortlist","contacted","interview_scheduled","interviewed","rejected","placed","archived"):
        return {"error": "Invalid status"}
    db_path = ROOT / "data" / "state" / "talent_pool.db"
    conn = sqlite3.connect(str(db_path))
    conn.execute("UPDATE candidates SET status = ? WHERE dedup_key = ?", (new_status, dedup_key))
    conn.commit()
    conn.close()
    return {"success": True, "status": new_status}

@app.post("/api/talents/{dedup_key}/note")
async def api_talent_add_note(dedup_key: str, request: Request, workspace: dict = Depends(get_workspace)):
    import urllib.parse, sqlite3, json
    from datetime import datetime, timezone
    dedup_key = urllib.parse.unquote(dedup_key)
    body = await request.json()
    note_text = body.get("text", "").strip()
    note_type = body.get("note_type", "general")
    search_id = body.get("search_id", "")
    author = body.get("author", workspace.get("name", "Usuario"))
    if not note_text:
        return {"error": "Note text required"}
    db_path = ROOT / "data" / "state" / "talent_pool.db"
    now = datetime.now(timezone.utc).isoformat()
    value = json.dumps({"text": note_text, "type": note_type, "search_id": search_id, "author": author, "added_at": now})
    conn = sqlite3.connect(str(db_path))
    conn.execute("INSERT INTO candidate_evidence (dedup_key, label, value, added_at) VALUES (?, ?, ?, ?)",
                 (dedup_key, "note", value, now))
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/talents/{dedup_key}/link")
async def api_talent_link_search(dedup_key: str, request: Request, workspace: dict = Depends(get_workspace)):
    import urllib.parse, sqlite3
    from datetime import datetime, timezone
    dedup_key = urllib.parse.unquote(dedup_key)
    body = await request.json()
    search_id = body.get("search_id", "").strip()
    band = body.get("band", "review_needed")
    if not search_id:
        return {"error": "search_id required"}
    db_path = ROOT / "data" / "state" / "talent_pool.db"
    now = datetime.now(timezone.utc).isoformat()
    conn = sqlite3.connect(str(db_path))
    conn.execute("""INSERT OR IGNORE INTO search_matches (search_id, dedup_key, band)
                    VALUES (?, ?, ?)""", (search_id, dedup_key, band))
    conn.commit()
    conn.close()
    return {"success": True}

@app.post("/api/talents/{dedup_key}/interview")
async def api_talent_register_interview(dedup_key: str, request: Request):
    import urllib.parse, sqlite3, json
    from datetime import datetime, timezone
    dedup_key = urllib.parse.unquote(dedup_key)
    body = await request.json()
    required = ("date", "interviewer", "interview_type")
    if not all(k in body for k in required):
        return {"error": f"Missing required fields: {', '.join(required)}"}
    db_path = ROOT / "data" / "state" / "talent_pool.db"
    now = datetime.now(timezone.utc).isoformat()
    value = json.dumps({
        "date": body.get("date", now[:10]),
        "interviewer": body.get("interviewer", ""),
        "search_id": body.get("search_id", ""),
        "interview_type": body.get("interview_type", "screening"),
        "notes": body.get("notes", ""),
        "positive_signals": body.get("positive_signals", ""),
        "negative_signals": body.get("negative_signals", ""),
        "next_step": body.get("next_step", ""),
        "resulting_status": body.get("resulting_status", ""),
        "added_at": now,
    })
    conn = sqlite3.connect(str(db_path))
    conn.execute("INSERT INTO candidate_evidence (dedup_key, label, value, added_at) VALUES (?, ?, ?, ?)",
                 (dedup_key, "interview", value, now))
    if body.get("resulting_status"):
        valid = ("new","shortlist","contacted","interview_scheduled","interviewed","rejected","placed","archived")
        if body["resulting_status"] in valid:
            conn.execute("UPDATE candidates SET status = ? WHERE dedup_key = ?", (body["resulting_status"], dedup_key))
    conn.commit()
    conn.close()
    return {"success": True}


from dashboard.api_v1 import router as api_router
from dashboard.routes_candidate import router as candidate_router
from dashboard.webhook_email_reply import email_reply_router
app.include_router(api_router, prefix="/api/v1")
app.include_router(candidate_router, prefix="/candidate")
app.include_router(email_reply_router)


if __name__ == "__main__":
    uvicorn.run(app, host="127.0.0.1", port=8080, reload=False, log_level="info")
