"""Nexus — Telegram remote control for Cerno/Talo dashboard API.

Speaks ONLY to the dashboard HTTP API, never imports Orchestrator directly.
This guarantees state consistency between Telegram and the web UI.

Requires:
  - Dashboard running on DASHBOARD_HOST:DASHBOARD_PORT
  - TELEGRAM_BOT_TOKEN and TELEGRAM_CHAT_ID in .env
  - DASHBOARD_API_TOKEN in .env

Commands:
  /help           — show available commands
  /status         — system status summary
  /pending        — numbered pending actions
  /approve N      — approve action #N (asks confirm first)
  /reject N msg   — reject action #N with optional reason
  /run            — run full pipeline
  /run <agent>    — run single agent
  <free text>     — task for CEO agent
"""
from __future__ import annotations

import json
import os
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

import requests
from core.config import settings

BOT_URL = f"https://api.telegram.org/bot{settings.telegram_bot_token}"
AUTHORIZED = str(settings.telegram_chat_id)

API_BASE = f"http://{settings.dashboard_host}:{settings.dashboard_port}/api"
API_TOKEN = settings.dashboard_api_token

# Per-chat numbered action mapping: { chat_id: { index: action_id } }
_action_map: dict[str, dict[int, str]] = {}
# Pending confirmation: { chat_id: { "action": str, "index": int, "action_id": str, "label": str } }
_pending_confirm: dict[str, dict] = {}

AGENTS_LIST = [
    "demand_radar", "knowledge", "criteria",
    "talent_sourcing", "intake", "normalization", "deduplication",
    "talent_signal", "career_context", "fit_scoring", "evidence",
    "memory_update", "qa", "outreach", "ceo",
]


def _headers() -> dict:
    h = {"Content-Type": "application/json"}
    if API_TOKEN:
        h["Authorization"] = f"Bearer {API_TOKEN}"
    return h


def send(text: str) -> None:
    try:
        requests.post(
            f"{BOT_URL}/sendMessage",
            json={"chat_id": AUTHORIZED, "text": text},
            timeout=10,
        )
    except Exception as e:
        print(f"[SEND ERROR] {e}")


def send_md(text: str) -> None:
    try:
        requests.post(
            f"{BOT_URL}/sendMessage",
            json={"chat_id": AUTHORIZED, "text": text, "parse_mode": "Markdown"},
            timeout=10,
        )
    except Exception as e:
        print(f"[SEND ERROR] {e}")


def typing() -> None:
    try:
        requests.post(
            f"{BOT_URL}/sendChatAction",
            json={"chat_id": AUTHORIZED, "action": "typing"},
            timeout=4,
        )
    except Exception:
        pass


def _api_get(path: str) -> dict:
    r = requests.get(f"{API_BASE}{path}", headers=_headers(), timeout=15)
    r.raise_for_status()
    return r.json()


def _api_post(path: str, body: dict | None = None) -> dict:
    r = requests.post(f"{API_BASE}{path}", headers=_headers(), json=body or {}, timeout=60)
    if not r.ok:
        try:
            detail = r.json().get("detail", r.text)
        except Exception:
            detail = r.text
        raise Exception(detail)
    return r.json()


def _refresh_action_map(chat_id: str) -> None:
    """Fetch pending actions and rebuild number→action_id mapping for this chat."""
    data = _api_get("/pending")
    pending = data.get("pending", [])
    _action_map[chat_id] = {i + 1: a["action_id"] for i, a in enumerate(pending)}
    return pending


