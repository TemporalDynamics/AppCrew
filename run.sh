#!/usr/bin/env bash
set -e

echo "=== GE Agent System ==="
echo ""

# Check if virtual env exists
if [ ! -d ".venv" ]; then
    echo "🔧 Creando entorno virtual..."
    python3 -m venv .venv
fi

source .venv/bin/activate

if [ ! -f ".venv/installed" ]; then
    echo "📦 Instalando dependencias..."
    pip install -q fastapi uvicorn pyyaml jinja2 httpx pydantic-settings pytest pytest-asyncio
    playwright install chromium 2>/dev/null || echo "⚠️  Playwright browser no instalado (opcional)"
    touch .venv/installed
    echo "✅ Instalación completa"
fi

CMD="${1:-dashboard}"

if [ "$CMD" = "dashboard" ]; then
    echo "🌐 Abrí el dashboard en: http://localhost:8080"
    echo ""
    python run.py dashboard
elif [ "$CMD" = "run-all" ]; then
    python run.py run-all
elif [ "$CMD" = "status" ]; then
    python run.py status
elif [ "$CMD" = "run" ]; then
    shift
    python run.py run "$@"
elif [ "$CMD" = "test" ]; then
    python run.py test
elif [ "$CMD" = "task" ]; then
    shift
    python run.py task "$@"
else
    python run.py "$@"
fi
