# DIAGNÓSTICO: Qué existe, qué falta, plan mínimo funcional

Fecha: 2026-05-27 | Demo: 2026-05-28 (MAÑANA)

---

## ✅ QUÉ EXISTE Y ESTÁ LISTO

### Backend
- **State Store (SQLite)**: Persistencia de runs, actions, agent_states
- **Orchestrator**: Descomposición de tareas, coordinación de agentes
- **13 Agentes implementados**: CEO, Demand Radar, Talent Sourcing, Fit Scoring, Career Context, Talent Signal, Outreach, QA, Knowledge, Doctrine Keeper, Tester, etc.
- **FastAPI Dashboard**: 8 endpoints POST ya definidos (`/api/ceo/task`, `/api/approve/{action_id}`, etc.)
- **Contracts**: Tipos de datos completos (AgentState, ActionType, ReviewPolicy)
- **Telegram Notifier**: Clase implementada con métodos para enviar alertas

### Frontend
- **Jinja2 templates** en `/dashboard/templates/`
- **Estado renderizable** (agents, pending actions, runs)

### Seguridad
- **MCP Verifiable Memory** en `/verifiable-memory-mcp/`: Hash chain funcional, verificación criptográfica

---

## ❌ QUÉ FALTA (Critical Path para Demo)

### 1. **Telegram Webhook → Backend** 🔴 CRÍTICO
**Estado**: No existe
**Por qué importa**: Rodri necesita mandar "/busca CTOs" desde Telegram
**Qué falta**:
- Token de bot real y chat_id en `.env`
- Endpoint `/api/telegram/webhook` en `dashboard/server.py`
- Lógica de parse del mensaje (reconocer comandos)
- Conexión webhook (setWebhook en Telegram)

**Tiempo estimado**: 30 min

---

### 2. **Candidatos Reales o Dataset Real** 🔴 CRÍTICO
**Estado**: Los agentes usan mocks
**Por qué importa**: No querés que la demo diga "candidatos ficticios"
**Opciones**:

**Opción A (Más simple)**: CSV/JSON cargado manualmente
- Archivo: `/data/candidates.json` con 50-100 candidatos realistas (LATAM tech)
- Agente **Talent Sourcing** lee de ahí en lugar de LinkedIn
- Ventaja: Cero dependencias externas, totalmente controlado
- Tiempo: 30 min (fabricar CSV realista)

**Opción B (Más elegante)**: Conector real a fuente
- Si tienes acceso a LinkedIn API (oficial) o Crunchbase → usar
- Si no → Opción A

**Recomendación**: Opción A para mañana. Datos mexicanos/LATAM, nombres reales, empresas reales, roles de CTO/VP Eng.

---

### 3. **UI `/ops` Funcional** 🟡 IMPORTANTE
**Estado**: Existe pero básica
**Por qué importa**: Rodri necesita VER el run ejecutándose, shortlist, botones de aprobación

**Qué falta**:
- Pantalla `/ops` que muestra:
  - Misión (el prompt que Rodri mandó)
  - Estado del run (running, completed, etc.)
  - Agentes ejecutándose (timeline o progress bar)
  - Shortlist real (tabla de candidatos con scores)
  - Botones: Aprobar / Rechazar / Pedir más evidencia
  - Ledger (timeline de eventos)

**Tiempo estimado**: 45 min (si usan un template base)

---

### 4. **Action Handlers Funcionales** 🟡 IMPORTANTE
**Estado**: Los endpoints existen pero algunos no hacen nada real
**Por qué importa**: Cuando Rodri aprueba un candidato, tiene que cambiar estado

**Qué falta**:
- `/api/approve/{action_id}` → actualizar BD, trigger outreach
- `/api/reject/{action_id}` → cambiar estado, registrar razón
- `/api/review/{action_id}` → cambiar estado a "needs_revision"
- Cada handler debe: actualizar estado en DB + notificar vía Telegram

**Tiempo estimado**: 20 min

---

### 5. **Agentes Ejecutándose en Tiempo Real** 🟡 IMPORTANTE
**Estado**: Existen pero con mocks, sin salida visible
**Por qué importa**: Rodri quiere VER que los agentes trabajan, no solo el resultado final

**Qué falta**:
- Cada agente debe escribir un **output mínimo** (1-2 líneas) al run
- Ejemplo: `[CEO] Interpretando misión: 'Buscar 5 CTOs en Fintech México'`
- El output aparece en el timeline de `/ops`
- Timing: No tiene que ser instantáneo, pero tiene que estar ahí mientras se ejecuta

**Tiempo estimado**: 15 min (agregar logging a cada agente)

---

### 6. **Ledger / Timeline de Decisiones** 🟡 IMPORTANTE
**Estado**: La BD tiene los eventos, pero no hay visualización
**Por qué importa**: Muestra integridad criptográfica

**Qué falta**:
- Tabla visual en `/ops` que muestre:
  - [19:55:06] Rodri pregunta en Telegram
  - [19:55:07] CEO inicia descomposición
  - [19:55:10] Demand Radar ejecuta (hash: 0x8f92...)
  - [19:55:12] Rodri aprueba candidato #1
  - Etc.
- Cada fila tiene un candadito ✓

**Tiempo estimado**: 20 min (template + loop en DB)

