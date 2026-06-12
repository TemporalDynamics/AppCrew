# Firecrawl Skill — Integración con fallback seguro

## Propósito
Wrapper compartido para Firecrawl que usan Demand Radar y Career Context.
Nunca rompe el demo. Siempre cae a mock_fallback si la API key no existe o falla.

## Reglas invariantes

1. **Nunca romper demo si Firecrawl falla.**
   - `FIRECRAWL_API_KEY` vacía o errónea → `mock_fallback`
   - Timeout o error de red → `mock_fallback`
   - Sin conexión → `mock_fallback`

2. **Siempre marcar `source_type: real | mock_fallback`.**
   - Si se usó Firecrawl real → `source_type: "real"`
   - Si se usó fallback → `source_type: "mock_fallback"`

3. **Siempre guardar URL/fuente.**
   - Si es real → `url` con la URL escrapeada
   - Si es mock → `url` vacío

4. **Toda acción generada debe incluir:**
   - `source_url`
   - `source_type`
   - `confidence`
   - `raw_excerpt` o `detail`

## Límites de autoridad

- Firecrawl solo lee páginas públicas (careers pages, blogs, notas, comunicados)
- No accede a LinkedIn (requiere sesión autenticada)
- No almacena datos personales
- No hace scraping agresivo (1 request por URL, rate limit natural)

## Fallback mock

Los datos mock están definidos en `core/tools/firecrawl_client.py`.
Incluyen 3 empresas demo (TechMex, FinTechMX, SoftCloud LATAM) con señales
y contexto público simulado. Suficiente para que el demo funcione sin API key.

## Heartbeat

Al usar Firecrawl, incluir en el heartbeat:
```json
{
  "source_type": "real | mock_fallback",
  "confidence": "high | medium | low",
  "api_available": true | false
}
```
