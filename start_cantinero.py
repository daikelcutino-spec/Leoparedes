#!/usr/bin/env python3
import subprocess
import json
import sys
import os

def load_cantinero_config():
    """Carga la configuración del bot cantinero desde secrets y config"""
    try:
        with open("cantinero_config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        
        api_token_env = os.getenv("CANTINERO_API_TOKEN", "")
        room_id_env = os.getenv("HIGHRISE_ROOM_ID", "")
        owner_id_env = os.getenv("OWNER_ID", "")
        admin_id_env = os.getenv("ADMIN_IDS", "")
        
        if api_token_env:
            config["api_token"] = api_token_env
        if room_id_env:
            config["room_id"] = room_id_env
        if owner_id_env:
            config["owner_id"] = owner_id_env
        if admin_id_env:
            admin_ids = [aid.strip() for aid in admin_id_env.split(",") if aid.strip()]
            if admin_ids:
                config["admin_id"] = admin_ids[0]
        
        return config
    except Exception as e:
        print(f"Error cargando configuración del cantinero: {e}")
        return {}

def start_cantinero():
    """Inicia el bot cantinero usando subprocess"""
    config = load_cantinero_config()
    room_id = config.get("room_id", "")
    api_token = config.get("api_token", "")
    
    if not room_id or not api_token:
        print("❌ Error: Faltan credenciales del bot cantinero")
        return
    
    print("🍻 Iniciando bot Cantinero NOCTURNO...")
    print(f"   Room ID: {room_id}")
    print(f"   Token: {api_token[:10]}...{api_token[-10:]}")
    
    cmd = ["highrise", "cantinero_bot:BartenderBot", room_id, api_token]
    bot_process = subprocess.Popen(cmd, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
    
    if bot_process.stdout:
        for line in iter(bot_process.stdout.readline, ''):
            if line:
                print(f"[CANTINERO] {line.rstrip()}")

if __name__ == "__main__":
    config = load_cantinero_config()
    
    if not config.get("api_token"):
        print("❌ Error: No se encontró CANTINERO_API_TOKEN")
        sys.exit(1)
    if not config.get("room_id"):
        print("❌ Error: No se encontró room_id")
        sys.exit(1)
    
    print("=" * 60)
    print("🍻 INICIANDO BOT CANTINERO NOCTURNO")
    print("=" * 60)
    print(f"🏠 Room ID: {config['room_id']}")
    print("=" * 60)
    
    try:
        start_cantinero()
    except KeyboardInterrupt:
        print("\n🛑 Deteniendo bot cantinero...")
        sys.exit(0)
