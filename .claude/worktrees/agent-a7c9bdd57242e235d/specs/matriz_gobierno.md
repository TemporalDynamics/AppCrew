# Matriz de Gobierno Operativo — GE Recruiting Desk

Estado del sistema al crear esta matriz:
- 11 agentes registrados ✅
- 38/38 tests pasan ✅
- QA no genera ruido de carpetas vacías ✅
- Firecrawl: API key vacía, integración parcial existente en Demand Radar
- No hay heartbeats, MCP, ni skills operativos todavía

---

## 1. Matriz principal: Agente → APIs → MCP → Skills → Heartbeat

| # | Agente | ID | APIs internas que necesita | APIs externas | MCP tools que expone/consume | Skill operativo | Heartbeat campos extra | Prioridad |
|---|--------|----|---------------------------|---------------|------------------------------|-----------------|----------------------|-----------|
| 1 | **CEO** | `ceo` | `/api/status`, `/api/run/{id}`, `/api/pending`, `/api/run-all` | Futuro: LLM local (Ollama) | `orchestrator.get_status`, `orchestrator.run_agent`, `orchestrator.run_all` | `skills/ceo/SKILL.md` — descomponer tareas, delegar, escalar | `current_task`, `delegated_agents`, `pending_decisions`, `blocked_reason` | P0 |
| 2 | **Tester** | `tester` | `/api/tester-results` | Ninguna | `tests.run`, `tests.report`, `safe_autofix.apply` | `skills/tester/SKILL.md` — qué puede auto-arreglar y qué no | `tests_total`, `tests_passed`, `tests_failed`, `autofix_attempts`, `critical_failures` | P2 |
| 3 | **Doctrine Keeper** | `doctrine_keeper` | `/api/doctrine/query` | Ninguna | `doctrine.get_principles`, `doctrine.query`, `doctrine.propose_update` | `skills/doctrine_keeper/SKILL.md` — custodiar filosofía GE | `doctrine_version`, `active_principles`, `queries_served`, `pending_updates` | P1 |
| 4 | **Talent Signal** | `talent_signal` | `/api/doctrine/query` | Opcional: LLM local | `candidate.read`, `doctrine.query`, `signal.generate` | `skills/talent_signal/SKILL.md` — hipótesis sin diagnosticar | `candidates_analyzed`, `signals_found`, `hypotheses_created`, `needs_human_review` | P1 |
| 5 | **Career Context** | `career_context` | `/api/doctrine/query`, `/api/sources/firecrawl/scrape` | **Firecrawl** (P0), News APIs | `company_context.scrape`, `context_signal.generate`, `firecrawl.search_company_context` | `skills/career_context/SKILL.md` — contexto empresa ≠ mérito candidato | `companies_analyzed`, `sources_found`, `risk_of_noise`, `fallback_used` | P1 |
| 6 | **Demand Radar** | `demand_radar` | `/api/sources/firecrawl/test`, `/api/sources/firecrawl/scrape` | **Firecrawl** (P0), News API | `market.scan`, `company.scrape`, `opportunity.create`, `firecrawl.scrape_url` | `skills/demand_radar/SKILL.md` — detectar demanda sin ruido | `sources_scanned`, `opportunities_found`, `real_sources`, `mock_fallbacks`, `confidence_avg` | P0 |
| 7 | **Talent Sourcing** | `talent_sourcing` | Ninguna | Futuro: LinkedIn (Playwright), no ahora | `candidate.extract`, `candidate.normalize` | `skills/talent_sourcing/SKILL.md` — sourcing read-only y rate limits | `profiles_seen`, `profiles_valid`, `blocked_by_login`, `rate_limit_state` | P3 |
| 8 | **Fit Scoring** | `fit_scoring` | `/api/doctrine/query` | Ninguna | `score.calculate`, `score.explain` | `skills/fit_scoring/SKILL.md` — scoring explicable, no black box | `candidates_scored`, `score_avg`, `weights_valid`, `missing_data_count` | P2 |
| 9 | **Outreach** | `outreach` | `/api/review/{id}` | Futuro: Email/LinkedIn (solo tras approval), no ahora | `draft.create`, `approval.check`, `send.blocked_by_default` | `skills/outreach/SKILL.md` — nunca enviar sin aprobación humana | `drafts_created`, `awaiting_approval`, `needs_revision`, `send_blocked` | P2 |
| 10 | **Knowledge** | `knowledge` | Ninguna | Ninguna | `filesystem.create_folder`, `knowledge.index`, `state.persist` | `skills/knowledge/SKILL.md` — crear estructura, nunca borrar | `accounts_checked`, `folders_created`, `folders_missing`, `write_errors` | P2 |
| 11 | **QA** | `qa` | `/api/qa/report` | Ninguna | `filesystem.readonly_check`, `state.inspect`, `issue.report` | `skills/qa/SKILL.md` — solo lectura, findings ≠ error | `checks_run`, `issues_found`, `critical_issues`, `read_only_confirmed` | P2 |

