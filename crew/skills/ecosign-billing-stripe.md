# ecosign-billing-stripe

Skill para todo lo relacionado con Stripe en EcoSign.
Invocar ante cualquier cambio en checkout, webhook, precios, planes o billing UI.

---

## Regla cardinal

> **El frontend NUNCA manda `price_id`. Solo manda `plan_key` + `billing`.**
> El backend mapea internamente via `PRICE_MAP` en `stripe-checkout/index.ts`.

Violación de esta regla = FAIL inmediato en auditoría.

---

## Mapa de planes

| plan_key | billing | Env var en Supabase |
|----------|---------|---------------------|
| pro | monthly | STRIPE_PRICE_PRO_MONTHLY |
| pro | annual | STRIPE_PRICE_PRO_ANNUAL |
| business | monthly | STRIPE_PRICE_BUSINESS_MONTHLY |
| business | annual | STRIPE_PRICE_BUSINESS_ANNUAL |

Productos (test mode):
- FREE: `prod_UaBnNU80lqGviw`
- PRO: `prod_UaBn88L6iF10Mf`
- BUSINESS: `prod_UaBnrMWlTkfisw`

---

## Checklist — stripe-checkout (Edge Function)

- [ ] Auth: requiere JWT de usuario (no anon, no service_role)
- [ ] `plan_key` y `billing` validados contra PRICE_MAP
- [ ] `price_id` resuelto en servidor, nunca del body del request
- [ ] `workspace_id` y `user_id` obtenidos del JWT, no del body
- [ ] Metadata en `subscription_data.metadata` Y en `session.metadata`
- [ ] `allow_promotion_codes: true`
- [ ] `success_url`: `${APP_URL}/dashboard/billing?success=1&plan=${plan_key}`
- [ ] `cancel_url`: `${APP_URL}/dashboard/billing?canceled=1`
- [ ] CORS correcto (ALLOWED_ORIGIN / SITE_URL / FRONTEND_URL)

---

## Checklist — stripe-webhook (Edge Function)

- [ ] Verificación de firma: `stripe.webhooks.constructEvent(body, signature, webhookSecret)`
- [ ] `body` leído como texto plano (no JSON) antes de verificar
- [ ] Idempotencia: eventos procesados dos veces no deben duplicar workspace_plan
- [ ] `checkout.session.completed`: solo si `session.mode === 'subscription'`
- [ ] `customer.subscription.deleted`: downgrade a FREE (`activatePlan(..., 'free', '', '', 'active')`)
- [ ] `invoice.payment_failed`: set `status = 'past_due'` via update directo (no activatePlan)
- [ ] Metadata requerida en eventos: `workspace_id`, `user_id`, `plan_key`
- [ ] `activatePlan` cancela plan vigente antes de insertar nuevo
- [ ] `auth.admin.updateUserById` actualiza `user_metadata` (opcional, no crítico)

---

## Checklist — workspace_plan (DB)

Después de checkout exitoso:
```sql
SELECT wp.*, p.key
FROM workspace_plan wp
JOIN plans p ON p.id = wp.plan_id
WHERE wp.workspace_id = '<id>'
ORDER BY wp.started_at DESC LIMIT 3;
```
Esperado:
- `key = 'pro'` (o el plan comprado)
- `status = 'active'`
- `metadata` contiene `stripe_customer_id` y `stripe_subscription_id`

```sql
SELECT * FROM compute_workspace_effective_limits_v2('<workspace_id>');
```
Esperado: límites del plan comprado (PRO: 50 ops/mes, 5 docs/op, 3 firmantes).

---

## Límites por plan

| Límite | FREE | PRO | BUSINESS |
|--------|------|-----|----------|
| operations_monthly_limit | 3 | 50 | 100 |
| max_documents_per_operation | 1 | 5 | 8 |
| signers_per_document | 2 | 3 | 3 |
| agent_seats_limit | 1 | 2 | 10 |

---

## Test E2E — flujo completo

### Setup
```bash
# NO crear .env.local con real Supabase en el repo. Usar variable de entorno temporal.
export VITE_SUPABASE_URL=https://uiyojopjbhooxrmamaiw.supabase.co
export VITE_SUPABASE_ANON_KEY=<anon key>
```

### Pasos
1. Crear usuario test con email real/controlable
2. Confirmar email si Supabase lo requiere
3. Login → navegar a `/planes`
4. Click "Upgrade a PRO" (mensual)
5. Verificar redirect a `checkout.stripe.com`
6. Usar tarjeta test: `4242 4242 4242 4242`, fecha futura, cualquier CVC
7. Verificar redirect a `/dashboard/billing?success=1&plan=pro`
8. Verificar DB (queries arriba)

### Cancel path
Usar usuario distinto (o antes del pago exitoso):
1. Click "Upgrade" → llega a Stripe
2. Click "← Back" en Stripe
3. Verificar redirect a `/dashboard/billing?canceled=1`
4. Verificar que `workspace_plan` NO cambió (sigue FREE)

---

## Go-live (live mode)

**No hacer hasta que el e2e en test mode pase completamente.**

Checklist go-live:
- [ ] Crear productos y precios en Stripe live mode (misma estructura que test)
- [ ] Setear secrets `STRIPE_*` en producción (separados de test)
- [ ] Rotary webhook secret de producción
- [ ] Verificar que `APP_URL` en secrets apunta a `https://app.ecosign.app`
- [ ] Primer checkout de producción con tarjeta real de $1 (reembolsar)
- [ ] Verificar webhook en Stripe Dashboard → Events

---

## Secrets en Supabase (nunca en código)

```
STRIPE_SECRET_KEY
STRIPE_WEBHOOK_SECRET
STRIPE_PRICE_PRO_MONTHLY
STRIPE_PRICE_PRO_ANNUAL
STRIPE_PRICE_BUSINESS_MONTHLY
STRIPE_PRICE_BUSINESS_ANNUAL
APP_URL
```

Verificar con:
```bash
supabase secrets list
```
