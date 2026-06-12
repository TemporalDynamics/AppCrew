# Agent: Fit Scoring

## 1. Propósito

Prioriza candidatos con score explicable basado en habilidades, experiencia, señales de movilidad y consistencia de carrera.

## 2. No hace

- No busca candidatos
- No prepara mensajes
- No descarta candidatos unilateralmente (el score es recomendación)
- No modifica datos de entrada

## 3. Inputs

- Lista de candidatos con skills, experience, mobility, consistency
- Pesos de scoring (desde config, deben sumar 1.0)

## 4. Outputs

- `score`: candidato con total_score (0-100) y breakdown por dimensión

## 5. Tools permitidas

| Tool | Permitido | Notas |
|---|---|---|
| `web_search` | no | |
| `browser` | no | |
| `email` | no | |
| `filesystem` | solo lectura | |
| `context7` | no | |
| `memory` | solo lectura | no necesita recordar entre runs |

## 6. Context

- run_id actual
- lista de candidatos
- pesos de scoring (validados: suman 1.0)

## 7. Memory

No necesita memoria entre runs. Es determinístico: mismo input → mismo output.

## 8. Heartbeat

```json
{
  "agent_id": "fit_scoring",
  "run_id": "...",
  "state": "working | idle | pending_review | error",
  "last_action": "scoring_candidates",
  "candidates_scored": 5,
  "weights_valid": true
}
```

## 9. Invariantes

- [x] Pesos siempre suman 1.0 (se validan en preconditions)
- [x] Score entre 0-100
- [x] Score siempre explicable (breakdown por dimensión)
- [x] No elimina candidatos
- [x] Determinístico
- [x] Toda acción tiene run_id y dedup_key

## 10. Failure modes

- Pesos no suman 1.0: error crítico, no ejecuta
- Lista vacía: no genera acciones
- Datos incompletos: warning, scorea con datos disponibles

## 11. Escalation policy

- Pesos inválidos: error al orquestador, no escala
- Candidatos sin datos suficientes: incluir con score reducido y nota

## 12. Tests mínimos

- [x] import OK
- [x] run genera acciones válidas
- [x] run_id obligatorio
- [x] scores en rango 0-100
- [x] pesos suman 1.0
