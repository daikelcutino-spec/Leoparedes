import asyncio
import json
import subprocess
import sys
import threading
import time
import os
from flask import Flask

# ======================================================
# 🚀 Servidor Web requerido por KOYEB para evitar shutdown
# ======================================================
app = Flask(__name__)

@app.route("/")
def home():
    return "Bots Highrise corriendo en Koyeb!"

def run_web():
    port = int(os.environ.get("PORT", 8080))
    app.run(host="0.0.0.0", port=port)

def start_web():
    t = threading.Thread(target=run_web, daemon=True)
    t.start()

# ======================================================

def load_config(config_file):
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando {config_file}: {e}")
        return None

def run_bot(bot_name, bot_file, room_id, api_token):
    print(f"\n{'='*60}")
    print(f"🤖 Iniciando {bot_name}")
    print(f"{'='*60}\n")
    
    cmd = [
        sys.executable,
        "-m",
        "highrise",
        bot_file,
        room_id,
        api_token
    ]
    
    process = None
    while True:
        try:
            process = subprocess.Popen(
                cmd,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
                text=True,
                bufsize=1
            )
            
            if process.stdout:
                for line in process.stdout:
                    print(f"[{bot_name}] {line}", end='')
            
            process.wait()
            
            if process.returncode != 0:
                print(f"\n❌ {bot_name} terminó con código {process.returncode}")
                print(f"🔄 Reiniciando {bot_name} en 5 segundos...")
                time.sleep(5)
            else:
                print(f"\n✅ {bot_name} terminó normalmente")
                break
                
        except Exception as e:
            print(f"\n❌ Error en {bot_name}: {e}")
            print(f"🔄 Reiniciando {bot_name} en 5 segundos...")
            time.sleep(5)

def main():
    print("\n" + "="*60)
    print("🕷️  NOCTURNO BOTS LAUNCHER (KOYEB READY) 🕷️")
    print("="*60 + "\n")

    # 🔥 IMPORTANTE: Mantiene vivo el servicio en KOYEB
    start_web()

    config_main = load_config("config.json")
    config_cantinero = load_config("cantinero_config.json")

    if not config_main or not config_cantinero:
        print("❌ Error en los archivos de configuración")
        return

    api_token_main = config_main.get("api_token")
    room_id_main = config_main.get("room_id")

    api_token_cantinero = config_cantinero.get("api_token")
    room_id_cantinero = config_cantinero.get("room_id", room_id_main)

    thread1 = threading.Thread(
        target=run_bot,
        args=("Bot Principal", "main:Bot", room_id_main, api_token_main),
        daemon=True
    )
    
    thread2 = threading.Thread(
        target=run_bot,
        args=("Bot Cantinero", "cantinero_bot:BartenderBot", room_id_cantinero, api_token_cantinero),
        daemon=True
    )

    thread1.start()
    thread2.start()
    
    print("🚀 Ambos bots están corriendo en Koyeb 24/7\n")

    while True:
        time.sleep(1)

if __name__ == "__main__":
    main()