---

## 2. APIs internas: estado actual y pendientes

| Endpoint | Método | Sirve para | Agentes que la usan | Estado |
|----------|--------|------------|---------------------|--------|
| `/api/status` | GET | Estado general del sistema | Dashboard, CEO, Tester | ✅ Existe |
| `/api/pending` | GET | Acciones pendientes de revisión | Dashboard, CEO | ✅ Existe |
| `/api/run/{agent_id}` | POST | Ejecutar agente específico | Dashboard, CEO, Tester | ✅ Existe |
| `/api/run-all` | POST | Ejecutar sistema completo | Dashboard, CEO, demo | ✅ Existe |
| `/api/approve/{action_id}` | POST | Aprobar acción | Dashboard, CEO | ✅ Existe |
| `/api/reject/{action_id}` | POST | Rechazar acción | Dashboard, CEO | ✅ Existe |
| `/api/review/{action_id}` | POST | Revisar acción con estado válido | Dashboard, CEO | ✅ Existe |
| `/api/review-options/{action_id}` | GET | Estados permitidos por action_type | Dashboard | ✅ Existe |
| `/api/load-demo` | POST | Precargar demo | Dashboard | ✅ Existe |
| `/api/agent/{agent_id}` | GET | Detalle de agente (contract, memoria, history) | Dashboard | ✅ Existe |
| `/api/tester-results` | GET | Resumen del Tester | Dashboard | ✅ Existe |
| `/api/ceo/task` | POST | Enviar tarea al CEO | UI, scripts | ✅ Existe |
| `/api/heartbeat/{agent_id}` | GET | Último heartbeat de un agente | Dashboard, CEO | 🔴 Crear |
| `/api/heartbeats` | GET | Heartbeats de toda la flota | Dashboard | 🔴 Crear |
| `/api/doctrine/query` | POST | Consultar doctrina activa | Talent Signal, Career Context, CEO | 🔴 Crear |
| `/api/sources/firecrawl/test` | GET | Probar API key y conectividad Firecrawl | Demand Radar, Career Context | 🔴 Crear |
| `/api/sources/firecrawl/scrape` | POST | Scrapear URL controlado | Demand Radar, Career Context | 🔴 Crear |
| `/api/kpis` | GET | KPIs limpios para presentation mode | Dashboard | 🔴 Crear |

---

## 3. MCP tools a crear

No crear un MCP por agente. Crear **un solo MCP server** (`global_executive_mcp`) con tools agrupadas por dominio.

### Dominio: Orchestrator
| MCP tool | Qué hace | Lo consume |
|----------|----------|-----------|
| `orchestrator.get_status` | Estado global del sistema | CEO, dashboard externo |
| `orchestrator.run_agent` | Ejecuta un agente específico | CEO |
| `orchestrator.run_all` | Ejecuta todos los agentes | CEO, demo |
| `orchestrator.get_heartbeats` | Heartbeats de flota | CEO, dashboard |

### Dominio: Actions (Decision Inbox)
| MCP tool | Qué hace | Lo consume |
|----------|----------|-----------|
| `actions.list_pending` | Lista decisiones pendientes | CEO, dashboard |
| `actions.review` | Aplica review validado por ReviewPolicy | Dashboard, CEO |
| `actions.get_review_options` | Estados permitidos para una acción | Dashboard |
| `actions.get_detail` | Detalle completo de una acción | Dashboard, CEO |

