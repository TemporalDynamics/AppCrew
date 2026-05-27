# Agent: Talent Sourcing

## 1. Propósito

Busca talento por rol, industria, seniority y país desde LinkedIn y fuentes complementarias.

## 2. No hace

- No contacta candidatos
- No envía InMails
- No scorea candidatos (eso lo hace Fit Scoring)
- No escribe en LinkedIn

## 3. Inputs

- `role`, `industry`, `seniority`, `location` (desde CEO)
- `max_results`: límite de resultados (config)
- Sesión de LinkedIn (desde BrowserManager)

## 4. Outputs

- `candidate`: perfil con nombre, rol, empresa, ubicación, score preliminar

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | sí | LinkedIn Search |
| `browser` | sí | solo lectura, sesión autenticada |
| `email` | no | |
| `filesystem` | solo lectura | |
| `context7` | no | |
| `memory` | escritura namespace propio | `memory/talent_sourcing/*` |

## 6. Context

- run_id actual
- criterios de búsqueda (rol, ubicación)
- sesión de LinkedIn (desde BrowserManager)
- max_results

## 7. Memory

**Puede recordar entre runs:**
- candidatos ya vistos
- búsquedas recientes para evitar repetir

**NO puede recordar:**
- datos fuera de su búsqueda
- decisiones de contratación

**Namespace:** `memory/talent_sourcing/*`

## 8. Heartbeat

```json
{
  "agent_id": "talent_sourcing",
  "run_id": "...",
  "state": "working | idle | pending_review | error",
  "last_action": "searching_linkedin",
  "candidates_found": 5,
  "pending_actions": 0,
  "blocked": false
}
```

## 9. Invariantes

- [x] Solo lectura: nunca escribe en LinkedIn
- [x] No comparte datos fuera del sistema
- [x] Respeto de tasa (delays 2-7s entre acciones)
- [x] Cada candidato tiene ubicación
- [x] Toda acción tiene run_id y dedup_key

## 10. Failure modes

- LinkedIn bloquea: rotar sesión, esperar, reintentar
- Sin sesión: cae a mock data
- Sin resultados: reportar "no encontrados"

## 11. Escalation policy

- Sin resultados después de 3 intentos → escalar al CEO
- LinkedIn pide verificación → escalar al humano

## 12. Tests mínimos

- [x] import OK
- [x] run genera acciones válidas
- [x] run_id obligatorio
- [x] dedup funciona
- [x] no viola tools prohibidas
