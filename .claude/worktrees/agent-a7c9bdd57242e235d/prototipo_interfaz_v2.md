# Prototipo de Interfaz v2 (Versión Oficial)
## Global Executive Agent System

---

## 0. Contexto de uso

Prototipo para presentación ejecutiva a socios y para validación operativa interna.

Esta versión busca mostrar:

1. Producto real y entendible por negocio.
2. Control humano del flujo de agentes.
3. Métricas comerciales y de operación.
4. Módulo opcional de transición como valor agregado.

> Nota: los números mostrados en pantallas son **datos simulados** para demo.

---

## 1. Panel Orquestador (Vista principal)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│  GE Agent System — Panel Orquestador                          [Manu] 18:30 │
│  Modo: [● DEMO] [○ PRODUCCIÓN]     País foco: [México ▼]     Semana: 20    │
├─────────────────────────────────────────────────────────────────────────────┤
│ KPI Ejecutivo Mensual                                                       │
│ ┌──────────────┬──────────────┬───────────────┬──────────────┬────────────┐│
│ │ Oportunidades│ Shortlists   │ Reuniones      │ Cierres       │ TTS*        ││
│ │ detectadas   │ enviadas     │ comerciales     │ estimados     │ 4.8 días    ││
│ │ 42           │ 18           │ 14              │ 3             │             ││
│ └──────────────┴──────────────┴───────────────┴──────────────┴────────────┘│
│ *TTS = Time to Shortlist                                                    │
│                                                                             │
│ Estado de Agentes                                                           │
│ Demand Radar: ✅ 08:30 | Talent Sourcing: ✅ 09:15 | Outreach: ⏳ 2 revisión │
│ Fit Scoring: ✅ 10:00 | Knowledge: ✅ 08:00 | Delivery QA: ✅ 11:30         │
│                                                                             │
│ Estado por País                                                             │
│ MX: 🟢 SLA 92%  |  CL: 🟡 SLA 78%  |  AR: 🟢 SLA 89%                         │
│                                                                             │
│ Alertas de Gestión                                                          │
│ - Equipo MX: 2 llegadas tardías registradas esta semana                    │
│ - 1 vacante crítica sin actualización en 48h                               │
│ - 2 InMails pendientes de aprobación                                        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 2. Bandeja de Aprobaciones

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Pendientes de Aprobación                                       [Ver todas]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Outreach propone 2 InMails                                                  │
│                                                                             │
│ ▸ Carlos Méndez — CEO, TechMex                                             │
│   Puntaje: 92/100 · Fuente: Demand Radar                                   │
│   [Editar] [Aprobar] [Rechazar]                                             │
│                                                                             │
│ ▸ Ana López — Directora HR, FinTechMX                                      │
│   Puntaje: 87/100 · Fuente: Talent Sourcing                                │
│   [Editar] [Aprobar] [Rechazar]                                             │
│                                                                             │
│                                                  [Aprobar todo]             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 3. Vista Detalle de Agente

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Agente Outreach                                                [← Volver]   │
├─────────────────────────────────────────────────────────────────────────────┤
│ Estado: Activo en espera | Última acción: 11:30                            │
│ Criterio de tono: Profesional consultivo                                   │
│                                                                             │
│ Acciones del día                                                            │
│ ⏳ Pendiente  | InMail a Carlos Méndez                            [Editar]  │
│ ⏳ Pendiente  | InMail a Ana López                                [Editar]  │
│ ✅ Enviado    | Seguimiento a Pedro Gómez                          [Ver]     │
│ ❌ Rechazado  | InMail a Laura Torres (tono demasiado directo)    [Ver]     │
│                                                                             │
│ Métricas semanales                                                          │
│ Enviados: 12 | Pendientes: 2 | Rechazados: 1 | Tasa aprobación: 92%        │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 4. Carpetas Ejecutivas

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Carpetas Ejecutivas                                            [Dashboard]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Cuenta: TechMex                                                             │
│ ├─ 01_Mercado                     (actualizado: hoy)                        │
│ ├─ 02_Oportunidades               (actualizado: hoy)                        │
│ ├─ 03_Candidatos                  (actualizado: ayer)                       │
│ ├─ 04_Contactos_y_Seguimiento     (actualizado: hoy)                        │
│ ├─ 05_Insights_Semanales          (actualizado: viernes)                    │
│ └─ 06_Riesgos_y_Bloqueos          (actualizado: martes)                     │
│                                                                             │
│ [+ Nueva Cuenta]                                                            │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 5. Módulo de Transición (Opcional)