### Dominio: Doctrine
| MCP tool | Qué hace | Lo consume |
|----------|----------|-----------|
| `doctrine.get_principles` | Lee doctrina activa | Talent Signal, Career Context |
| `doctrine.query` | Pregunta qué principio aplica | Talent Signal, Career Context, CEO |
| `doctrine.get_limits` | Límites éticos vigentes | Career Context, Talent Signal |

### Dominio: Firecrawl (wrapper compartido)
| MCP tool | Qué hace | Lo consume |
|----------|----------|-----------|
| `firecrawl.scrape_url` | Scrapea URL pública con fallback mock | Demand Radar, Career Context |
| `firecrawl.search_company_context` | Busca contexto público de empresa | Career Context |
| `firecrawl.scan_market` | Escanea señales de mercado | Demand Radar |
| `firecrawl.test_connection` | Prueba API key | Demand Radar, Career Context, dashboard |

### Dominio: Signals & Context
| MCP tool | Qué hace | Lo consume |
|----------|----------|-----------|
| `signals.analyze_candidate` | Ejecuta análisis cualitativo | Talent Signal |
| `signals.get_hypotheses` | Hipótesis activas sobre candidatos | Dashboard, CEO |
| `context.analyze_company` | Analiza contexto empresa/carrera | Career Context |

### Dominio: Scoring
| MCP tool | Qué hace | Lo consume |
|----------|----------|-----------|
| `scores.explain_candidate` | Breakdown del score de un candidato | Fit Scoring, Dashboard |

### Dominio: QA & Tests
| MCP tool | Qué hace | Lo consume |
|----------|----------|-----------|
| `qa.run_checks` | Corre QA read-only | QA, Tester |
| `tests.run_suite` | Corre tests del sistema | Tester, CEO |

### Dominio: State & Knowledge
| MCP tool | Qué hace | Lo consume |
|----------|----------|-----------|
| `state.save_snapshot` | Persiste estado actual | Orchestrator |
| `state.load_snapshot` | Restaura estado previo | Orchestrator |
| `knowledge.ensure_structure` | Crea/verifica carpetas por cuenta | Knowledge |

---

## 4. Skills operativos a crear

| Skill | Archivo | Propósito | Prioridad |
|-------|---------|-----------|-----------|
| CEO | `skills/ceo/SKILL.md` | Cómo interpretar tareas, delegar, resumir y escalar | P1 |
| Doctrine Keeper | `skills/doctrine_keeper/SKILL.md` | Cómo consultar/modificar doctrina sin romper autoridad | P1 |
| Talent Signal | `skills/talent_signal/SKILL.md` | Cómo generar hipótesis sin diagnosticar ni inventar | P1 |
| Career Context | `skills/career_context/SKILL.md` | Cómo separar contexto empresa de contribución del candidato | P1 |
| Demand Radar | `skills/demand_radar/SKILL.md` | Cómo detectar señales de mercado con fuentes reales | P0 |
| Talent Sourcing | `skills/talent_sourcing/SKILL.md` | Cómo buscar perfiles sin escribir ni violar límites | P3 |
| Fit Scoring | `skills/fit_scoring/SKILL.md` | Cómo calcular y explicar scores | P2 |
| Outreach | `skills/outreach/SKILL.md` | Cómo redactar borradores sin enviar | P2 |
| Knowledge | `skills/knowledge/SKILL.md` | Cómo organizar carpetas/memoria sin borrar | P2 |
| QA | `skills/qa/SKILL.md` | Cómo auditar solo en lectura | P2 |
| Tester | `skills/tester/SKILL.md` | Qué puede auto-fixear y qué debe escalar | P2 |
| **Firecrawl** | `skills/firecrawl/SKILL.md` | Cómo usar Firecrawl con fallback seguro | **P0** |
| **ReviewPolicy** | `skills/review_policy/SKILL.md` | Cómo aplicar estados por action_type | **P0** |
| Demo | `skills/demo/SKILL.md` | Cómo cargar demo, presentation mode y flujo de pitch | P1 |

---

## 5. Heartbeat estándar base

Todos los agentes emiten este mínimo:

```json
{
  "agent_id": "career_context",
  "run_id": "run_20260514_150910_xxxx",
  "state": "idle | working | pending_review | error",
  "last_action": "analizando contexto público de FinTechMX",
  "last_run_at": "2026-05-14T15:09:10Z",
  "actions_created": 3,
  "pending_actions": 1,
  "errors": [],
  "blocked": false,
  "blocked_reason": "",
  "source_type": "real | mock_fallback | internal",
  "confidence": "high | medium | low"
}
```

