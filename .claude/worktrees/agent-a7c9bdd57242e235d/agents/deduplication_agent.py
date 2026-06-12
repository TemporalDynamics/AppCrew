from agents.base import BaseAgent
from contracts import AgentAction, ActionType
from core.talent_pool import TalentPool


class DeduplicationAgent(BaseAgent):
    id = "deduplication"
    name = "Deduplication"
    icon = "🔍"
    description = "Marca candidatos ya existentes en Talent Pool sin eliminarlos"
    read_only = True
    never_sends = True

    def _init_contract(self):
        self.contract = {
            "authority": "worker",
            "tools": {"memory": {"permitted": True, "notes": "solo lectura de TalentPool"}},
            "invariants": [
                "No elimina candidatos — solo marca",
                "Consulta TalentPool por dedup_key",
            ],
            "context": ["run_id actual", "candidatos entrantes"],
        }

    async def work(self) -> list[AgentAction]:
        actions = []
        pool = TalentPool()
        for action in self.pending_actions:
            if action.action_type != "candidate":
                continue
            payload = action.payload or {}
            name = payload.get("name", action.target)
            role = payload.get("current_role") or payload.get("role", "")
            company = payload.get("company", "")
            source = payload.get("source", "unknown")
            source_url = payload.get("source_url", "")
            name_slug = name.lower().replace(" ", "_")
            url_slug = source_url.split("/")[-1] if source_url else ""
            dedup_key = f"{name_slug}|{url_slug}"

            existing = pool.get_candidate(dedup_key)
            if existing:
                actions.append(AgentAction(
                    agent_id=self.id,
                    action_type=ActionType.NOTE.value,
                    target=f"dedup_hit:{name}",
                    reason=f"Candidato ya existe en pool (veces visto: {existing.get('times_surfaced', 1)})",
                    payload={
                        "dedup_key": dedup_key,
                        "times_surfaced": existing.get("times_surfaced", 1),
                        "status": existing.get("status", "unknown"),
                    },
                    score=0,
                ))
        if not actions:
            actions.append(AgentAction(
                agent_id=self.id,
                action_type=ActionType.NOTE.value,
                target="dedup_clean",
                reason="No se detectaron duplicados en esta ronda",
                payload={},
                score=0,
            ))
        return actions
