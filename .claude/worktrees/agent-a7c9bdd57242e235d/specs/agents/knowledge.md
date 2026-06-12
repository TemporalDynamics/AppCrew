# Agent: Knowledge

## 1. Propósito

Organiza la memoria operativa del sistema. Mantiene la estructura de carpetas ejecutivas por cuenta. Solo crea, nunca elimina.

## 2. No hace

- No interpreta datos
- No scorea
- No genera contenido nuevo
- No elimina carpetas o archivos existentes

## 3. Inputs

- Lista de cuentas activas (desde config o autodetectadas)
- Estructura de carpetas definida

## 4. Outputs

- `folder_structure`: confirmación de carpetas creadas por cuenta

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | no | |
| `browser` | no | |
| `email` | no | |
| `filesystem` | escritura controlada | solo crear carpetas, nunca borrar |
| `context7` | no | |
| `memory` | no | |

## 6. Context

- run_id actual
- lista de cuentas
- estructura de carpetas

## 7. Memory

No necesita memoria entre runs. Es idempotente.

## 8. Heartbeat

```json
{
  "agent_id": "knowledge",
  "run_id": "...",
  "state": "working | idle | error",
  "last_action": "creating_folders",
  "accounts_organized": 3,
  "folders_created": 5,
  "pending_actions": 0
}
```

## 9. Invariantes

- [x] Nunca elimina datos
- [x] Estructura uniforme (todas las cuentas igual)
- [x] Idempotente (N ejecuciones = 1 ejecución)
- [x] Sin contenido generado (solo carpetas)
- [x] Toda acción tiene run_id y dedup_key

## 10. Failure modes

- Permisos de filesystem: error, reporta
- Disco lleno: error, escala

## 11. Escalation policy

- Error de permisos: escala al CEO
- Las cuentas no se pre-crean automáticamente si hay error

## 12. Tests mínimos

- [x] import OK
- [x] run genera acciones
- [x] carpetas existen después del run
- [x] run_id obligatorio
- [x] idempotente (segundo run no duplica)
