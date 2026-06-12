# Prompts Base — Talo

Este archivo junta prompts reutilizables para correr skills y comparar respuestas entre modelos.

La regla es simple:

- mismo prompt
- mismo contexto
- mismo objetivo

Solo así la comparación entre skills o modelos sirve.

---

## 1. Diagnóstico De UX

Usar con:
- `abogado-del-diablo`
- `frontend-ui-engineering`
- modelos de OpenCode

```text
Analiza Talo como producto de reclutamiento asistido. Evalúa la experiencia actual de landing, setup, blind, pool, coverage y candidate profile.

Quiero que respondas:
1. Qué no se entiende rápido
2. Qué rompe confianza
3. Qué pasos sobran
4. Qué información falta para decidir
5. Qué partes parecen consola interna en vez de producto claro

No quiero halagos. Quiero fallas concretas y mejoras accionables.
```

---

## 2. Simplificación De Flujo

Usar con:
- `brainstorming`
- `frontend-ui-engineering`

```text
Propón una versión más simple del flujo de Talo.

Objetivo:
- menos pasos
- más claridad
- onboarding más fuerte
- mejor conexión entre coverage, pool, blind y candidate profile

No diseñes por estética primero. Diseña por comprensión y confianza del usuario.
Devuelve:
1. flujo ideal
2. pantallas necesarias
3. pantallas redundantes
4. cambios de navegación
```

---

## 3. Landing Y Posicionamiento

Usar con:
- `seo-analysis`
- `content-writer`

```text
Ayúdame a posicionar Talo.

Talo no quiere vender “más IA para reclutamiento”.
Quiere vender un sistema de búsqueda ejecutiva con:
- criterio explícito
- revisión ciega inicial
- trazabilidad de evidencia
- decisión humana defendible

Quiero:
1. categoría de producto
2. keywords principales
3. estructura de landing
4. promesa principal
5. diferenciales reales frente a una landing genérica de recruiting AI
```

---

## 4. Reescritura De Copy

Usar con:
- `content-writer`
- `humanizer`
- `humanizalo`

```text
Reescribe este copy para Talo.

Restricciones:
- no sonar genérico
- no sonar como “AI slop”
- no inflar promesas
- sonar claro, adulto y preciso
- vender control, criterio y trazabilidad

El resultado debe sentirse como producto serio, no como app mágica de IA.
```

---

## 5. Presentación De Candidatos

Usar con:
- `frontend-ui-engineering`
- `abogado-del-diablo`

```text
Rediseña la presentación de candidatos en Talo.

Problema actual:
- el usuario ve listas largas
- no entiende por qué alguien quedó dentro o fuera
- blind review puede sentirse como falta de información
- coverage explica números pero no expone bien la lógica

Quiero una propuesta donde:
1. el usuario vea motivo, no solo identidad
2. pueda auditar descartes
3. el proceso tenga continuidad visible
4. el blind no se sienta arbitrario
```

---

## 6. Landing Para Ads

Usar con:
- `ads-landing`
- `ads-audit`
- `google-ads-landing`
- `meta-ads-audit`

```text
Evalúa si esta landing de Talo sirve para tráfico pago.

Necesito saber:
1. si el hero conecta con intención de compra
2. si la promesa es clara
3. si la página sostiene un clic de anuncio
4. qué objeciones no están resueltas
5. qué cambios aumentan conversion sin meter humo
```

---

## 7. Auditoría De Skill De Terceros

Usar con:
- `cyber-neo`
- `code-review-skill`

```text
Audita este skill de terceros antes de usarlo en Talo.

Quiero saber:
1. qué herramientas pide
2. si sus permisos son razonables
3. si hay riesgos de shell / filesystem / red
4. si intenta hacer demasiado para su propósito
5. si debería aprobarse, aprobarse con límites, o bloquearse

No quiero opinión superficial. Quiero riesgos concretos.
```

---

## 8. Prompt Para Registrar Auditoría En Verifiable Memory

Usar con:
- `verifiable-memory-mcp`

```text
Remember: Auditamos el skill [NOMBRE_SKILL] del repo [OWNER/REPO]. Herramientas permitidas: [LISTA]. Riesgos encontrados: [LISTA]. Decisión: [APROBADO / APROBADO_LIMITADO / BLOQUEADO]. Motivo: [RESUMEN]. Tags: skill-audit, [skill], [estado]
```

---

## 9. Prompt Para Comparar Modelos

Usar con:
- cualquier modelo de OpenCode

```text
Resuelve esta tarea con foco en utilidad real, no en verbosidad.
Si algo no está claro, dilo.
Si una promesa del producto no se sostiene, señálalo.
Devuelve una respuesta estructurada en:
1. diagnóstico
2. propuesta
3. riesgos
4. siguiente paso recomendado
```
