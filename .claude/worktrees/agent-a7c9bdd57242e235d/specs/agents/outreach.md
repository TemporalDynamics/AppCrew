# Agent: Outreach

## 1. Propósito

Genera borradores de contacto inicial y seguimiento para clientes potenciales y candidatos. **NUNCA envía sin aprobación humana explícita.**

## 2. No hace

- **NUNCA ejecuta el envío** (invariante crítica)
- No modifica mensajes después de aprobados
- No genera contenido fuera de su propósito (solo drafts de contacto)

## 3. Inputs

- Lista de targets con nombre, rol, empresa, canal, contexto
- Tono (desde config)
- Nombre del remitente

## 4. Outputs

- `inmail` / `email` / `connection_request`: borrador con mensaje, target, score

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | no | |
| `browser` | no | el envío lo ejecuta el orquestador después de aprobación |
| `email` | no | prohibido absolutamente |
| `filesystem` | solo lectura | |
| `context7` | no | |
| `memory` | escritura namespace propio | `memory/outreach/*` |

## 6. Context

- run_id actual
- targets con contexto
- tono configurado
- require_approval (debe ser True)

## 7. Memory

**Puede recordar entre runs:**
- mensajes ya enviados (para no repetir)
- targets contactados recientemente

**NO puede recordar:**
- contraseñas, tokens, datos sensibles

**Namespace:** `memory/outreach/*`

## 8. Heartbeat

```json
{
  "agent_id": "outreach",
  "run_id": "...",
  "state": "working | idle | pending_review | error",
  "last_action": "preparing_drafts",
  "drafts_prepared": 2,
  "pending_approval": 2,
  "blocked": false
}
```

## 9. Invariantes

- [x] **NUNCA envía** — solo prepara drafts. Es la regla más importante.
- [x] Si `require_approval = False`, no arranca (critical precondition)
- [x] Mensaje no se modifica después de aprobado
- [x] Trazabilidad completa (action_id único)
- [x] Máximo 1 mensaje por target por día
- [x] Toda acción tiene run_id y dedup_key

## 10. Failure modes

- require_approval en false: no arranca, error crítico
- Target sin datos suficientes: no genera draft, reporta

## 11. Escalation policy

- requiere_approval desactivado: error al orquestador, no escala al humano
- Contenido sensible detectado: escala al CEO para revisión manual

## 12. Tests mínimos

- [x] import OK
- [x] run genera borradores
- [x] run_id obligatorio
- [x] dedup funciona
- [x] never_sends = True
- [x] needs_approval = True
- [x] precondition crítica si require_approval = False