### Campos extra por agente

| Agente | Campos extra |
|--------|-------------|
| CEO | `current_task`, `delegated_agents`, `recommendation`, `human_decisions_required` |
| Tester | `tests_total`, `tests_passed`, `tests_failed`, `autofix_attempts` |
| Doctrine Keeper | `doctrine_version`, `active_principles`, `queries_served`, `pending_updates`, `contradictions_detected` |
| Talent Signal | `candidates_analyzed`, `signals_found`, `hypotheses_created`, `needs_human_review` |
| Career Context | `companies_analyzed`, `sources_found`, `context_signals`, `risk_of_noise`, `fallback_used` |
| Demand Radar | `sources_scanned`, `opportunities_found`, `real_sources`, `mock_fallbacks`, `confidence_avg` |
| Talent Sourcing | `profiles_seen`, `profiles_valid`, `candidates_created`, `blocked_by_login`, `rate_limit_state` |
| Fit Scoring | `candidates_scored`, `weights_valid`, `score_avg`, `missing_data_count` |
| Outreach | `drafts_created`, `awaiting_approval`, `needs_revision`, `send_blocked` |
| Knowledge | `accounts_checked`, `folders_created`, `folders_missing`, `write_errors` |
| QA | `checks_run`, `issues_found`, `critical_issues`, `qa_summary_created`, `read_only_confirmed` |

---

## 6. Plan de implementación priorizado

### P0 — Hacer antes de tocar Firecrawl

```
1. core/heartbeat.py             ← heartbeat estándar + emisión
2. /api/heartbeats               ← endpoint GET
3. /api/heartbeat/{agent_id}     ← endpoint GET
4. skills/firecrawl/SKILL.md     ← reglas de uso con fallback
5. skills/review_policy/SKILL.md ← estados por action_type
6. skills/demand_radar/SKILL.md  ← reglas de detección
```

### P0 — Firecrawl (wrapper compartido + integración)

```
7. core/tools/firecrawl_client.py ← wrapper con fallback mock
8. /api/sources/firecrawl/test    ← test de conectividad
9. /api/sources/firecrawl/scrape  ← scrape controlado
10. Demand Radar → firecrawl_client ← reemplazar lógica actual
11. Career Context → firecrawl_client ← extender con Firecrawl
```

### P1 — Skills críticos + MCP base

```
12. skills/ceo/SKILL.md
13. skills/doctrine_keeper/SKILL.md
14. skills/talent_signal/SKILL.md
15. skills/career_context/SKILL.md
16. skills/demo/SKILL.md
17. global_executive_mcp (orchestrator, doctrine, actions)
```

### P2 — Skills restantes + MCP completo

```
18. skills/tester/SKILL.md
19. skills/fit_scoring/SKILL.md
20. skills/outreach/SKILL.md
21. skills/knowledge/SKILL.md
22. skills/qa/SKILL.md
23. /api/doctrine/query
24. /api/kpis
25. MCP restante (signals, scores, qa, tests, state, knowledge)
```

### P3 — No ahora

```
26. LinkedIn Playwright wrapper
27. Talent Sourcing con datos reales
28. Outreach con envío real (solo tras approval humano)
29. skills/talent_sourcing/SKILL.md
```

---

## 7. Reglas invariantes para la integración

- **Firecrawl nunca rompe el demo.** Si la API key no existe o falla → `mock_fallback`.
- **Toda action** generada con Firecrawl incluye: `source_url`, `source_type: "real" | "mock_fallback"`, `confidence`, `raw_excerpt`.
- **Career Context** nunca atribuye eventos de empresa al candidato sin evidencia directa.
- **Career Context** solo genera contexto, hipótesis y preguntas de validación — nunca juicios.
- **Toda acción** tiene `source_type` explícito.
- **Toda acción** pasa por ReviewPolicy — no se pueden inventar estados de revisión.
- **Ningún agente** puede enviar email, inmail, o contacto directo sin approval humano.
- **QA** es solo lectura: findings ≠ error, no modifica nada.
