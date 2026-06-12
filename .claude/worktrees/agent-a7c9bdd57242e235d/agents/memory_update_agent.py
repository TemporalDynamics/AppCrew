from agents.base import BaseAgent
from contracts import AgentAction, ActionType
from contracts.talent import CandidateSignal, CandidateEvidence
from core.talent_pool import TalentPool


class MemoryUpdateAgent(BaseAgent):
    id = "memory_update"
    name = "Memory Update"
    icon = "💾"
    description = "Persiste candidatos aprobados al Talent Pool después de cada run"
    read_only = False
    never_sends = True

    def _init_contract(self):
        self.contract = {
            "authority": "worker",
            "tools": {"memory": {"permitted": True, "notes": "escritura en TalentPool"}},
            "invariants": [
                "Solo persiste candidatos con state approved o shortlisted",
                "No duplica entradas existentes (upsert por dedup_key)",
            ],
            "context": ["run_id actual", "candidatos revisados del run anterior"],
        }

    async def work(self) -> list[AgentAction]:
        pool = TalentPool()
        saved = 0
        skipped = 0
        for action in self.history:
            if action.action_type != "candidate":
                continue
            if action.state not in ("approved", "shortlisted", "acknowledged"):
                skipped += 1
                continue
            payload = action.payload or {}
            evidence_list = []
            raw_ev = payload.get("evidence", [])
            if isinstance(raw_ev, list):
                for e in raw_ev:
                    if isinstance(e, dict):
                        evidence_list.append(CandidateEvidence(
                            label=e.get("label", ""),
                            value=e.get("value", ""),
                            url=e.get("url", ""),
                        ))
            signal = CandidateSignal(
                name=payload.get("name", action.target),
                current_role=payload.get("current_role") or payload.get("role", ""),
                company=payload.get("company", ""),
                location=payload.get("location", ""),
                source=payload.get("source", "manual"),
                source_url=payload.get("source_url", ""),
                availability_signal=payload.get("availability_signal", "unknown"),
                skills=payload.get("skills", []),
                evidence=evidence_list,
                raw_score=float(payload.get("raw_score", payload.get("score", 0) or 0)),
                risk_flags=payload.get("risk_flags", []),
                confidence=payload.get("confidence", "medium"),
            )
            pool.upsert_candidate(signal, run_id=action.run_id)
            saved += 1

        return [AgentAction(
            agent_id=self.id,
            action_type=ActionType.NOTE.value,
            target="memory_summary",
            reason=f"Guardados: {saved}, omitidos (no aprobados): {skipped}",
            payload={
                "saved": saved,
                "skipped": skipped,
                "pool_after": pool.get_pool_size(),
            },
            score=0,
        )]
