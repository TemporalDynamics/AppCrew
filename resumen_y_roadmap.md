# GE Agent System — Resumen + Roadmap

---

## Resumen de lo que tenemos

### Proyecto
```
global_executive/
├── contracts/          ← Tipos canónicos (AgentAction, AgentState, TestResult…)
├── agents/
│   ├── base.py         ← Agente base con máquina de estados
│   ├── ceo.py          ← Coordinador, traduce tareas humanas a órdenes
│   ├── demand_radar.py ← Detecta oportunidades (hiring signals)
│   ├── talent_sourcing.py ← Busca candidatos
│   ├── fit_scoring.py  ← Scorea candidatos con breakdown
│   ├── outreach.py     ← Prepara borradores (nunca envía sin aprobar)
│   ├── knowledge.py    ← Organiza carpetas ejecutivas
│   ├── qa.py           ← Control de calidad
│   └── tester.py       ← Auto-tester con 3 intentos de fix
├── core/
│   ├── config.py       ← Settings vía .env (pydantic-settings)
│   ├── browser.py      ← Playwright manager (LinkedIn)
│   └── orchestrator.py ← Orquestador + aprobaciones
├── dashboard/
│   ├── server.py       ← FastAPI
│   └── templates/      ← dashboard.html + ceo.html (mobile-first)
├── specs/              ← 8 specs con invariantes explícitas
│   ├── _index.md, relaciones.md
│   ├── ceo.md, demand_radar.md, talent_sourcing.md, fit_scoring.md
│   ├── outreach.md, knowledge.md, qa.md, tester.md
├── tests/
│   └── test_agents.py  ← Pytest (10 tests)
├── .env / .env.example
├── config.yaml
├── run.py / run.sh
├── propuesta_comercial_global_executive_agentes.md
└── arquitectura_tecnica.md
```

### Lo que funciona hoy
- **8 agentes** registrados y ejecutables (CEO, Tester + 6 workers)
- **10 tests** todos pasando (imports, config, cada agente, orquestador, approval flow)
- **Dashboard web** mobile-first con aprobación/rechazo de acciones
- **CEO Agent** que descompone tareas en lenguaje natural y coordina workers
- **Tester Agent** con auto-fix en 3 intentos
- **Contratos canónicos** que son el único punto de verdad del sistema
- **Flujo de aprobación** funcionando: PENDING_REVIEW → APPROVED/REJECTED
- **Estructura de carpetas ejecutivas** creada automáticamente

### Lo que es mock / pendiente
- Demand Radar, Talent Sourcing, Fit Scoring → datos mock, no conectados a fuentes reales
- Outreach prepara borradores pero no envía (por diseño, falta la ejecución)
- Playwright manager armado pero sin sesión de LinkedIn configurada
- CEO Agent usa regex, no LLM real
- Dashboard es HTML plano sin framework

---

## Roadmap

### Hito 1: Conectar fuentes reales
- Configurar sesión de LinkedIn en Playwright (persistente, stealth)
- Conectar Firecrawl con API key real
- Demand Radar escanea news reales (sin mock fallback)
- Talent Sourcing busca en LinkedIn con cuenta real
- Fit Scoring recibe datos reales de Sourcing

### Hito 2: CEO con LLM real
- Reemplazar regex por llamado a modelo (local vía Ollama)
- CEO puede interpretar tareas complejas: "Buscá CTOs en fintech mexicana que hayan escalado equipos"
- CEO redacta resúmenes en lenguaje natural
- CEO mantiene contexto de conversación

### Hito 3: Ejecución real de outreach
- Outreach conectado a LinkedIn real vía Playwright
- Flujo de aprobación → envío real de InMail
- Seguimiento automático de respuestas
- Tasa de respuesta como métrica

### Hito 4: Calidad producto
- Dashboard con framework frontend (React / Tailwind)
- Agentes con animaciones y estados visuales
- Vista proyector/TV para presentaciones
- Vista mobile nativa (PWA o app)
- Onboarding: conectar LinkedIn en 1 click

### Hito 5: Multicliente (vendible)
- Sistema de cuentas/clientes con aislamiento de datos
- White-label: logo, colores, nombre del sistema por cliente
- Tester Agent corre en cada cliente
- Reportes ejecutivos automáticos

### Hito 6: Offline total con Ollama
- Todo el stack funciona 100% local
- Sin dependencia de internet para operación diaria
- CEO, scoring, QA todo con modelo local
- Sincronización opcional cuando hay conexión

### Hito 7: Escalamiento
- Múltiples cuentas de LinkedIn rotativas
- Rate limiting inteligente por plataforma
- Agentes compiten por recursos (cola de tareas)
- Dashboard multi-orquestador

---

*Cada hito es un punto de validación: se puede usar en ese estado. No requiere completar hitos anteriores para arrancar el siguiente.*
