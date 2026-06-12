from __future__ import annotations

from datetime import datetime, timezone
from typing import Any

from contracts import AgentAction, AgentState, InvariantViolation


class BaseAgent:
    id: str = ""
    name: str = ""
    icon: str = ""
    description: str = ""
    state: AgentState = AgentState.IDLE
    last_action: str = ""
    last_run: str | None = None
    last_run_id: str | None = None
    pending_actions: list[AgentAction] = []
    history: list[AgentAction] = []

    invariants: list[dict] = []
    read_only: bool = False
    never_sends: bool = True
    needs_approval: bool = True

    contract: dict = {}

    def __init__(self, config: dict | None = None):
        self.config = config or {}
        self._init_contract()

    def _init_contract(self):
        self.contract = {
            "tools": {},
            "context": [],
            "memory": {"namespace": "N/A", "can_remember": [], "cannot_remember": []},
            "invariants": [],
            "failure_modes": [],
            "escalation": [],
            "tests": [],
            "authority": "worker",
        }

    def reset_state(self):
        self.pending_actions = []
        self.history = []
        self.state = AgentState.IDLE
        self.last_action = ""
        self.last_run = None
        self.last_run_id = None

    async def run(self, run_id: str) -> list[AgentAction]:
        self.state = AgentState.WORKING
        self.last_run_id = run_id
        violations = self._check_preconditions()
        if violations:
            self.state = AgentState.ERROR
            self.last_action = f"Invariante violada: {violations[0].invariant}"
            return []

        try:
            actions = await self.work()
            deduped = self._deduplicate(actions)
            self._check_postconditions(actions)

            for idx, a in enumerate(deduped):
                a.run_id = run_id
                raw = f"{a.agent_id}|{run_id}|{a.action_type}|{a.target}|{idx}"
                h = abs(hash(raw))
                a.action_id = f"{a.agent_id}_{run_id[:12]}_{h % 10**12:012d}"
                self.pending_actions.append(a)

            if deduped:
                self.state = AgentState.PENDING_REVIEW
            else:
                self.state = AgentState.IDLE
            self.last_run = datetime.now(timezone.utc).isoformat()
            skipped = len(actions) - len(deduped)
            self.last_action = f"{len(deduped)} acciones ({skipped} duplicadas omitidas)"
            return deduped
        except Exception as e:
            self.state = AgentState.ERROR
            self.last_action = f"Error: {e}"
            return []

    async def work(self) -> list[AgentAction]:
        raise NotImplementedError

    def _check_preconditions(self) -> list[InvariantViolation]:
        return []

    def _check_postconditions(self, actions: list[AgentAction]) -> None:
        pass

    def _deduplicate(self, actions: list[AgentAction]) -> list[AgentAction]:
        existing = {a.dedup_key() for a in self.pending_actions}
        historical = {a.dedup_key() for a in self.history}
        all_seen = existing | historical
        return [a for a in actions if a.dedup_key() not in all_seen]

    def to_dict(self) -> dict:
        tools_list = sorted(
            k for k, v in self.contract.get("tools", {}).items() if v.get("permitted")
        )
        return {
            "id": self.id,
            "name": self.name,
            "icon": self.icon,
            "description": self.description,
            "state": self.state.value if hasattr(self.state, "value") else str(self.state),
            "last_action": self.last_action,
            "last_run": self.last_run,
            "last_run_id": self.last_run_id,
            "pending_count": len(self.pending_actions),
            "history_count": len(self.history),
            "contract_summary": {
                "tools": tools_list,
                "tools_count": len(tools_list),
                "invariant_count": len(self.contract.get("invariants", [])),
                "authority": self.contract.get("authority", "worker"),
                "memory_namespace": self.contract.get("memory", {}).get("namespace", "N/A"),
                "failure_modes": len(self.contract.get("failure_modes", [])),
                "escalation_rules": len(self.contract.get("escalation", [])),
                "tests": len(self.contract.get("tests", [])),
            },
        }

    def get_contract(self) -> dict:
        return self.contract

    def get_pending_actions(self) -> list[dict]:
        return [a.to_dict() for a in self.pending_actions]