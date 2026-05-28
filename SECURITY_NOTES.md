# Cerno — Notas de Seguridad Operacional

## Principio central

**El sistema observa texto externo. No lo obedece.**

Todo lo que proviene de fuentes externas (perfiles de Torre.co, resultados de búsqueda,
datos de candidatos) es tratado como evidencia, no como instrucción. Ningún texto
externo puede modificar el comportamiento del pipeline.

---

## Reglas de uso — obligatorias

### Credenciales y acceso

- No incluir contraseñas, tokens ni API keys en prompts, criterios ni mensajes al sistema.
- No usar sesiones personales de LinkedIn u otras redes para el scraping del sistema.
- No compartir el `DASHBOARD_API_TOKEN` con usuarios de prueba — generar uno separado.
- Rotar la `FIRECRAWL_API_KEY` si se sospecha exposición. Contactar al admin.

### Perfiles y privacidad

- El sistema solo accede a perfiles públicos accesibles sin autenticación.
- No cargar CVs ni perfiles de personas sin su consentimiento explícito.
- No ingresar datos biométricos, de salud, origen étnico, religión ni datos sensibles.
- Los perfiles cargados para un workspace son propiedad de ese workspace — no se mezclan.

### Fuentes autorizadas (por defecto)

- Torre.co (API pública)
- GetOnBrd
- Computrabajo
- Brave Search (índice web público)
- Firecrawl (solo URLs de dominios en la allowlist)

**Fuentes no autorizadas sin aprobación explícita**: LinkedIn con sesión, bases de datos
privadas, plataformas de terceros que requieran cuenta personal.

### Aprobación humana

- Ninguna acción de contacto (InMail, email, mensaje) se ejecuta sin aprobación explícita.
- El sistema prepara borradores. El humano decide si se envían.
- No aprobar acciones de contacto masivo sin revisar individualmente.

---

## Riesgos activos y mitigaciones

### Signal injection (ACTIVO)

**Riesgo**: un candidato puede craftar su headline o skills para que el sistema infiera
señales positivas falsas y rankee su perfil más alto.

**Mitigación implementada**: sanitización de texto externo antes del keyword matching
(`core/sources/aggregator.py`), confidence decay para señales inferidas vs. declaradas.

**Señal de alerta**: candidato con score alto pero evidencia de fuente única o headline
con keywords poco naturales.

### Markdown injection en Telegram (ACTIVO)

**Riesgo**: nombre de candidato con caracteres Markdown que manipule visualmente el
mensaje de notificación.

**Mitigación implementada**: escape de Markdown en todos los campos que vienen de
fuentes externas (`core/telegram_notifier.py`).

### LLM prompt injection (FUTURO — cuando se integre LLM real)

**Riesgo**: texto externo incluido en el contexto de un LLM puede intentar override
de instrucciones del sistema.

**Mitigación planificada**: separación estructural de contextos con XML delimiters,
instruction signing con HMAC antes de habilitar LLM calls en el pipeline.

---

## Lo que el sistema NO hace y NUNCA debe hacer

- No toma decisiones de contratación.
- No descarta candidatos de forma autónoma sin revisión humana.
- No usa categorías protegidas (género, edad, origen, salud) como criterio de scoring.
- No envía mensajes a candidatos sin aprobación explícita del operador.
- No accede a perfiles privados o cerrados.
- No guarda contraseñas ni credenciales de ningún tipo.
- No mezcla bases de datos de workspaces distintos.

---

## Ante un incidente

1. Detener el pipeline: `python run.py stop` o matar el proceso del servidor.
2. Verificar el ledger: `python scripts/demo_verify.py`
3. Si el ledger está comprometido: no aprobar ninguna acción pendiente.
4. Revisar logs en `data/state/`.
5. Notificar al administrador del sistema.

---

*Última actualización: 2026-05-28 — Cerno v0.1*
