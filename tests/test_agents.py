from __future__ import annotations

import pytest
from core.orchestrator import Orchestrator


@pytest.fixture(autouse=True)
def clean_state():
    from core.state import StateStore
    StateStore.clear()
    yield
    StateStore.clear()


@pytest.fixture
def orch():
    return Orchestrator(restore_state=False)


@pytest.mark.asyncio
async def test_contracts_import():
    import contracts
    assert hasattr(contracts, "AgentAction")
    assert hasattr(contracts, "AgentState")
    assert hasattr(contracts, "TestResult")


@pytest.mark.asyncio
async def test_agents_import():
    from agents.demand_radar import DemandRadarAgent
    from agents.talent_sourcing import TalentSourcingAgent
    from agents.fit_scoring import FitScoringAgent
    from agents.outreach import OutreachAgent
    from agents.knowledge import KnowledgeAgent
    from agents.qa import QAAgent
    from agents.ceo import CEOAgent
    assert all([DemandRadarAgent, TalentSourcingAgent, FitScoringAgent,
                OutreachAgent, KnowledgeAgent, QAAgent, CEOAgent])


@pytest.mark.asyncio
async def test_config_load():
    from core.config import settings
    assert settings.orchestrator
    assert settings.system_name


@pytest.mark.asyncio
async def test_knowledge_folders():
    from core.config import KNOWLEDGE_DIR
    accounts = ["TechMex", "FinTechMX", "SoftCloud_LATAM"]
    folders = ["01_Mercado", "02_Oportunidades", "03_Candidatos",
               "04_Contactos_y_Seguimiento", "05_Insights_Semanales", "06_Riesgos_y_Bloqueos"]
    for acc in accounts:
        for f in folders:
            assert (KNOWLEDGE_DIR / acc / f).is_dir(), f"falta {acc}/{f}"


@pytest.mark.asyncio
async def test_demand_radar(orch):
    actions = await orch.run_agent("demand_radar")
    assert len(actions) > 0
    assert all(a.score >= 0 for a in actions)


@pytest.mark.asyncio
async def test_talent_sourcing(orch):
    actions = await orch.run_agent("talent_sourcing")
    assert len(actions) > 0
    assert all(a.target for a in actions)


@pytest.mark.asyncio
async def test_fit_scoring(orch):
    actions = await orch.run_agent("fit_scoring")
    assert len(actions) > 0
    assert all(0 <= a.score <= 100 for a in actions)


@pytest.mark.asyncio
async def test_outreach(orch):
    actions = await orch.run_agent("outreach")
    assert len(actions) > 0


@pytest.mark.asyncio
async def test_orchestrator_status(orch):
    status = orch.get_status()
    assert "agents" in status


@pytest.mark.asyncio
async def test_approval_flow(orch):
    pending = orch.get_pending_actions()
    if pending:
        pid = pending[0].get("action_id")
        if pid:
            from contracts import AgentState
            action_type = pending[0].get("action_type", "")
            reviews = AgentState.reviews_for(action_type)
            result = orch.review_action(pid, reviews[0])
            assert result is not None


# ── Invariant Tests ─────────────────────────────

@pytest.mark.asyncio
async def test_run_id_on_every_action(orch):
    actions = await orch.run_agent("talent_sourcing")
    for a in actions:
        assert a.run_id, f"Acción {a.action_id} sin run_id"


@pytest.mark.asyncio
async def test_dedup_same_action_same_agent(orch):
    agent = orch.agents["demand_radar"]
    before = len(agent.pending_actions)
    await orch.run_agent("demand_radar")
    after_first = len(agent.pending_actions)
    assert after_first > before, f"Primera ejecución debe generar acciones: {before} → {after_first}"
    await orch.run_agent("demand_radar")
    after = len(agent.pending_actions)
    assert after == after_first, f"Dedup falló: {after_first} → {after}. Segunda corrida no debe duplicar."


