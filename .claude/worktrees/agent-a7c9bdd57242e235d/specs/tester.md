# Tester Agent

## Propósito

Prueba automáticamente todo el sistema: importaciones, configuración, ejecución de cada agente, flujo de aprobación y estructura de datos. Si encuentra un fallo **claro y simple de corregir**, lo arregla y reintenta hasta **3 veces**. Si no puede, reporta el fallo y sigue con la siguiente prueba.

## Precondiciones

- El sistema está instalado (dependencias en `pyproject.toml`)
- Los contracts existen y son importables
- El orquestador está inicializado

## Postcondiciones

- Todos los tests ejecutados (pasen o fallen)
- Los fallos auto-corregibles se intentaron hasta 3 veces
- Se genera un reporte con: tests totales, pasados, soft-fail, hard-fail

## Invariantes

1. **Nunca modifica contracts** — solo corrige estructura de datos (carpetas, archivos)
2. **3 intentos máx** — si falla 3 veces, abandona y marca HARD_FAIL
3. **No bloqueante** — un test que falla no detiene a los demás
4. **Auto-fix solo para fallos predecibles** — carpetas faltantes, imports obvios. No intenta corregir lógica de negocio
5. **Reporte completo** — siempre produce un resumen, aunque todo falle

## Tests ejecutados

| Test | ¿Qué verifica? | ¿Auto-fix? |
|---|---|---|
| `contracts_import` | Que contracts/__init__.py importa sin errores | No |
| `agents_import` | Que todos los agentes importan | No |
| `config_load` | Que .env se carga correctamente | No |
| `knowledge_folders` | Que las carpetas ejecutivas existen | Sí (crea faltantes) |
| `demand_radar_run` | Que Demand Radar genera acciones con score | No |
| `talent_sourcing_run` | Que Sourcing genera candidatos | No |
| `fit_scoring_run` | Que Scoring respeta rango 0-100 | No |
| `outreach_run` | Que Outreach genera borradores | No |
| `orchestrator_status` | Que el status tiene agents | No |
| `pending_flow` | Que aprobar/rechazar funciona | No |

## Interfaz

### Output (hacia dashboard)

```python
{
    "total": 10,
    "passed": 8,
    "soft_fail": 1,   # se arregló pero no del todo
    "hard_fail": 1,   # requiere atención humana
    "results": [
        {"test_name": "knowledge_folders", "verdict": "PASS", "attempts": 2, "fix_applied": "creadas carpetas faltantes"},
        {"test_name": "...", "verdict": "HARD_FAIL", "detail": "...", "attempts": 3},
        ...
    ]
}
```
