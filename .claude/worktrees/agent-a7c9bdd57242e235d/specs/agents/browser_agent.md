# BrowserAgent — Spec

## Propósito

`BrowserAgent` es un agente de solo lectura que navega páginas públicas para extraer evidencia adicional sobre candidatos ya identificados por otros agentes (por ejemplo, `TalentSourcingAgent`). No busca candidatos por sí solo; recibe una URL y devuelve señales estructuradas.

## Estado actual

Stub. El método `work()` imprime un aviso y retorna lista vacía. El sandbox de browser no está activo todavía.

## Allowed domains

El agente solo puede acceder a dominios en `ALLOWED_DOMAINS`:

- `torre.co`
- `getonbrd.com`
- `computrabajo.com` / `computrabajo.com.mx`
- `linkedin.com`
- `glassdoor.com`
- `crunchbase.com`
- `angel.co`

Cualquier URL fuera de esta lista es rechazada por `_validate_url()` antes de hacer cualquier request.

## Blocked actions

- Login o autenticación en plataformas externas
- POST, submit o escritura en sistemas externos
- Acceso a perfiles privados o cerrados
- Acceso a dominios fuera del allowlist
- Almacenamiento de datos sensibles (biométricos, salud, credenciales)

## Cómo expandir el allowlist

1. Agregar el dominio base (sin `www.`) al frozenset `ALLOWED_DOMAINS` en `agents/browser_agent.py`.
2. Verificar que el dominio es una fuente pública de perfiles profesionales.
3. Agregar un test en `tests/` que valide `_validate_url` con el nuevo dominio.
4. Documentar la fuente en `docs/` con justificación de uso.

## Cuándo activar

El agente se activa cuando:

1. Existe un sandbox de browser seguro (Playwright/Firecrawl) disponible en el entorno.
2. Se implementa el método `work()` con lógica real de scraping.
3. Se verifica que el rate limiting y el manejo de errores HTTP están en su lugar.

Hasta entonces, el stub es seguro de registrar en el orquestador sin efectos secundarios.
