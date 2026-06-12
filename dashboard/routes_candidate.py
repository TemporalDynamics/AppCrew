from fastapi import APIRouter, Request, UploadFile, File, Form
from fastapi.responses import HTMLResponse, JSONResponse
from jinja2 import Environment, FileSystemLoader
from pathlib import Path

router = APIRouter()
HERE = Path(__file__).parent
templates = Environment(loader=FileSystemLoader(HERE / "templates"))

@router.get("/portal", response_class=HTMLResponse)
async def candidate_portal(request: Request):
    template = templates.get_template("candidate_portal.html")
    # Dummy data for gamification presentation
    candidate_data = {
        "name": "Alex Developer",
        "role": "Senior Backend Engineer",
        "talo_score": 75,
        "level": 3,
        "daily_mission": {
            "title": "Escenario: Incidente de Producción",
            "description": "Tu réplica principal de la base de datos acaba de perder sincronización durante el Black Friday. Describe tus primeras 3 acciones para mitigar el impacto sin perder transacciones.",
            "points": 15
        },
        "peer_interview": {
            "title": "Entrevista P2P (Peer-to-Peer)",
            "description": "Te han emparejado con otro talento para una entrevista de diseño de sistemas de 15 minutos. Hoy tomarás el rol de ENTREVISTADOR.",
            "points": 25
        }
    }
    return template.render(candidate=candidate_data)

@router.post("/upload_cv")
async def upload_cv(
    file: UploadFile | None = File(None),
    mode: str = Form("upload"),
    nombre: str | None = Form(None),
    email: str | None = Form(None),
    linkedin: str | None = Form(None),
    ubicacion: str | None = Form(None),
    rol_actual: str | None = Form(None),
    anios_experiencia: str | None = Form(None),
    resumen: str | None = Form(None),
):
    # Stub intake endpoint for both CV upload and manual profile entry.
    if file is not None:
        return JSONResponse({
            "success": True,
            "mode": "upload",
            "filename": file.filename,
            "message": "CV cargado exitosamente. La IA lo está analizando.",
        })

    has_manual_profile = any([
        nombre,
        email,
        linkedin,
        ubicacion,
        rol_actual,
        anios_experiencia,
        resumen,
    ])
    if mode == "manual" and has_manual_profile:
        return JSONResponse({
            "success": True,
            "mode": "manual",
            "message": "Perfil recibido. Ya tenemos tu información para analizarla mejor.",
        })

    return JSONResponse(
        {"success": False, "message": "Necesitamos un CV o un perfil básico para continuar."},
        status_code=400,
    )

@router.post("/submit_mission")
async def submit_mission(request: Request):
    data = await request.json()
    answer = data.get("answer", "")
    # Gamification Hook: Pass answer to fit_scoring agent to evaluate quality
    return JSONResponse({
        "success": True, 
        "points_earned": 15, 
        "new_score": 90, 
        "message": "¡Misión completada! +15 Talo Score."
    })
