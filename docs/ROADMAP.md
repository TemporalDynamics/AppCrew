# Roadmap — Plataforma de Sourcing Asistido (Cerno)

> Cada fase tiene checkboxes para marcar lo completado.

---

## Fase 1 — Limpieza y renombre

- [ ] Confirmar nombre temporal del producto (pendiente)
- [x] Revisar README, UI, rutas, variables, textos donde aparezca "Global Executive" (README actualizado, DB renombrada a `state.db`, ledger tags limpiados)
- [ ] Separar: repo/producto propio vs workspace Global Executive vs workspace SelectaHR
- [x] Verificar que no haya secretos, tokens, claves, datos reales sensibles ni `.env` expuestos (`.env` en gitignore, no trackeado)
- [x] Crear `.env.example` limpio
- [ ] Crear `SECURITY_NOTES.md` con reglas mínimas

---

## Fase 2 — Seguridad activa

- [x] Sanitizar texto externo antes de keyword matching (`_sanitize_external_text()` en `aggregator.py`)
- [x] Escapar Markdown en Telegram (mejorado `_esc()` en `telegram_notifier.py` — chars restantes + usado en todos los métodos)
- [x] Bajar peso de señales inferidas desde fuentes externas (`signals_inferred` flag en payload, badge en dashboard)
- [x] Registrar `signal_evidence`: qué campo o keyword generó cada señal (dict en `aggregator.py:signal_to_candidate_dict()`)
- [x] Evitar que una señal inferida se muestre como verificada (badge "📡 señales inferidas" + "📡 inferido" en inbox, brief contabiliza inferidas)
- [x] Diseño de instruction signing / HMAC documentado en `docs/INTERNO/HMAC_DESIGN.md`

---

## Fase 3 — Talent Pool persistente

- [x] Crear tabla `candidates`
- [x] Crear tabla `candidate_identities`
- [x] Crear tabla `candidate_snapshots`
- [x] Crear tabla `candidate_evidence`
- [x] Crear tabla `search_requests`
- [x] Crear tabla `search_matches`
- [x] Crear tabla `review_events`
- [x] Mantener `dedup_key`, `last_seen`, `source`, `confidence`, `status`
- [x] Separar identidad real de vista anonimizada (`get_anonymous_view()`)
- [x] Registrar cada aparición de un candidato sin duplicarlo (`import_from_candidate_action()` con upsert)
- [x] Implementado en `core/talent_pool.py` con API completa + test verificado

---

## Fase 4 — Pipeline de responsabilidad clara

- [x] Intake Agent: valida candidatos entrantes (`agents/intake_agent.py`)
- [x] Criteria Agent: lee criterios desde `data/demo_rodri_criteria.yaml` (`agents/criteria_agent.py`)
- [x] Sourcing Agent: busca en fuentes permitidas (existente)
- [x] Normalization Agent: normaliza location/skills/company (`agents/normalization_agent.py`)
- [x] Deduplication Agent: detecta repetidos contra TalentPool (`agents/deduplication_agent.py`)
- [x] Evidence Agent: audit trail de keywords que dispararon señales (`agents/evidence_agent.py`)
- [x] Scoring Agent: ubica en bandas (existente)
- [x] Blind Review Agent: vista anonimizada (Fase 5)
- [x] Human Review: aprueba/descarta (existente vía dashboard)
- [x] Memory Update Agent: persiste candidatos aprobados al TalentPool (`agents/memory_update_agent.py`)
- [x] Pipeline paralelo en 4 fases implementado en `orchestrator.py:run_all()`

---

## Fase 5 — Blind Review

- [x] Crear vista anonimizada de candidato (`get_anonymous_view()` en `talent_pool.py`)
- [x] Ocultar nombre, foto, links directos y datos identificatorios (template `blind_review.html`)
- [x] Mostrar: experiencia relevante, señales de encaje, señales dudosas, fuente, confianza, banda
- [x] Agregar acción "revelar identidad" (botón + API `/api/blind/reveal/{id}`)
- [x] Registrar quién reveló, cuándo y por qué (`record_review()` con stage `revealed`)
- [x] Comunicar como reducción de sesgo temprano, no eliminación total (intro en template)
- [x] Ruta `/blind` en dashboard con cards anonimizadas + acciones shortlist/dismiss/reveal

---

## Fase 6 — Coverage Report y volumen

- [x] Reporte por búsqueda: encontrados, por banda, por fuente, por estado (`/coverage` route + `dashboard/templates/coverage.html`)
- [x] Score Bands: prioridad 1, prioridad 2, revisar manual, descartar (barras de progreso en template)
- [ ] Cohorts: ubicación, seniority, disponibilidad, industria, experiencia, tipo de rol
- [ ] Batch review para revisar por grupos
- [ ] El sistema responde al tamaño de la necesidad (no cantidades fijas)

---

## Fase 7 — Cuenta privada para Rodrigo / SelectaHR

- [x] Crear workspace `selectahr` (tabla `workspaces` en `talent_pool.py`)
- [x] Crear usuario Rodrigo con permisos limitados (tabla `workspace_users`, seed automático al arrancar dashboard)
- [x] Definir límites: fuentes, volumen, acciones permitidas (en schema: `allowed_sources`, `max_queries`, `max_candidates`)
- [ ] Permitir: cargar criterio, buscar, revisar, aprobar/descartar, pedir evidencia, revelar identidad (Fase 4-5 ya cubren flujo)
- [ ] Bloquear: acceso a otros workspaces, prompts maestros, credenciales, config global, fuentes no autorizadas, auto-contacto (falta middleware de auth)
- [x] Documentar alcance de la cuenta privada (en `docs/PARA_RODRIGO/`)

