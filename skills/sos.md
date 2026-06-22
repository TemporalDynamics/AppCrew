# Skill: Crew S.O.S.

**Trigger**: Human is blocked, something is broken, they don't know where to start.

**Goal**: Diagnose the first visible broken layer. Present minimum evidence. Offer 3 numbered options. Wait.

---

## Protocol

### Step 1 — Scan the first visible layer only

Do NOT:
- Run a full system audit
- Check all logs from the beginning of time
- Investigate every possible cause
- Propose architecture changes

DO:
- Check the immediate error or symptom
- Identify what is responding vs. not responding
- Find the first broken link in the chain

### Step 2 — Present evidence in ≤5 lines

Format:
```
S.O.S. detectó bloqueo en [component].

Barrido rápido:
  • [Thing that works]
  • [Thing that works]
  • [Thing that is broken]
  • [Specific error or missing piece]
```

### Step 3 — Offer exactly 3 options

Option 1 is always the fastest path to unblocking (may incur technical debt, clearly labeled).  
Option 2 is the safe/clean path.  
Option 3 is "investigate further before deciding."

Format:
```
Opciones:

1. [Fastest fix] — [consequence or debt incurred]
2. [Clean fix] — [what it requires]
3. Seguir investigando — [what more info would reveal]

Elegí 1, 2 o 3.
```

### Step 4 — Wait

Do not execute any option until the human responds with 1, 2, or 3.

---

## Hard constraints (never violate during S.O.S.)

- No refactoring
- No architecture changes
- No production data modification
- No installing large dependencies
- No infinite investigation loop
- No over-explaining
- No proposing more than 3 options
- No executing without human input

---

## Example

**Input**: "The login is broken. Users can't get in. I don't know what's happening."

**S.O.S. response**:

```
S.O.S. detectó bloqueo en autenticación.

Barrido rápido:
  • Frontend responde en :3000 ✓
  • Backend responde en :8080 ✓
  • POST /auth/login retorna 401
  • Variable AUTH_SECRET no está cargada en el proceso del backend

Opciones:

1. Arreglar ahora: cargar AUTH_SECRET desde .env.example y reiniciar backend.
2. Workaround seguro: activar bypass local si existe (buscar env var DEV_AUTH_BYPASS).
3. Seguir investigando: ver logs completos del backend desde el arranque.

Elegí 1, 2 o 3.
```

---

## When NOT to use S.O.S.

- When the human has a clear task and is not blocked
- When the issue requires domain knowledge the crew doesn't have (escalate to human expert)
- When the system state is production-critical and any change could cause data loss (do not act — alert only)
