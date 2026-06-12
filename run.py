#!/usr/bin/env python3
"""Entry Point — Sourcing Platform"""

import argparse
import asyncio
import sys
from pathlib import Path

import uvicorn

from core.orchestrator import Orchestrator
from core.config import settings
from core.logger import get_logger

logger = get_logger("cli")


def _check_env():
    if not settings.openrouter_api_key:
        logger.warning("OPENROUTER_API_KEY no configurada — LLM no disponible")
    if not settings.serper_api_key and not settings.brave_search_api_key:
        logger.warning("SERPER_API_KEY no configurada — búsqueda web limitada a mock")
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        logger.info("TELEGRAM no configurado — notificaciones en mock")


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
    _check_env()

    if args.command == "dashboard":
        logger.info("Dashboard: http://%s:%s", args.host, args.port)
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
                agent = orch.agents[args.agent]
                logger.info("%s %s", agent.icon, agent.name)
                logger.info("→ %d acciones generadas", len(actions))
                for a in actions:
                    logger.info("  · %s → %s (score: %s)", a.action_type, a.target, a.score)
            else:
                logger.warning("Especificá un agente con --agent. Opciones: %s",
                               ", ".join(Orchestrator().agents.keys()))
        asyncio.run(run_single())

    elif args.command == "run-all":
        async def run_all():
            orch = Orchestrator()
            results = await orch.run_all()
            logger.info("Todos los agentes ejecutados:")
            for agent_id, actions in results.items():
                agent = orch.agents[agent_id]
                logger.info("  %s %s: %d acciones", agent.icon, agent.name, len(actions))
                for a in actions[:3]:
                    logger.info("    · %s → %s (score: %s)", a.action_type, a.target, a.score)
                if len(actions) > 3:
                    logger.info("    ... y %d más", len(actions) - 3)
            logger.info("%d acciones pendientes de revisión", orch.get_status()["pending_count"])
        asyncio.run(run_all())

    elif args.command == "status":
        orch = Orchestrator()
        status = orch.get_status()
        logger.info("%s — Cerno", status["orchestrator"])
        for aid, agent in status["agents"].items():
            logger.info("  %s %-20s %-20s %s", agent["icon"], agent["name"], agent["state"], agent["last_action"])
        logger.info("  Pendientes: %d · Historial total: %d", status["pending_count"], status["total_history"])

    elif args.command == "task":
        async def run_task():
            orch = Orchestrator()
            task_text = " ".join(args.task_text) if args.task_text else ""
            if not task_text:
                logger.warning("Especificá una tarea. Ej: python run.py task \"Buscar CTOs en México\"")
                return
            logger.info("Procesando: %s", task_text)
            result = await orch.run_task(task_text)
            logger.info(result.get("summary", ""))
            pending = result.get("pending_actions", [])
            if pending:
                logger.info("%d acción(es) pendiente(s) de revisión", len(pending))
        asyncio.run(run_task())

    elif args.command == "test":
        async def run_tests():
            from core.state import StateStore
            StateStore.clear()
            orch = Orchestrator(restore_state=False)
            logger.info("Ejecutando tests del sistema...")
            actions = await orch.run_agent("tester")
            tester = orch.agents["tester"]
            summary = tester.get_summary()
            for r in summary["results"]:
                icon = "PASS" if r["verdict"] == "PASS" else "FAIL" if r["verdict"] == "HARD_FAIL" else "SOFT"
                logger.info("  %s %s %s intentos=%d", icon, r["test_name"], r["verdict"], r["attempts"])
            logger.info("  %d/%d tests OK", summary["passed"], summary["total"])
            if summary["hard_fail"]:
                logger.warning("%d test(s) requieren atención humana", summary["hard_fail"])
        asyncio.run(run_tests())


if __name__ == "__main__":
    main()
