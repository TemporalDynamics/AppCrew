"""
Telegram bot for candidate conversations.

Uses long-polling to receive messages from candidates.
The recruiter notification channel (TelegramNotifier) uses a separate chat_id
but the same bot token — they coexist fine because we route by chat_id.
"""
from __future__ import annotations

import threading
import time
from typing import Callable

import requests

from core.logger import get_logger

logger = get_logger("core.tools.telegram_bot")

_polling_thread: threading.Thread | None = None
_stop_event = threading.Event()


def send_message(chat_id: str | int, text: str, parse_mode: str = "Markdown") -> bool:
    """Send a Telegram message to any chat_id."""
    from core.config import settings
    token = settings.telegram_bot_token
    if not token:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado — mensaje no enviado")
        return False
    try:
        r = requests.post(
            f"https://api.telegram.org/bot{token}/sendMessage",
            json={"chat_id": chat_id, "text": text, "parse_mode": parse_mode},
            timeout=5,
        )
        return r.status_code == 200
    except Exception as e:
        logger.error("Error enviando mensaje Telegram a %s: %s", chat_id, e)
        return False


def start_polling(handler: Callable[[dict], None]) -> None:
    """Start background polling thread. handler(message) is called for each incoming message."""
    global _polling_thread, _stop_event

    from core.config import settings
    if not settings.telegram_bot_token:
        logger.warning("TELEGRAM_BOT_TOKEN no configurado — bot de candidatos desactivado")
        return

    _stop_event.clear()

    def _poll():
        token = settings.telegram_bot_token
        offset = 0
        base_url = f"https://api.telegram.org/bot{token}"
        logger.info("Telegram bot polling iniciado")

        while not _stop_event.is_set():
            try:
                r = requests.get(
                    f"{base_url}/getUpdates",
                    params={"offset": offset, "timeout": 20},
                    timeout=25,
                )
                if r.status_code != 200:
                    time.sleep(2)
                    continue

                updates = r.json().get("result", [])
                for upd in updates:
                    offset = upd["update_id"] + 1
                    msg = upd.get("message") or upd.get("edited_message")
                    if msg:
                        try:
                            handler(msg)
                        except Exception as e:
                            logger.error("Error en handler de mensaje: %s", e, exc_info=True)

            except requests.exceptions.ReadTimeout:
                continue
            except Exception as e:
                logger.error("Error en polling loop: %s", e)
                time.sleep(3)

    _polling_thread = threading.Thread(target=_poll, name="telegram-poll", daemon=True)
    _polling_thread.start()


def stop_polling() -> None:
    _stop_event.set()
