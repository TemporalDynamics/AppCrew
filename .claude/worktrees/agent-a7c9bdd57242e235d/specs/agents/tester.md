# Agent: Tester

## 1. Propósito

Prueba automáticamente todo el sistema. Si encuentra un fallo claro y simple, lo corrige y reintenta hasta 3 veces. Si no puede, reporta y sigue.

## 2. No hace

- No modifica contracts
- No modifica lógica de negocio
- No bloquea el sistema (los tests corren en paralelo)

## 3. Inputs

- orquestador con todos los agentes registrados
- contracts del sistema
- config actual

## 4. Outputs

- `qa_summary`: resultado de cada test (PASS / SOFT_FAIL / HARD_FAIL)

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | no | |
| `browser` | no | |
| `email` | no | |
| `filesystem` | escritura controlada | solo para auto-fix de carpetas |
| `context7` | no | |
| `memory` | no | |

## 6. Context

- run_id actual
- orquestador con agentes registrados
- contracts

## 7. Memory

No necesita memoria entre runs. Cada ejecución de tests es fresca.

## 8. Heartbeat

```json
{
  "agent_id": "tester",
  "run_id": "...",
  "state": "working | idle | error",
  "last_action": "running_tests",
  "tests_passed": 10,
  "tests_failed": 0,
  "tests_total": 10
}
```

## 9. Invariantes

- [x] 3 intentos máximo por test
- [x] Auto-fix solo para fallos predecibles (carpetas)
- [x] No bloqueante: un test que falla no detiene los demás
- [x] Siempre produce reporte completo
- [x] Toda acción tiene run_id y dedup_key

## 10. Failure modes

- Orquestador no disponible: no corre
- Tests cuelgan: timeout de 10s por test

## 11. Escalation policy

- HARD_FAIL: se reporta en dashboard, requiere atención humana
- SOFT_FAIL con fix: se aplica y se registra

## 12. Tests mínimos

- [x] import OK
- [x] run produce resultados
- [x] 10 tests de sistema
- [x] 8 tests de invariantes
