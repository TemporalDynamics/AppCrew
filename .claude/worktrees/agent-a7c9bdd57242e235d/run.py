#!/usr/bin/env python3
"""Entry Point — Sourcing Platform"""

import argparse
import asyncio
import sys
from pathlib import Path

import uvicorn

from core.orchestrator import Orchestrator
from core.config import settings


def main():
    parser = argparse.ArgumentParser(description="Sourcing Platform Dashboard")
    parser.add_argument("command", nargs="?", default="dashboard",
                        choices=["dashboard", "run", "run-all", "status", "task", "test"],
                        help="Comando a ejecutar")
    parser.add_argument("task_text", nargs="*", help="Texto de tarea para 'task'")
    parser.add_argument("--agent", "-a", help="Agente específico para 'run'")
    parser.add_argument("--port", "-p", type=int, default=settings.dashboard_port, help="Puerto del dashboard")
    parser.add_argument("--host", default=settings.dashboard_host, help="Host del dashboard")

    args = parser.parse_args()

    if args.command == "dashboard":
        print(f"🌐 Dashboard: http://{args.host}:{args.port}")
        uvicorn.run(
            "dashboard.server:app",
            host=args.host,
            port=args.port,
            reload=False,
            log_level="info",
        )

    elif args.command == "run":
        async def run_single():
            orch = Orchestrator()
            if args.agent:
                actions = await orch.run_agent(args.agent)
                print(f"\n  {orch.agents[args.agent].icon} {orch.agents[args.agent].name}")
                print(f"  → {len(actions)} acciones generadas")
                for a in actions:
                    print(f"    · {a.action_type} → {a.target} (score: {a.score})")
            else:
                print("⚠️  Especificá un agente con --agent. Opciones: " +
                      ", ".join(Orchestrator().agents.keys()))
        asyncio.run(run_single())

    elif args.command == "run-all":
        async def run_all():
            orch = Orchestrator()
            results = await orch.run_all()
            print("\n📊 Todos los agentes ejecutados:\n")
            for agent_id, actions in results.items():
                agent = orch.agents[agent_id]
                print(f"  {agent.icon} {agent.name}: {len(actions)} acciones")
                for a in actions[:3]:
                    print(f"    · {a.action_type} → {a.target} (score: {a.score})")
                if len(actions) > 3:
                    print(f"    ... y {len(actions)-3} más")
            print(f"\n⏳ {orch.get_status()['pending_count']} acciones pendientes de revisión")
        asyncio.run(run_all())

    elif args.command == "status":
        orch = Orchestrator()
        status = orch.get_status()
        print(f"\n🎛️  {status['orchestrator']} — Cerno\n")
        for aid, agent in status["agents"].items():
            print(f"  {agent['icon']} {agent['name']:20s} {agent['state']:20s} {agent['last_action']}")
        print(f"\n  Pendientes: {status['pending_count']} · Historial total: {status['total_history']}")

    elif args.command == "task":
        async def run_task():
            orch = Orchestrator()
            task_text = " ".join(args.task_text) if args.task_text else ""
            if not task_text:
                print("⚠️  Especificá una tarea. Ej: python run.py task \"Buscar CTOs en México\"")
                return
            print(f"\n🧠 Procesando: {task_text}\n")
            result = await orch.run_task(task_text)
            print(result.get("summary", ""))
            pending = result.get("pending_actions", [])
            if pending:
                print(f"\n⏳ {len(pending)} acción(es) pendiente(s) de revisión. Abrí el dashboard para aprobar.")
        asyncio.run(run_task())

    elif args.command == "test":
        async def run_tests():
            from core.state import StateStore
            StateStore.clear()
            orch = Orchestrator(restore_state=False)
            print("\n🔬 Ejecutando tests del sistema...\n")
            actions = await orch.run_agent("tester")
            tester = orch.agents["tester"]
            summary = tester.get_summary()
            for r in summary["results"]:
                icon = "✅" if r["verdict"] == "PASS" else "⚠️" if r["verdict"] == "SOFT_FAIL" else "❌"
                print(f"  {icon} {r['test_name']:30s} {r['verdict']:12s} intentos={r['attempts']}")
            print(f"\n  {summary['passed']}/{summary['total']} tests OK")
            if summary["hard_fail"]:
                print(f"  ❌ {summary['hard_fail']} test(s) requieren atención humana")
        asyncio.run(run_tests())


if __name__ == "__main__":
    main()
