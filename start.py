import os
import subprocess
from threading import Thread
from flask import Flask
import time
import socket

# === FLASK RÁPIDO (URL PÚBLICA INMEDIATA) ===
app = Flask(__name__)

@app.route('/')
def home():
    return f"""
    <h1> BOT DUAL 24/7</h1>
    <p>Principal + Cantinero</p>
    <p>URL: <code>{os.environ.get('REPL_SLUG')}--{os.environ.get('REPL_OWNER')}.repl.co</code></p>
    <p>Auto-hosting GRATIS</p>
    """

# === AUTO-PING INTERNO (MANTIENE VIVO) ===
def auto_ping():
    while True:
        try:
            s = socket.create_connection(("8.8.8.8", 53), timeout=5)
            s.close()
        except:
            pass
        time.sleep(60)

# === BOTS EN BUCLE ===
def run_bot(cmd, name):
    while True:
        try:
            print(f"{name} iniciado")
            subprocess.Popen(cmd).wait()
            print(f"{name} caído. Reiniciando...")
            time.sleep(5)
        except Exception as e:
            print(f"Error: {e}")
            time.sleep(5)

# === INICIO ===
if __name__ == "__main__":
    print("INICIANDO AUTO-HOSTING 24/7...")

    # Flask (URL pública)
    Thread(target=lambda: app.run(
        host='0.0.0.0',
        port=int(os.environ.get('PORT', 8080)),
        debug=False,
        use_reloader=False
    ), daemon=True).start()

    # Auto-ping (mantiene vivo)
    Thread(target=auto_ping, daemon=True).start()

    # Bots
    token1 = os.getenv("HIGHRISE_API_TOKEN")
    room = os.getenv("HIGHRISE_ROOM_ID")
    if token1 and room:
        cmd1 = ["python", "-m", "highrise", "main:Bot", room, token1]
        Thread(target=run_bot, args=(cmd1, "Bot Principal")).start()

    token2 = os.getenv("CANTINERO_API_TOKEN")
    if token2 and room:
        cmd2 = ["python", "-m", "highrise", "cantinero_bot:BartenderBot", room, token2]
        Thread(target=run_bot, args=(cmd2, "Bot Cantinero")).start()

    # Mantener vivo
    while True:
        time.sleep(100)