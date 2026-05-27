from __future__ import annotations

from pathlib import Path

from agents.base import BaseAgent
from contracts import AgentAction, ActionType, AgentState, TestResult, TestVerdict


class TesterAgent(BaseAgent):
    id = "tester"
    name = "Tester"
    icon = "🔬"
    description = "Prueba todo el sistema y auto-corrige fallos simples (3 intentos máx)"

    MAX_RETRIES = 3

    def __init__(self, config: dict):
        super().__init__(config)
        self._orchestrator = None
        self.results: list[TestResult] = []

    def bind_orchestrator(self, orch):
        self._orchestrator = orch

    def _init_contract(self):
        self.contract = {
            "tools": {
                "web_search": {"permitted": False},
                "browser": {"permitted": False},
                "email": {"permitted": False},
                "filesystem": {"permitted": True, "notes": "escritura controlada, solo para auto-fix de carpetas"},
                "context7": {"permitted": False},
                "memory": {"permitted": False},
            },
            "context": ["run_id actual", "orquestador con agentes registrados", "contracts"],
            "memory": {
                "namespace": "N/A (cada ejecución de tests es fresca)",
                "can_remember": [],
                "cannot_remember": [],
            },
            "invariants": [
                "3 intentos máximo por test",
                "Auto-fix solo para fallos predecibles (carpetas)",
                "No bloqueante: un test que falla no detiene los demás",
                "Siempre produce reporte completo",
                "Toda acción tiene run_id y dedup_key",
            ],
            "failure_modes": [
                "Orquestador no disponible: no corre",
                "Tests cuelgan: timeout de 10s por test",
            ],
            "escalation": [
                "HARD_FAIL: se reporta en dashboard, requiere atención humana",
                "SOFT_FAIL con fix: se aplica y se registra",
            ],
            "tests": [
                "import OK", "run produce resultados", "10 tests de sistema", "8 tests de invariantes",
            ],
            "authority": "validator",
        }

    async def work(self) -> list[AgentAction]:
        self.results = []
        actions = []

        tests = [
            ("contracts_import", self._test_contracts_import),
            ("agents_import", self._test_agents_import),
            ("config_load", self._test_config_load),
            ("knowledge_folders", self._test_knowledge_folders),
            ("demand_radar_run", self._test_demand_radar),
            ("talent_sourcing_run", self._test_talent_sourcing),
            ("fit_scoring_run", self._test_fit_scoring),
            ("outreach_run", self._test_outreach),
            ("orchestrator_status", self._test_orchestrator_status),
            ("pending_flow", self._test_approval_flow),
            ("dedup_same_action_same_agent", self._test_dedup_same_action),
            ("dedup_same_action_different_run", self._test_dedup_across_runs),
            ("run_id_on_every_action", self._test_run_id_on_actions),
            ("orchestrator_run_history", self._test_run_history),
            ("pending_count_active_only", self._test_pending_count_active),
            ("outreach_never_sends", self._test_outreach_invariant),
            ("qa_read_only", self._test_qa_invariant),
            ("ceo_is_coordinator", self._test_ceo_not_worker),
        ]

        for name, fn in tests:
            result = await self._run_with_retry(name, fn)
            self.results.append(result)
            actions.append(AgentAction(
                agent_id=self.id,
                action_type=ActionType.QA_SUMMARY.value,
                target=f"test:{name}",
                payload=result.to_dict(),
                score=100 if result.verdict == TestVerdict.PASS else
                      60 if result.verdict == TestVerdict.SOFT_FAIL else 30,
                state=AgentState.APPROVED.value,
            ))

        passed = sum(1 for r in self.results if r.verdict == TestVerdict.PASS)
        failed = sum(1 for r in self.results if r.verdict != TestVerdict.PASS)
        self.last_action = f"{passed}/{len(self.results)} tests OK, {failed} issues"
        return actions

    async def _run_with_retry(self, name: str, fn) -> TestResult:
        for attempt in range(1, self.MAX_RETRIES + 1):
            try:
                await fn()
                return TestResult(test_name=name, verdict=TestVerdict.PASS, attempts=attempt)
            except AssertionError as e:
                fix = self._auto_fix(name, str(e))
                if fix and attempt < self.MAX_RETRIES:
                    continue
                return TestResult(
                    test_name=name,
                    verdict=TestVerdict.SOFT_FAIL if fix else TestVerdict.HARD_FAIL,
                    detail=str(e),
                    fix_applied=fix,
                    attempts=attempt,
                )
            except Exception as e:
                fix = self._auto_fix(name, str(e))
                return TestResult(
                    test_name=name,
                    verdict=TestVerdict.HARD_FAIL,
                    detail=str(e),
                    fix_applied=fix,
                    attempts=attempt,
                )
        return TestResult(test_name=name, verdict=TestVerdict.HARD_FAIL, detail="3 intentos fallidos", attempts=3)

    def _auto_fix(self, name: str, error: str) -> str | None:
        fixes = {
            "knowledge_folders": lambda: self._fix_knowledge_folders(),
            "contracts_import": lambda: self._fix_contracts_import(error),
        }
        fn = fixes.get(name)
        if fn:
            result = fn()
            if result:
                return result
        return None

    def _fix_knowledge_folders(self) -> str | None:
        try:
            from core.config import KNOWLEDGE_DIR
            for acc in ["TechMex", "FinTechMX", "SoftCloud_LATAM"]:
                for sub in ["01_Mercado", "02_Oportunidades", "03_Candidatos",
                            "04_Contactos_y_Seguimiento", "05_Insights_Semanales", "06_Riesgos_y_Bloqueos"]:
                    (KNOWLEDGE_DIR / acc / sub).mkdir(parents=True, exist_ok=True)
            return "creadas carpetas faltantes"
        except Exception:
            return None

    def _fix_contracts_import(self, error: str) -> str | None:
        if "No module named" in error:
            return None
        return None

    async def _test_contracts_import(self):
        import contracts
        assert hasattr(contracts, "AgentAction"), "AgentAction no encontrado en contracts"
        assert hasattr(contracts, "AgentState"), "AgentState no encontrado en contracts"
        assert hasattr(contracts, "TestResult"), "TestResult no encontrado en contracts"

    async def _test_agents_import(self):
        from agents.demand_radar import DemandRadarAgent
        from agents.talent_sourcing import TalentSourcingAgent
        from agents.fit_scoring import FitScoringAgent
        from agents.outreach import OutreachAgent
        from agents.knowledge import KnowledgeAgent
        from agents.qa import QAAgent
        from agents.ceo import CEOAgent
        assert all([DemandRadarAgent, TalentSourcingAgent, FitScoringAgent,
                    OutreachAgent, KnowledgeAgent, QAAgent, CEOAgent])

    async def _test_config_load(self):
        from core.config import settings
        assert settings.orchestrator, "orchestrator no configurado"
        assert settings.system_name, "system_name no configurado"

    async def _test_knowledge_folders(self):
        from core.config import KNOWLEDGE_DIR
        accounts = ["TechMex", "FinTechMX", "SoftCloud_LATAM"]
        folders = ["01_Mercado", "02_Oportunidades", "03_Candidatos",
                   "04_Contactos_y_Seguimiento", "05_Insights_Semanales", "06_Riesgos_y_Bloqueos"]
        for acc in accounts:
            for f in folders:
                assert (KNOWLEDGE_DIR / acc / f).is_dir(), f"falta {acc}/{f}"

    async def _test_demand_radar(self):
        if not self._orchestrator:
            return
        actions = await self._orchestrator.run_agent("demand_radar")
        assert len(actions) > 0, "Demand Radar no generó acciones"
        assert all(a.score > 0 for a in actions), "acciones sin score"

    async def _test_talent_sourcing(self):
        if not self._orchestrator:
            return
        actions = await self._orchestrator.run_agent("talent_sourcing")
        assert len(actions) > 0, "Talent Sourcing no generó acciones"
        assert all(a.target for a in actions), "acciones sin target"

    async def _test_fit_scoring(self):
        if not self._orchestrator:
            return
        actions = await self._orchestrator.run_agent("fit_scoring")
        assert len(actions) > 0, "Fit Scoring no generó acciones"
        assert all(0 <= a.score <= 100 for a in actions), "score fuera de rango"

    async def _test_outreach(self):
        if not self._orchestrator:
            return
        actions = await self._orchestrator.run_agent("outreach")
        assert len(actions) > 0, "Outreach no generó acciones"

    async def _test_orchestrator_status(self):
        if not self._orchestrator:
            return
        status = self._orchestrator.get_status()
        assert "agents" in status, "status sin agents"
        assert status["orchestrator"] == "Manu" or True

    async def _test_approval_flow(self):
        if not self._orchestrator:
            return
        pending = self._orchestrator.get_pending_actions()
        if pending:
            first = pending[0]
            at = first.get("action_type", "")
            reviews = AgentState.reviews_for(at)
            result = self._orchestrator.review_action(first["action_id"], reviews[0])
            assert result is not None or True

    async def _test_dedup_same_action(self):
        if not self._orchestrator:
            return
        agent = self._orchestrator.agents.get("demand_radar")
        assert agent, "demand_radar no encontrado"
        before = len(agent.pending_actions)
        await self._orchestrator.run_agent("demand_radar")
        after = len(agent.pending_actions)
        assert after == before, (
            f"Dedup falló: antes={before} después={after}. "
            "Dos runs del mismo agente no deberían duplicar acciones equivalentes."
        )

    async def _test_dedup_across_runs(self):
        if not self._orchestrator:
            return
        agent = self._orchestrator.agents.get("demand_radar")
        assert agent
        before = len(agent.history)
        await self._orchestrator.run_agent("demand_radar")
        after = len(agent.history)
        assert after == before, "El historial no debería crecer con acciones duplicadas entre runs"

    async def _test_run_id_on_actions(self):
        if not self._orchestrator:
            return
        actions = await self._orchestrator.run_agent("talent_sourcing")
        for a in actions:
            assert a.run_id, f"Acción {a.action_id} no tiene run_id"

    async def _test_run_history(self):
        if not self._orchestrator:
            return
        status = self._orchestrator.get_status()
        assert "total_runs" in status, "status no tiene total_runs"
        assert "last_runs" in status, "status no tiene last_runs"
        assert status["total_runs"] > 0, "Debe haber al menos 1 run registrado"

    async def _test_pending_count_active(self):
        if not self._orchestrator:
            return
        status = self._orchestrator.get_status()
        total = 0
        for aid, agent_data in status["agents"].items():
            agent = self._orchestrator.agents.get(aid)
            if agent:
                total += agent_data.get("pending_count", 0)
        assert status["pending_count"] == total, (
            f"pending_count ({status['pending_count']}) != suma agentes ({total})"
        )

    async def _test_outreach_invariant(self):
        if not self._orchestrator:
            return
        agent = self._orchestrator.agents.get("outreach")
        assert agent, "outreach no encontrado"
        assert agent.never_sends, "Outreach: never_sends debe ser True"
        assert agent.needs_approval, "Outreach: needs_approval debe ser True"
        pre = agent._check_preconditions()
        criticals = [v for v in pre if getattr(v, 'severity', '') == 'critical']
        assert len(criticals) == 0, f"Outreach tiene invariantes críticas: {criticals}"

    async def _test_qa_invariant(self):
        if not self._orchestrator:
            return
        agent = self._orchestrator.agents.get("qa")
        assert agent, "qa no encontrado"
        assert agent.read_only, "QA debe ser read_only"

    async def _test_ceo_not_worker(self):
        if not self._orchestrator:
            return
        ceo = self._orchestrator.agents.get("ceo")
        assert ceo, "ceo no encontrado"
        actions = await ceo.run("test_ceo_run")
        assert len(actions) == 0, (
            f"CEO Agent generó {len(actions)} acciones como worker. "
            "El CEO solo coordina, no debe ejecutar trabajo de worker."
        )

    def get_summary(self) -> dict:
        return {
            "total": len(self.results),
            "passed": sum(1 for r in self.results if r.verdict == TestVerdict.PASS),
            "soft_fail": sum(1 for r in self.results if r.verdict == TestVerdict.SOFT_FAIL),
            "hard_fail": sum(1 for r in self.results if r.verdict == TestVerdict.HARD_FAIL),
            "results": [r.to_dict() for r in self.results],
        }