# Decision Log

## 2026-06-04 — Selecta público y flujo de perfil

### Decisión
Separar definitivamente Selecta público de Talo interno a nivel de experiencia, navegación y promesa de producto.

### Alcance
- `landing`
- `cargar-cv`

### Qué quedó decidido
- Selecta público ya no se presenta solo como carga de CV.
- La promesa visible pasa a ser **sumar perfil profesional**.
- El acceso interno a Talo se mantiene discreto en footer.
- Talo no comparte navegación mental con las páginas públicas.

### Implementado en Selecta público
- Header y footer unificados entre `landing` y `cargar-cv`.
- Lockup de marca actualizado a:
  - `HR`
  - `Selecta`
  - `Solutions`
- Reemplazo de `Sumá tu CV` por `Sumá tu perfil` en:
  - navegación
  - CTAs
  - footer

### Implementado en `cargar-cv`
- Nueva propuesta de valor:
  - **Subí tu CV o armá tu perfil profesional**
- Se definieron dos caminos visibles:
  1. `Ya tengo CV`
  2. `No tengo CV`

### Camino 1 — Ya tengo CV
- Se mantiene el upload de PDF/Word.
- El sistema sigue usando el endpoint de carga actual.
- El formulario mínimo pide:
  - nombre
  - email

### Camino 2 — No tengo CV
- Se agrega carga manual campo a campo.
- Primera versión mínima definida con estos campos:
  - nombre completo
  - email
  - LinkedIn o portfolio
  - ubicación o mercado
  - rol actual, área o tipo de perfil
  - años de experiencia
  - resumen breve

### Decisión de producto detrás del flujo manual
- No exigir un CV listo para entrar al ecosistema de Selecta.
- Permitir que perfiles en desarrollo también puedan sumar información útil.
- Empezar relación con talento que puede encajar hoy o más adelante.

### Decisión técnica
- El endpoint `POST /candidate/upload_cv` ahora acepta dos modos:
  - `upload`
  - `manual`
- El modo manual no requiere archivo obligatorio.
- Por ahora ambos caminos terminan en el mismo mensaje de éxito y mismo intake stub.

### Estado
- Implementado en frontend
- Implementado en endpoint stub
- Falta QA visual final en navegador
- Falta decidir si el modo manual pedirá más campos en una segunda iteración

### Siguiente decisión sugerida
- Cerrar QA final de Selecta público
- Dejar foco completo en Talo interno

