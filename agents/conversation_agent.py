"""
ConversationAgent — califica candidatos via Telegram.

Estado por chat_id:
  NUEVO           → saludo + primera pregunta
  CALIFICANDO     → hace 3-4 preguntas clave
  LISTO           → envía link de Calendly
  NO_INTERESADO   → cierra con dignidad
  ARCHIVADO       → ignorar mensajes posteriores
"""
from __future__ import annotations

import json
import re
from datetime import datetime, timezone
from typing import Literal

from core.logger import get_logger
from core.tools import telegram_bot

logger = get_logger("agents.conversation_agent")

Stage = Literal["NUEVO", "CALIFICANDO", "LISTO", "NO_INTERESADO", "ARCHIVADO"]

_conversations: dict[str, dict] = {}  # chat_id → state


SYSTEM_PROMPT = """Sos un asistente de reclutamiento amigable y directo que trabaja para {recruiter_name}.
Estás calificando a un candidato para la búsqueda: "{search_title}".

CRITERIOS DE LA BÚSQUEDA:
{criteria_summary}

Tu objetivo es hacer exactamente 3 preguntas (una por mensaje) para entender:
1. Disponibilidad: ¿cuándo podrías empezar?
2. Expectativa salarial (o rango aceptable)
3. Motivación: ¿qué buscás en tu próximo rol?

Reglas:
- Mensajes cortos (máximo 3 líneas).
- Tono conversacional, no formal.
- Si el candidato dice que no le interesa → responder con amabilidad y marcar como NO_INTERESADO.
- Después de la 3ra respuesta → marcar como LISTO.
- Si pide hablar con una persona → escalar.

Al final de cada respuesta incluí una de estas etiquetas (en la última línea, sin texto adicional):
[CALIFICANDO] | [LISTO] | [NO_INTERESADO] | [ESCALAR]
"""

QUESTIONS = [
    "¿Cuándo podrías empezar, en caso de que encontremos algo que te interese?",
    "¿Tenés alguna expectativa de rango salarial? Podés ser aproximado.",
    "¿Qué es lo más importante para vos en tu próximo rol?",
]


def _get_llm_response(system: str, history: list[dict], user_message: str) -> str:
    try:
        from core.tools.llm_client import LLMClient
        client = LLMClient()
        messages = history + [{"role": "user", "content": user_message}]
        return client.chat_messages(system=system, messages=messages)
    except Exception as e:
        logger.error("Error llamando LLM en ConversationAgent: %s", e)
        return "Gracias por tu mensaje. Te respondo en un momento. [CALIFICANDO]"


def _extract_stage(text: str) -> Stage | None:
    for tag in ["LISTO", "NO_INTERESADO", "ESCALAR", "CALIFICANDO"]:
        if f"[{tag}]" in text:
            return tag if tag != "ESCALAR" else "LISTO"  # type: ignore
    return None


def _clean_response(text: str) -> str:
    return re.sub(r"\[(CALIFICANDO|LISTO|NO_INTERESADO|ESCALAR)\]\s*$", "", text).strip()


def _notify_recruiter(conv: dict) -> None:
    """Send a summary to the recruiter's Telegram chat."""
    from core.config import settings
    from core.telegram_notifier import TelegramNotifier

    notifier = TelegramNotifier()
    candidate_name = conv.get("candidate_name", "Candidato")
    search_title = conv.get("search_title", "búsqueda")

    summary_lines = []
    for i, q in enumerate(QUESTIONS):
        ans = conv.get("answers", {}).get(str(i), "—")
        summary_lines.append(f"• {q}\n  → _{ans}_")

    body = (
        f"✅ *Candidato calificado via Telegram*\n\n"
        f"👤 *{candidate_name}*\n"
        f"🔍 Búsqueda: _{search_title}_\n\n"
        + "\n".join(summary_lines)
        + f"\n\n📅 [Agendar entrevista]({settings.calendly_link})"
        if settings.calendly_link else ""
    )

    notifier.send_raw_message(body, escaped=True)
    logger.info("Recruiter notificado — candidato %s calificado", candidate_name)


