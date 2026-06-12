# Template de Spec para Agentes

Cada agente tiene un archivo `.md` en `specs/agents/` con esta estructura. Es un **contrato operativo**: los tests validan contra esto.

## 1. Propósito

Qué hace el agente. Una frase.

## 2. No hace

Qué tiene prohibido hacer explícitamente.

## 3. Inputs

Qué recibe para operar.

## 4. Outputs

Qué puede producir (tipos de acciones, eventos).

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | sí / no | |
| `browser` | sí / no | |
| `email` | sí / no | |
| `filesystem` | solo lectura / escritura controlada / prohibido | |
| `context7` | sí / no | para documentación técnica |
| `memory` | lectura / escritura namespace propio / prohibido | |

## 6. Context

Qué necesita para operar este run:
- configuración global
- run_id actual
- historial de acciones recientes
- criterios del CEO
- límites de búsqueda/cantidad

## 7. Memory

**Puede recordar entre runs:**
- ...

**NO puede recordar:**
- ...

**Namespace de memoria:** `memory/{agent_id}/*`

## 8. Heartbeat

Qué reporta periódicamente:

```json
{
  "agent_id": "...",
  "run_id": "...",
  "state": "working | idle | pending_review | error",
  "last_action": "...",
  "items_found": 0,
  "pending_actions": 0,
  "blocked": false,
  "blocked_reason": ""
}
```

## 9. Invariantes

Reglas que se cumplen siempre. Cada una es verificable por test.

- [ ] ...
- [ ] ...

## 10. Failure modes

Qué pasa si falla:
- fuente inaccesible
- API caída
- datos ambiguos
- duplicado detectado
- falta de contexto

## 11. Escalation policy

Cuándo escala al CEO:
- score bajo
- contradicción entre fuentes
- acción externa requerida
- información insuficiente

## 12. Tests mínimos

- [ ] import OK
- [ ] run genera acciones válidas
- [ ] run_id obligatorio
- [ ] dedup_key obligatorio
- [ ] heartbeat válido
- [ ] no viola tools prohibidas
