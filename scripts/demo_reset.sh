#!/usr/bin/env bash
# Reset limpio para la demo.
# Borra estado, recarga seed, verifica que todo corre.
#
# Uso: bash scripts/demo_reset.sh

set -e

PYTHON="${PYTHON:-python3}"

echo ""
echo "=== DEMO RESET ==="
echo ""

# 1. Borrar ledger anterior
echo "[1/4] Limpiando estado anterior..."
rm -f data/state/verifiable-memory-mcp/memory.db
rm -f data/state/demo_ledger_fallback.jsonl
echo "  ✓ Ledger borrado."

# 2. Correr criterion intake en modo demo
echo ""
echo "[2/4] Cargando criterio de Rodri..."
$PYTHON scripts/demo_criterion_intake.py --demo
echo "  ✓ Criterio listo en data/demo_rodri_criteria.yaml"

# 3. Correr talent mission para sembrar estado
echo ""
echo "[3/4] Ejecutando Talent Mission Capsule..."
$PYTHON scripts/demo_talent_mission.py
echo "  ✓ Shortlist generada, ledger sembrado, Telegram notificado."

# 4. Verificar integridad del ledger
echo ""
echo "[4/4] Verificando integridad del ledger..."
$PYTHON scripts/demo_verify.py
echo "  ✓ Cadena íntegra. Todo listo para la demo."

echo ""
echo "=== RESET COMPLETADO ==="
echo ""
echo "Para arrancar el dashboard: python dashboard/server.py"
echo "Para la secuencia completa de demo: ver .crew/DEMO.md"
echo ""