```text
┌─────────────────────────────────────────────────────────────────────────────┐
│ Transition Support (Opcional)                                  [Activado]  │
├─────────────────────────────────────────────────────────────────────────────┤
│ Empresa cliente: NovaLog                                                     │
│ Escenario: Reemplazo + crecimiento de equipo                                 │
│                                                                             │
│ Riesgo de transición actual: 🟡 Medio                                        │
│                                                                             │
│ Handover Assistant                                                           │
│ - Tareas críticas documentadas: 18/24                                       │
│ - Contactos clave traspasados: 7/9                                          │
│                                                                             │
│ Team Load Assistant                                                          │
│ - Sobrecarga estimada del equipo receptor: +22%                             │
│ - Recomendación: redistribuir 3 tareas por 3 semanas                        │
│                                                                             │
│ Onboarding Assistant                                                         │
│ - Plan 30-60-90: ✅ cargado                                                  │
│ - Hitos semana 1: 5/7 cumplidos                                             │
│                                                                             │
│ Integration Pulse Assistant                                                  │
│ - Señal: baja claridad de prioridades en célula comercial                   │
│ - Acción sugerida: reunión de 20 min + checklist semanal                    │
└─────────────────────────────────────────────────────────────────────────────┘
```

Problemas que resuelve:

1. Reduce el desorden en cambios de personal.
2. Reduce la sobrecarga del equipo que absorbe trabajo.
3. Acelera la integración productiva del nuevo talento.

---

## 6. Flujo semanal y gobernanza

```text
Lunes AM   -> Investigación (Radar + Sourcing)
Lunes PM   -> Scoring + borradores de Outreach
Lunes 18:00-> Revisión humana obligatoria
Lunes 19:00-> Ejecución de acciones aprobadas
Mar-Jue    -> Seguimiento + investigación ligera
Viernes    -> Cierre semanal + reporte ejecutivo
```

Reglas:

1. Ningún mensaje externo sale sin aprobación humana en fase inicial.
2. Toda decisión queda en bitácora exportable.
3. Cambios de criterio quedan versionados por fecha y responsable.

---

## 7. Bitácora y auditoría

```text
13/05 18:04 | Manu   | Aprobó InMail a Carlos Méndez | Score 92 | Enviado
13/05 18:06 | Manu   | Rechazó InMail a Laura Torres | Motivo: tono directo
13/05 18:10 | Manu   | Ajustó tono Outreach: +diplomático
13/05 18:20 | Sistema| Alerta tardanza equipo MX (2 eventos)
13/05 18:25 | Manu   | Solicitó seguimiento supervisor local
```

---

## 8. Modo Demo vs Modo Producción

### Modo Demo

1. Datos simulados.
2. Flujo completo sin impacto externo.
3. Uso principal: reunión de socios.

### Modo Producción

1. Cuentas y procesos reales.
2. Trazabilidad y SLA por país/cuenta.
3. Permisos y gobernanza activos.

---

## 9. Próximas iteraciones

1. Interfaz web clickeable.
2. Vista móvil de seguimiento para dirección.
3. Panel financiero por pipeline.
4. Notificaciones en tiempo real.
5. Plantillas por industria.

---

*Versión oficial consolidada para presentación ejecutiva*
