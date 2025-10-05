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
    data = {"vip_users": set(), "hearts": {}, "activity": {}, "user_info": {}}

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

    # Cargar info de usuarios
    if os.path.exists("data/user_info.json"):
        try:
            with open("data/user_info.json", "r", encoding="utf-8") as f:
                data["user_info"] = json.load(f)
        except:
            pass

    return data


def load_bot_inventory():
    """Carga el inventario del bot desde archivo JSON"""
    if os.path.exists("data/bot_inventory.json"):
        try:
            with open("data/bot_inventory.json", "r", encoding="utf-8") as f:
                return json.load(f)
        except:
            return []
    return []


def write_console_command(command):
    """Escribe un comando para que el bot lo ejecute"""
    try:
        with open("console_message.txt", "w", encoding="utf-8") as f:
            f.write(command)
        return True
    except:
        return False


@app.route('/')
def index():
    config = load_config()
    user_data = load_user_data()

    # Top 10 por corazones
    top_hearts = sorted(user_data["hearts"].items(),
                        key=lambda x: x[1],
                        reverse=True)[:10]

    # Top 10 por actividad
    top_activity = sorted(user_data["activity"].items(),
                          key=lambda x: x[1],
                          reverse=True)[:10]

    # Inventario del bot (primeros 10 items)
    bot_inventory = load_bot_inventory()[:10]

    # Estadísticas adicionales
    total_users = len(user_data["user_info"])
    total_messages = sum(user_data["activity"].values())
    avg_hearts = sum(user_data["hearts"].values()) / len(
        user_data["hearts"]) if user_data["hearts"] else 0

    return render_template('index.html',
                           config=config,
                           vip_count=len(user_data["vip_users"]),
                           total_hearts=sum(user_data["hearts"].values()),
                           total_users=total_users,
                           total_messages=total_messages,
                           avg_hearts=round(avg_hearts, 1),
                           top_hearts=top_hearts,
                           top_activity=top_activity,
                           bot_inventory=bot_inventory)


@app.route('/vip')
def vip_management():
    user_data = load_user_data()
    return render_template('vip.html',
                           vip_users=sorted(user_data["vip_users"]))


@app.route('/users')
def users_list():
    user_data = load_user_data()

    # Combinar toda la información de usuarios
    users_combined = []
    for username in set(
            list(user_data["hearts"].keys()) +
            list(user_data["activity"].keys())):
        user_info = {
            "username": username,
            "hearts": user_data["hearts"].get(username, 0),
            "messages": user_data["activity"].get(username, 0),
            "is_vip": username in user_data["vip_users"]
        }
        users_combined.append(user_info)

    # Ordenar por corazones
    users_combined.sort(key=lambda x: x["hearts"], reverse=True)

    return render_template('users.html', users=users_combined)


@app.route('/analytics')
def analytics():
    user_data = load_user_data()

    # Preparar datos para gráficos
    hearts_data = sorted(user_data["hearts"].items(),
                         key=lambda x: x[1],
                         reverse=True)[:15]
    activity_data = sorted(user_data["activity"].items(),
                           key=lambda x: x[1],
                           reverse=True)[:15]

    return render_template('analytics.html',
                           hearts_data=hearts_data,
                           activity_data=activity_data)


@app.route('/inventory')
def inventory():
    bot_inventory = load_bot_inventory()

    # Contar items por tipo
    item_counts = {"clothing": 0, "furniture": 0, "emote": 0, "other": 0}

    for item in bot_inventory:
        item_type = item.get("type", "other")
        if item_type in item_counts:
            item_counts[item_type] += item.get("amount", 1)
        else:
            item_counts["other"] += item.get("amount", 1)

    return render_template('inventory.html',
                           inventory=bot_inventory,
                           total_items=len(bot_inventory),
                           item_counts=item_counts)


@app.route('/api/add_vip', methods=['POST'])
def add_vip():
    username = request.form.get('username', '').strip()
    if not username:
        return jsonify({
            "success": False,
            "message": "Nombre de usuario vacío"
        })

    try:
        user_data = load_user_data()
        if username in user_data["vip_users"]:
            return jsonify({"success": False, "message": "Usuario ya es VIP"})

        # Agregar a archivo
        with open("data/vip.txt", "a", encoding="utf-8") as f:
            f.write(f"{username}\n")

        return jsonify({
            "success": True,
            "message": f"{username} agregado como VIP"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/remove_vip', methods=['POST'])
def remove_vip():
    username = request.form.get('username', '').strip()
    if not username:
        return jsonify({
            "success": False,
            "message": "Nombre de usuario vacío"
        })

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

        return jsonify({
            "success": True,
            "message": f"{username} removido de VIP"
        })
    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/send_command', methods=['POST'])
def send_command():
    """Envía un comando al bot a través de console_message.txt"""
    try:
        data = request.json
        command = data.get('command', '').strip()

        if not command:
            return jsonify({"success": False, "message": "Comando vacío"})

        if write_console_command(command):
            return jsonify({
                "success": True,
                "message": f"Comando enviado: {command}"
            })
        else:
            return jsonify({
                "success": False,
                "message": "Error escribiendo comando"
            })

    except Exception as e:
        return jsonify({"success": False, "message": str(e)})


@app.route('/api/stats')
def get_stats():
    user_data = load_user_data()
    return jsonify({
        "vip_count":
        len(user_data["vip_users"]),
        "total_hearts":
        sum(user_data["hearts"].values()),
        "total_users":
        len(
            set(
                list(user_data["hearts"].keys()) +
                list(user_data["activity"].keys()))),
        "total_messages":
        sum(user_data["activity"].values()),
        "active_users":
        len(user_data["activity"])
    })

@app.route('/api/bot_responses')
def get_bot_responses():
    """Obtiene las últimas respuestas del bot"""
    try:
        if os.path.exists("bot_responses.txt"):
            with open("bot_responses.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
            
            # Filtrar líneas vacías y comentarios
            valid_lines = [
                line.strip() 
                for line in lines 
                if line.strip() and not line.strip().startswith('#')
            ]
            
            # Retornar las últimas 20 líneas válidas
            return jsonify({
                "success": True, 
                "responses": valid_lines[-20:] if valid_lines else []
            })
        
        return jsonify({"success": True, "responses": []})
    except Exception as e:
        return jsonify({"success": False, "message": str(e), "responses": []})


if __name__ == '__main__':
    os.makedirs("templates", exist_ok=True)
    app.run(host='0.0.0.0', port=5000, debug=True)
