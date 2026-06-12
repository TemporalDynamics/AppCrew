# crew/

Infraestructura de agentes de EcoSign.

```
crew/
├── AGENTS.md          # Roster: roles, responsabilidades, modelo asignado
├── HARNESS.md         # Protocolo de orquestación entre agentes
├── docker-compose.yml # Hermes runtime (gateway + Telegram)
├── .env.example       # Variables requeridas (copiar a .env, nunca commitear .env)
├── skills/            # Skills de Claude Code para tareas específicas
│   ├── ecosign-release-check.md
│   ├── ecosign-supabase-migration.md
│   ├── ecosign-billing-stripe.md
│   └── ... (7 más por agregar)
├── briefs/            # Briefs operativos generados por orchestrator (git-tracked)
└── logs/              # Logs de sesiones de Hermes (gitignored)
```

## Cómo invocar un skill desde Claude Code

```
/ecosign-release-check
/ecosign-supabase-migration
/ecosign-billing-stripe
```

## Levantar Hermes local

```bash
cp crew/.env.example crew/.env
# completar crew/.env con API keys y Telegram token
docker compose -f crew/docker-compose.yml up -d
```

Dashboard disponible en `http://localhost:9119` (o via Tailscale desde fuera).
