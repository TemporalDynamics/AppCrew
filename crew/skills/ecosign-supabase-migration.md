# ecosign-supabase-migration

Skill para crear y aplicar migraciones de Supabase en EcoSign.
Invocar ante cualquier cambio de schema, función SQL, trigger o RLS.

---

## Patrón de nombre de archivo
```
supabase/migrations/YYYYMMDDHHMMSS_descripcion_corta.sql
```
Siempre timestamp único. Nunca reutilizar ni editar migration ya aplicada.

---

## Checklist al escribir la migration

### Encabezado obligatorio
```sql
-- Migration: <descripcion>
-- Fecha: <YYYY-MM-DD>
-- Afecta: <tabla/función/trigger>
-- Autor: ecosign-bot

SET search_path = public, extensions;
```

### RLS
- Toda tabla nueva → `ALTER TABLE <t> ENABLE ROW LEVEL SECURITY;`
- Toda policy nueva → verificar que no haya policy con mismo nombre ya existente
- Usar `DROP POLICY IF EXISTS` antes de `CREATE POLICY`

### Funciones SQL
- Si cambia el return type → DROP y recrear en misma migration
- Siempre `CREATE OR REPLACE FUNCTION` si no cambia firma
- Agregar `SECURITY DEFINER` solo si está en allowlist (`docs/contratos/`)
- `SET search_path = public, extensions` dentro de la función

### Triggers
- `DROP TRIGGER IF EXISTS` antes de `CREATE TRIGGER`
- Verificar que la función del trigger exista antes de crear trigger

### Grants
```sql
GRANT EXECUTE ON FUNCTION <nombre> TO authenticated;
-- o
GRANT EXECUTE ON FUNCTION <nombre> TO service_role;
```
Nunca dejar función sin grant explícito si es nueva.

---

## Smoke test SQL (obligatorio)

Al final de cada migration, incluir en comentario el smoke test:

```sql
-- SMOKE TEST (ejecutar manualmente después de aplicar):
-- SELECT <funcion_o_query_que_verifica_el_cambio>;
-- Resultado esperado: <descripción>
```

Para enforcement de límites, smoke tests mínimos:
```sql
-- SELECT compute_workspace_effective_limits_v2('<workspace_id>');
-- Verificar que devuelve límites correctos para plan pro/business/free
```

---

## Verificación remota antes de aplicar en producción

```bash
# Ver migrations aplicadas
supabase db remote migrations list --db-url $DATABASE_URL

# Ver funciones existentes (evitar colisiones)
psql $DATABASE_URL -c "\df public.*"

# Ver triggers existentes
psql $DATABASE_URL -c "SELECT trigger_name, event_object_table FROM information_schema.triggers WHERE trigger_schema = 'public';"
```

---

## Deploy a producción

```bash
# Verificar qué migrations pendientes hay
supabase db push --dry-run

# Aplicar (requiere confirmación humana)
supabase db push
```

**Nunca** hacer `db push` en producción sin dry-run previo.
**Nunca** hacer `db push` si el smoke test SQL no pasó en local primero.

---

## Casos especiales

### Cambio de función con return type distinto
```sql
-- 1. Drop la función vieja
DROP FUNCTION IF EXISTS <nombre>(<args>);
-- 2. Recrear con nueva firma
CREATE OR REPLACE FUNCTION <nombre>(<new_args>) RETURNS <new_type> ...
-- 3. Re-grant
GRANT EXECUTE ON FUNCTION <nombre> TO authenticated;
```

### Nueva tabla con foreign key a workspaces
```sql
ALTER TABLE <nueva_tabla> ADD CONSTRAINT fk_workspace
  FOREIGN KEY (workspace_id) REFERENCES workspaces(id) ON DELETE CASCADE;
ALTER TABLE <nueva_tabla> ENABLE ROW LEVEL SECURITY;
CREATE POLICY "<tabla>_workspace_isolation" ON <nueva_tabla>
  FOR ALL TO authenticated
  USING (workspace_id = (SELECT id FROM workspaces WHERE owner_id = auth.uid() LIMIT 1));
```
