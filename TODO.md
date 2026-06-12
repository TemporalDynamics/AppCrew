# TODO — Talo / Global Executive (estado verificado 2026-06-12: 17/18 tests, dashboard ✅, bot Telegram ✅, 19 keys reales en .env)

Cliente: Rodri (Global Executive / SelectaHR). Regla: nunca mezclar con proyectos personales.
Verificación global: `python3 run.py test` (hoy: 17/18)

## P0 — Idempotencia (riesgo de papelón con cliente)
- [ ] Arreglar `dedup_same_action_same_agent` (HARD_FAIL): sin esto una acción puede
      ejecutarse 2 veces (ej: dos mails al mismo candidato)
      → Verificar: `python3 run.py test` debe dar 18/18

## P1 — Inventario real vs mock
- [ ] Auditar conectores tras el trabajo post-demo: qué fuente usa datos reales hoy
      (las keys de Firecrawl/Serper/Apollo/OpenRouter están cargadas; `estado_mvp_vs_produccion.md`
      del 14-may decía "parcialmente mock" — confirmar qué cambió)

## P2 — Deploy fuera de la laptop
- [ ] VPS chico (~$5-10/mes) + `deploy/platform.service` (ya escrito) + dashboard detrás de
      auth (ADMIN_ACCESS_CODE y DASHBOARD_API_TOKEN ya existen)
- [ ] Separar entorno demo vs piloto (lo pide el propio `plan_hardening_30_60_dias.md`, Fase 0)

## Web SelectaHR — NO HACER hasta que la pidan
- El cliente dijo que la hace él. Cuando vuelva (va a volver): alcance cerrado
  (landing: hero + cómo funciona + contacto/Calendly que ya está en .env) y precio APARTE.
- [ ] Hoy solo: confirmarle por escrito "la web la hacés vos, ¿cierto?" — deja registro para cotizar

## Fáciles (cualquier tarde)
- [ ] Sacar imágenes personales del repo (cami y rodri.png, etc.) si se va a compartir con el cliente
- [ ] Resolver la copia interna de verifiable-memory-mcp (apuntar al paquete npm publicado
      en vez de copia divergente)
