# Experimentos — Skills y Modelos

Este documento sirve para comparar:

- skills distintos
- modelos distintos
- respuestas distintas al mismo problema

No sirve si cambiamos el prompt, el contexto y el objetivo al mismo tiempo.

---

## Regla Del Experimento

Cada prueba debe mantener fijos:

1. contexto
2. prompt
3. objetivo
4. criterio de evaluación

Lo único que debe cambiar es:

- skill
- modelo
- o ambos

---

## Plantilla Base

Copiar y pegar por experimento:

```md
## Experimento

- Fecha:
- Proyecto: Talo
- Objetivo:
- Pantalla / área:
- Skill:
- Modelo:
- Repo del skill:
- Estado del skill: aprobado / aprobado limitado / bloqueado

### Contexto dado

### Prompt usado

### Respuesta resumida

### Evaluación

- Claridad:
- Profundidad:
- Foco en UX:
- Foco en negocio:
- Utilidad real:
- Riesgo de humo:
- Riesgo técnico:
- Tokens / costo:

### Veredicto

- Lo usaría de nuevo:
- Para qué sí:
- Para qué no:
- Cambios antes de reutilizarlo:
```

---

## Matriz De Evaluación

Puntuar de 1 a 5:

### Calidad de respuesta

- 1 = superficial o inútil
- 3 = correcta pero parcial
- 5 = accionable y reusable

### Foco en UX

- 1 = habla generalidades
- 3 = detecta algunos problemas
- 5 = entiende fricción, confianza, continuidad y decisión

### Riesgo de humo

- 1 = casi no inventa
- 3 = mezcla cosas útiles con relleno
- 5 = vende humo fuerte

### Alineación con Talo

- 1 = genérico
- 3 = algo contextualizado
- 5 = entiende bien el producto y sus tensiones

---

## Pipeline De Prueba Recomendado

### Etapa 1 — Auditoría del skill

Antes de usar un skill:

1. revisar `SKILL.md`
2. correr `cyber-neo`
3. correr `code-review-skill`
4. registrar hallazgo en `verifiable-memory-mcp`

### Etapa 2 — Prueba funcional

1. correr el mismo prompt con el skill
2. correr el mismo prompt sin el skill
3. correr el mismo prompt en otro modelo
4. comparar outputs

### Etapa 3 — Decisión

Clasificar:

- aprobado
- aprobado solo para texto
- aprobado solo para análisis
- aprobado solo para research
- bloqueado

---

## Uso De Verifiable Memory En Los Experimentos

`verifiable-memory-mcp` no decide si un skill es bueno.

Lo que hace es dejar un historial verificable de:

- qué se probó
- con qué prompt
- con qué modelo
- qué resultado dio
- qué decisión tomamos

### Registro mínimo recomendado

```text
Remember: Probamos el skill [SKILL] con el modelo [MODELO] sobre la tarea [TAREA]. Resultado: [RESUMEN]. Decisión: [APROBADO / BLOQUEADO / LIMITADO]. Tags: experiment, [skill], [modelo], [estado]
```

### Verificación recomendada

Después de varias pruebas:

```text
Chain
```

Y si hace falta validar una entrada concreta:

```text
Verify mem_xxxxxxxx
```

---

## Primer Lote Recomendado Para Talo

### Lote A — Diagnóstico

- `abogado-del-diablo`
- `frontend-ui-engineering`
- sin skill

Objetivo:
- ver quién entiende mejor los problemas de flujo

### Lote B — Landing

- `seo-analysis`
- `content-writer`
- `humanizer`
- `humanizalo`

Objetivo:
- ver quién produce mejor copy

### Lote C — Distribución

- `ads-landing`
- `meta-ads-audit`
- `google-ads-landing`

Objetivo:
- ver quién conecta mejor producto con adquisición

---

## Qué Grabar

Cada experimento grabable debería mostrar:

1. problema real
2. prompt exacto
3. skill/modelo usado
4. respuesta
5. crítica tuya
6. veredicto

Eso convierte el experimento en contenido útil.

---

## Regla Editorial

Si un skill responde bonito pero no mejora una decisión real, no cuenta como bueno.

La métrica no es:

- “sonó inteligente”

La métrica es:

- “me ayudó a mejorar Talo”

---

## Experimento 1

- Fecha: 2026-06-03
- Proyecto: Talo
- Objetivo: evaluar si `humanizalo` mejora el copy inicial de la landing inspirada en SelectaHR sin volverlo genérico ni inflado
- Pantalla / área: landing
- Skill: `humanizalo`
- Modelo: OpenCode Zen / Big Pickle
- Repo del skill: `Hainrixz/humanizalo`
- Estado del skill: aprobado limitado

### Contexto dado

Se usó como texto base el primer copy de una landing demo montada en Talo con inspiración visual y verbal de SelectaHR. El objetivo era volver el mensaje más humano, más claro y más específico, sin sonar a brochure de consultora ni meter promesas vacías.

### Prompt usado

```text
Reescribe este copy para Talo.

Objetivo:
- sonar más humano
- sonar más claro
- no sonar genérico
- no sonar como texto inflado de agencia
- mantener tono profesional
- vender criterio, acompañamiento y mejores contrataciones
- conservar inspiración de SelectaHR, pero con mejor redacción

Restricciones:
- no usar clichés vacíos
- no prometer magia
- no meter “IA” si no ayuda
- evitar frases que suenen corporativas o frías
- escribir en español natural de negocio

Texto base:

Excelencia en recursos humanos

#FormandoEquiposConstruyendoFuturos

Conectamos talentos con oportunidades.

En SelectaHR Solutions encontramos la pieza clave para tu empresa. Con nuestro servicio de selección especializado optimizarás tu proceso de contratación y podrás concentrar tus esfuerzos en hacer crecer tu negocio.

Nosotros te ayudamos a encontrar mejor ajuste, más rápido y con menos desgaste.

Asegura contrataciones exitosas y construye un futuro sólido para tu empresa.

Devuélveme:
1. hero
2. subtítulo
3. bloque corto de valor
4. una versión más cálida
5. una versión más sobria
```

### Respuesta resumida

El modelo no cargó `humanizalo` como skill nativo de OpenCode. En cambio, leyó el contenido del skill desde `~/.codex/skills/humanizalo` y aplicó manualmente su metodología.

La respuesta produjo:

- un hero más filoso y menos genérico
- un subtítulo claro y usable
- un bloque de valor bastante mejor que el original
- dos variantes de tono
- una auditoría explícita de patrones de escritura artificial

La mejor idea rescatable del output fue:

- el problema no es encontrar candidatos, sino saber cuáles resisten criterio real
- primero revisar señales, después abrir nombres
- la decisión sigue siendo humana

### Evaluación

- Claridad: 4/5
- Profundidad: 4/5
- Foco en UX: 3/5
- Foco en negocio: 4/5
- Utilidad real: 4/5
- Riesgo de humo: 2/5
- Riesgo técnico: 3/5
- Tokens / costo: medio

### Veredicto

- Lo usaría de nuevo: sí
- Para qué sí: pulido de copy, detección de frases infladas, humanización de tono
- Para qué no: todavía no probado como skill operativo nativo dentro de OpenCode; tampoco probado fuera de tareas de escritura
- Cambios antes de reutilizarlo: configurar OpenCode para cargar skills desde `~/.codex/skills` o replicar esta prueba directamente en Codex para una validación más limpia

### Hallazgo principal

`humanizalo` quedó aprobado con límites:

- aprobado para copy
- no aprobado todavía como benchmark de integración de skills en OpenCode
- el experimento validó la metodología, no la integración nativa del skill
