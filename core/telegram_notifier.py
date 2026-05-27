import os
import requests
import json
from datetime import datetime, timezone

class TelegramNotifier:
    def __init__(self, bot_token: str | None = None, chat_id: str | None = None):
        # Read from config/env or fall back
        self.bot_token = bot_token or os.getenv("TELEGRAM_BOT_TOKEN", "")
        self.chat_id = chat_id or os.getenv("TELEGRAM_CHAT_ID", "")
        self.enabled = bool(self.bot_token and self.chat_id)

    def send_raw_message(self, text: str) -> bool:
        if not self.enabled:
            print(f"\n[MOCK TELEGRAM NOTIFICATION] Text:\n{text}\n")
            return False
        
        url = f"https://api.telegram.org/bot{self.bot_token}/sendMessage"
        payload = {
            "chat_id": self.chat_id,
            "text": text,
            "parse_mode": "Markdown"
        }
        
        try:
            r = requests.post(url, json=payload, timeout=5)
            return r.status_code == 200
        except Exception as e:
            print(f"[TELEGRAM ERROR] No se pudo enviar mensaje: {e}")
            return False

    def send_signal_alert(self, agent_name: str, candidate_name: str, role: str, signals: list[str], validation_questions: list[str], confidence: str = "media-alta") -> bool:
        emoji_map = {
            "talent_signal": "🔍",
            "career_context": "🏢",
            "demand_radar": "🎯",
            "outreach": "✉️"
        }
        emoji = emoji_map.get(agent_name.lower(), "🤖")
        
        title = f"{emoji} *[EJÉRCITO DE AGENTES - {agent_name.upper()}]*"
        timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
        
        body = (
            f"{title}\n"
            f"📅 Hora: `{timestamp}` UTC | Confianza: `{confidence.upper()}`\n\n"
            f"👤 *Candidato Cazado:* `{candidate_name}`\n"
            f"💼 *Posición:* `{role}`\n\n"
            f"📝 *Señales Observables:*\n"
        )
        
        for s in signals[:3]:
            body += f"• {s}\n"
            
        body += "\n❓ *Preguntas de Validación (para Rodri):*\n"
        for q in validation_questions[:2]:
            body += f"_\" {q} \"_\n"
            
        body += (
            f"\n⚡ *Borrador de contacto listo en el Dashboard de Global Executive.*"
        )
        
        return self.send_raw_message(body)

    def send_tamper_alarm(self, block_id: str, detail: str) -> bool:
        timestamp = datetime.now(timezone.utc).strftime('%H:%M:%S')
        body = (
            f"🚨 *[S.O.S. - SISTEMA DE DEFENSA DE MEMORIA]* 🚨\n"
            f"⚠️ *¡INTENTO DE INTRUSIÓN DETECTADO!* ⚠️\n\n"
            f"🔴 *Bloque Afectado:* `{block_id}`\n"
            f"⏰ *Hora del Incidente:* `{timestamp}` UTC\n\n"
            f"🔍 *Detalle Forense:* _La cadena de hashes de memoria se rompió en este punto. Alguien editó manualmente la base de datos o el modelo intentó inyectar datos falsos._\n\n"
            f"🚫 *ACCIÓN CORRECTIVA:* El pipeline de envío de mensajes en LinkedIn ha sido **CONGELADO** automáticamente para proteger la marca y la reputación de Global Executive.\n\n"
            f"👉 _Revisa el centro de control para auditar el hash chain._"
        )
        return self.send_raw_message(body)
