
from flask import Flask, render_template, request, jsonify, redirect, url_for
import json
import os
from datetime import datetime

app = Flask(__name__)

# Cargar configuración
def load_config():
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return {}

# Cargar datos de usuarios
def load_user_data():
    data = {
        "vip_users": set(),
        "hearts": {},
        "activity": {}
    }
    
    # Cargar VIP
    if os.path.exists("data/vip.txt"):
        with open("data/vip.txt", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    data["vip_users"].add(line.strip())
    
    # Cargar corazones
    if os.path.exists("data/hearts.txt"):
        with open("data/hearts.txt", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    parts = line.strip().split(":")
                    if len(parts) >= 3:
                        data["hearts"][parts[2]] = int(parts[1])
    
    # Cargar actividad
    if os.path.exists("data/activity.txt"):
        with open("data/activity.txt", "r", encoding="utf-8") as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    parts = line.strip().split(":")
                    if len(parts) >= 4:
                        data["activity"][parts[3]] = int(parts[1])
    
    return data

@app.route('/')
def index():
    config = load_config()
    user_data = load_user_data()
    
    # Top 10 por corazones
    top_hearts = sorted(user_data["hearts"].items(), key=lambda x: x[1], reverse=True)[:10]
    
    # Top 10 por actividad
    top_activity = sorted(user_data["activity"].items(), key=lambda x: x[1], reverse=True)[:10]
    
    return render_template('index.html', 
                         config=config,
                         vip_count=len(user_data["vip_users"]),
                         total_hearts=sum(user_data["hearts"].values()),
                         top_hearts=top_hearts,
                         top_activity=top_activity)

@app.route('/vip')
def vip_management():
    user_data = load_user_data()
    return render_template('vip.html', vip_users=sorted(user_data["vip_users"]))

@app.route('/api/add_vip', methods=['POST'])
def add_vip():
    username = request.form.get('username', '').strip()
    if not username:
        return jsonify({"success": False, "message": "Nombre de usuario vacío"})
    
    try:
        user_data = load_user_data()
        if username in user_data["vip_users"]:
            return jsonify({"success": False, "message": "Usuario ya es VIP"})
        
        # Agregar a archivo
        with open("data/vip.txt", "a", encoding="utf-8") as f:
            f.write(f"{username}\n")
        
        return jsonify({"success": True, "message": f"{username} agregado como VIP"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/remove_vip', methods=['POST'])
def remove_vip():
    username = request.form.get('username', '').strip()
    if not username:
        return jsonify({"success": False, "message": "Nombre de usuario vacío"})
    
    try:
        user_data = load_user_data()
        if username not in user_data["vip_users"]:
            return jsonify({"success": False, "message": "Usuario no es VIP"})
        
        # Reescribir archivo sin el usuario
        user_data["vip_users"].discard(username)
        with open("data/vip.txt", "w", encoding="utf-8") as f:
            f.write("# Usuarios VIP (un username por línea)\n")
            for vip_user in sorted(user_data["vip_users"]):
                f.write(f"{vip_user}\n")
        
        return jsonify({"success": True, "message": f"{username} removido de VIP"})
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})

@app.route('/api/stats')
def get_stats():
    user_data = load_user_data()
    return jsonify({
        "vip_count": len(user_data["vip_users"]),
        "total_hearts": sum(user_data["hearts"].values()),
        "total_users": len(user_data["hearts"]),
        "active_users": len(user_data["activity"])
    })

if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
