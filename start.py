import os
import asyncio
import importlib
from threading import Thread
from flask import Flask
from highrise import BaseBot

# Intenta importar las clases de los bots
try:
    main_bot = importlib.import_module("main").Bot  # Ajusta si la clase no es "Bot"
except (ImportError, AttributeError) as e:
    print(f"❌ Error al importar el bot principal (main.py): {e}")
    main_bot = None

try:
    cantinero_bot = importlib.import_module("cantinero_bot").BartenderBot  # Ajusta si la clase no es "BartenderBot"
except (ImportError, AttributeError) as e:
    print(f"❌ Error al importar el bot cantinero (cantinero_bot.py): {e}")
    cantinero_bot = None

# Configura Flask
app = Flask(__name__)

@app.route('/')
def home():
    return "¡Bots vivos!"

def run_flask():
    print("🌐 Iniciando servidor Flask en puerto 8080...")
    app.run(host='0.0.0.0', port=8080)

# Función para correr un bot
async def run_bot(bot_class, token, room_id, bot_name):
    if bot_class is None:
        print(f"❌ No se puede iniciar {bot_name}: clase no importada correctamente")
        return
    bot = bot_class()
    print(f"🤖 Iniciando bot {bot_name} ({bot_class.__name__})...")
    try:
        await bot.run(token, room_id)
    except Exception as e:
        print(f"❌ Error en bot {bot_name}: {e}")

# Función principal para iniciar ambos bots
async def main():
    # Obtén tokens y room ID desde variables de entorno
    main_token = os.getenv("HIGHRISE_API_TOKEN")
    cantinero_token = os.getenv("CANTINERO_API_TOKEN")
    room_id = os.getenv("HIGHRISE_ROOM_ID")

    if not main_token or not cantinero_token or not room_id:
        print("❌ Error: Faltan credenciales (HIGHRISE_API_TOKEN, CANTINERO_API_TOKEN o HIGHRISE_ROOM_ID)")
        return

    # Inicia ambos bots en la misma habitación
    tasks = []
    if main_bot:
        tasks.append(asyncio.create_task(run_bot(main_bot, main_token, room_id, "Bot principal")))
    if cantinero_bot:
        tasks.append(asyncio.create_task(run_bot(cantinero_bot, cantinero_token, room_id, "Bot cantinero")))
    
    if not tasks:
        print("❌ Error: No se pudo iniciar ningún bot")
        return
    
    await asyncio.gather(*tasks)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA DUAL DE BOTS")
    print("=" * 60)

    # Inicia Flask en un hilo separado
    flask_thread = Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Inicia los bots
    asyncio.run(main())