import asyncio
import json
import subprocess
import sys
import threading
import time
import os

# ------------------------------
# SERVIDOR WEB PARA KOYEB
# ------------------------------
from flask import Flask

app = Flask(__name__)

@app.route("/")
def home():
    return "Bots Highrise corriendo en Koyeb!"

def start_web():
    """Inicia un servidor web para que Koyeb no cierre la app."""
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port)


# ------------------------------
# CARGA DE CONFIGURACIONES
# ------------------------------
def load_config(config_file):
    """Carga la configuración desde un archivo JSON"""
    try:
        with open(config_file, "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando {config_file}: {e}")
        return None


# ------------------------------
# EJECUCIÓN DE BOTS HIGHRISE
# ------------------------------
def run_bot(bot_name, bot_file, room_id, api_token):
    """Ejecuta un bot usando el SDK de Highrise"""
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
                
        except KeyboardInterrupt:
            print(f"\n⚠️ Deteniendo {bot_name}...")
            if process:
                process.kill()
            break
        except Exception as e:
            print(f"\n❌ Error en {bot_name}: {e}")
            print(f"🔄 Reiniciando {bot_name} en 5 segundos...")
            time.sleep(5)


# ------------------------------
# PROCESO PRINCIPAL
# ------------------------------
def main():
    print("\n" + "="*60)
    print("🕷️  NOCTURNO BOTS LAUNCHER 🕷️")
    print("="*60 + "\n")
    
    config_main = load_config("config.json")
    config_cantinero = load_config("cantinero_config.json")
    
    if not config_main:
        print("❌ Error: No se pudo cargar config.json")
        print("📝 Debe contener api_token y room_id")
        return
    
    if not config_cantinero:
        print("❌ Error: No se pudo cargar cantinero_config.json")
        print("📝 Debe contener api_token y (opcional) room_id")
        return
    
    api_token_main = config_main.get("api_token")
    room_id_main = config_main.get("room_id")
    
    api_token_cantinero = config_cantinero.get("api_token")
    room_id_cantinero = config_cantinero.get("room_id", room_id_main)
    
    if not api_token_main or not room_id_main:
        print("❌ Error: config.json debe contener 'api_token' y 'room_id'")
        return
    
    if not api_token_cantinero:
        print("❌ Error: cantinero_config.json debe contener 'api_token'")
        return
    
    print("✅ Configuración cargada correctamente\n")
    print("📋 Bots a ejecutar:")
    print(f"   1. Bot Principal (main.py)")
    print(f"   2. Bot Cantinero (cantinero_bot.py)")
    print(f"\n🔗 Sala: {room_id_main}\n")
    
    # Detectar Replit (no pedir Enter)
    is_replit = os.getenv('REPL_ID') is not None or os.getenv('REPLIT_DB_URL') is not None
    
    if not is_replit:
        input("Presiona ENTER para iniciar los bots...")
    else:
        print("🚀 Iniciando bots automáticamente...")
    
    # Hilos para los bots
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
    
    print("\n" + "="*60)
    print("🚀 Ambos bots están corriendo")
    print("⚠️  Presiona Ctrl+C para detener todos los bots (si estás en PC)")
    print("="*60 + "\n")
    
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        print("\n\n" + "="*60)
        print("⛔ Deteniendo todos los bots...")
        print("="*60 + "\n")
        print("✅ Bots detenidos correctamente")
        print("👋 ¡Hasta pronto!\n")


# ------------------------------
# INICIO DEL PROGRAMA
# ------------------------------
if __name__ == "__main__":
    # Servidor web para Koyeb
    web_thread = threading.Thread(target=start_web, daemon=True)
    web_thread.start()

    # Iniciar launcher
    main()
