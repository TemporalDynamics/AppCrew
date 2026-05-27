# Especificación de Agentes — Global Executive

## Arquitectura

```
Humano (Orquestador)
    │
    ▼
┌──────────────┐
│  CEO Agent   │ ← Coordina, comunica, traduce
└──────┬───────┘
       │
       ▼
┌──────┴───────┐
│  Workers     │ → Demand Radar, Talent Sourcing, Fit Scoring,
│  (read-only) │   Outreach, Knowledge, QA
└──────────────┘
```

## Principios

1. **Cada agente tiene un dominio acotado** — no hace cosas fuera de su responsabilidad
2. **Invariantes explícitas** — precondiciones y postcondiciones documentadas
3. **CEO Agent es el único que habla directo con el humano** — los workers reportan al CEO
4. **Ningún worker ejecuta acciones externas sin aprobación** — eso lo gestiona el CEO + orquestador
5. **Todo se loguea** — cada acción, decisión y cambio de estado queda registrado

## Catálogo

| Agente | Rol | Comunicación |
|---|---|---|
| [CEO](ceo.md) | Coordinador, traduce tareas humanas a órdenes de agentes | Humano ↔ CEO ↔ Workers |
| [Demand Radar](demand_radar.md) | Detecta oportunidades de contratación | CEO → Radar → CEO |
| [Talent Sourcing](talent_sourcing.md) | Busca candidatos | CEO → Sourcing → CEO |
| [Fit Scoring](fit_scoring.md) | Scorea y prioriza | CEO → Scoring → CEO |
| [Outreach](outreach.md) | Prepara borradores de contacto | CEO → Outreach → CEO → Humano |
| [Knowledge](knowledge.md) | Organiza memoria operativa | CEO → Knowledge → CEO |
| [Delivery QA](qa.md) | Control de calidad | CEO → QA → CEO → Humano |

## Convención de invariantes

Cada agente define:

- **Propósito**: qué hace (y qué NO hace)
- **Precondiciones**: qué debe ser verdad antes de ejecutar
- **Postcondiciones**: qué garantiza después de ejecutar
- **Invariantes**: reglas que se cumplen siempre
- **Interfaz**: cómo se comunica con otros agentes y con el humano
