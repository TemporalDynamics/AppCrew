# Índice de Relaciones — Dependencias entre Agentes y Contratos

## Contratos Canónicos (`contracts/__init__.py`)

Son el **único punto de verdad** del sistema. Todos los agentes importan desde acá.

```
contracts/
└── __init__.py     ← AgentState, AgentAction, TestResult, CEOResponse, etc.
       ▲
       │
       ├── agents/base.py         (herencia)
       ├── agents/demand_radar.py  (usa AgentAction)
       ├── agents/talent_sourcing.py
       ├── agents/fit_scoring.py
       ├── agents/outreach.py
       ├── agents/knowledge.py
       ├── agents/qa.py
       ├── agents/ceo.py          (usa CEOResponse)
       ├── agents/tester.py       (usa TestResult)
       ├── core/orchestrator.py   (usa AgentAction, SystemStatus)
       ├── dashboard/server.py    (usa orchestrator)
       └── tests/*.py
```

## Grafo de Dependencias

```
                tests/
                  │
                  ▼
           ┌─────────────┐
           │ Orchestrator │
           └──────┬───────┘
                  │
     ┌────────────┼────────────┬──────────┐
     ▼            ▼            ▼          ▼
 ┌───────┐  ┌──────────┐  ┌───────┐  ┌───────┐
 │ CEO   │  │ Tester   │  │ base  │  │config │
 │ Agent │  │ Agent    │  │ Agent │  │(.env) │
 └───┬───┘  └────┬─────┘  └───────┘  └───────┘
     │           │                │
     │           │           ┌────┴─────┐
     │           │           │contracts │
     │           │           └──────────┘
     ▼           ▼
 ┌──────────────────────────────┐
 │ Worker Agents                │
 │ demand_radar, sourcing,      │
 │ fit_scoring, outreach,       │
 │ knowledge, qa                │
 └──────────────────────────────┘
```

## Matriz de Dependencias

| Componente | Depende de | Usa contratos |
|---|---|---|
| `contracts/__init__` | — | — |
| `agents/base.py` | `contracts` | AgentState, AgentAction |
| `agents/demand_radar.py` | `base`, `contracts` | AgentAction, ActionType |
| `agents/talent_sourcing.py` | `base`, `contracts` | AgentAction |
| `agents/fit_scoring.py` | `base`, `contracts` | AgentAction |
| `agents/outreach.py` | `base`, `contracts` | AgentAction |
| `agents/knowledge.py` | `base`, `contracts` | AgentAction, ActionType |
| `agents/qa.py` | `base`, `contracts` | AgentAction, AgentState |
| `agents/ceo.py` | `base`, `contracts` | AgentAction, AgentState |
| `agents/tester.py` | `base`, `contracts` | TestResult, TestVerdict |
| `core/orchestrator.py` | `agents.*` | AgentAction, AgentState |
| `core/config.py` | `.env` | — |
| `core/browser.py` | `config.yaml` | — |
| `dashboard/server.py` | `orchestrator` | — |
| `tests/test_agents.py` | `orchestrator` | — |

## Flujo de datos

```
.env  ──→  config.py  ──→  orchestrator  ──→  dashboard/server.py
                              │
                    ┌─────────┴──────────┐
                    ▼                    ▼
             CEO Agent             Worker Agents
                    │                    │
                    └────────┬───────────┘
                             ▼
                      contracts/
                      AgentAction
                      (pending_review)
                             │
                             ▼
                      Orchestrator
                      (aprueba/rechaza)
                             │
                             ▼
                      Historial + Carpetas
```

## Reglas de dependencia

1. Los `contracts` **no importan nada del sistema** — son types puros
2. Los agentes importan `contracts` y `base` — nada más del sistema
3. El `orquestador` importa agentes — los agentes no importan al orquestador
4. El `dashboard` importa al orquestador — el orquestador no importa al dashboard
5. `config.py` solo depende de `.env` — no importa agentes ni contratos
