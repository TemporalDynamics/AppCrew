# Career Context Skill — Contexto empresa ≠ mérito candidato

## Propósito
Reconstruir el contexto público de empresas donde trabajó un candidato
para interpretar mejor su trayectoria. Nunca atribuir eventos de empresa
al candidato sin evidencia directa.

## Reglas invariantes (no negociables)

1. **Nunca atribuir eventos de empresa al candidato sin evidencia directa.**
   - Que la empresa haya tenido una ronda de inversión no significa que el candidato la lideró.
   - Que la empresa haya tenido una crisis no significa que el candidato la causó o la resolvió.

2. **Nunca penalizar por industria, momento de empresa o crisis externa.**

3. **Nunca usar rumores ni fuentes no verificables.**

4. **Toda acción incluye `risk_of_noise`:**
   - `baja` → contexto completo, fuentes múltiples
   - `media` → contexto parcial o alguna empresa sin datos
   - `alta` → mayoría de empresas sin contexto recuperable

5. **Toda acción incluye `validation_questions`:**
   Separar contexto público de contribución real del candidato.
   Ej: "Durante tu etapa en TechMex (2021-2024), la empresa atravesó [evento].
   ¿Qué parte te tocó liderar o gestionar directamente?"

6. **Nunca recomendar contratar, descartar ni priorizar candidatos.**

## Fuentes permitidas

- Firecrawl (scraping de páginas públicas)
- Crunchbase (datos de inversión/liderazgo)
- Prensa/noticias públicas
- LinkedIn (solo páginas de empresa públicas, no perfiles de candidato)

## Formato de acción

```python
AgentAction(
    agent_id="career_context",
    action_type="context_signal",
    target="Nombre Candidato — Rol",
    payload={
        "candidate_name": "...",
        "companies_analyzed": [...],
        "hypothesis": "...",
        "risk_of_noise": "baja | media | alta",
        "validation_questions": [...],
        "sources": [...],
        "source_type": "real | mock_fallback",
    },
    score=based_on_confidence,
)
```

## Heartbeat campos extra

- `companies_analyzed`: número de empresas procesadas
- `sources_found`: fuentes únicas consultadas
- `risk_of_noise`: nivel de ruido actual
- `fallback_used`: si se usó mock (bool)