---

### 7. **Telegram Response (Bot Envía Respuesta)** 🟡 IMPORTANTE
**Estado**: Notifier existe pero no se trigguerea
**Por qué importa**: Rodri ve los resultados en Telegram, no solo en la UI

**Qué falta**:
- Cuando el run termina: bot envía resumen a Telegram
- Resumen: "Encontré 5 CTOs. 3 recomendados, 2 en espera. Revisa en /ops"
- Cuando Rodri aprueba: bot confirma en Telegram

**Tiempo estimado**: 15 min

---

## 📋 PLAN MÍNIMO PARA MAÑANA (Orden de Ejecución)

```
[1] Telegram Setup (30 min)
    └─ Token real + chat_id en .env
    └─ POST /api/telegram/webhook
    └─ Parse de comandos

[2] Dataset Real (30 min)
    └─ /data/candidates.json (100 CTOs/VPs realistas)
    └─ Talent Sourcing lee de JSON en lugar de mock

[3] Agent Logging (15 min)
    └─ Cada agente: agent.write_to_run(message)
    └─ Run acumula logs

[4] Action Handlers (20 min)
    └─ /api/approve/{action_id} → update DB + Telegram
    └─ /api/reject/{action_id}
    └─ /api/review/{action_id}

[5] UI /ops (45 min)
    └─ Template Jinja que muestra run state
    └─ Shortlist (tabla)
    └─ Timeline (ledger)
    └─ Botones funcionales

[6] Telegram Respuesta (15 min)
    └─ Cuando run completa → enviar resumen
    └─ Cuando acción aprobada → confirmar

TOTAL: ~2.5 horas de código quirúrgico

```

---

## 🎯 Qué Mostrar Mañana (Sin Estas Piezas)

Si faltan algunas piezas pequeñas, el circuito funciona así:

### **Escena A: Mensaje Telegram**
```
Rodri en Telegram: "Buscá 5 CTOs en Fintech México"
↓
Bot recibe, crea run_id
↓
Backend: orchestrator.process_task("Buscá...")
```

### **Escena B: Agentes Ejecutando**
```
Terminal abierta mostrando:
[CEO] Descomponiendo: talento_sourcing, fit_scoring, career_context...
[Demand Radar] Buscando empresas fintech en México...
[Talent Sourcing] Encontré 47 candidatos potenciales
[Fit Scoring] Calculando scores... (87, 84, 82, 79, 76)
[Career Context] Validando contexto de empresas...
[Talent Signal] Preguntas de validación generadas
```

### **Escena C: UI /ops**
```
Run: 20260528_150530
Misión: "Buscá 5 CTOs en Fintech México"
Estado: COMPLETED

Shortlist:
┌─────────────────────────────────────────┐
│ #1 Luis García (87pts) - Aprobado ✅    │
│ #2 María Rodríguez (84pts) - Pendiente  │
│ #3 Carlos López (82pts) - Rechazado ❌  │
└─────────────────────────────────────────┘

Ledger:
[19:55:06] Rodri: "Buscá 5 CTOs..."
[19:55:07] CEO: Descomposición iniciada
[19:55:10] Talent Sourcing: 47 candidatos
[19:55:15] Fit Scoring: Scoring completado
[19:55:20] Rodri: Aprobó Luis García
[19:55:21] Outreach: Borrador generado
```

### **Escena D: Telegram Respuesta**
```
Bot → Rodri:
"✅ Encontré 5 CTOs en Fintech México
• 3 RECOMENDADOS (80+ pts)
• 2 PARA REVISAR (75-79 pts)
Revisa scores en /ops o aprobá aquí 👇"
```

---

## 🔴 Si Falta Algo en Demo

**No hagas nada "graceful".**

Si falta el webhook de Telegram, decís:
> "Normalmente el bot recibiría el mensaje de Telegram, pero hoy lo voy a simular con un POST manual"

Y haces:
```bash
curl -X POST http://localhost:8080/api/telegram/webhook \
  -d '{"message": "Buscá 5 CTOs en Fintech México"}'
```

**El circuito tiene que cerrarse. Lo que importa es que funcione de punta a punta, aunque una pieza sea manual.**

---

## ✨ Lo Que NO Hacer

- ❌ No grabes videos de demostraciones
- ❌ No hagas pantallas estáticas que no respondan
- ❌ No prometas candidatos reales si son mocks
- ❌ No abras 5 terminales sin propósito
- ❌ No muestres código fuente (es feo en proyector)

Lo que sí:
- ✅ Uno o dos terminalesy una UI
- ✅ Un mensaje real de Telegram
- ✅ Datos reales (aunque sean CSV cargados)
- ✅ Botones que funcionan
- ✅ Estado que cambia en tiempo real

---

## 📞 Resumen para Ejecutar Ahora

**Siguiente paso**: Decidir qué piezas implementas vos vs cuál quiero que haga yo.

1. ¿Tenés token de Telegram bot real + chat_id?
2. ¿De dónde saco los 100 candidatos realistas? (te los fabrico yo en JSON?)
3. ¿Cuál es la prioridad: webhook primero o UI /ops primero?
4. ¿Los agentes tienen que escribir logs ahora o puedo dejarlos mudos?

Una vez respondas, me lanzo a codificar.
