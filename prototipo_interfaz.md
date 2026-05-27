# Prototipo de Interfaz v0.2 — Producto Vendible (Mobile-First)

> Diseñado para teléfono/tablet como uso principal.
> Presentación vía proyector/TV compartiendo pantalla.
> Aspecto de producto profesional, no de prototipo interno.

---

## Principios de Diseño

1. **Mobile-first** — orquestador revisa y apruepa desde el celular
2. **Escalable a pantalla grande** — dashboard se reacomoda limpiamente en TV/proyector
3. **Vendible** — se ve como producto terminado, no como herramienta casera
4. **Brandeable** — paleta, logo, nombre intercambiables por cliente
5. **Charming pero profesional** — agentes con personalidad sutil, no infantil

---

## 1. Login / Onboarding (primera impresión vendible)

```
┌──────────────────────┐
│                      │
│    ╔══════════╗      │
│    ║  GE      ║      │  ← Logo del cliente
│    ║  Agents  ║      │
│    ╚══════════╝      │
│                      │
│   Autonomous         │
│   Recruiting Desk    │
│                      │
│   ┌──────────────┐   │
│   │ manu@ge.com  │   │
│   └──────────────┘   │
│   ┌──────────────┐   │
│   │ ••••••••••   │   │
│   └──────────────┘   │
│                      │
│   [     Entrar     ] │
│                      │
│   ¿Primera vez?      │
│   Conectar LinkedIn → │
│                      │
└──────────────────────┘
```

---

## 2. Dashboard Principal (mobile — vista día)

```
┌──────────────────────┐
│ ←  LUN 18:30     📊 │
│                      │
│  Todos los agentes   │
│  listos. 2 pendientes│
│  de revisión.        │
│                      │
│ ── Estado ──         │
│                      │
│ 🛰️ Radar  🎯 Source │
│ ✅ 08:30  ✅ 09:15  │
│                      │
│ 📊 Fit    ✉️ Outreach│
│ ✅ 10:00  ⏳ 2 REV   │
│                      │
│ 🗂️ Know    ✅ QA     │
│ ✅ 08:00  ✅ 11:30  │
│                      │
│ ── Pendientes ──     │
│                      │
│ ┌──────────────────┐ │
│ │ ✉️ Outreach      │ │
│ │ 2 InMails listos │ │
│ │ para revisar     │ │
│ │                  │ │
│ │ Carlos Méndez    │ │
│ │   Score 92       │ │
│ │ Ana López        │ │
│ │   Score 87       │ │
│ │                  │ │
│ │ [   Revisar   ]  │ │
│ └──────────────────┘ │
│                      │
│ ┌──────────────────┐ │
│ │ 🛰️ Demand Radar  │ │
│ │ 3 oportunidades  │ │
│ │ nuevas detectadas│ │
│ │                  │ │
│ │ [   Ver más   ]  │ │
│ └──────────────────┘ │
│                      │
│  [  📋  Ver Semana  ]│
│                      │
└──────────────────────┘
```

---

## 3. Approval Detail (mobile — flujo de aprobación)

```
┌──────────────────────┐
│ ← Revisar InMail     │
│                      │
│ ┌──────────────────┐ │
│ │                  │ │
│ │ ✉️ Outreach      │ │
│ │ quiere enviar a: │ │
│ │ Carlos Méndez    │ │
│ │ CEO en TechMex   │ │
│ │ Score: 92        │ │
│ │                  │ │
│ └──────────────────┘ │
│                      │
│ ── Contexto ──       │
│ TechMex Serie B $12M │
│ Nuevo CTO en marzo   │
│                      │
│ ── Mensaje ──        │
│ ┌──────────────────┐ │
│ │ Hola Carlos,     │ │
│ │                  │ │
│ │ Vi que TechMex   │ │
│ │ está expandiendo │ │
│ │ con la Serie B.  │ │
│ │ En GE ayudamos a │ │
│ │ empresas en esa  │ │
│ │ etapa a encontrar│ │
│ │ talento clave... │ │
│ │                  │ │
│ │ ¿15 min la       │ │
│ │ semana que viene?│ │
│ │                  │ │
│ │ Saludos, Manu    │ │
│ └──────────────────┘ │
│                      │
│ [✏️ Editar]          │
│                      │
│ [❌ Rechazar]        │
│ [✅ Aprobar y Enviar]│
│                      │
└──────────────────────┘
```

---

## 4. Timeline Semanal (tablet / proyector)

