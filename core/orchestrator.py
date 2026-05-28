from datetime import datetime, timezone
from typing import Any
from uuid import uuid4

import yaml

from agents.base import AgentAction
from agents.demand_radar import DemandRadarAgent
from agents.talent_sourcing import TalentSourcingAgent
from agents.fit_scoring import FitScoringAgent
from agents.outreach import OutreachAgent
from agents.knowledge import KnowledgeAgent
from agents.qa import QAAgent
from agents.ceo import CEOAgent
from agents.tester import TesterAgent
from agents.doctrine_keeper import DoctrineKeeperAgent
from agents.talent_signal import TalentSignalAgent
from agents.career_context import CareerContextAgent

from agents.intake_agent import IntakeAgent
from agents.criteria_agent import CriteriaAgent
from agents.normalization_agent import NormalizationAgent
from agents.deduplication_agent import DeduplicationAgent
from agents.evidence_agent import EvidenceAgent
from agents.memory_update_agent import MemoryUpdateAgent

from contracts import RunRecord


from core.heartbeat import HeartbeatStore, build_heartbeat
from core.state import StateStore


class Orchestrator:
    def __init__(self, config_path: str = "config.yaml", restore_state: bool = True):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        from core.config import settings
        fc_key = settings.firecrawl_api_key
        if fc_key and not self.config.get("firecrawl", {}).get("api_key"):
            self.config.setdefault("firecrawl", {})["api_key"] = fc_key
        search_key = settings.brave_search_api_key
        if search_key and not self.config.get("search", {}).get("api_key"):
            self.config.setdefault("search", {})["api_key"] = search_key
        llm_key = settings.openrouter_api_key
        if llm_key:
            self.config.setdefault("openrouter", {})["api_key"] = llm_key
            self.config.setdefault("openrouter", {})["model"] = settings.openrouter_model
        self.agents: dict[str, Any] = {}
        self.runs: list[RunRecord] = []
        self._register_agents()
        self._reset_all_agents()
        if restore_state:
            self.restore_state()

    def _reset_all_agents(self):
        for agent in self.agents.values():
            agent.reset_state()

    def _register_agents(self):
        cfg = self.config.get("agents", {})

        ceo = CEOAgent(self.config)
        ceo.bind_orchestrator(self)
        self.agents["ceo"] = ceo

        tester = TesterAgent(self.config)
        tester.bind_orchestrator(self)
        self.agents["tester"] = tester

        doctrine = DoctrineKeeperAgent(self.config)
        self.agents["doctrine_keeper"] = doctrine

        talent_signal = TalentSignalAgent(self.config)
        talent_signal.bind_doctrine(doctrine)
        self.agents["talent_signal"] = talent_signal

        career_context = CareerContextAgent(self.config)
        career_context.bind_doctrine(doctrine)
        self.agents["career_context"] = career_context

        legacy_registry = {
            "demand_radar": DemandRadarAgent,
            "talent_sourcing": TalentSourcingAgent,
            "fit_scoring": FitScoringAgent,
            "outreach": OutreachAgent,
            "knowledge": KnowledgeAgent,
            "qa": QAAgent,
        }
        for agent_id, cls in legacy_registry.items():
            if cfg.get(agent_id, {}).get("enabled", True):
                self.agents[agent_id] = cls(self.config)

        pipeline_registry = {
            "intake": IntakeAgent,
            "criteria": CriteriaAgent,
            "normalization": NormalizationAgent,
            "deduplication": DeduplicationAgent,
            "evidence": EvidenceAgent,
            "memory_update": MemoryUpdateAgent,
        }
        for agent_id, cls in pipeline_registry.items():
            if cfg.get(agent_id, {}).get("enabled", True):
                self.agents[agent_id] = cls(self.config)

    def _new_run_id(self) -> str:
        return f"run_{datetime.now(timezone.utc).strftime('%Y%m%d_%H%M%S')}_{uuid4().hex[:6]}"

    async def run_agent(self, agent_id: str) -> list[AgentAction]:
        agent = self.agents.get(agent_id)
        if not agent:
            return []
        run_id = self._new_run_id()
        record = RunRecord(run_id=run_id, agent_id=agent_id,
                           started_at=datetime.now(timezone.utc).isoformat())
        actions = await agent.run(run_id)
        record.actions_created = len(actions)
        record.finished_at = datetime.now(timezone.utc).isoformat()
        self.runs.append(record)
        self._record_heartbeat(agent, len(actions))
        self.save_state()
        return actions

    def _record_heartbeat(self, agent, actions_created: int = 0) -> None:
        extra = {}
        agent_id = agent.id
        if agent_id == "demand_radar":
            extra = {
                "source_type": getattr(agent, "_source_type", "internal"),
                "confidence": "alta",
            }
        elif agent_id == "career_context":
            extra = {
                "companies_analyzed": len(getattr(agent, "_last_companies", [])),
                "risk_of_noise": getattr(agent, "_last_risk", "baja"),
                "fallback_used": getattr(agent, "_fallback_used", False),
            }
        elif agent_id == "talent_signal":
            extra = {
                "candidates_analyzed": len(getattr(agent, "_last_candidates", [])),
                "needs_human_review": getattr(agent, "_needs_review", 0),
            }
        elif agent_id == "doctrine_keeper":
            extra = {
                "active_principles": len(getattr(agent, "_principles", [])),
                "queries_served": getattr(agent, "_queries_count", 0),
            }
        heartbeat = build_heartbeat(agent, actions_created=actions_created, **extra)
        HeartbeatStore.record(agent_id, heartbeat)

    async def run_task(self, task_text: str) -> dict:
        ceo = self.agents.get("ceo")
        if not ceo:
            return {"error": "CEO Agent not found"}
        result = await ceo.process_task(task_text)
        self.save_state()
        return result

    async def run_all(self) -> dict[str, list[AgentAction]]:
        results = {}

        import asyncio

        # Fase 1: inteligencia de mercado (paralela)
        phase1 = ["demand_radar", "knowledge", "criteria"]
        phase1_tasks = {aid: self.run_agent(aid) for aid in phase1 if aid in self.agents}
        phase1_results = await asyncio.gather(*phase1_tasks.values(), return_exceptions=True)
        for aid, result in zip(phase1_tasks.keys(), phase1_results):
            results[aid] = result if not isinstance(result, Exception) else []

        # Fase 2: sourcing + intake (paralela)
        phase2 = ["talent_sourcing", "intake", "normalization", "deduplication"]
        phase2_tasks = {aid: self.run_agent(aid) for aid in phase2 if aid in self.agents}
        phase2_results = await asyncio.gather(*phase2_tasks.values(), return_exceptions=True)
        for aid, result in zip(phase2_tasks.keys(), phase2_results):
            results[aid] = result if not isinstance(result, Exception) else []

        # Fase 3: análisis (paralela)
        phase3 = ["talent_signal", "career_context", "fit_scoring", "evidence"]
        phase3_tasks = {aid: self.run_agent(aid) for aid in phase3 if aid in self.agents}
        phase3_results = await asyncio.gather(*phase3_tasks.values(), return_exceptions=True)
        for aid, result in zip(phase3_tasks.keys(), phase3_results):
            results[aid] = result if not isinstance(result, Exception) else []

        # Fase 4: memoria + QA + outreach (serial — dependen de fases anteriores)
        for aid in ["memory_update", "qa", "outreach", "ceo"]:
            if aid in self.agents:
                results[aid] = await self.run_agent(aid)

        return results

    def get_pending_actions(self) -> list[dict]:
        all_pending = []
        for agent_id, agent in self.agents.items():
            for action in agent.pending_actions:
                all_pending.append(action.to_dict())
        return sorted(all_pending, key=lambda a: a.get("score", 0), reverse=True)

    def _find_and_review(self, action_id: str, review_action: str, comment: str = ""):
        for agent in self.agents.values():
            for i, action in enumerate(agent.pending_actions):
                if action.action_id == action_id:
                    action.review(review_action, comment)
                    agent.pending_actions.pop(i)
                    agent.history.append(action)
                    self.save_state()
                    return action.to_dict()
        return None

    def approve_action(self, action_id: str, comment: str = ""):
        return self._find_and_review(action_id, "approved", comment)

    def reject_action(self, action_id: str, comment: str = ""):
        return self._find_and_review(action_id, "rejected", comment)

    def review_action(self, action_id: str, review_action: str, comment: str = ""):
        return self._find_and_review(action_id, review_action, comment)

    def get_status(self) -> dict:
        return {
            "run_id": self.runs[-1].run_id if self.runs else "N/A",
            "orchestrator": self.config["system"]["orchestrator"],
            "agents": {k: v.to_dict() for k, v in self.agents.items()},
            "pending_count": sum(len(a.pending_actions) for a in self.agents.values()),
            "total_history": sum(len(a.history) for a in self.agents.values()),
            "total_runs": len(self.runs),
            "last_runs": [r.to_dict() for r in self.runs[-5:]],
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }

    def get_agent_detail(self, agent_id: str) -> dict | None:
        agent = self.agents.get(agent_id)
        if not agent:
            return None
        return {
            **agent.to_dict(),
            "contract": agent.get_contract(),
            "pending_actions": [a.to_dict() for a in agent.pending_actions],
            "history": [a.to_dict() for a in agent.history[-20:]],
        }

    def run_tester(self):
        return self.agents["tester"].get_summary() if "tester" in self.agents else {}

    def save_state(self) -> None:
        try:
            StateStore.save_runs([r.to_dict() for r in self.runs])
            all_actions = []
            for agent in self.agents.values():
                for a in list(agent.pending_actions) + list(agent.history):
                    all_actions.append(a.to_dict())
            StateStore.save_actions(all_actions)
            agent_states = {aid: agent.to_dict() for aid, agent in self.agents.items()}
            StateStore.save_agent_states(agent_states)
        except Exception:
            pass

    def restore_state(self) -> dict:
        try:
            return StateStore.restore(self)
        except Exception:
            return {"runs_restored": 0, "agents_restored": 0}

    def clear_state(self) -> None:
        StateStore.clear()
        self.runs = []
        self._reset_all_agents()
