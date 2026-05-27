# Demand Radar Agent

## Propósito

Detecta empresas con señales de contratación futura o inminente. Escanea fuentes públicas en busca de: rondas de inversión, nuevos ejecutivos, expansión geográfica, apertura de nuevas oficinas, cambios organizacionales.

NO contacta empresas, NO busca candidatos individuales.

## Precondiciones

- Al menos una fuente configurada (TechCrunch, Google News, Crunchbase, etc.)
- API key de Firecrawl configurada (opcional, cae a mock data si no hay)

## Postcondiciones

- Se genera una lista de oportunidades con empresa, señal, fuente, detalle y score
- Cada oportunidad tiene score entre 0-100
- No hay empresas duplicadas en una misma ejecución

## Invariantes

1. **Solo lectura** — nunca escribe en LinkedIn, nunca envía mensajes, nunca contacta empresas
2. **Toda oportunidad tiene score** — no se reportan oportunidades sin priorizar
3. **Deduplicación por empresa** — la misma empresa no aparece dos veces en el mismo ciclo
4. **Tasa de escaneo limitada** — máximo 1 escaneo por hora por fuente (evitar bans)
5. **Transparencia de fuente** — cada oportunidad indica de dónde se obtuvo

## Interfaz

### Parámetros (desde CEO)

```python
{
    "sources": ["techcrunch", "google_news", "crunchbase"],  # opcional, usa config por defecto
    "max_results": 10,
    "region": "México",  # o "LATAM", None = global
}
```

### Output (hacia CEO)

```python
[
    {
        "company": "TechMex",
        "signal": "Ronda Serie B por $12M — expansión de equipo",
        "source": "crunchbase",
        "detail": "...",
        "score": 92,
    },
    ...
]
```

## Fuentes

| Fuente | Método | API Key requerida |
|---|---|---|
| Firecrawl | Web crawling/scraping | Sí |
| Google News | HTTP GET (newsapi o scraping) | No (mock si falla) |
| Crunchbase | Firecrawl | Sí |
| LinkedIn Company Pages | Playwright (sesión autenticada) | Sesión LinkedIn |
