# Playbook — Skills Para Talo

## Objetivo

Este documento define:

1. qué skill usar
2. para qué usarlo
3. en qué orden usarlo
4. qué output esperamos
5. cómo convertir ese proceso en material grabable
6. cómo repetir el mismo experimento luego con modelos de OpenCode

La meta no es "usar muchos skills". La meta es que Talo comunique mejor, tenga un flujo más claro y que el proceso quede documentado para iteración y contenido.

---

## Principio Operativo

Cada skill cumple uno de estos roles:

- diagnóstico
- ideación
- diseño / UX
- copy / SEO
- adquisición
- QA / seguridad
- aprendizaje

Si mezclamos roles en la misma sesión, el proceso se ensucia. La disciplina correcta es:

1. criticar
2. definir hipótesis
3. diseñar
4. escribir
5. validar
6. guardar aprendizaje

Además:

7. registrar auditoría verificable

Ese último paso vive en `verifiable-memory-mcp`.

No sirve para "detectar bugs" por sí mismo.
Sí sirve para dejar una bitácora append-only de:

- qué skill auditamos
- qué repo instalamos
- qué riesgos encontramos
- qué decidimos aprobar o bloquear
- qué modelo produjo qué resultado

Eso evita que después el proceso quede ambiguo o editable a conveniencia.

---

## Orden Recomendado

### Fase 1 — Diagnóstico duro

#### `abogado-del-diablo`

Para qué:
- destruir la experiencia actual
- detectar fricción, promesas falsas, pasos redundantes
- encontrar puntos donde el usuario pierde confianza

Cuándo usarlo:
- antes de rediseñar
- antes de grabar una demo
- cuando una idea "suena bien" pero no convence

Prompt tipo:

```text
Critica Talo sin piedad. Evaluá la experiencia actual de landing, setup, blind, pool, coverage y candidate profile. Quiero saber qué no se entiende, qué rompe confianza y qué haría que un usuario abandone.
```

Output esperado:
- lista de fallas
- riesgos de UX
- riesgos de producto
- contradicciones entre promesa y realidad

---

### Fase 2 — Abrir caminos de solución

#### `brainstorming`

Para qué:
- abrir 3 a 5 rutas de solución
- no casarnos con la primera idea
- generar variantes de navegación, posicionamiento y estructura

Cuándo usarlo:
- después de la crítica
- antes de tocar código

Prompt tipo:

```text
Propón 5 maneras distintas de simplificar Talo para que un usuario entienda rápido qué hace, cómo revisar candidatos y cómo auditar decisiones.
```

Output esperado:
- enfoques distintos de UX
- propuestas de arquitectura de pantallas
- opciones de positioning

#### `gstack`

Para qué:
- bajar ideas a un sistema más ordenado
- pensar dependencias, secuencia y tradeoffs

Cuándo usarlo:
- cuando ya hay varias rutas posibles

Output esperado:
- una dirección más consistente
- decisiones con mayor rigor operativo

---

### Fase 3 — Rediseño de UX y flujo

#### `frontend-ui-engineering`

Para qué:
- simplificar pantallas
- ordenar jerarquía visual
- mejorar onboarding
- mejorar pool, coverage, blind y candidate profile

Cuándo usarlo:
- cuando ya sabemos qué problema resolvemos
- antes de rehacer copy fino

Foco para Talo:
- menos pasos
- onboarding del primer uso
- explicar el proceso
- mejores estados vacíos
- vistas que transmitan control

Prompt tipo:

```text
Reestructura Talo como una experiencia más clara. Quiero menos pasos, mejor onboarding, una lógica visible entre setup, coverage, pool y candidate profile, y vistas que expliquen por qué un candidato quedó dentro o fuera.
```

Output esperado:
- propuestas de estructura
- cambios de layout
- componentes prioritarios
- plan de implementación

#### `abogado-del-diablo` otra vez

Para qué:
- atacar el rediseño propuesto

Uso:
- después de cualquier propuesta nueva

Regla:
- si la propuesta no sobrevive una segunda crítica, todavía no está lista

---

### Fase 4 — Posicionamiento, landing y copy

#### `seo-analysis`

Para qué:
- decidir cómo posicionar Talo
- definir categoría, keywords e intención de búsqueda

Cuándo usarlo:
- cuando ya sabemos qué producto estamos vendiendo

Preguntas clave:
- ¿Talo es "talent intelligence"?
- ¿o es "executive search workflow with blind review and traceability"?
- ¿qué busca alguien que tendría este problema?

Output esperado:
- keywords prioritarias
- estructura de landing
- ángulos de posicionamiento

#### `content-writer`

Para qué:
- escribir hero, subtítulos, secciones, FAQs, claims y CTA

