#!/usr/bin/env bash
# ─────────────────────────────────────────────────────────────
# start_local_control.sh — Levanta dashboard + bot Telegram
# ─────────────────────────────────────────────────────────────
# Uso:
#   ./scripts/start_local_control.sh              # ambos procesos
#   ./scripts/start_local_control.sh --bot-only    # solo el bot
#   ./scripts/start_local_control.sh --dashboard-only
#
# Los logs van a data/logs/.
# Para detener: Ctrl+C mata ambos (o kill el script).
# ─────────────────────────────────────────────────────────────

set -e
ROOT="$(cd "$(dirname "$0")/.." && pwd)"
cd "$ROOT"

mkdir -p data/logs
DASHBOARD_LOG="data/logs/dashboard.log"
BOT_LOG="data/logs/bot.log"
PID_FILE="data/logs/.pids"

cleanup() {
    echo ""
    echo "🛑 Deteniendo procesos..."
    if [ -f "$PID_FILE" ]; then
        while read -r pid; do
            kill "$pid" 2>/dev/null || true
        done < "$PID_FILE"
        rm -f "$PID_FILE"
    fi
    echo "✅ Detenido."
    exit 0
}
trap cleanup SIGINT SIGTERM

start_dashboard() {
    echo "🌐 Levantando dashboard en :8080 ..."
    nohup python3 -m dashboard.server > "$DASHBOARD_LOG" 2>&1 &
    echo $! >> "$PID_FILE"
    echo "   Dashboard PID: $!"
}

start_bot() {
    echo "🤖 Levantando Nexus bot (Telegram)..."
    nohup python3 scripts/telegram_bot.py > "$BOT_LOG" 2>&1 &
    echo $! >> "$PID_FILE"
    echo "   Bot PID: $!"
}

case "${1:-both}" in
    --bot-only)
        start_bot
        ;;
    --dashboard-only)
        start_dashboard
        ;;
    *)
        start_dashboard
        sleep 2
        start_bot
        echo ""
        echo "✅ Ambos procesos levantados."
        echo "   Dashboard: http://127.0.0.1:8080"
        echo "   Logs:"
        echo "     dashboard → $DASHBOARD_LOG"
        echo "     bot       → $BOT_LOG"
        echo ""
        echo "   Ctrl+C para detener todo."
        ;;
esac

# Keep running so trap works
wait
