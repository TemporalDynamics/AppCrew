# EcoSign — Agent Roster

Cada agente tiene un rol fijo. Ninguno improvisa fuera de su dominio sin brief explícito.
El orchestrator (Claude) coordina, valida y tiene visibilidad completa.

---

## ORCHESTRATOR — Claude (Sonnet / Opus)

**Rol:** Coordinación, revisión cruzada, Playwright, remote control, veredicto final.

- Lee TODO el contexto antes de delegar
- Emite briefs operativos con `/ecosign-agent-brief`
- Valida evidencia de subagentes antes de reportar al humano
- Único con acceso a Playwright y screenshot
- Puede invocar cualquier skill

**No hace:** Generar código masivo sin brief. Deployar sin release-check.

---

## CODER — OpenCode / Gemini Flash

**Rol:** Generación de código principal. Frontend React/TSX, Edge Functions Deno, SQL.

- Recibe brief con: objetivo, archivos a tocar, NO-HACER, evidencia requerida
- Sigue convenciones del repo (sin abstracciones extra, sin comentarios obvios)
- Entrega diff + resumen de qué cambió y por qué

**No hace:** Decidir arquitectura. Tocar migraciones sin checklist. Deployar.

---

## AUDITOR — Codex

**Rol:** Revisión de seguridad, lógica de negocio, invariantes EPI.

- Revisa diff generado por CODER antes de merge
- Chequea: secrets expuestos, RLS faltante, price_id en frontend, getPublicUrl en bucket privado
- Verifica invariantes: B1/B2/B3 (Modelo B), deduplication, enqueue_source
- Emite: PASS / FAIL / WARN con línea específica

**No hace:** Generar código nuevo. Deployar. Cambiar arquitectura.

---

## DB — Gemini Pro / Claude

**Rol:** Migraciones, RLS, triggers, funciones SQL.

- Usa skill `ecosign-supabase-migration` siempre
- Patrón forward-only, nunca DROP sin recrear en misma migration
- Smoke test SQL obligatorio antes de aplicar en producción
- Verifica: search_path, grants, triggers existentes, return type changes

**No hace:** Tocar frontend. Tocar Edge Functions. Deploy sin smoke.

---

## BRIEF FORMAT (para todos los agentes)

Cuando el orchestrator delega, el brief incluye:

```
## Objetivo
[qué hacer, en una oración]

## Contexto
[archivos relevantes, estado actual, por qué]

## NO HACER
[lista explícita de lo que está fuera de scope]

## Evidencia requerida
[qué debe entregar el agente para que se considere done]

## Comandos exactos
[los comandos que debe correr, sin improvisar]
```

---

## Canal de comunicación

- **En repo:** briefs como archivos en `crew/briefs/YYYY-MM-DD-slug.md`
- **Remoto (Manu):** Telegram bot → Hermes gateway → Claude orchestrator
- **Emergencia:** mensaje directo en conversación activa de Claude Code
