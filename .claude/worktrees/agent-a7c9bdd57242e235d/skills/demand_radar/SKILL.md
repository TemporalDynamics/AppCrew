# Demand Radar Skill — Detectar señales de mercado con fuentes reales

## Propósito
Detectar empresas con señales públicas de contratación futura usando Firecrawl
como fuente primaria, con fallback a mock. Nunca contacta empresas ni candidatos.

## Fuentes (por orden de prioridad)

1. **Firecrawl** (real) — si hay API key configurada
2. **News API** — fallback parcial si Firecrawl falla pero hay conexión
3. **Mock fallback** — datos demo predefinidos

## Reglas invariantes

1. **Solo lectura.** Nunca escribe en LinkedIn ni contacta empresas.
2. **Toda oportunidad tiene score 0-100.** Validado en `_check_postconditions`.
3. **Deduplicación por empresa en mismo ciclo.** No repetir empresa.
4. **Toda acción incluye:** `source_url`, `source_type`, `confidence`, `detail`.
5. **Nunca falsear fuente.** Si es mock, `source_type: "mock_fallback"`.

## Formato de acción

```python
AgentAction(
    agent_id="demand_radar",
    action_type="opportunity",
    target=company_name,
    reason=signal_description,
    payload={
        "company": "...",
        "signal": "...",
        "source_type": "real | mock_fallback",
        "detail": "...",
        "url": "...",
        "confidence": "alta | media | baja",
    },
    score=0-100,
)
```

## Heartbeat campos extra

- `sources_scanned`: número de fuentes consultadas
- `opportunities_found`: oportunidades generadas
- `real_sources`: cuántas vienen de Firecrawl real
- `mock_fallbacks`: cuántas son fallback
- `confidence_avg`: promedio de confianza

## Límites

- No busca candidatos (es dominio de Talent Sourcing)
- No calcula fit (es dominio de Fit Scoring)
- No escribe a empresas (es dominio de Outreach con approval humano)
