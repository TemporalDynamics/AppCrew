# Acceptance

La demo esta lista cuando:

- `python scripts/demo_criterion_intake.py --demo` genera `data/demo_rodri_criteria.yaml`.
- `python scripts/demo_talent_mission.py` corre en menos de 10 segundos.
- La salida muestra brief, celulas, shortlist, match de criterio y decision humana pendiente.
- Si Telegram no esta configurado, imprime `[TELEGRAM MOCK]` y sigue.
- Si el ledger verificable no puede escribir, imprime `[MCP MOCK]` y sigue.
- No requiere red, LinkedIn, Firecrawl ni modelos externos.