def handle(text: str) -> None:
    raw = text.strip()
    if not raw:
        return
    parts = raw.split()
    cmd = parts[0].lower()
    chat_id = AUTHORIZED

    # ── Help ──
    if cmd in ("/help", "/start"):
        send(
            "Nexus — Control Remoto\n\n"
            "/status — estado del sistema\n"
            "/pending — acciones pendientes (numeradas)\n"
            "/approve N [confirm] — aprobar acción\n"
            "/reject N [motivo] — rechazar acción\n"
            "/run — pipeline completo\n"
            "/run <agente> — ejecutar un agente\n"
            "/agents — lista de agentes disponibles\n"
            "/tamper — simular tamper en ledger de memoria\n"
            "/reset — restaurar ledger de memoria\n"
            "texto libre — tarea para CEO Agent"
        )
        return

    # ── Tamper ──
    if cmd == "/tamper":
        send("⚠️ Ejecutando simulación de tamper (adulterando ledger)...")
        try:
            result = _api_post("/tamper")
            if result.get("success"):
                send("🔥 Tamper completado. El primer registro del ledger de memoria fue adulterado en la base de datos de SQLite directamente.")
            else:
                send(f"❌ Error al adulterar ledger: {result.get('error')}")
        except Exception as e:
            send(f"❌ Error: {e}")
        return

    # ── Reset ──
    if cmd == "/reset":
        send("🔄 Restaurando ledger a estado inicial...")
        try:
            result = _api_post("/reset")
            if result.get("success"):
                send("✅ Ledger restaurado y verificado. Todo verde.")
            else:
                send(f"❌ Error al restaurar ledger: {result.get('error')}")
        except Exception as e:
            send(f"❌ Error: {e}")
        return

    typing()

    # ── Status ──
    if cmd == "/status":
        try:
            st = _api_get("/status")
        except Exception as e:
            send(f"Error al conectar con dashboard: {e}")
            return
        agents = st.get("agents", {})
        lines = [f"🎛️ {st.get('orchestrator', 'Cerno')} — {st.get('total_runs', 0)} runs"]
        for aid, a in agents.items():
            icon = a.get("icon", "•")
            name = a.get("name", aid)[:18]
            state = a.get("state", "?")[:16]
            lines.append(f"  {icon} {name:18s} {state}")
        lines.append(f"\n⏳ Pendientes: {st.get('pending_count', 0)}")
        lines.append(f"📚 Historial: {st.get('total_history', 0)}")
        send("\n".join(lines))
        return

    # ── Pending ──
    if cmd == "/pending":
        try:
            pending = _refresh_action_map(chat_id)
        except Exception as e:
            send(f"Error: {e}")
            return
        if not pending:
            send("✅ Sin acciones pendientes.")
            return
        lines = [f"📋 {len(pending)} pendientes:"]
        for i, a in enumerate(pending, 1):
            atype = a.get("action_type", "?")
            target = a.get("target", "")[:30]
            score = a.get("score", 0)
            lines.append(f"  {i}. [{score}] {atype} → {target}")
        send("\n".join(lines))
        return

    # ── Approve ──
    if cmd == "/approve":
        _handle_approve(chat_id, parts)
        return

    # ── Reject ──
    if cmd == "/reject":
        _handle_reject(chat_id, parts)
        return

    # ── Run (all or single agent) ──
    if cmd == "/run":
        _handle_run(parts)
        return

    # ── Agents list ──
    if cmd == "/agents":
        send("Agentes disponibles:\n" + "\n".join(f"  • {a}" for a in AGENTS_LIST))
        return

    # ── Free text → CEO task ──
    _handle_task(raw)


def _handle_approve(chat_id: str, parts: list[str]) -> None:
    if len(parts) < 2 or not parts[1].isdigit():
        send("Uso: /approve N [confirm]\nEj: /approve 1  (muestra preview)")
        return
    idx = int(parts[1])
    is_confirm = len(parts) >= 3 and parts[2].lower() == "confirm"

    # If we have a pending confirmation and this matches, execute
    if is_confirm and chat_id in _pending_confirm:
        pc = _pending_confirm[chat_id]
        if pc.get("index") == idx:
            try:
                result = _api_post(f"/approve/{pc['action_id']}", {"comment": ""})
                if result.get("success"):
                    send(f"✅ Aprobado: {pc['label']}")
                else:
                    send(f"⚠️ Error al aprobar: {result}")
                del _pending_confirm[chat_id]
                return
            except Exception as e:
                send(f"❌ Error: {e}")
                del _pending_confirm[chat_id]
                return

    # Refresh mapping and find the action
    try:
        pending = _refresh_action_map(chat_id)
    except Exception as e:
        send(f"Error: {e}")
        return

    if idx < 1 or idx > len(pending):
        send(f"Índice inválido. /pending para ver acciones (1-{len(pending)}).")
        return

    action = pending[idx - 1]
    action_id = action["action_id"]
    label = f"{action.get('action_type', '?')} → {action.get('target', '')[:40]}"
    _pending_confirm[chat_id] = {
        "action": "approve",
        "index": idx,
        "action_id": action_id,
        "label": label,
    }
    send(
        f"⚠️ ¿Aprobar?\n"
        f"  {label}\n\n"
        f"Respondé: /approve {idx} confirm\n"
        f"O enviá otro comando para cancelar."
    )