---

## Fase 8 — Documentos para Rodrigo

- [ ] Documento de visión y uso (qué hace, qué no hace, rol del humano, fuentes, blind review, límites)
- [ ] Acuerdo de piloto (participación independiente, propiedad, cuenta limitada, fuentes autorizadas, no compromiso comercial)
- [ ] Documento de CVs (base privada SelectaHR, opt-in para ecosistema, no mezcla automática)
- [ ] Los 3 documentos listos para enviar antes del link

---

## Fase 9 — Browser Agent / Playwright / MCP

- [ ] Definir browser como herramienta controlada (no libertad total)
- [ ] Sandbox por job: contexto limpio por búsqueda
- [ ] No usar sesiones personales, cookies personales ni cuentas privadas
- [ ] No acceder a perfiles cerrados
- [ ] Permitir: navegar, leer, capturar evidencia, screenshot, extraer datos permitidos
- [ ] Bloquear: formularios sensibles, envío de mensajes, login con credenciales personales, scraping fuera de fuentes autorizadas
- [ ] Evaluar Playwright MCP como integración (`@playwright/mcp`)
- [ ] Exponer browser tools solo con permisos y logs

---

## Fase 10 — Remote Operator Mode

- [ ] Definir remote control como modo operativo (no reemplaza Playwright, lo complementa)
- [ ] El agente puede operar sobre máquina persistente (VPS / Mac dedicado)
- [ ] Playwright/MCP = ojos sobre páginas web
- [ ] Remote control = manos sobre entorno operativo
- [ ] Telegram/móvil = interfaz humana remota
- [ ] VPS = residencia 24/7
- [ ] Human approval = freno de seguridad
- [ ] Sandbox + permisos + logs + fuentes autorizadas
- [ ] Acciones sensibles requieren aprobación humana

---

## Fase 11 — API / MCP / Integraciones

- [ ] API interna para dashboard y backend
- [ ] Webhooks para eventos
- [ ] Export CSV / Sheets
- [ ] Integración futura con ATS
- [ ] MCP server para agentes externos o internos
- [ ] Self-hosted / BYOC solo si un cliente lo justifica

---

## Fase 12 — Deployment 24/7

- [x] Nivel 1: Local demo (corre en máquina de desarrollo)
- [ ] Nivel 2: VPS managed (corre 24/7, piloto con Rodrigo) — pendiente VPS real
- [ ] Nivel 3: Self-hosted / BYOC (infraestructura del cliente, futuro B2B)
- [x] Dockerfile + docker-compose para deploy
- [x] Systemd service (`deploy/platform.service`)
- [ ] Documentación de deploy

---

## Fase 13 — Source Connector Policy

- [ ] Clasificar cada fuente: API, carga manual, pública con límites, requiere revisión legal, bloqueada
- [ ] Cada candidato debe tener: `source_url`, `fuente`, `fecha`, `evidencia`, `confianza`
- [ ] Indicar si es perfil público o dato aportado
- [ ] Indicar si su identidad puede mostrarse o no
- [ ] El objetivo es tener conectores confiables, no muchos scrapers

---

## Fase 14 — CVs voluntarios y ecosistema

- [ ] CVs cargados para SelectaHR quedan en base privada de SelectaHR
- [ ] Visibilidad ampliada solo si el talento lo autoriza
- [ ] Opt-in separado para ecosistema general
- [ ] No mezcla automática de bases privadas

---

## Primera versión validable (con Rodrigo)

Checklist de lanzamiento:

- [ ] Rodrigo tiene cuenta privada en workspace `selectahr`
- [ ] Puede cargar o definir criterio de búsqueda
- [ ] El sistema busca en fuentes permitidas
- [ ] Evita duplicados (memoria viva)
- [ ] Guarda candidatos en base reutilizable
- [ ] Muestra perfiles de forma anonimizada (blind review)
- [ ] Rodrigo revisa, aprueba, descarta o pide más información
- [ ] El sistema registra evidencia y decisión
- [ ] Rodrigo puede decir si los candidatos tienen sentido

---

## Arquitectura conceptual

```
Telegram / Mobile ──► Cuenta privada (Rodrigo)
                           │
                    ┌──────┴──────────┐
                    │  Orchestrator    │
                    │  (pipeline de    │
                    │   autoridad)     │
                    └──────┬──────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
   Intake Agent    Sourcing Agent     Memory Agent
   Criteria Agent  Evidence Agent     Review Agent
                   Scoring Agent      Blind Review
                           │
                    ┌──────┴──────────┐
                    │  Talent Pool    │
                    │  (SQLite viva)  │
                    └─────────────────┘
                           │
         ┌─────────────────┼─────────────────┐
         ▼                 ▼                  ▼
  Browser Agent     Remote Operator    API / MCP
  (Playwright/MCP)  (modo supervisado) (integraciones)
                           │
                    ┌──────┴──────────┐
                    │   VPS / 24/7   │
                    │  (residencia)   │
                    └─────────────────┘
```

---

## Principios rectores

1. **Pipeline secuencial en autoridad. Ejecución paralela en volumen.**
2. **El agente puede navegar, pero no puede decidir solo.**
3. **La app nunca obedece texto externo. Solo observa, sanitiza y somete a reglas de confianza.**
4. **Una búsqueda no crea candidatos duplicados. Crea matches contra talentos existentes.**
5. **Remote control no significa libertad total. Significa operación supervisada sobre entorno controlado.**
6. **Un agente operativo no debería depender de que tu laptop esté prendida.**
7. **El objetivo no es tener muchos scrapers. Es tener conectores confiables.**
8. **La API es el contrato del producto. MCP es una capa para agentes.**