Cuándo usarlo:
- después del análisis SEO

Output esperado:
- copy base de landing
- copy de onboarding
- copy de empty states

#### `humanizer`

Para qué:
- quitar tono robótico
- bajar el olor a texto genérico

Uso:
- después del primer draft

#### `humanizalo`

Para qué:
- refinar todavía más el tono
- forzar voz más humana, menos inflada

Uso:
- cuando queramos una versión más apta para contenido o grabación

Regla práctica:
- `content-writer` genera
- `humanizer` limpia
- `humanizalo` da una última pasada de estilo

#### `meta-tags-optimizer`

Para qué:
- title
- description
- Open Graph
- snippets

Uso:
- cuando el copy ya está estable

#### `schema-markup-generator`

Para qué:
- generar structured data de la landing

Uso:
- al final del proceso SEO

---

### Fase 5 — Ads y distribución

#### `ads-landing`

Para qué:
- revisar si la landing soporta tráfico pago
- detectar dónde se cae la conversión

Uso:
- después del rediseño de landing

#### `ads-audit`

Para qué:
- revisar promesas de anuncio
- traducir la propuesta de valor a canales pagos

Uso:
- antes de lanzar campañas

#### `google-ads-copy`

Para qué:
- headlines y descriptions para search

#### `google-ads-landing`

Para qué:
- adaptar landing al tráfico de Google Ads

#### `meta-ads-audit`

Para qué:
- evaluar promesa, hook y legibilidad para Meta

Regla:
- no escribir ads antes de tener una tesis clara de producto

---

### Fase 6 — QA, seguridad y cierre

#### `code-review-skill`

Para qué:
- revisar regresiones reales
- detectar fallas funcionales

#### `code-review-and-quality`

Para qué:
- elevar calidad general
- revisar deuda visible

#### `verification-before-completion`

Para qué:
- obligarnos a no decir "ya quedó" sin evidencia

Uso:
- siempre antes de cerrar una iteración

#### `cyber-neo`

Para qué:
- revisión de seguridad
- detectar exposición innecesaria si Talo se publica o se muestra con datos reales

Uso:
- antes de deploy o demo sensible

#### `verifiable-memory-mcp`

Para qué:
- registrar hallazgos de auditoría
- dejar constancia de decisiones
- verificar que el registro no fue adulterado

Qué sí hace:
- `remember`: guarda una decisión o hallazgo
- `recall`: recupera auditorías previas
- `verify`: comprueba integridad de una entrada
- `chain`: comprueba integridad de la cadena completa
- `timeline`: deja ver el historial cronológico

Qué no hace:
- no encuentra bugs automáticamente
- no reemplaza `cyber-neo`
- no reemplaza code review

Uso correcto:
1. auditar el skill con review / seguridad
2. registrar resultado en `verifiable-memory-mcp`
3. verificar cadena antes de confiar en el historial

Ejemplo de uso:

```text
Remember: Auditamos el skill humanizalo del repo Hainrixz/humanizalo. Riesgos: ninguno crítico encontrado en revisión inicial. Estado: aprobado para copy, no aprobado para tocar código. Tags: skill-audit, humanizalo, approved-copy-only
```

```text
Chain
```

```text
Verify mem_xxxxxxxx
```

---

### Fase 7 — Aprendizaje operativo

#### `aprende`

Para qué:
- guardar aprendizajes del proceso
- registrar qué funcionó y qué no

#### `learn`

Para qué:
- versión más enfocada a reflexión / documentación de errores

Uso:
- al final de cada sprint o bloque grande

Output esperado:
- lecciones reusables
- errores a no repetir
- prompts que sí funcionaron

---

## Qué No Usar De Entrada

### `caveman`

Útil para:
- ahorrar tokens
- respuestas más secas

No útil para:
- copy
- ideación rica
- exploración de UX

### `all-deploy`

Útil para:
- publicar una vez que el producto esté sólido

No usar:
- antes de ordenar el flujo

### `the-architect`

Útil para:
- diseñar un sistema nuevo desde cero

No prioritario para:
- iterar Talo en su estado actual

---

## Flujo Recomendado Para Talo

### Sprint 1 — Claridad de producto

Objetivo:
- entender por qué Talo no comunica bien
- ordenar el journey

Secuencia:
1. `abogado-del-diablo`
2. `brainstorming`
3. `frontend-ui-engineering`
4. `abogado-del-diablo`
5. `code-review-skill`

Output:
- nueva arquitectura de experiencia
- lista de pasos redundantes
- mapa del flujo ideal

### Sprint 2 — Landing y narrativa

Objetivo:
- rehacer landing
- rehacer onboarding
- hacer explícito el diferencial

