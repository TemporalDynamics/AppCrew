# SelectaHR Solutions — Landing + CV Upload Design

## Arquitectura

```
selectahrsolutions.com
  ├── /              → Landing firma de búsqueda ejecutiva
  ├── /cargar-cv     → CV upload + CV analyst

talo.selectahrsolutions.com
  └── Sistema de agentes Talo (subdominio controlado por el usuario)
      → Si el cliente quiere dominio propio: paga
```

## Landing pública — secciones

1. **Hero** — posicionamiento de SelectaHR como firma de búsqueda ejecutiva
2. **Cómo trabajamos** — metodología propia + tecnología (Talo como motor invisible, siempre adaptándose a nuevas tecnologías para mejores búsquedas)
3. **Señales / Resultados** — industrias, expertise, evidencia concreta
4. **CTA final** — contacto / demo

Sin testimonios, FAQ ni secciones infladas. Mínimo viable, focused.

## CV Upload — /cargar-cv

**Header link:** "Sumá tu CV"

**Flujo anónimo:**
1. Usuario llega a /cargar-cv, sube CV (drag-and-drop o file picker)
2. Sistema extrae campos automáticamente
3. Si faltan campos → chat conversacional: "Falta tu experiencia en liderazgo. ¿Cuántos años tenés?"
4. CV guardado en base de SelectaHR (incluso sin registro)
5. Feedback estructurado: checklist con lo que tiene y lo que falta
6. Toast de invitación: "Tu CV tiene buen score. Registrate para que sea considerado en nuestras búsquedas."

**Flujo registrado:**
- Mismas secciones que el anónimo
- Además: botón "Solicitar recomendaciones" → IA generativa con sugerencias personalizadas
- Toast NO se muestra (ya está registrado)

## CV Analyst

- **Sin cuenta:** feedback estructurado (checklist)
- **Con cuenta:** feedback estructurado + botón "Solicitar recomendaciones" → recomendaciones generativas solo si el usuario hace clic explícito
- Híbrido: sin cuenta ves qué falta, con cuenta accedés a recomendaciones profundas

## Dominio

- selectahrsolutions.com → landing + CV upload
- talo.selectahrsolutions.com → sistema de agentes (control del usuario)
- Si cliente quiere integración en su dominio → paga
