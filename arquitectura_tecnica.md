# Arquitectura Técnica y Operativa — Global Executive Agent System

## 1. Principio rector

Sistema de agentes con supervisión humana obligatoria para acciones externas sensibles.

Objetivo: mejorar velocidad y cobertura sin perder control, trazabilidad ni criterio consultivo.

---

## 2. Modelo operativo

1. Los agentes investigan, organizan y proponen.
2. El orquestador humano valida y aprueba.
3. Solo se ejecutan acciones aprobadas.
4. Toda acción queda en bitácora auditable.

Estados de flujo:

`PENDIENTE_REVISION -> APROBADO -> EJECUTADO`  
`PENDIENTE_REVISION -> RECHAZADO`

---

## 3. Agentes Core

1. **Demand Radar Agent**: señales de demanda de talento y oportunidades comerciales.
2. **Talent Sourcing Agent**: búsqueda estructurada de candidatos.
3. **Fit Scoring Agent**: priorización con criterios explicables.
4. **Outreach Agent**: borradores de contacto y seguimiento.
5. **Knowledge Agent**: memoria operativa por cuenta.
6. **Delivery QA Agent**: control de calidad de entregables.

---

## 4. Stack sugerido (ajustable)

| Capa | Opción recomendada | Función |
|---|---|---|
| Interfaz | React/Next.js | Panel de operación y aprobación |
| Backend | FastAPI (Python) | Orquestación y reglas de negocio |
| Jobs | Redis + RQ/Celery | Tareas asíncronas |
| Almacenamiento | PostgreSQL/SQLite + Filesystem | Datos operativos y carpetas |
| Integraciones | APIs y conectores autorizados | Fuentes de mercado y CRM |

---

## 5. Fuentes y cumplimiento

Principios:

1. Priorizar fuentes con uso permitido y datos públicos.
2. Evitar estrategias de evasión de controles de plataformas.
3. Mantener cadencias de uso responsables y auditables.
4. Definir políticas de uso por plataforma antes de producción.

---

## 6. Gobierno de datos y seguridad

1. **Acceso por rol (RBAC)**: Socio, Orquestador, Recruiter, Viewer.
2. **Trazabilidad**: toda aprobación/rechazo y cambios de criterio quedan registrados.
3. **Retención**: política configurable (ej. 90/180 días por tipo de dato).
4. **Resguardo**: backups periódicos y control de restauración.
5. **Protección PII**: mínimo necesario, acceso restringido y exportación controlada.

---

## 7. Estructura de carpetas ejecutivas

```text
data/
  cuentas/
    {cuenta}/
      01_Mercado/
      02_Oportunidades/
      03_Candidatos/
      04_Contactos_y_Seguimiento/
      05_Insights_Semanales/
      06_Riesgos_y_Bloqueos/
  agentes/
    demand_radar/
    talent_sourcing/
    fit_scoring/
    outreach/
    knowledge/
    delivery_qa/
  config/
    criterios_scoring.yaml
    workflow_cadencia.yaml
    politicas_gobernanza.yaml
```

---

## 8. Cadencia semanal recomendada

1. **Lunes AM**: investigación (radar + sourcing).
2. **Lunes PM**: scoring + borradores outreach.
3. **Lunes 18:00**: revisión humana.
4. **Lunes 19:00**: ejecución de aprobados.
5. **Mar-Jue**: seguimiento y nueva investigación.
6. **Viernes**: cierre semanal y reporte ejecutivo.

---

## 9. KPIs operativos técnicos

1. Tiempo promedio de generación de shortlist.
2. Tasa de acciones aprobadas vs rechazadas.
3. Cumplimiento de SLA por país/cuenta.
4. Trazabilidad completa por acción.
5. Disponibilidad del sistema y tasa de errores.

---

## 10. Plan técnico por etapas

1. **MVP (0-30 días)**: dashboard, workflow de aprobación, 3 agentes base.
2. **Operación inicial (30-90 días)**: 6 agentes core, bitácora completa, KPIs.
3. **Escala (90+ días)**: módulos por industria, transición opcional, integraciones adicionales.

---

## 11. Criterio de éxito técnico

El sistema es exitoso cuando GE puede operar más procesos con el mismo equipo senior, con trazabilidad completa y sin degradar la calidad consultiva.

---

*Documento consolidado — versión final para presentación ejecutiva*