def _handle_reject(chat_id: str, parts: list[str]) -> None:
    if len(parts) < 2 or not parts[1].isdigit():
        send("Uso: /reject N [motivo]\nEj: /reject 1 perfil no encaja")
        return
    idx = int(parts[1])
    comment = " ".join(parts[2:]) if len(parts) > 2 else ""

    try:
        pending = _refresh_action_map(chat_id)
    except Exception as e:
        send(f"Error: {e}")
        return

    if idx < 1 or idx > len(pending):
        send(f"Índice inválido. /pending para ver acciones (1-{len(pending)}).")
        return

    action = pending[idx - 1]
    action_id = action["action_id"]
    label = f"{action.get('action_type', '?')} → {action.get('target', '')[:40]}"

    try:
        result = _api_post(f"/reject/{action_id}", {"comment": comment})
        if result.get("success"):
            msg = f"❌ Rechazado: {label}"
            if comment:
                msg += f"\n   Motivo: {comment}"
            send(msg)
        else:
            send(f"⚠️ Error al rechazar: {result}")
    except Exception as e:
        send(f"❌ Error: {e}")


def _handle_run(parts: list[str]) -> None:
    if len(parts) >= 2:
        agent = parts[1].lower()
        if agent not in AGENTS_LIST:
            send(f"Agente '{agent}' no reconocido. /agents para lista.")
            return
        send(f"▶️ Ejecutando {agent}...")
        try:
            result = _api_post(f"/run/{agent}")
            n = result.get("actions", 0)
            send(f"✅ {agent}: {n} acciones generadas.")
        except Exception as e:
            send(f"❌ Error: {e}")
        return

    send("▶️ Ejecutando pipeline completo...")
    try:
        result = _api_post("/run-all")
        parts_list = [f"{k}: {v}" for k, v in result.items()]
        send(f"✅ Pipeline completo.\n" + "\n".join(parts_list))
    except Exception as e:
        send(f"❌ Error: {e}")


def _handle_task(task_text: str) -> None:
    send("🧠 Procesando tarea para CEO...")
    try:
        result = _api_post("/ceo/task", {"task": task_text})
        response = (
            result.get("response")
            or result.get("output")
            or result.get("summary")
            or json.dumps(result, ensure_ascii=False)
        )
        send(str(response)[:400])
    except Exception as e:
        send(f"❌ Error: {e}")


def main() -> None:
    if not settings.telegram_bot_token or not settings.telegram_chat_id:
        print("ERROR: faltan TELEGRAM_BOT_TOKEN o TELEGRAM_CHAT_ID en .env")
        sys.exit(1)

    print(f"[NEXUS BOT] Arrancando — chat_id: {AUTHORIZED}")
    print(f"[NEXUS BOT] API: {API_BASE}")
    send("Nexus Bot conectado. /help para comandos.")

    offset = None
    while True:
        try:
            params: dict = {"timeout": 10, "allowed_updates": ["message"]}
            if offset:
                params["offset"] = offset
            r = requests.get(f"{BOT_URL}/getUpdates", params=params, timeout=15)
            data = r.json()

            for upd in data.get("result", []):
                offset = upd["update_id"] + 1
                msg = upd.get("message", {})
                text = msg.get("text", "").strip()
                chat_id = str(msg.get("chat", {}).get("id", ""))

                if not text:
                    continue
                if chat_id != AUTHORIZED:
                    continue

                print(f"[BOT] {text!r}")
                handle(text)

        except KeyboardInterrupt:
            print("\n[NEXUS BOT] Detenido.")
            break
        except Exception as e:
            print(f"[ERROR] {e}")
            time.sleep(3)


if __name__ == "__main__":
    main()
