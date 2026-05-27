# Agent: CEO

## 1. Propósito

Coordina la comunicación entre el humano y los agentes worker. Recibe tareas en lenguaje natural, las descompone, delega a los workers apropiados, recolecta resultados y sintetiza una respuesta accionable.

## 2. No hace

- No ejecuta trabajo de workers (no busca candidatos, no scorea, no prepara borradores)
- No envía mensajes externos
- No modifica memoria interna de otros agentes
- No almacena datos operativos (carpetas, candidatos, oportunidades)

## 3. Inputs

- `task_text`: tarea en lenguaje natural desde el humano
- `context` (opcional): cuenta, prioridad, notas
- `reply_to` (opcional): id de tarea anterior para seguimiento

## 4. Outputs

- `CEOResponse`: resumen, plan, resultados por agente, acciones pendientes

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | no | |
| `browser` | no | |
| `email` | no | |
| `filesystem` | solo lectura de config | |
| `context7` | sí | para resolver dudas técnicas del humano |
| `memory` | lectura de resúmenes de workers | solo lectura, namespace `memory/ceo/*` |

## 6. Context

- run_id actual
- lista de workers disponibles y sus capacidades
- historial de conversación (últimos 20 mensajes)

## 7. Memory

**Puede recordar entre runs:**
- historial de conversación con el humano
- últimos planes generados

**NO puede recordar:**
- datos operativos de workers
- decisiones de aprobación no resueltas

**Namespace:** `memory/ceo/*`

## 8. Heartbeat

```json
{
  "agent_id": "ceo",
  "run_id": "...",
  "state": "listening | interpreting | delegating | collecting | synthesizing | reporting | escalating",
  "last_action": "...",
  "conversation_length": 5,
  "pending_tasks": 0
}
```

## 9. Invariantes

- [ ] `work()` siempre devuelve lista vacía (es coordinador, no worker)
- [ ] Nunca ejecuta acciones externas
- [ ] Toda comunicación se loguea en conversation_log
- [ ] No modifica memoria interna de workers
- [ ] Escala al humano si no puede descomponer una tarea

## 10. Failure modes

- Tarea ambigua: escala al humano pidiendo aclaración
- Worker no disponible: reporta error parcial
- Timeout de worker: reintenta 1 vez, luego escala

## 11. Escalation policy

- Tarea no descomponible → humano
- Worker falla → CEO reintenta 1 vez, luego reporta error parcial
- Se requiere acción externa → deriva a orquestador para aprobación humana

## 12. Tests mínimos

- [x] import OK
- [x] `work()` devuelve 0 acciones
- [x] `process_task()` descompone y delega correctamente
- [x] No contiene lógica de worker