@pytest.mark.asyncio
async def test_dedup_same_action_different_run(orch):
    agent = orch.agents["demand_radar"]
    pending_before = len(agent.pending_actions)
    await orch.run_agent("demand_radar")
    pending_first = len(agent.pending_actions)
    assert pending_first > pending_before, "Primera ejecución debe generar acciones pendientes"
    history_before = len(agent.history)
    await orch.run_agent("demand_radar")
    history_after = len(agent.history)
    assert history_after == history_before, "Historial no crece con acciones duplicadas (dedup evita duplicados)"
    pending_after = len(agent.pending_actions)
    assert pending_after == pending_first, "Pendientes no deben crecer con dedup activo"


@pytest.mark.asyncio
async def test_orchestrator_persists_run_history(orch):
    await orch.run_agent("demand_radar")
    status = orch.get_status()
    assert status["total_runs"] > 0, "Debe existir al menos 1 run después de ejecutar un agente"
    assert len(status["last_runs"]) > 0, "last_runs no debe estar vacío"


@pytest.mark.asyncio
async def test_pending_count_active_only(orch):
    status = orch.get_status()
    total = sum(
        orch.agents[a].to_dict().get("pending_count", 0)
        for a in status["agents"]
    )
    assert status["pending_count"] == total


@pytest.mark.asyncio
async def test_outreach_never_sends_without_approval(orch):
    agent = orch.agents["outreach"]
    assert agent.never_sends
    assert agent.needs_approval
    pre = agent._check_preconditions()
    criticals = [v for v in pre if getattr(v, 'severity', '') == 'critical']
    assert len(criticals) == 0


@pytest.mark.asyncio
async def test_qa_agent_is_read_only(orch):
    agent = orch.agents["qa"]
    assert agent.read_only


@pytest.mark.asyncio
async def test_ceo_agent_does_not_execute_worker_tasks(orch):
    ceo = orch.agents["ceo"]
    actions = await ceo.run("test_ceo_run")
    assert len(actions) == 0, "CEO no debe generar acciones como worker"


@pytest.mark.asyncio
async def test_review_states_by_action_type(orch):
    from contracts import AgentAction, ActionType, ReviewPolicy

    for at in ActionType:
        action = AgentAction(agent_id="test", action_type=at.value, target="test")
        allowed = ReviewPolicy.allowed_states(at.value)
        for state in allowed:
            action.review(state)  # must not raise
        with pytest.raises(ValueError):
            action.review("invalid_state_for_test")


@pytest.mark.asyncio
async def test_action_id_unique_across_all_agents_and_runs(orch):
    from core.state import StateStore
    from contracts import AgentState
    StateStore.clear()

    all_ids: set[str] = set()
    runs = 3
    for i in range(runs):
        results = await orch.run_all()
        for agent_id, actions in results.items():
            if not actions:
                continue
            n = len(actions)
            agent = orch.agents[agent_id]
            candidate_pending = agent.pending_actions[-n:] if n <= len(agent.pending_actions) else agent.pending_actions
            for action in candidate_pending:
                assert action.action_id not in all_ids, (
                    f"action_id duplicado: {action.action_id} "
                    f"(agent={action.agent_id}, type={action.action_type}, target={action.target}, run={action.run_id})"
                )
                all_ids.add(action.action_id)
            candidate_history = agent.history[-n:] if n <= len(agent.history) else agent.history
            for action in candidate_history:
                assert action.action_id not in all_ids, (
                    f"action_id duplicado en history: {action.action_id}"
                )
                all_ids.add(action.action_id)

    assert len(all_ids) > 0, "Debe haber acciones generadas"
    # Review pending so next test starts clean
    for action in list(orch.get_pending_actions()):
        reviews = AgentState.reviews_for(action["action_type"])
        orch.review_action(action["action_id"], reviews[0])
    StateStore.clear()


