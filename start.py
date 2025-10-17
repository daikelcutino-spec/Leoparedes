
import os
import subprocess
from threading import Thread
from flask import Flask

# Configura Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "¡Bots vivos!"

def run_flask():
    print("🌐 Iniciando servidor Flask en puerto 8080...")
    app.run(host='0.0.0.0', port=8080)

def run_main_bot():
    """Ejecuta el bot principal usando subprocess"""
    token = os.getenv("HIGHRISE_API_TOKEN")
    room_id = os.getenv("HIGHRISE_ROOM_ID")
    
    if not token or not room_id:
        print("❌ Error: Faltan HIGHRISE_API_TOKEN o HIGHRISE_ROOM_ID")
        return
    
    print(f"🤖 Iniciando bot principal...")
    try:
        subprocess.run([
            "python", "-m", "highrise", 
            "main:Bot", 
            room_id, 
            token
        ])
    except Exception as e:
        print(f"❌ Error en bot principal: {e}")

def run_cantinero_bot():
    """Ejecuta el bot cantinero usando subprocess"""
    token = os.getenv("CANTINERO_API_TOKEN")
    room_id = os.getenv("HIGHRISE_ROOM_ID")
    
    if not token or not room_id:
        print("❌ Error: Faltan CANTINERO_API_TOKEN o HIGHRISE_ROOM_ID")
        return
    
    print(f"🤖 Iniciando bot cantinero...")
    try:
        subprocess.run([
            "python", "-m", "highrise", 
            "cantinero_bot:BartenderBot", 
            room_id, 
            token
        ])
    except Exception as e:
        print(f"❌ Error en bot cantinero: {e}")

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA DUAL DE BOTS")
    print("=" * 60)

    # Inicia Flask en un hilo separado
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Inicia ambos bots en hilos separados
    main_bot_thread = Thread(target=run_main_bot, daemon=False)
    cantinero_bot_thread = Thread(target=run_cantinero_bot, daemon=False)
    
    main_bot_thread.start()
    cantinero_bot_thread.start()
    
    # Esperar a que los bots terminen (nunca deberían terminar en operación normal)
    main_bot_thread.join()
    cantinero_bot_thread.join()
