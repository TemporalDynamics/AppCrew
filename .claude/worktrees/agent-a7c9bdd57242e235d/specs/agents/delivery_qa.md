# Agent: Delivery QA

## 1. Propósito

Control de calidad. Inspecciona datos, carpetas y acciones; reporta issues. **Solo lee, nunca modifica.**

## 2. No hace

- No modifica datos (invariante crítica)
- No elimina nada
- No bloquea procesos (solo informa)
- No toma decisiones

## 3. Inputs

- `scope`: "all" | "candidates" | "opportunities" | "folders"
- Datos del sistema: carpetas, acciones pendientes

## 4. Outputs

- `quality_issue`: problema detectado (severidad 40-100)
- `qa_summary`: reporte general PASS/FAIL

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | no | |
| `browser` | no | |
| `email` | no | |
| `filesystem` | solo lectura | nunca escribe |
| `context7` | no | |
| `memory` | no | |

## 6. Context

- run_id actual
- datos del sistema a inspeccionar

## 7. Memory

No necesita memoria entre runs. Cada inspección es fresca.

## 8. Heartbeat

```json
{
  "agent_id": "qa",
  "run_id": "...",
  "state": "working | idle | error",
  "last_action": "inspecting_folders",
  "checks_run": 10,
  "issues_found": 0,
  "pending_actions": 1
}
```

## 9. Invariantes

- [x] Solo lectura (read_only = True)
- [x] Nunca modifica datos
- [x] Siempre produce reporte (mínimo QA_SUMMARY)
- [x] Issue siempre tiene severidad
- [x] Accionable (cada issue incluye qué hacer)
- [x] No bloqueante
- [x] Toda acción tiene run_id y dedup_key

## 10. Failure modes

- Datos no disponibles: reporta "no data to inspect"
- Permisos de lectura: error, escala

## 11. Escalation policy

- Issues críticos (severidad > 80): destacar en reporte
- No puede leer datos: escala al CEO

## 12. Tests mínimos

- [x] import OK
- [x] run siempre produce al menos QA_SUMMARY
- [x] read_only = True
- [x] run_id obligatorio
- [x] dedup funciona