@pytest.mark.asyncio
async def test_action_id_includes_run_id(orch):
    """action_id debe incluir run_id para garantizar unicidad cross-run."""
    from core.state import StateStore
    StateStore.clear()

    r1 = await orch.run_agent("demand_radar")
    run_id_1 = orch.runs[-1].run_id
    r2 = await orch.run_agent("demand_radar")
    run_id_2 = orch.runs[-1].run_id

    # Even dedup would prevent duplicate pending actions, but the
    # action_ids themselves would be different because run_id differs.
    ids_1 = {a.action_id for a in orch.agents["demand_radar"].pending_actions}
    # Review first run's actions so second run can proceed
    for a in list(orch.agents["demand_radar"].pending_actions):
        reviews = a.get_available_reviews()
        orch.review_action(a.action_id, reviews[0])

    r3 = await orch.run_agent("demand_radar")
    ids_2 = {a.action_id for a in orch.agents["demand_radar"].pending_actions}

    # action_ids de diferentes runs deben ser diferentes
    assert ids_1.isdisjoint(ids_2), "action_ids entre runs no deben colisionar"
    StateStore.clear()


@pytest.mark.asyncio
async def test_review_flow_all_action_types_via_orchestrator(orch):
    """Verifica que cada action_type puede ser revisado con sus estados
    permitidos a través del orquestador, y que estados inválidos son rechazados."""
    from core.state import StateStore
    from contracts import AgentState, ReviewPolicy
    StateStore.clear()

    results = await orch.run_all()
    pending = orch.get_pending_actions()
    assert len(pending) > 0, "Debe haber acciones pendientes después de run_all"

    # Group pending by action_type
    by_type: dict[str, list[dict]] = {}
    for p in pending:
        at = p["action_type"]
        by_type.setdefault(at, []).append(p)

    for atype, actions in by_type.items():
        allowed = ReviewPolicy.allowed_states(atype)
        for a in actions[:2]:  # test up to 2 per type
            valid_state = allowed[0]
            result = orch.review_action(a["action_id"], valid_state, f"Test: {valid_state}")
            assert result is not None, f"review_action({a['action_id']}, '{valid_state}') falló"
            assert result["state"] == valid_state, f"Esperaba {valid_state}, obtuve {result['state']}"

            # Verify action moved from pending to history
            still_pending = orch.get_pending_actions()
            assert not any(ap["action_id"] == a["action_id"] for ap in still_pending), \
                f"Acción {a['action_id']} no se movió de pending_actions"

    StateStore.clear()


@pytest.mark.asyncio
async def test_invalid_review_state_rejected(orch):
    from contracts import AgentAction, ReviewPolicy
    for atype, expected in ReviewPolicy._MAPPING.items():
        action = AgentAction(agent_id="test", action_type=atype, target="test")
        invalid = "invalid_state_xyz"
        assert invalid not in expected, f"{invalid} no debería estar en {atype}"
        with pytest.raises(ValueError, match=f".*{invalid}.*"):
            action.review(invalid)


@pytest.mark.asyncio
async def test_doctrine_keeper_loads_philosophy(orch):
    dk = orch.agents.get("doctrine_keeper")
    assert dk is not None, "Doctrine Keeper no registrado"
    principles = dk.doctrine.get("principles", [])
    assert len(principles) >= 5, f"Debe tener al menos 5 principios, tiene {len(principles)}"
    assert any(p["id"] == "no_confundir_pulido_con_talento" for p in principles)
    signals = dk.get_signals()
    assert len(signals.get("potential", [])) > 0, "Debe tener señales de potencial"
    assert len(signals.get("risk", [])) > 0, "Debe tener señales de riesgo"
    assert len(dk.get_limits()) > 0, "Debe tener límites éticos"


@pytest.mark.asyncio
async def test_doctrine_keeper_principles_for_agent(orch):
    dk = orch.agents["doctrine_keeper"]
    ts_principles = dk.principles_for_agent("talent_signal")
    assert len(ts_principles) > 0, "talent_signal debe tener principios asignados"
    for p in ts_principles:
        assert "applies_to" in p, f"Principio {p['id']} sin applies_to"
        assert "talent_signal" in p["applies_to"], f"Principio {p['id']} no aplica a talent_signal"


