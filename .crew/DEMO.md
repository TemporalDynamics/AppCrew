# Demo Mission

## Objetivo

Mostrar que Global Executive no opera agentes sueltos: opera una Talent Mission Capsule con criterio, celulas, evidencia, aprobacion humana y memoria verificable.

## Secuencia

1. Capturar criterio de Rodri.
2. Generar brief operativo.
3. Hidratar 4 microcelulas de busqueda.
4. Cargar golden set de calibracion: obvio, fino, dudoso y falso positivo.
5. Producir shortlist curada y explicar que hizo el sistema con cada tipo.
6. Registrar eventos en ledger verificable o fallback.
7. Notificar por Telegram o mock.

## No Hacer

- No usar LinkedIn en vivo.
- No depender de APIs externas.
- No prometer que los datos demo son reales.
- No refactorizar dashboard.
- No crear 25 clones.
- No enviar mensajes reales.

## Frase de demo

"Antes de buscar, el sistema captura como piensa Rodri. Despues calibra contra cuatro perfiles: uno obvio, uno fino, uno dudoso y uno que parece bueno pero no lo es. Recién despues busca como Global Executive."

## Runbook de manana

### Arranque limpio

```bash
bash scripts/demo_reset.sh
python dashboard/server.py
```

Qué tiene que verse:

- criterion intake cargado
- Talent Mission Capsule generada
- 4/4 calibracion visibles
- shortlist con 4 candidatos
- verify OK del ledger

### Momento 1: criterio + shortlist

```bash
python3 scripts/demo_criterion_intake.py --demo
python3 scripts/demo_talent_mission.py
```

Qué tiene que verse:

- golden set cargado: 4
- obvio / fino / dudoso / falso positivo
- comportamiento esperado
- comportamiento observado
- cierre: "El sistema no solo encontró perfiles; mostró si entiende el criterio de Rodri."

### Momento 2: integridad verificable

```bash
bash scripts/demo_tamper.sh
```

Qué tiene que verse:

- verify OK antes del tamper
- modificación directa en SQLite
- verify FAIL después del tamper
- `[TELEGRAM MOCK]` con alerta

### Restauración después del show

```bash
bash scripts/demo_reset.sh
```

## Contingencias

- Si `demo_tamper.sh` dice que el ledger no existe o ya está roto: correr `bash scripts/demo_reset.sh`.
- Si Telegram no está configurado: el mock en consola es comportamiento esperado.
- Si MCP no puede escribir en SQLite: el fallback JSONL es comportamiento esperado.
