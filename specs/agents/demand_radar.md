# Agent: Demand Radar

## 1. Propósito

Detecta empresas con señales de contratación futura o inminente (rondas de inversión, nuevos ejecutivos, expansión geográfica, cambios organizacionales).

## 2. No hace

- No contacta empresas
- No busca candidatos individuales
- No escribe en LinkedIn
- No envía mensajes

## 3. Inputs

- `sources`: lista de fuentes a escanear (config)
- `firecrawl_api_key`: para crawling web (config)
- `region`: filtro geográfico (opcional, desde CEO)

## 4. Outputs

- `opportunity`: empresa detectada con señal, fuente, detalle y score

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | sí | newsapi, firecrawl |
| `browser` | sí | solo lectura (LinkedIn company pages) |
| `email` | no | |
| `filesystem` | solo lectura | |
| `context7` | no | |
| `memory` | escritura namespace propio | `memory/demand_radar/*` |

## 6. Context

- run_id actual
- fuentes configuradas
- API key de Firecrawl (opcional)
- región de interés (desde CEO)

## 7. Memory

**Puede recordar entre runs:**
- empresas ya vistas (para no repetir)
- fuentes confiables / no confiables

**NO puede recordar:**
- datos de candidatos (no es su dominio)
- decisiones de aprobación humanas

**Namespace:** `memory/demand_radar/*`

## 8. Heartbeat

```json
{
  "agent_id": "demand_radar",
  "run_id": "...",
  "state": "working | idle | pending_review | error",
  "last_action": "scanning_sources",
  "items_found": 3,
  "pending_actions": 1,
  "blocked": false,
  "blocked_reason": ""
}
```

## 9. Invariantes

- [x] Solo lectura: nunca escribe en LinkedIn ni contacta empresas
- [x] Toda oportunidad tiene score entre 0-100
- [x] Deduplicación por empresa en mismo ciclo
- [x] Tasa de escaneo limitada (1 scan/hora/fuente)
- [x] Toda acción tiene run_id
- [x] Toda acción tiene dedup_key (agent_id + action_type + target)

## 10. Failure modes

- Fuente inaccesible: log y continua con otras fuentes
- API caída (newsapi, firecrawl): cae a mock data
- Sin fuentes configuradas: warning, usa mock

## 11. Escalation policy

- Score bajo (< 50): incluir en reporte pero no forzar revisión
- Contradicción entre fuentes: marcar como "pendiente de verificación"
- Acción externa requerida: nunca aplica (solo lectura)

## 12. Tests mínimos

- [x] import OK
- [x] run genera acciones válidas
- [x] run_id obligatorio
- [x] dedup funciona
- [x] no viola tools prohibidas
