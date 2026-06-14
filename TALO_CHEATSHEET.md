# Talo — Cheat Sheet para la Demo

## ¿Qué es Talo en dos palabras?

Talo es un **cazatalentos automático**. Busca candidatos en internet, arma una lista para que vos revises, y si aprobás, les mails. Todo lo que Talo hace, vos lo ves y lo autorizás antes de que pase.

---

## Búsqueda Rápida

```
python run.py task "Buscá CTOs en México, 10 candidatos, prepará borradores"
python run.py task "Necesito VP Sales en Colombia, listo para contactar"
python run.py task "Buscá Directores Financieros en Chile, borradores"
```

Talo solo busca. Los mails NO se mandan hasta que vos digas que sí.

---

## ¿Qué perfiles sabe buscar Talo?

| Vertical | Ejemplos de roles |
|---|---|
| **INGENIERÍA** | CTO, VP Engineering, Engineering Manager, Tech Lead, Head of Product |
| **FINANZAS & BANKING** | CFO, Finance Director, Controller, Treasury, Risk Manager |
| **VENTAS & MARKETING** | VP Sales, Sales Director, CMO, Head of Growth, Head of Marketing |
| **RRHH** | CHRO, HR Director, Head of People, Talent Acquisition Manager |
| **LOGÍSTICA** | COO, Supply Chain Director, Operations Manager, Warehouse Manager |
| **GENERAL** | CEO, Country Manager, Founder, Director of Operations |

---

## ¿Dónde busca?

| Fuente | Qué datos encuentra |
|---|---|
| **Torre.co** | Perfiles LATAM abiertos a oportunidades |
| **Google** (Serper.dev) | LinkedIn, GitHub, AngelList, CVs PDF, Medium, Stack Overflow |
| **GitHub** | Perfiles de GitHub con role + ubicación |
| **PDF OSINT** | CVs públicos indexados por Google |

---

## El flujo entero (de principio a fin)

```
┌─────────────────────────────────────────────────────────────────────┐
│ 1. VOS decís "buscá CTOs en México"                                 │
│    → Talo traduce eso a 5 búsquedas en paralelo                     │
│    → Google + GitHub + Torre + PDFs al mismo tiempo                │
├─────────────────────────────────────────────────────────────────────┤
│ 2. Talo junta resultados, saca duplicados, los califica            │
│    → Te muestra una lista en el dashboard                          │
│    → Cada candidato tiene: nombre, rol, empresa, ubicación, link   │
├─────────────────────────────────────────────────────────────────────┤
│ 3. REVISIÓN HUMANA — VOS tenés el control                           │
│    → Ves los candidatos en pantalla                                 │
│    → Aprobás o descartás cada uno                                   │
│    → No se envía NADA sin tu autorización                           │
├─────────────────────────────────────────────────────────────────────┤
│ 4. Si aprobás: Talo mails                                           │
│    → Busca el email del candidato (Torre / Apollo.io)              │
│    → Genera un mail personalizado con por qué encaja               │
│    → Te manda un Telegram: "✉️ Email enviado a Juan Pérez"       │
├─────────────────────────────────────────────────────────────────────┤
│ 5. El candidato recibe el mail                                      │
│    → Tiene un botón: "Charlemos por Telegram"                      │
│    → Si el candidato lo toca, abre un chat con Talo                │
├─────────────────────────────────────────────────────────────────────┤
│ 6. Talo conversa con el candidato (3 preguntas)                     │
│    → ¿Cuándo podrías empezar?                                       │
│    → ¿Expectativa salarial?                                         │
│    → ¿Qué buscás en tu próximo rol?                                 │
├─────────────────────────────────────────────────────────────────────┤
│ 7. Si el candidato responde todo:                                    │
│    → Talo le manda link de Calendly para agendar 20 min            │
│    → Talo te notifica a VOS por Telegram con las respuestas        │
│    → "✅ Candidato calificado por Telegram — respuestas: ..."    │
└─────────────────────────────────────────────────────────────────────┘
```

---

## ¿Qué dice el mail que recibe el candidato?

**Asunto:** `Juan, ¿te interesa esta oportunidad? — chief revenue officer`

**Cuerpo:**

> **Manu te contacta**
> Oportunidad: chief revenue officer
>
> Hola Juan,
>
> Vi tu perfil en **Torre.co** y creo que hay una oportunidad que podría interesarte.
>
> **Por qué encajás:**
> Experiencia liderando revenue en startups SaaS LATAM, con background en fintech B2B.
>
> Si tenés 5 minutos para contarme un poco más de vos, podemos ver si vale la pena seguir conversando. Sin compromisos.
>
> **[ 💬 Charlemos por Telegram ]**
>
> O respondé este email si preferís continuar por acá.
>
> ---
> Recibiste este mensaje porque tu perfil es público en Torre.co.
> Si no querés recibir más contactos de este tipo, respondé con "No gracias".
>
> Enviado desde **Talo** · sistema de búsqueda de talento.

---

## ¿Cómo habla Talo con el candidato por Telegram?

**Paso 1 — Saludo:**
> ¡Hola Juan! 👋
> Gracias por responder. Soy el asistente de Manu.
> Me gustaría hacerte 3 preguntas rápidas para entender mejor tu perfil.
>
> ¿Cuándo podrías empezar, en caso de que encontremos algo que te interese?

**Paso 2 — Cuando responde:**
> ¿Tenés alguna expectativa de rango salarial? Podés ser aproximado.

**Paso 3 — Cuando responde:**
> ¿Qué es lo más importante para vos en tu próximo rol?

**Paso 4 — Cuando responde la 3ra:**
> ¡Perfecto! Muchas gracias.
>
> Podés agendar una charla de 20 min acá:
> https://calendly.com/...

**Y a vos te llega al Telegram de reclutador:**
> ✅ Candidato calificado via Telegram
> 👤 Juan Pérez
> 🔍 Búsqueda: chief revenue officer
>
> • ¿Cuándo podrías empezar?
> → En 30 días
> • ¿Expectativa salarial?
> → $80-100k USD
> • ¿Qué es lo más importante?
> → Autonomía y ownership
>
> 📅 Agendar entrevista: https://calendly.com/...

---

## La regla de oro

**Talo NUNCA mails nada sin tu permiso.**

Todo el flujo está diseñado para que vos seas el que dice "sí" o "no" a cada candidato. Talo prepara los borradores, vos revisás, y solo cuando aprobás se dispara el mail. No hay automatismos ocultos.

---

## Comandos útiles

```
python run.py task "Buscá <rol> en <país>, <cantidad> candidatos, prepará borradores"
python run.py run-all                      # Pipeline completo
python run.py task "mostrame el estado"    # Qué pasó hasta ahora
python run.py run --agent outreach         # Solo prepara borradores
```

## Dashboard

```
http://127.0.0.1:8080/command-room
    → Ahí ves candidatos, aprobás, ves el historial
```