```
┌──────────────────────────────────────────────────────────────────┐
│  Semana del 11 Mayo                                    [👤 Manu]│
├──────────────────────────────────────────────────────────────────┤
│                                                                  │
│  LUN 11     │  MAR 12     │  MIE 13     │  JUE 14    │  VIE 15  │
│  ─────────  │  ─────────  │  ─────────  │  ─────────  │  ─────  │
│  🔍Research │  🔍Research │  🔍Research │  🔍Research │  📊Cierre│
│  📝Borrador │  💬Propuesta│  💬Propuesta│  💬Propuesta│  📈Reporte│
│  ✅REVIEW   │             │             │             │          │
│             │             │             │             │          │
│  3 detect.  │  2 detect.  │  1 detect.  │  2 detect.  │  8 total │
│  2 pend. ✅ │  0 pend.    │  1 pend.    │  0 pend.    │  3 aprob │
│             │             │             │             │  1 rech   │
│                                                                  │
│  ── Próximos Pendientes ──                                       │
│  ┌────────────────────────────────────────────────────────────┐  │
│  │ ✉️  Carlos Méndez — TechMex          Score 92  [✅] [✏️] [❌]│  │
│  │ ✉️  Ana López — FinTechMX            Score 87  [✅] [✏️] [❌]│  │
│  │ 🛰️  SoftCloud — contratando 5 devs  — ver oportunidad      │  │
│  └────────────────────────────────────────────────────────────┘  │
│                                                                  │
└──────────────────────────────────────────────────────────────────┘
```

---

## 5. Vista Proyector / TV (presentación a clientes)

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                      GE Autonomous Recruiting Desk                          │
│                                                                             │
│                    [          Hoy en vivo — LUN 11 Mayo          ]          │
│                                                                             │
│  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐  ┌──────────┐     │
│  │   🛰️    │  │   🎯    │  │   📊    │  │   ✉️    │  │   🗂️    │     │
│  │  Radar  │  │ Sourcing │  │  Fit     │  │ Outreach │  │ Knowledge│     │
│  │  ✅ 8:30│  │  ✅ 9:15 │  │  ✅ 10:00│  │  ⏳ 2/2  │  │  ✅ 8:00 │     │
│  │  3 opps │  │  8 perf. │  │  8 scored│  │ pend.    │  │  4 ctas  │     │
│  └──────────┘  └──────────┘  └──────────┘  └──────────┘  └──────────┘     │
│                                                                             │
│  ─── Flujo de la Semana ─────────────────────────────────────              │
│                                                                             │
│  LUN 🟢  MAR 🟡  MIE 🟡  JUE 🟡  VIE 🔵                                 │
│  ●●●●●  ●●●○○  ●●●●○  ●●●○○  ●●●●●                                      │
│  Done    Prog.  Prog.  Prog.  Cierre                                      │
│                                                                             │
│  ─── Resultados a la Fecha ───                                             │
│                                                                             │
│  Oportunidades detectadas:  12                     │                        │
│  InMails enviados:          10                     │                        │
│  Tasa de respuesta:         60%                    │                        │
│  Candidatos en pipeline:    24                     │                        │
│                                                                             │
│  ─── Próxima Revisión: HOY 18:30 ───                                      │
│  [2 InMails pendientes de aprobación]                                      │
│                                                                             │
└─────────────────────────────────────────────────────────────────────────────┘
```

---

## 6. Configuración (brandeable por cliente)

```
┌──────────────────────┐
│ ← ⚙️ Configuración  │
│                      │
│ ── Identidad ──      │
│                      │
│ Nombre del sistema   │
│ [GE Recruiting Desk] │
│                      │
│ Logo                 │
│ [Upload image]       │
│                      │
│ Color primario       │
│ [■ #1a365d]          │
│                      │
│ ── Agentes Activos ──│
│                      │
│ 🛰️ Demand Radar  [📴]│
│ 🎯 Sourcing      [📴]│
│ 📊 Fit Scoring   [📴]│
│ ✉️ Outreach      [📴]│
│ 🗂️ Knowledge     [📴]│
│ ✅ QA            [📴]│
│                      │
│ ── Cadencia ──       │
│                      │
│ Días:  [L][M][X][J][V] [S] [D]│
│                      │
│ Review hora: [18:00] │
│                      │
│ ── Permisos ──       │
│                      │
│ InMails → aprobar   │
│ Emails → aprobar    │
│ Connection Req → automático│
│                      │
└──────────────────────┘
```

---

## Resumen de Pantallas para Implementar

| # | Pantalla | Prioridad | Dispositivo |
|---|---|---|---|
| 1 | Login / LinkedIn Connect | Alta | Mobile + Desktop |
| 2 | Dashboard Principal | Alta | Mobile-first |
| 3 | Approval Detail | Alta | Mobile-first |
| 4 | Timeline Semanal | Media | Tablet / Desktop |
| 5 | Vista Proyector (presentación) | Alta | Desktop / TV |
| 6 | Configuración (branding) | Media | Desktop |
| 7 | Executive Folders | Baja | Desktop |
| 8 | Historial / Reportes | Baja | Desktop |

---

## Estrategia de Venta (en la interfaz)

El producto se llama **"Autonomous Recruiting & Sales Desk"** y se vende como:

- **Dashboard white-label** — cada cliente pone su logo y colores
- **Suscripción mensual** — setup + operación de agentes
- **Demo de 30 min** — se abre el dashboard en vivo desde el celular de Manu, se comparte al TV, se muestran los 6 agentes trabajando y el flujo de aprobación
- **Diferenciador:** no es una herramienta más de IA, es un **equipo digital** que rinde cuentas

---

*Prototipo v0.2 — Mobile-first, vendible, presentable en proyector*
*14 de mayo de 2026*
