"""
Webhook para respuestas a emails enviados via Resend.

Configurar en el dashboard de Resend:
  Evento: email.replied (o usar el evento genérico con inbound email)
  URL: https://tu-dominio.com/webhook/email-reply

Para activar en server.py: app.include_router(email_reply_router)
"""
from __future__ import annotations

from fastapi import APIRouter, Request
from fastapi.responses import JSONResponse

from agents.reply_agent import handle_email_reply
from core.logger import get_logger

logger = get_logger("dashboard.webhook_email_reply")

email_reply_router = APIRouter()


@email_reply_router.post("/webhook/email-reply")
async def handle_resend_reply(request: Request):
    """Receive Resend inbound/reply webhook and dispatch to ReplyAgent."""
    try:
        body = await request.json()
    except Exception:
        return JSONResponse(status_code=400, content={"error": "Invalid JSON"})

    logger.info("Webhook email-reply recibido: %s", list(body.keys()))

    # Resend inbound email payload structure
    from_email = body.get("from", "")
    from_name = body.get("fromName", "") or from_email.split("@")[0]
    reply_text = body.get("text") or body.get("html") or ""
    subject = body.get("subject", "")

    # Extract search code from headers if Resend forwards them
    headers = body.get("headers", {})
    search_code = headers.get("X-Talo-Search-Code", "")

    if not from_email or not reply_text:
        return JSONResponse(status_code=200, content={"status": "ignored", "reason": "empty payload"})

    result = handle_email_reply(
        candidate_name=from_name,
        candidate_email=from_email,
        reply_text=reply_text,
        search_code=search_code,
    )

    logger.info("Reply de %s procesada: intent=%s action=%s",
                from_email, result.get("intent"), result.get("action_taken"))

    return {"status": "ok", **result}
