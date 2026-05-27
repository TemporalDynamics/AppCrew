# Global Executive Crew Profile

Este repo contiene la demo de Global Executive: una celula operativa de talento que convierte criterio humano en busqueda, shortlist, aprobacion y evidencia.

## Puesta en marcha rapida

```bash
python scripts/demo_criterion_intake.py --demo
python scripts/demo_talent_mission.py
python demo_siren.py
```

## Piezas relevantes

- `agents/`: agentes de dominio de Global Executive.
- `crew/`: harness general que inspiro el protocolo de brief, evidencia y cierre.
- `verifiable-memory-mcp/`: memoria local verificable.
- `core/demo_notifiers.py`: fallback seguro para Telegram y ledger.
- `scripts/demo_criterion_intake.py`: captura criterio demo de Rodri.
- `scripts/demo_talent_mission.py`: corre la Talent Mission Capsule offline.

