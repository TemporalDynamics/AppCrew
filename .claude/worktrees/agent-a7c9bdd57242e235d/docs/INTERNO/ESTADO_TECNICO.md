# Estado técnico actual — Plataforma de sourcing

> Documento interno — para dev / colaborador técnico.

---

## Stack

- Python 3.11+ (FastAPI, Playwright, Pydantic)
- SQLite (WAL mode)
- 11 agentes con contractos, estado, dedup, ciclo de aprobación humana
- Dashboard web (FastAPI + Jinja2)
- Ledger verificable (SHA-256 hash chain)
- 3 fuentes de talento conectadas (Torre.co, Brave Search, Firecrawl)
- Modo offline para desarrollo (demo data)

---

## Lo que ya existe

| Componente | Archivo | Estado |
|---|---|---|
| BaseAgent con state machine | `agents/base.py` | ✅ |
| 11 agentes implementados | `agents/*.py` | ✅ |
| Contract system (permisos por agente) | `agents/base.py` / `contracts/__init__.py` | ✅ |
| Revisión humana (approve/reject) | `core/orchestrator.py` | ✅ |
| Dedup entre runs | `agents/base.py:_deduplicate()` | ✅ |
| Persistencia SQLite | `core/state.py` | ✅ |
| Dashboard web | `dashboard/server.py` | ✅ |
| Notificación Telegram (outbound) | `core/telegram_notifier.py` | ✅ |
| Ledger verificable | `core/demo_notifiers.py` | ✅ |
| BrowserManager (Playwright) | `core/browser.py` | ✅ |
| Firecrawl scraper | `core/tools/firecrawl_client.py` | ✅ |
| Brave Search | `core/tools/search_client.py` | ✅ |
| Talent aggregator | `core/sources/aggregator.py` | ✅ |
| Demo completa | `scripts/demo_talent_mission.py` | ✅ |
| Test suite | `tests/test_agents.py` | ✅ |

---

## Lo que existe pero está incompleto

| Componente | Qué falta |
|---|---|
| BrowserManager (`core/browser.py`) | Solo LinkedIn, headless=False, sin MCP, sin browser-use |
| Telegram (`core/telegram_notifier.py`) | Solo outbound. No hay inbound bot |
| Pipeline (`core/orchestrator.py:run_all()`) | Secuencial puro. Sin paralelismo real |
| Memoria de talento | `deduplicate()` solo contra sesión actual |
| Config (`config.yaml`) | `max_results: 20` — sin concepto de volumen |

---

## Lo que hay que construir

| Componente | Prioridad |
|---|---|
| Inbound Telegram Bot | 🔴 Alta |
| Anti-prompt-injection (signed instruction key) | 🔴 Alta |
| Browser sandbox por job | 🔴 Alta |
| Memoria viva de talento (cross-run) | 🔴 Alta |
| Playwright MCP server o browser-use | 🟡 Media |
| Dockerfile + docker-compose + systemd | 🟡 Media |
| Paralelismo real en pipeline | 🟡 Media |
| Blind screening (cohortes anonimizadas) | 🟡 Media |
| Batch review / coverage reports / cohorts | 🟡 Media |
| Remote Operator Mode | 🟡 Media |
| Documentación de API y deploy | 🟡 Media |

---

## Roadmap interno (fases)

1. **Limpieza y renombre** — sacar "Global Executive" del código, limpiar secretos
2. **Seguridad activa** — sanitización, escaping, signal evidence, instruction key design
3. **Talent Pool persistente** — tablas candidates, identities, snapshots, evidence, matches, reviews
4. **Pipeline de responsabilidad** — intake → criteria → sourcing → normalize → dedup → evidence → score → blind → human → memory
5. **Blind Review** — vista anonimizada, ocultar nombre/foto, acción "revelar identidad"
6. **Coverage Report y volumen** — bands, cohorts, batch review
7. **Cuenta privada SelectaHR** — workspace, usuario, límites
8. **Documentos para Rodrigo** — ya están
9. **Browser Agent** — Playwright/MCP como tool controlada
10. **Remote Operator Mode** — Playwright = ojos, remote control = manos, Telegram = interfaz, VPS = residencia, human approval = freno
11. **API / MCP / Integraciones** — webhooks, CSV, ATS, self-hosted futuro
12. **Deployment 24/7** — local, VPS managed, BYOC
13. **Source Connector Policy** — clasificar fuentes, evidencia por candidato
14. **CVs voluntarios y ecosistema** — base privada vs opt-in

---

## Lo que necesita un dev para arrancar

- Python backend (asyncio, FastAPI, SQLite)
- Playwright o Puppeteer (browser automation)
- Deseable: MCP (Model Context Protocol)
- Inglés técnico
- Capacidad de trabajar con código existente y respetar convenciones

### Tiempo estimado

- Fase 1-2: ~1-2 semanas
- Fase 3-5: ~2-3 semanas
- Fase 6-8: ~2-3 semanas
- Fase 9-14: ~3-4 semanas
- **Total:** 8-12 semanas
