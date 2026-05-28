from __future__ import annotations

from urllib.parse import urlparse

from agents.base import BaseAgent
from contracts import AgentAction


ALLOWED_DOMAINS = frozenset([
    "torre.co", "getonbrd.com", "computrabajo.com", "computrabajo.com.mx",
    "linkedin.com", "glassdoor.com", "crunchbase.com", "angel.co",
])


class BrowserAgent(BaseAgent):
    id = "browser"
    name = "Browser Scout"
    icon = "🌐"
    description = "Lee páginas públicas para extraer evidencia de candidatos"
    read_only = True
    never_sends = True

    def _init_contract(self):
        self.contract = {
            "tools": {
                "browser": {"permitted": True, "notes": "solo lectura, domínios en ALLOWED_DOMAINS"},
                "web_search": {"permitted": False},
                "email": {"permitted": False},
                "filesystem": {"permitted": False},
                "memory": {"permitted": False},
            },
            "context": ["URL de perfil público", "dedup_key del candidato"],
            "memory": {
                "namespace": "N/A",
                "can_remember": [],
                "cannot_remember": ["datos personales", "credenciales", "perfiles cerrados"],
            },
            "invariants": [
                "Solo accede a dominios en ALLOWED_DOMAINS",
                "Nunca autentica ni hace login en plataformas externas",
                "Solo lectura: no escribe en ningún sistema externo",
                "No guarda datos biométricos ni privados",
            ],
            "blocked_actions": [
                "login_or_authenticate",
                "post_or_submit",
                "access_private_profile",
                "access_domain_outside_allowlist",
                "store_sensitive_data",
            ],
            "failure_modes": [
                "Dominio fuera del allowlist: rechazar URL, loguear intento",
                "Página no disponible: retornar lista vacía, no reintentar",
                "Sandbox no activo: retornar stub vacío con advertencia",
            ],
            "escalation": [],
            "tests": [
                "import OK",
                "_validate_url acepta dominios en allowlist",
                "_validate_url rechaza dominios fuera del allowlist",
                "work() retorna lista vacía en stub",
            ],
            "authority": "researcher",
        }

    def _validate_url(self, url: str) -> bool:
        """Return True only if the URL's netloc is in ALLOWED_DOMAINS."""
        try:
            parsed = urlparse(url)
            host = parsed.netloc.lower().lstrip("www.")
            # Check exact match or subdomain match
            if host in ALLOWED_DOMAINS:
                return True
            for domain in ALLOWED_DOMAINS:
                if host == domain or host.endswith("." + domain):
                    return True
            return False
        except Exception:
            return False

    async def work(self) -> list[AgentAction]:
        print("[BROWSER] Sandboxed browser not yet active")
        return []