def handle_message(message: dict) -> None:
    """Entry point — called by telegram_bot polling for each incoming message."""
    from core.config import settings

    chat_id = str(message.get("chat", {}).get("id", ""))
    text = (message.get("text") or "").strip()
    from_user = message.get("from", {})
    first_name = from_user.get("first_name", "")

    if not chat_id or not text:
        return

    recruiter_chat = str(settings.telegram_chat_id or "")
    if chat_id == recruiter_chat:
        return

    conv = _conversations.get(chat_id)

    # /start SEARCH-XXXX — new conversation initiated from email link
    if text.startswith("/start"):
        parts = text.split(maxsplit=1)
        search_code = parts[1].strip() if len(parts) > 1 else ""
        search_info = _resolve_search(search_code)

        _conversations[chat_id] = {
            "stage": "NUEVO",
            "search_code": search_code,
            "search_title": search_info.get("title", "posición abierta"),
            "criteria_summary": search_info.get("criteria_summary", ""),
            "recruiter_name": search_info.get("recruiter_name", settings.orchestrator),
            "candidate_name": first_name,
            "history": [],
            "answers": {},
            "question_index": 0,
            "started_at": datetime.now(timezone.utc).isoformat(),
        }
        conv = _conversations[chat_id]

        greeting = (
            f"¡Hola {first_name}! 👋\n\n"
            f"Gracias por responder. Soy el asistente de *{conv['recruiter_name']}*.\n"
            f"Me gustaría hacerte 3 preguntas rápidas para entender mejor tu perfil.\n\n"
            f"{QUESTIONS[0]}"
        )
        telegram_bot.send_message(chat_id, greeting)
        conv["question_index"] = 0
        conv["stage"] = "CALIFICANDO"
        return

    if not conv or conv.get("stage") == "ARCHIVADO":
        telegram_bot.send_message(
            chat_id,
            "Hola 👋 Si recibiste un email nuestro, usá el link del botón para iniciar la conversación.",
        )
        return

    stage = conv.get("stage", "CALIFICANDO")

    if stage in ("LISTO", "NO_INTERESADO"):
        return

    # Record answer to current question
    q_idx = conv.get("question_index", 0)
    conv.setdefault("answers", {})[str(q_idx)] = text
    conv["history"].append({"role": "user", "content": text})

    next_q_idx = q_idx + 1

    if next_q_idx < len(QUESTIONS):
        # Still have questions
        response = QUESTIONS[next_q_idx]
        conv["question_index"] = next_q_idx
        telegram_bot.send_message(chat_id, response)
        conv["history"].append({"role": "assistant", "content": response})
    else:
        # All questions answered — LLM closes and assesses
        system = SYSTEM_PROMPT.format(
            recruiter_name=conv["recruiter_name"],
            search_title=conv["search_title"],
            criteria_summary=conv["criteria_summary"],
        )
        raw = _get_llm_response(system, conv["history"], text)
        new_stage = _extract_stage(raw) or "LISTO"
        clean = _clean_response(raw)

        if new_stage == "NO_INTERESADO":
            conv["stage"] = "NO_INTERESADO"
            farewell = clean or "Entiendo, ¡gracias por tu tiempo! Si en el futuro cambia tu situación, con gusto retomamos."
            telegram_bot.send_message(chat_id, farewell)
        else:
            conv["stage"] = "LISTO"
            calendly = settings.calendly_link
            closing = clean or "¡Perfecto, muchas gracias por compartir esa info!"
            if calendly:
                closing += f"\n\nPodés agendar una charla de 20 min acá:\n{calendly}"
            else:
                closing += "\n\nNos vamos a comunicar para coordinar un momento."
            telegram_bot.send_message(chat_id, closing)
            _notify_recruiter(conv)

        conv["history"].append({"role": "assistant", "content": clean})

    _conversations[chat_id] = conv


def _resolve_search(search_code: str) -> dict:
    """Look up search context from TalentPool or criteria files."""
    if not search_code:
        return {}
    try:
        from core.talent_pool import TalentPool
        # Try to find by run_id or search_code in searches table
        import sqlite3
        from pathlib import Path
        db_path = Path("data/state/talent_pool.db")
        if db_path.exists():
            conn = sqlite3.connect(str(db_path))
            conn.row_factory = sqlite3.Row
            row = conn.execute(
                "SELECT * FROM searches WHERE search_id = ? OR search_id LIKE ? LIMIT 1",
                (search_code, f"%{search_code}%"),
            ).fetchone()
            conn.close()
            if row:
                criteria = json.loads(row["criteria"] or "{}")
                return {
                    "title": row.get("role_target") or criteria.get("role", "posición abierta"),
                    "criteria_summary": _summarize_criteria(criteria),
                    "recruiter_name": criteria.get("recruiter_name", ""),
                }
    except Exception as e:
        logger.warning("No se pudo resolver search_code %s: %s", search_code, e)

    # Fallback: try criteria files
    try:
        import yaml
        from pathlib import Path
        for f in Path("data/criteria").glob("*.yaml"):
            c = yaml.safe_load(f.read_text())
            if search_code in (c.get("search_id", ""), f.stem):
                return {
                    "title": c.get("role", "posición abierta"),
                    "criteria_summary": _summarize_criteria(c),
                    "recruiter_name": c.get("recruiter_name", ""),
                }
    except Exception:
        pass

    return {}


def _summarize_criteria(criteria: dict) -> str:
    parts = []
    if criteria.get("role"):
        parts.append(f"Rol: {criteria['role']}")
    if criteria.get("required_skills"):
        skills = criteria["required_skills"]
        if isinstance(skills, list):
            parts.append(f"Skills requeridos: {', '.join(skills[:5])}")
    if criteria.get("location"):
        parts.append(f"Ubicación: {criteria['location']}")
    if criteria.get("seniority"):
        parts.append(f"Seniority: {criteria['seniority']}")
    return "\n".join(parts) or "Sin criterios adicionales disponibles."
