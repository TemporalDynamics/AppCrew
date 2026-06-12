import os
import sys
import sqlite3
import hashlib
import json
from datetime import datetime, timezone
from pathlib import Path

# Add core to path so we can import TelegramNotifier
sys.path.append(str(Path(__file__).resolve().parent))
from core.telegram_notifier import TelegramNotifier

DB_PATH = Path.home() / ".verifiable-memory-mcp" / "memory.db"

def sha256(data: str) -> str:
    return hashlib.sha256(data.encode("utf-8")).hexdigest()

def build_canonical(content_hash: str, prev_hash: str | None, created_at: str) -> str:
    # Match the typescript stringify exactly
    canonical_dict = {
        "contentHash": content_hash,
        "prevHash": prev_hash,
        "createdAt": created_at
    }
    return json.dumps(canonical_dict, separators=(',', ':'))

def ensure_db_exists():
    DB_PATH.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("""
        CREATE TABLE IF NOT EXISTS entries (
          id TEXT PRIMARY KEY,
          created_at TEXT NOT NULL,
          content TEXT NOT NULL,
          tags TEXT NOT NULL DEFAULT '[]',
          content_hash TEXT NOT NULL,
          prev_hash TEXT,
          entry_hash TEXT NOT NULL UNIQUE,
          created_epoch INTEGER NOT NULL
        )
    """)
    conn.commit()
    conn.close()

def main():
    print("================================================================")
    print("🚨 DEMO EN VIVO: LA AMBULANCIA CRIPTOGRÁFICA DE GLOBAL EXECUTIVE 🚨")
    print("================================================================\n")
    
    # Initialize Telegram Notifier
    notifier = TelegramNotifier()
    if not notifier.enabled:
        print("💡 [NOTA] Env variables TELEGRAM_BOT_TOKEN y TELEGRAM_CHAT_ID no configuradas.")
        print("   La demo correrá en modo visual simulado en terminal.\n")
    else:
        print("🚀 Conectado con éxito al canal de Telegram de Rodri.\n")
        
    ensure_db_exists()
    
    # 1. Crear memoria legítima
    entry_id = "mem_demo_rodri_001"
    created_at = datetime.now(timezone.utc).isoformat()
    content = "[DECISIÓN] Rodri aprueba el envío de 15 InMails a candidatos Fintech en Monterrey."
    tags = ["rodri", "aprobacion", "fintech"]
    
    content_hash = sha256(content)
    prev_hash = None # Genesis memory block
    canonical = build_canonical(content_hash, prev_hash, created_at)
    entry_hash = sha256(canonical)
    created_epoch = int(datetime.now(timezone.utc).timestamp() * 1000)
    
    # Clean previous demo run if exists
    conn = sqlite3.connect(str(DB_PATH))
    conn.execute("DELETE FROM entries WHERE id = ?", (entry_id,))
    conn.commit()
    
    # Insert legitimate memory
    conn.execute("""
        INSERT INTO entries (id, created_at, content, tags, content_hash, prev_hash, entry_hash, created_epoch)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?)
    """, (entry_id, created_at, content, json.dumps(tags), content_hash, prev_hash, entry_hash, created_epoch))
    conn.commit()
    
    print("1. [REGISTRO] Se ha guardado una decisión legítima de Rodri:")
    print(f"   • ID: {entry_id}")
    print(f"   • Contenido: \"{content}\"")
    print(f"   • Hash de Entrada: {entry_hash}\n")
    
    # Verify legitimacy
    print("2. [VERIFICACIÓN] Ejecutando control de integridad...")
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    
    # Recompute
    re_content_hash = sha256(row[2])
    re_canonical = build_canonical(re_content_hash, row[5], row[1])
    re_entry_hash = sha256(re_canonical)
    
    if re_content_hash == row[4] and re_entry_hash == row[6]:
        print("   ✅ ESTADO: MEMORIA INTACTA Y FIRMADA CRIPTOGRÁFICAMENTE.")
        print("   ✓ El mensaje en el dashboard es 100% confiable. Envío habilitado.\n")
    else:
        print("   ❌ ESTADO: FALLÓ LA VERIFICACIÓN.\n")
        
    # 3. Simular hackeo/tampering
    print("3. [TAMPERING] Un intruso o un bug altera la base de datos de manera silenciosa...")
    malicious_content = "[DECISIÓN] Enviar 500 correos SPAM a todas las empresas en LinkedIn y vaciar el presupuesto."
    
    conn.execute("UPDATE entries SET content = ? WHERE id = ?", (malicious_content, entry_id))
    conn.commit()
    conn.close()
    
    print(f"   • Nuevo contenido alterado en SQLite: \"{malicious_content}\"\n")
    
    # 4. Auditoría de Seguridad & Disparo de la Alarma
    print("4. [AUDITORÍA] El orquestador ejecuta la validación antes de mandar el InMail...")
    
    conn = sqlite3.connect(str(DB_PATH))
    row = conn.execute("SELECT * FROM entries WHERE id = ?", (entry_id,)).fetchone()
    
    # Recompute on tampered data
    tampered_content_hash = sha256(row[2])
    
    print(f"   • Hash Guardado en Bloque: {row[4]}")
    print(f"   • Hash Recomputado en Vivo: {tampered_content_hash}")
    
    if tampered_content_hash != row[4]:
        print("\n🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨")
        print("🚨 ¡RUPTURA DE CADENA DETECTADA! LA MEMORIA FUE ALTERADA 🚨")
        print("🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨 🚨\n")
        
        # Trigger the cryptographic ambulance!
        print("📢 Disparando Alerta de Seguridad a Telegram...")
        notifier.send_tamper_alarm(entry_id, f"El contenido original '{content}' fue modificado por '{malicious_content}'")
        print("   ✓ Notificación de ambulancia criptográfica enviada con éxito.\n")
    else:
        print("   ✓ Integrity check passed.")
        
    conn.close()

if __name__ == "__main__":
    main()