Secuencia:
1. `seo-analysis`
2. `content-writer`
3. `humanizer`
4. `humanizalo`
5. `meta-tags-optimizer`
6. `schema-markup-generator`

Output:
- landing nueva
- copy más claro
- metadata lista

### Sprint 3 — Distribución y contenido

Objetivo:
- preparar Talo para anuncios y videos

Secuencia:
1. `ads-landing`
2. `ads-audit`
3. `google-ads-copy`
4. `meta-ads-audit`
5. `verification-before-completion`

Output:
- hooks
- promesas válidas
- ángulos para campañas y contenido

### Sprint 4 — Seguridad y memoria

Objetivo:
- endurecer antes de exponer
- registrar aprendizajes

Secuencia:
1. `cyber-neo`
2. `code-review-and-quality`
3. `verifiable-memory-mcp`
4. `aprende`
5. `learn`

---

## Protocolo De Auditoría De Skills De Terceros

Antes de usar cualquier skill de terceros en Talo:

1. revisar `SKILL.md`
2. revisar herramientas permitidas
3. revisar si escribe archivos, ejecuta shell o usa red
4. correr revisión con `cyber-neo`
5. correr revisión con `code-review-skill`
6. registrar hallazgo en `verifiable-memory-mcp`
7. marcar estado:

- aprobado
- aprobado solo para texto
- aprobado solo para análisis
- bloqueado

### Criterios de bloqueo

- pide herramientas más amplias de lo razonable
- ejecuta comandos peligrosos sin control
- modifica archivos fuera de su alcance esperado
- mezcla prompts vagos con permisos altos
- intenta ocultar o saltarse validaciones

### Criterios de aprobación limitada

- sirve para copy pero no para tocar código
- sirve para análisis pero no para escritura
- sirve para brainstorming pero no para decisiones finales

---

## Cómo Probar Esto Con Modelos De OpenCode

La idea correcta es usar este mismo playbook como harness.

### Estructura recomendada

Para cada skill/modelo:

1. mismo objetivo
2. mismo contexto
3. mismo prompt inicial
4. mismo criterio de evaluación

### Template de experimento

```text
Modelo:
Skill:
Objetivo:
Input:
Output:
Tiempo:
Tokens:
Calidad percibida:
Utilidad real:
¿Lo volveríamos a usar?:
```

### Qué comparar

- claridad
- profundidad
- foco en UX
- si inventa o no
- si propone acciones útiles
- si produce output reutilizable
- costo / tokens

### Criterio de aptitud

Un skill/modelo es apto si:

- entiende el problema sin demasiada guía
- no se va por las ramas
- produce algo accionable
- no rompe el contexto del producto
- mejora una decisión real

No es apto si:

- habla mucho y resuelve poco
- produce copy genérico
- da feedback superficial
- inventa capacidades del producto

---

## Cómo Convertir Esto En Contenido Grabable

La clave no es grabar "todo". La clave es grabar con estructura.

### Formato recomendado

1. problema
2. skill que vamos a probar
3. prompt que le damos
4. respuesta
5. análisis crítico
6. decisión: sirve / no sirve

### Guión de episodio

```text
Hoy voy a usar [skill] para mejorar [parte de Talo].
Este es el problema actual.
Este es el prompt exacto.
Esta fue la respuesta.
Esto fue útil.
Esto fue humo.
Esto sí lo implementaría.
Esto no lo usaría.
```

### Buenos temas para grabar

- "Probé 5 skills para arreglar la landing de mi startup"
- "Usé un devil's advocate agent para destruir mi UX"
- "Qué tan buenos son los skills de SEO para una startup real"
- "Le pedí a varios agentes que arreglen el onboarding de Talo"
- "Qué skills realmente sirven y cuáles son puro hype"

### Regla editorial

Siempre mostrar:

- el problema real
- el prompt real
- la respuesta real
- tu criterio

No vender magia. Mostrar proceso.

---

## Chat Seguro y Reproducible

Si querés conservar este chat "sano y salvo", la forma práctica no es depender solo del historial del chat.

Conviene guardar:

1. este playbook
2. los prompts que funcionen
3. un registro por experimento

Sugerencia de archivos futuros:

- `docs/PLAYBOOK_TALO_SKILLS.md`
- `docs/PROMPTS_TALO.md`
- `docs/EXPERIMENTOS_MODELOS.md`
- `docs/GRABACION_TALO.md`

---

## Siguiente Paso Recomendado

Empezar con este bloque:

1. `abogado-del-diablo`
2. `frontend-ui-engineering`
3. `seo-analysis`

Eso nos da:

- crítica real del producto
- propuesta de flujo
- dirección de landing

Después de eso:

- reescribimos Talo
- lo probamos con otros modelos
- documentamos cuáles skills de verdad merecen quedarse