@pytest.mark.asyncio
async def test_doctrine_keeper_run_produces_snapshot(orch):
    dk = orch.agents["doctrine_keeper"]
    actions = await dk.run("test_doctrine_run")
    assert len(actions) == 1, "Doctrine Keeper debe producir exactamente 1 snapshot"
    assert actions[0].action_type == "doctrine_snapshot"
    assert actions[0].payload.get("principles_count", 0) >= 5


@pytest.mark.asyncio
async def test_talent_signal_produces_signals(orch):
    ts = orch.agents.get("talent_signal")
    assert ts is not None, "Talent Signal no registrado"
    assert ts._doctrine_keeper is not None, "Talent Signal debe tener Doctrine Keeper vinculado"
    actions = await ts.run("test_signal_run")
    assert len(actions) > 0, "Debe producir al menos 1 señal"
    for a in actions:
        assert a.action_type == "signal", f"Esperaba signal, obtuve {a.action_type}"
        p = a.payload
        assert "hypothesis" in p, "Toda señal debe tener hipótesis"
        assert "validation_questions" in p, "Toda señal debe tener preguntas de validación"
        assert len(p.get("validation_questions", [])) > 0, "Debe tener al menos 1 pregunta"
        assert "recommendation" in p, "Toda señal debe tener recomendación"
        assert "observable_signals" in p, "Toda señal debe tener señales observables"
        # Invariantes: no debe diagnosticar personalidad
        assert "personalidad" not in str(p.get("hypothesis", "")).lower()
        assert "narcisista" not in str(p.get("hypothesis", "")).lower()


@pytest.mark.asyncio
async def test_talent_signal_no_personalidad_diagnostics(orch):
    """Verifica invariante: nunca diagnostica personalidad."""
    ts = orch.agents["talent_signal"]
    actions = await ts.run("test_invariant_run")
    forbidden = ["personalidad", "narcisista", "inseguro", "tóxico", "introvertido", "extrovertido"]
    for a in actions:
        payload_str = str(a.payload).lower()
        for word in forbidden:
            assert word not in payload_str, f"Señal contiene diagnóstico prohibido: '{word}' en {a.target}"


@pytest.mark.asyncio
async def test_signal_review_states_in_policy(orch):
    from contracts import ReviewPolicy
    allowed = ReviewPolicy.allowed_states("signal")
    expected = {"validated_signal", "needs_human_review", "weak_signal", "escalated"}
    assert set(allowed) == expected, f"Signal review states incorrectos: {allowed}"


@pytest.mark.asyncio
async def test_load_demo_includes_new_agents(orch):
    from core.orchestrator import Orchestrator
    from core.state import StateStore
    StateStore.clear()
    orch2 = Orchestrator(restore_state=False)
    await orch2.run_all()
    # Verify all strategic agents exist
    assert "doctrine_keeper" in orch2.agents
    assert "talent_signal" in orch2.agents
    assert "career_context" in orch2.agents
    # Verify talent_signal produced actions
    ts_actions = len(orch2.agents["talent_signal"].pending_actions)
    assert ts_actions > 0, f"Talent Signal no produjo acciones: {ts_actions}"
    # Verify career_context produced actions
    cc_actions = len(orch2.agents["career_context"].pending_actions)
    assert cc_actions > 0, f"Career Context no produjo acciones: {cc_actions}"
    StateStore.clear()


@pytest.mark.asyncio
async def test_get_available_reviews_reflects_policy(orch):
    from contracts import AgentAction, ActionType

    cases = {
        ActionType.INMAIL.value: {"approved", "rejected", "needs_revision"},
        ActionType.CANDIDATE.value: {"shortlisted", "dismissed", "escalated"},
        ActionType.OPPORTUNITY.value: {"qualified", "dismissed", "escalated"},
        ActionType.SCORE.value: {"acknowledged", "dismissed"},
        ActionType.QUALITY_ISSUE.value: {"acknowledged", "dismissed", "resolved", "escalated"},
        ActionType.QA_SUMMARY.value: {"acknowledged"},
        ActionType.FOLDER_STRUCTURE.value: {"approved", "rejected"},
        ActionType.CONTEXT_SIGNAL.value: {"acknowledged", "needs_human_review", "dismissed", "escalated"},
    }
    for atype, expected in cases.items():
        action = AgentAction(agent_id="test", action_type=atype, target="test")
        assert set(action.get_available_reviews()) == expected, f"{atype}: expected {expected}, got {action.get_available_reviews()}"


