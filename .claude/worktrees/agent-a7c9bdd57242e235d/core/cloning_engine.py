import copy
from typing import Any
from contracts import AgentAction, ActionType

class HydroClone:
    def __init__(self, clone_id: str, name: str, icon: str, base_agent: Any, hydration_context: dict):
        self.clone_id = clone_id
        self.name = name
        self.icon = icon
        self.base_agent = base_agent
        self.context = hydration_context
        self.state = "idle"
        
    def to_dict(self) -> dict:
        return {
            "clone_id": self.clone_id,
            "name": self.name,
            "icon": self.icon,
            "context": self.context,
            "state": self.state
        }

class CloningEngine:
    @staticmethod
    def hydrate_army(base_agent: Any, industries: list[str], cities: list[str]) -> list[HydroClone]:
        clones = []
        counter = 1
        
        # We pair each industry with each city to spawn specialized parallel clones (Micro-Tokens)
        for ind in industries:
            for city in cities:
                clone_id = f"{base_agent.id}_clone_{counter:02d}"
                clone_name = f"{base_agent.name} - {ind} {city}"
                
                # Context is ultra-lightweight (hydration context)
                hydration_context = {
                    "target_industry": ind,
                    "target_city": city,
                    "role_filter": "C-Level / VP / Director",
                    "channel": "linkedin",
                    "max_token_budget": 500  # Enforces cheap, fast Gemini 3.5 Flash calls
                }
                
                # Dynamic visual representation
                icon = base_agent.icon
                if "Fintech" in ind:
                    icon = "💳"
                elif "SaaS" in ind:
                    icon = "☁️"
                elif "E-Commerce" in ind:
                    icon = "🛒"
                elif "Health" in ind:
                    icon = "🏥"
                
                clone = HydroClone(
                    clone_id=clone_id,
                    name=clone_name,
                    icon=icon,
                    base_agent=base_agent,
                    hydration_context=hydration_context
                )
                clones.append(clone)
                counter += 1
                
        return clones

    @staticmethod
    def simulate_parallel_run(clones: list[HydroClone], run_id: str) -> list[AgentAction]:
        actions = []
        for clone in clones:
            clone.state = "working"
            # Simulate a quick search action for this clone
            target_company = f"Startup {clone.context['target_industry']} {clone.context['target_city']}"
            
            action = AgentAction(
                agent_id=clone.clone_id,
                action_type=ActionType.SIGNAL.value,
                target=target_company,
                reason=f"Clon ciber-reclutador rastreó {clone.context['target_industry']} en {clone.context['target_city']}.",
                payload={
                    "hydration": clone.context,
                    "evidence": f"Señal de crecimiento activa en {target_company}",
                    "confidence": "alta",
                    "run_id": run_id
                },
                score=90
            )
            actions.append(action)
            clone.state = "idle"
            
        return actions
