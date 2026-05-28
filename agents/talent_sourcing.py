from __future__ import annotations

from agents.base import BaseAgent
from contracts import AgentAction, ActionType
from core.sources.aggregator import TalentSourceAggregator


class TalentSourcingAgent(BaseAgent):
    id = "talent_sourcing"
    name = "Talent Sourcing"
    icon = "🎯"
    description = "Busca talento por rol, industria, seniority y país"
    read_only = True
    never_sends = True

    def __init__(self, config: dict):
        super().__init__(config)
        self.max_results = config.get("agents", {}).get("talent_sourcing", {}).get("max_results", 10)
        self._aggregator = TalentSourceAggregator()

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": True, "notes": "Torre.co + Brave Search público"},
                "browser": {"permitted": True, "notes": "solo lectura, perfiles públicos"},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "solo lectura"},
                "context7": {"permitted": False},
                "memory": {"permitted": True, "notes": "escritura, namespace `memory/talent_sourcing/*`"},
            },
            "context": ["run_id actual", "criterios de búsqueda (rol, ubicación)", "max_results"],
            "memory": {
                "namespace": "memory/talent_sourcing/*",
                "can_remember": ["candidatos ya vistos", "búsquedas recientes para evitar repetir"],
                "cannot_remember": ["datos fuera de su búsqueda", "decisiones de contratación"],
            },
            "invariants": [
                "Solo lectura: nunca escribe en plataformas externas",
                "No comparte datos fuera del sistema",
                "Cada candidato tiene source_url verificable",
                "Toda acción tiene run_id y dedup_key",
            ],
            "failure_modes": [
                "Torre rate limit: esperar, reintentar",
                "Sin API keys: cae a demo_seed claramente marcado",
                "Sin resultados: reportar 'no encontrados'",
            ],
            "escalation": [
                "Sin resultados después de 3 intentos → escalar al CEO",
            ],
            "tests": [
                "import OK", "run genera acciones válidas", "run_id obligatorio",
                "dedup funciona", "no viola tools prohibidas",
            ],
            "authority": "researcher",
        }

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        for a in actions:
            assert a.target, "Candidato sin nombre"
            loc = a.payload.get("location", "")
            assert loc, f"Candidato {a.target} sin ubicación"

    async def work(self) -> list[AgentAction]:
        criteria = {
            "role_target": self.config.get("role_target", "CTO / VP Engineering"),
            "markets": self.config.get("markets", ["Mexico"]),
            "industries": self.config.get("industries", ["fintech", "SaaS B2B"]),
            "limit": self.max_results,
        }
        signals = await self._aggregator.search(criteria)
        actions = []
        for s in signals:
            actions.append(
                AgentAction(
                    agent_id=self.id,
                    action_type=ActionType.CANDIDATE.value,
                    target=s.name,
                    reason=f"{s.current_role} en {s.company} [{s.source}] — {s.availability_signal}",
                    payload={
                        "name": s.name,
                        "role": s.current_role,
                        "company": s.company,
                        "location": s.location,
                        "source_url": s.source_url,
                        "source": s.source,
                        "availability_signal": s.availability_signal,
                        "skills": s.skills,
                        "confidence": s.confidence,
                        "summary": s.evidence[0].value[:80] if s.evidence else "",
                    },
                    score=int(s.raw_score) or 70,
                )
            )
        return actions
