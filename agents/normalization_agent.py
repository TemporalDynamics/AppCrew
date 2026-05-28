from agents.base import BaseAgent
from contracts import AgentAction, ActionType


_COUNTRY_MAP = {
    "mx": "Mexico", "méxico": "Mexico", "mexico": "Mexico",
    "cdmx": "Mexico City", "cdmx": "Mexico City",
    "ar": "Argentina", "argentina": "Argentina",
    "co": "Colombia", "colombia": "Colombia",
    "cl": "Chile", "chile": "Chile",
    "pe": "Peru", "perú": "Peru", "peru": "Peru",
    "br": "Brazil", "brasil": "Brazil", "brazil": "Brazil",
}


def _normalize_location(raw: str) -> str:
    if not raw:
        return ""
    raw_lower = raw.strip().lower()
    return _COUNTRY_MAP.get(raw_lower, raw.strip())


class NormalizationAgent(BaseAgent):
    id = "normalization"
    name = "Normalization"
    icon = "🔧"
    description = "Normaliza campos de candidatos: location, skills, company"
    read_only = True
    never_sends = True

    def _init_contract(self):
        self.contract = {
            "authority": "worker",
            "tools": {},
            "invariants": [
                "No elimina datos — solo normaliza",
                "Skills se pasan a lowercase y se deduplican",
                "Location se mapea a país/ciudad estándar",
            ],
            "context": ["run_id actual", "candidatos desde intake"],
        }

    async def work(self) -> list[AgentAction]:
        actions = []
        for action in self.pending_actions:
            if action.action_type != "candidate":
                continue
            payload = dict(action.payload)
            loc = _normalize_location(payload.get("location", ""))
            skills_raw = payload.get("skills", [])
            if isinstance(skills_raw, list):
                skills = list(dict.fromkeys(s.lower().strip() for s in skills_raw if s))
            else:
                skills = []
            company = (payload.get("company") or "").strip()
            payload["location"] = loc
            payload["skills"] = skills
            payload["company"] = company
            actions.append(AgentAction(
                agent_id=self.id,
                action_type=ActionType.CANDIDATE.value,
                target=action.target,
                reason=f"Normalizado: loc={loc}, skills={len(skills)}, company={company[:30]}",
                payload=payload,
                score=action.score,
            ))
        return actions
