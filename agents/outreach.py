from __future__ import annotations

import hashlib
from pathlib import Path

from agents.base import BaseAgent
from contracts import AgentAction, ActionType, InvariantViolation
from core.logger import get_logger

logger = get_logger("agents.outreach")

HERE = Path(__file__).resolve().parent.parent
TEMPLATE_PATH = HERE / "dashboard" / "templates" / "cold_email.html"


class OutreachAgent(BaseAgent):
    id = "outreach"
    name = "Outreach"
    icon = "✉️"
    description = "Genera borradores — NUNCA envía sin aprobación humana"
    never_sends = True
    needs_approval = True

    INVARIANT_NEVER_SENDS = "NUNCA ejecuta el envío. Solo prepara drafts. El humano autoriza."

    def __init__(self, config: dict):
        super().__init__(config)
        self.require_approval = config.get("agents", {}).get("outreach", {}).get("require_approval", True)

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": False},
                "browser": {"permitted": False},
                "email": {"permitted": False, "notes": "prohibido absolutamente"},
                "filesystem": {"permitted": True, "notes": "solo lectura"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "escritura, namespace `memory/outreach/*`"},
            },
            "context": ["run_id actual", "targets con contexto", "tono configurado", "require_approval (debe ser True)"],
            "memory": {
                "namespace": "memory/outreach/*",
                "can_remember": ["mensajes ya enviados (para no repetir)", "targets contactados recientemente"],
                "cannot_remember": ["contraseñas, tokens, datos sensibles"],
            },
            "invariants": [
                "NUNCA envía — solo prepara drafts",
                "Si require_approval = False, no arranca (critical precondition)",
                "Mensaje no se modifica después de aprobado",
                "Trazabilidad completa (action_id único)",
                "Máximo 1 mensaje por target por día",
                "Toda acción tiene run_id y dedup_key",
            ],
            "failure_modes": [
                "require_approval en false: no arranca, error crítico",
                "Target sin datos suficientes: no genera draft, reporta",
            ],
            "escalation": [
                "require_approval desactivado: error al orquestador",
                "Contenido sensible detectado: escala al CEO para revisión manual",
            ],
            "tests": [
                "import OK", "run genera borradores", "run_id obligatorio",
                "never_sends = True", "needs_approval = True",
            ],
            "authority": "draft-only",
        }

    def _check_preconditions(self) -> list[InvariantViolation]:
        if not self.require_approval:
            return [InvariantViolation(
                agent_id=self.id, invariant="requiere_aprobacion",
                detail="require_approval está en false. Outreach nunca debe enviar sin aprobación.",
                severity="critical",
            )]
        return []

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        from contracts import AgentState
        for a in actions:
            assert a.state == AgentState.PENDING_REVIEW.value, \
                f"Acción {a.action_id} no está en PENDING_REVIEW"

    async def work(self) -> list[AgentAction]:
        return self._prepare_outreach()

    def _prepare_outreach(self) -> list[AgentAction]:
        from core.config import settings
        candidates = self._load_candidates()

        if not candidates:
            logger.warning("OutreachAgent: no hay candidatos en el pool para generar drafts")
            return []

        actions = []
        for c in candidates[:5]:
            search_code = self._search_code_for(c)
            telegram_link = self._telegram_link(search_code, settings)
            email_html = self._render_email(c, telegram_link, settings)
            subject = self._generate_subject(c, settings)

            action = AgentAction(
                agent_id=self.id,
                action_type=ActionType.INMAIL.value,
                target=f"{c.get('name', 'Candidato')} — {c.get('current_role', '')} @ {c.get('company', '')}",
                reason=self._fit_summary(c),
                payload={
                    "subject": subject,
                    "email_html": email_html,
                    "channel": "email",
                    "to_email": c.get("email", ""),
                    "candidate_name": c.get("name", ""),
                    "source_url": c.get("source_url", ""),
                    "search_code": search_code,
                    "telegram_link": telegram_link,
                    "requires_approval": True,
                },
                score=int(c.get("raw_score", 0) * 100),
            )
            actions.append(action)

        return actions

    def _load_candidates(self) -> list[dict]:
        """Pull top candidates from TalentPool that haven't been contacted yet."""
        try:
            from core.talent_pool import TalentPool
            result = TalentPool._get_candidates_with_evidence(workspace_id="default", include_demo=True)
            return result[:10] if isinstance(result, list) else []
        except Exception as e:
            logger.error("Error cargando candidatos del pool: %s", e, exc_info=True)
            return []

    def _search_code_for(self, candidate: dict) -> str:
        key = candidate.get("dedup_key", candidate.get("name", "unknown"))
        return "SRCH-" + hashlib.md5(key.encode()).hexdigest()[:6].upper()

    def _telegram_link(self, search_code: str, settings) -> str:
        username = getattr(settings, "telegram_bot_username", "") or ""
        if username:
            return f"https://t.me/{username}?start={search_code}"
        return ""

    def _render_email(self, candidate: dict, telegram_link: str, settings) -> str:
        try:
            template_text = TEMPLATE_PATH.read_text(encoding="utf-8")
        except FileNotFoundError:
            logger.warning("Template cold_email.html no encontrado, usando fallback texto plano")
            return self._plain_text_fallback(candidate, telegram_link, settings)

        replacements = {
            "{{ CANDIDATE_NAME }}": candidate.get("name", ""),
            "{{ CV_SOURCE }}": candidate.get("source", "tu perfil público").replace("_", " ").title(),
            "{{ FIT_REASON }}": self._fit_reason_llm(candidate),
            "{{ TELEGRAM_LINK }}": telegram_link or "#",
            "{{ SEARCH_TITLE }}": self._search_title(settings),
            "{{ RECRUITER_NAME }}": settings.orchestrator or "El equipo de Talo",
        }
        html = template_text
        for k, v in replacements.items():
            html = html.replace(k, v)
        return html

    def _fit_reason_llm(self, candidate: dict) -> str:
        try:
            from core.tools.llm_client import LLMClient
            client = LLMClient()
            prompt = (
                f"Candidato: {candidate.get('name')} — {candidate.get('current_role')} en {candidate.get('company')}.\n"
                f"Skills: {', '.join((candidate.get('skills') or [])[:6])}.\n"
                f"Ubicación: {candidate.get('location', '')}.\n\n"
                f"Escribí UNA oración (máx 25 palabras) en español explicando por qué este candidato "
                f"encaja para una búsqueda de talento tech en LATAM. "
                f"No empieces con 'Tu perfil'. Sé específico y directo."
            )
            return client.complete(prompt).strip()
        except Exception as e:
            logger.warning("LLM no disponible para FIT_REASON: %s", e)
            return self._fit_summary(candidate)

    def _fit_summary(self, candidate: dict) -> str:
        role = candidate.get("current_role", "")
        company = candidate.get("company", "")
        skills = candidate.get("skills") or []
        parts = []
        if role:
            parts.append(role)
        if company:
            parts.append(f"en {company}")
        if skills:
            parts.append(f"— {', '.join(skills[:3])}")
        return " ".join(parts) or "Perfil relevante para la búsqueda"

    def _generate_subject(self, candidate: dict, settings) -> str:
        name = candidate.get("name", "").split()[0] if candidate.get("name") else ""
        title = self._search_title(settings)
        if name:
            return f"{name}, ¿te interesa esta oportunidad? — {title}"
        return f"Oportunidad para vos — {title}"

    def _search_title(self, settings) -> str:
        try:
            import yaml
            from pathlib import Path
            criteria_dir = Path("data/criteria")
            if criteria_dir.exists():
                files = sorted(criteria_dir.glob("*.yaml"))
                if files:
                    c = yaml.safe_load(files[0].read_text())
                    return c.get("role", "posición abierta")
        except Exception:
            pass
        return "posición abierta"

    def _plain_text_fallback(self, candidate: dict, telegram_link: str, settings) -> str:
        name = candidate.get("name", "")
        reason = self._fit_summary(candidate)
        recruiter = settings.orchestrator or "El equipo de Talo"
        tg = f'\n\nCharlemos por Telegram: {telegram_link}' if telegram_link else ""
        return (
            f"<p>Hola {name},</p>"
            f"<p>{reason}</p>"
            f"<p>¿Te interesa explorar esta oportunidad?{tg}</p>"
            f"<p>Saludos,<br>{recruiter}</p>"
        )


from contracts import AgentState
AgentState.PENDING_REVIEW  # ensure import
