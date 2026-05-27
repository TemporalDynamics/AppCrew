#!/usr/bin/env bash
# El show de la ambulancia.
# Demuestra que el sistema detecta tamper antes de que el humano lo note.
#
# Uso: bash scripts/demo_tamper.sh

set -e

LEDGER_DB="data/state/verifiable-memory-mcp/memory.db"
PYTHON="${PYTHON:-python3}"

echo ""
echo "=== DEMO: Verificación de integridad del ledger ==="
echo ""

# 1. Verificar que el ledger está íntegro
echo "[PASO 1] Verificando integridad antes del tamper..."
if $PYTHON scripts/demo_verify.py; then
    echo "  ✓ Todo verde. La cadena está intacta."
else
    echo "  El ledger ya tiene problemas antes del tamper. Corre demo_reset.sh primero."
    exit 1
fi

echo ""
echo "[PASO 2] Modificando un registro directamente en SQLite..."
echo "         (Esto simula a alguien interviniendo el sistema sin pasar por los agentes)"
echo ""

# 2. Tamper: cambiar el content de la primera entrada
sqlite3 "$LEDGER_DB" \
    "UPDATE entries SET content = content || ' [DATO ALTERADO]' WHERE id = (SELECT id FROM entries ORDER BY created_epoch ASC LIMIT 1);"

echo "  → Registro modificado. Para el ojo humano, el dashboard no muestra nada diferente."
echo ""

# 3. Correr verify — debe FALLAR y disparar Telegram
echo "[PASO 3] Verificando cadena con el registro adulterado..."
echo ""

if $PYTHON scripts/demo_verify.py; then
    echo "  ERROR: el sistema no detectó el tamper. Algo está mal con el verificador."
    exit 1
else
    echo ""
    echo "  ✓ El sistema detectó el tamper antes de ejecutar cualquier acción."
    echo "  ✓ El Telegram ya avisó."
    echo "  ✓ Ningún agente puede actuar con un ledger comprometido."
fi

echo ""
echo "=== Show completado. Para restaurar: bash scripts/demo_reset.sh ==="
echo ""
