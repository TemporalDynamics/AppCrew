# ecosign-release-check

Skill de pre-deploy/pre-merge para EcoSign.
Invocar antes de todo push a main o deploy a Vercel/Supabase.

---

## Qué revisar, en orden

### 1. Git diff — secrets
```bash
git diff HEAD --stat
git diff HEAD | grep -iE "(sk-|eyJ|service_role|STRIPE_|WEBHOOK_SECRET|password\s*=)" | head -20
```
Si aparece algún secret → **STOP. No continuar.**

### 2. Archivos modificados
Clasificar en:
- `client/src/` → frontend
- `supabase/functions/` → edge functions
- `supabase/migrations/` → DB
- `supabase/functions/_shared/` → shared (afecta a todas las functions)

### 3. Frontend (si hay cambios en client/)
```bash
cd client && npm run typecheck 2>&1 | tail -20
```
Cero errores TS requerido. Si hay errores → listarlos y parar.

### 4. Edge Functions (si hay cambios en supabase/functions/)
Por cada función tocada:
```bash
deno check supabase/functions/<nombre>/index.ts
```
Si falla → listar error y parar.

### 5. Migraciones nuevas (si hay en supabase/migrations/)
- ¿Son forward-only? (no DROP sin recrear en misma migration)
- ¿Tienen smoke test SQL?
- Invocar `ecosign-supabase-migration` para checklist completo

### 6. Billing (si hay cambios en stripe-checkout, stripe-webhook, DashboardPricingPage)
- Invocar `ecosign-billing-stripe` checklist

---

## Resumen final obligatorio

Emitir exactamente este bloque:

```
## Release Check — <fecha>

**Veredicto:** SAFE TO DEPLOY | NOT SAFE

### Checks
- [ ] Secrets: ninguno en diff
- [ ] TypeScript: 0 errores
- [ ] Deno check: OK en funciones tocadas (listar cuáles)
- [ ] Migrations: forward-only, smoke test incluido
- [ ] Billing: test mode, sin price_id en frontend

### Advertencias
[lista o "ninguna"]

### Archivos modificados
[lista por categoría]
```

Si el veredicto es NOT SAFE → listar exactamente qué falló y parar. No continuar con deploy.
