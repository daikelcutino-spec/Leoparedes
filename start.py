#!/usr/bin/env python3
import subprocess
import json
import sys
import os
import time
import threading

def load_config():
    """Carga la configuración desde config.json y secrets (prioridad a secrets)"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        api_token_env = os.getenv("HIGHRISE_API_TOKEN", "")
        room_id_env = os.getenv("HIGHRISE_ROOM_ID", "")
        
        if api_token_env:
            config["api_token"] = api_token_env
        if room_id_env:
            config["room_id"] = room_id_env
        
        return config
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return {}

def start_bot():
    """Inicia el bot de Highrise usando subprocess"""
    config = load_config()
    room_id = config.get("room_id", "")
    api_token = config.get("api_token", "")
    
    if not room_id or not api_token:
        print("❌ Error: Faltan credenciales del bot")
        return
    
    print("🤖 Iniciando bot de Highrise...")
    print(f"   Room ID: {room_id}")
    print(f"   Token: {api_token[:10]}...{api_token[-10:]}")
    
    os.environ["HIGHRISE_API_TOKEN"] = api_token
    os.environ["HIGHRISE_ROOM_ID"] = room_id
    
    cmd = ["highrise", "main:Bot", room_id, api_token]
    bot_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    for line in iter(bot_process.stdout.readline, ''):
        if line:
            print(f"[BOT] {line.rstrip()}")

def start_web_panel():
    """Inicia el panel web"""
    print("🌐 Iniciando panel web...")
    subprocess.run(["python", "web_panel.py"])

if __name__ == "__main__":
    config = load_config()
    
    if not config.get("api_token"):
        print("❌ Error: No se encontró api_token")
        sys.exit(1)
    if not config.get("room_id"):
        print("❌ Error: No se encontró room_id")
        sys.exit(1)
    
    print("=" * 60)
    print("🚀 INICIANDO SISTEMA COMPLETO")
    print("=" * 60)
    print(f"🏠 Room ID: {config['room_id']}")
    print(f"🌐 Panel Web: http://0.0.0.0:5000")
    print("=" * 60)
    
    bot_thread = threading.Thread(target=start_bot, daemon=True)
    bot_thread.start()
    
    time.sleep(3)
    
    try:
        start_web_panel()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo servicios...")
        sys.exit(0)
