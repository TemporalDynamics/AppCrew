# EcoSign — Agent Harness

Protocolo de orquestación. Define cómo se inicia, delega, valida y cierra trabajo entre agentes.

---

## Principios

1. **Brief antes de código.** Ningún agente empieza sin brief escrito.
2. **Evidencia antes de merge.** El orchestrator valida antes de reportar done.
3. **Un agente, un dominio.** No cross-contaminar roles.
4. **Test mode primero.** Ningún cambio de billing va a live sin pasar test mode.
5. **Secretos nunca en diff.** Release-check bloquea si detecta secrets.

---

## Ciclo de tarea

```
Manu (Telegram / Claude Code)
  │
  ▼
Orchestrator (Claude)
  ├─ Lee contexto + skills relevantes
  ├─ Emite brief operativo
  │
  ▼
Agente asignado (CODER / DB / AUDITOR)
  ├─ Ejecuta dentro de scope
  ├─ Entrega diff + evidencia
  │
  ▼
Orchestrator valida
  ├─ Corre Playwright / checks automáticos
  ├─ PASS → reporta a Manu + merge
  └─ FAIL → brief de corrección → loop
```

---

## Skills disponibles

| Skill | Cuándo invocar |
|-------|---------------|
| `ecosign-release-check` | Antes de todo deploy/merge |
| `ecosign-supabase-migration` | Toda migration nueva o cambio de función SQL |
| `ecosign-billing-stripe` | Cualquier cambio en checkout, webhook, precios |
| `ecosign-edge-function` | Crear o modificar Edge Function |
| `ecosign-plan-enforcement` | Cambio en límites de plan o pricing |
| `ecosign-notifications` | Cambio en emails o ALLOWED_TYPES |
| `ecosign-artifacts-storage` | Artifacts, ECO, signed URLs |
| `ecosign-signature-flow` | apply/reject signature, workflow events |
| `ecosign-share-security` | Compartir documentos, OTP, rate limiting |
| `ecosign-agent-brief` | Generar brief para subagente |

---

## Hermes gateway (Telegram → Orchestrator)

El bot de Telegram envía mensajes al Hermes gateway.
El gateway resuelve el agente/skill correspondiente y ejecuta.
Claude actúa como orchestrator con acceso al repo y Playwright.

Config en: `crew/docker-compose.yml`
Variables requeridas: ver `crew/.env.example`

---

## Reglas de escalación

- Si una tarea toca **billing + DB + frontend** al mismo tiempo → brief separado por dominio, no un solo agente
- Si AUDITOR emite FAIL → CODER recibe brief de corrección, no el humano
- Si migration falla smoke test → no continúa, se reporta a Manu con evidencia exacta
- Si hay conflicto de arquitectura → orchestrator escala a Manu con opciones, no decide solo

---

## Registro de sesiones

Briefs activos: `crew/briefs/`
Log de agentes: `crew/logs/` (generado por Hermes)
Skills: `crew/skills/`
