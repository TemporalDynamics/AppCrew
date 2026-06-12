from __future__ import annotations

from core.logger import get_logger

logger = get_logger("core.tools.email_client")


def send_email(
    to: str,
    subject: str,
    html_body: str,
    from_name: str | None = None,
) -> bool:
    """Send an email via Resend. Returns True on success, False otherwise."""
    from core.config import settings

    if not settings.resend_api_key:
        logger.warning("RESEND_API_KEY no configurada — email no enviado a %s", to)
        return False

    try:
        import resend  # type: ignore
        resend.api_key = settings.resend_api_key

        display = from_name or "Talo"
        from_addr = f"{display} <talo@email.ecosign.app>"

        r = resend.Emails.send({
            "from": from_addr,
            "to": [to],
            "subject": subject,
            "html": html_body,
        })
        logger.info("Email enviado a %s — id: %s", to, getattr(r, "id", r))
        return True
    except Exception as e:
        logger.error("Error enviando email a %s: %s", to, e, exc_info=True)
        return False
