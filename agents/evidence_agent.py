from agents.base import BaseAgent
from contracts import AgentAction, ActionType


class EvidenceAgent(BaseAgent):
    id = "evidence"
    name = "Evidence"
    icon = "📎"
    description = "Genera audit trail de qué keywords dispararon qué señales y el razonamiento analítico"
    read_only = True
    never_sends = True

    def _init_contract(self):
        self.contract = {
            "authority": "auditor",
            "tools": {},
            "invariants": [
                "No modifica datos — solo reporta",
                "Cada señal debe tener keyword o razonamiento que la originó",
            ],
            "context": ["run_id actual", "candidatos con signal_evidence o hypothesis en payload"],
        }

    async def work(self) -> list[AgentAction]:
        actions = []
        for action in self.pending_actions:
            if action.action_type not in ("candidate", "signal", "context_signal"):
                continue
            
            payload = action.payload or {}
            name = payload.get("candidate_name") or payload.get("name") or action.target
            
            # Case 1: Traditional Signal Evidence (Keywords)
            signal_evidence = payload.get("signal_evidence", {})
            
            # Case 2: Deep Analytical Signal (Talent Signal)
            observable_signals = payload.get("observable_signals", [])
            hypothesis = payload.get("hypothesis", "")
            
            # Case 3: Career Context
            companies_analyzed = payload.get("companies_analyzed", [])

            if not (signal_evidence or observable_signals or companies_analyzed or hypothesis):
                continue

            lines = []
            if signal_evidence:
                lines.append("--- Keywords detectadas ---")
                for signal_name, keyword in signal_evidence.items():
                    lines.append(f"• {signal_name}: {keyword}")
            
            if observable_signals:
                lines.append("--- Señales Observables (Análisis Profundo) ---")
                for s in observable_signals:
                    lines.append(f"• {s}")
            
            if hypothesis:
                lines.append("--- Hipótesis de Valor ---")
                lines.append(hypothesis)
            
            if companies_analyzed:
                lines.append("--- Contexto de Empresas ---")
                for c in companies_analyzed:
                    status = c.get("status", "desconocido")
                    signals = c.get("signals", [])
                    lines.append(f"• {c['company']} ({c['period']}): {status}")
                    if signals:
                        lines.append(f"  └ Señales: {', '.join(signals)}")

            audit = "\n".join(lines)
            actions.append(AgentAction(
                agent_id=self.id,
                action_type=ActionType.NOTE.value,
                target=f"proof:{name}",
                reason=f"Evidencia analítica consolidada para {name}",
                payload={
                    "candidate": name,
                    "audit_trail": audit,
                    "source_agent": action.agent_id,
                },
                score=0,
            ))
        return actions
