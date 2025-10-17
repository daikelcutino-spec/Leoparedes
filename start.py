#!/usr/bin/env python3
import os
import subprocess
import threading
from flask import Flask

app = Flask(__name__)

@app.route('/')
def home():
    return '¡Bots vivos!'

def start_main_bot():
    """Inicia el bot principal (main.py)"""
    api_token = os.getenv("HIGHRISE_API_TOKEN", "")
    room_id = os.getenv("HIGHRISE_ROOM_ID", "")
    
    if not api_token or not room_id:
        print("❌ Error: Faltan credenciales (HIGHRISE_API_TOKEN o HIGHRISE_ROOM_ID)")
        return
    
    print("🤖 Iniciando bot principal...")
    cmd = ["highrise", "main:Bot", room_id, api_token]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[MAIN BOT] {line.rstrip()}")

def start_cantinero_bot():
    """Inicia el bot cantinero (cantinero_bot.py)"""
    api_token = os.getenv("CANTINERO_API_TOKEN", "")
    room_id = os.getenv("HIGHRISE_ROOM_ID", "")
    
    if not api_token or not room_id:
        print("❌ Error: Faltan credenciales (CANTINERO_API_TOKEN o HIGHRISE_ROOM_ID)")
        return
    
    print("🍻 Iniciando bot cantinero...")
    cmd = ["highrise", "cantinero_bot:BartenderBot", room_id, api_token]
    process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    if process.stdout:
        for line in iter(process.stdout.readline, ''):
            if line:
                print(f"[CANTINERO BOT] {line.rstrip()}")

def run_flask():
    """Ejecuta el servidor Flask en puerto 5000"""
    print("🌐 Iniciando servidor Flask en puerto 5000...")
    app.run(host='0.0.0.0', port=5000)

if __name__ == "__main__":
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA DUAL DE BOTS")
    print("=" * 60)
    
    main_bot_thread = threading.Thread(target=start_main_bot, daemon=True)
    cantinero_bot_thread = threading.Thread(target=start_cantinero_bot, daemon=True)
    
    main_bot_thread.start()
    cantinero_bot_thread.start()
    
    run_flask()