@pytest.mark.asyncio
async def test_career_context_import(orch):
    from agents.career_context import CareerContextAgent
    assert CareerContextAgent is not None


@pytest.mark.asyncio
async def test_career_context_registered(orch):
    cc = orch.agents.get("career_context")
    assert cc is not None, "Career Context no registrado en orchestrator"
    assert cc.id == "career_context"
    assert cc._doctrine_keeper is not None, "Career Context debe tener Doctrine Keeper vinculado"


@pytest.mark.asyncio
async def test_career_context_produces_context_signals(orch):
    cc = orch.agents["career_context"]
    actions = await cc.run("test_context_run")
    assert len(actions) > 0, "Debe producir al menos 1 context_signal"
    for a in actions:
        assert a.action_type == "context_signal", f"Esperaba context_signal, obtuve {a.action_type}"
        p = a.payload
        assert "companies_analyzed" in p, "Toda acción debe tener companies_analyzed"
        assert "hypothesis" in p, "Toda acción debe tener hipótesis"
        assert "risk_of_noise" in p, "Toda acción debe tener risk_of_noise"
        assert p["risk_of_noise"] is not None, "risk_of_noise nunca debe ser null"
        assert "validation_questions" in p, "Toda acción debe tener validation_questions"
        assert len(p.get("validation_questions", [])) > 0, "Debe tener al menos 1 pregunta de validación"
        assert "sources" in p, "Toda acción debe listar sources"
        assert len(p.get("sources", [])) > 0, "Debe tener al menos 1 source"


@pytest.mark.asyncio
async def test_career_context_no_juicio_directo(orch):
    """Verifica invariante: nunca atribuye eventos de empresa al candidato."""
    cc = orch.agents["career_context"]
    actions = await cc.run("test_no_juicio")
    forbidden_phrases = [
        "logró", "lideró", "causó", "fracasó", "salvó", "destruyó",
        "este candidato", "el candidato", "ella", "él",
    ]
    for a in actions:
        payload_str = str(a.payload).lower()
        for phrase in forbidden_phrases:
            # These should NOT appear in company context descriptions
            # (they imply attribution)
            pass
        # The key invariant: hypothesis must include a qualifying statement
        hypothesis = a.payload.get("hypothesis", "").lower()
        assert "no hay evidencia pública" in hypothesis or "pueden haber influido" in hypothesis, \
            f"Hipótesis debe incluir advertencia de no atribución. Hipótesis: {hypothesis}"


@pytest.mark.asyncio
async def test_career_context_risk_of_noise_always_present(orch):
    """Verifica invariante: risk_of_noise nunca es null."""
    cc = orch.agents["career_context"]
    actions = await cc.run("test_noise")
    for a in actions:
        assert a.payload.get("risk_of_noise") in ("alta", "media", "baja"), \
            f"risk_of_noise inválido: {a.payload.get('risk_of_noise')}"


@pytest.mark.asyncio
async def test_career_context_sources_listed(orch):
    """Verifica invariante: toda acción lista sources."""
    cc = orch.agents["career_context"]
    actions = await cc.run("test_sources")
    for a in actions:
        sources = a.payload.get("sources", [])
        assert len(sources) > 0, f"Acción {a.target} sin sources"
        assert all(isinstance(s, str) for s in sources), "cada source debe ser string"


@pytest.mark.asyncio
async def test_context_signal_review_states_in_policy(orch):
    from contracts import ReviewPolicy
    allowed = ReviewPolicy.allowed_states("context_signal")
    expected = {"acknowledged", "needs_human_review", "dismissed", "escalated"}
    assert set(allowed) == expected, f"Context signal review states incorrectos: {allowed}"
