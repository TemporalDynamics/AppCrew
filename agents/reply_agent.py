"""
ReplyAgent — clasifica respuestas a cold emails y toma acción.

Intenciones:
  INTERESADO      → genera segundo email con link de Telegram
  PIDE_INFO       → genera respuesta informativa
  NO_INTERESADO   → archiva el candidato en TalentPool
  OTRO            → escala al recruiter para revisión manual
"""
from __future__ import annotations

from core.logger import get_logger

logger = get_logger("agents.reply_agent")

CLASSIFICATION_PROMPT = """Clasificá la siguiente respuesta a un cold email de reclutamiento.

Email original enviado a: {candidate_name}
Respuesta recibida:
---
{reply_text}
---

Respondé SOLO con una de estas etiquetas (sin texto adicional):
INTERESADO | PIDE_INFO | NO_INTERESADO | OTRO
"""

REPLY_INTERESTED = """Hola {candidate_name},

Me alegra que te interese. El próximo paso es una charla rápida de 20 minutos.

Podés chatear con nuestro asistente por Telegram para coordinar:
{telegram_link}

O si preferís, respondé este email con tu disponibilidad y lo arreglamos directamente.

Saludos,
{recruiter_name}
"""

REPLY_INFO = """Hola {candidate_name},

Con gusto te cuento más.

{info_response}

¿Hay algo más específico que quieras saber?

Saludos,
{recruiter_name}
"""


def classify_intent(reply_text: str, candidate_name: str) -> str:
    """Classify the intent of an email reply using LLM."""
    try:
        from core.tools.llm_client import LLMClient
        client = LLMClient()
        prompt = CLASSIFICATION_PROMPT.format(
            candidate_name=candidate_name,
            reply_text=reply_text[:1000],
        )
        result = client.complete(prompt).strip().upper()
        for intent in ("INTERESADO", "PIDE_INFO", "NO_INTERESADO", "OTRO"):
            if intent in result:
                return intent
        return "OTRO"
    except Exception as e:
        logger.error("Error clasificando reply: %s", e)
        return "OTRO"


def handle_email_reply(
    candidate_name: str,
    candidate_email: str,
    reply_text: str,
    search_code: str = "",
) -> dict:
    """
    Process an incoming email reply from a candidate.
    Returns a dict with: intent, action_taken, response_sent.
    """
    from core.config import settings

    intent = classify_intent(reply_text, candidate_name)
    logger.info("Reply de %s clasificada como: %s", candidate_name, intent)

    result = {"intent": intent, "action_taken": None, "response_sent": False}

    if intent == "NO_INTERESADO":
        _archive_candidate(candidate_name, candidate_email)
        result["action_taken"] = "archived"

    elif intent == "INTERESADO":
        telegram_link = _telegram_link(search_code, settings)
        body = REPLY_INTERESTED.format(
            candidate_name=candidate_name.split()[0],
            telegram_link=telegram_link or settings.calendly_link or "(link próximamente)",
            recruiter_name=settings.orchestrator or "El equipo de Talo",
        )
        sent = _send_reply(
            to=candidate_email,
            subject=f"Re: Oportunidad — siguiente paso",
            body_text=body,
        )
        result["action_taken"] = "sent_telegram_link"
        result["response_sent"] = sent

    elif intent == "PIDE_INFO":
        info = _generate_info_response(reply_text)
        body = REPLY_INFO.format(
            candidate_name=candidate_name.split()[0],
            info_response=info,
            recruiter_name=settings.orchestrator or "El equipo de Talo",
        )
        sent = _send_reply(
            to=candidate_email,
            subject=f"Re: Más información",
            body_text=body,
        )
        result["action_taken"] = "sent_info"
        result["response_sent"] = sent

    else:  # OTRO — escalar al recruiter
        _notify_recruiter_for_review(candidate_name, candidate_email, reply_text)
        result["action_taken"] = "escalated_to_recruiter"

    return result


def _send_reply(to: str, subject: str, body_text: str) -> bool:
    from core.tools.email_client import send_email
    html_body = body_text.replace("\n", "<br>")
    return send_email(to=to, subject=subject, html_body=f"<p>{html_body}</p>")


def _archive_candidate(name: str, email: str) -> None:
    logger.info("Archivando candidato %s (%s) — no interesado", name, email)


def _generate_info_response(reply_text: str) -> str:
    try:
        from core.tools.llm_client import LLMClient
        client = LLMClient()
        prompt = (
            f"Un candidato respondió un cold email de reclutamiento con:\n\n{reply_text[:500]}\n\n"
            f"Escribí UNA respuesta informativa breve (máx 3 oraciones) que responda su pregunta "
            f"de forma genérica sobre una posición tech en LATAM. En español, tono profesional pero amigable."
        )
        return client.complete(prompt).strip()
    except Exception:
        return "Esta es una posición a tiempo completo en modalidad remota, con excelente ambiente de trabajo y oportunidades de crecimiento."


def _notify_recruiter_for_review(name: str, email: str, reply_text: str) -> None:
    from core.telegram_notifier import TelegramNotifier
    notifier = TelegramNotifier()
    msg = (
        f"📩 *Reply de candidato requiere tu atención*\n\n"
        f"👤 *{name}* ({email})\n\n"
        f"Mensaje:\n_{reply_text[:300]}_\n\n"
        f"Clasificado como: `OTRO` — revisión manual necesaria."
    )
    notifier.send_raw_message(msg)


def _telegram_link(search_code: str, settings) -> str:
    username = getattr(settings, "telegram_bot_username", "") or ""
    if username and search_code:
        return f"https://t.me/{username}?start={search_code}"
    return ""
