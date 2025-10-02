import asyncio
import json
import os
import random
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union

from highrise import BaseBot, Position, User, Reaction, AnchorPosition
from highrise.models import Position as HighrisePosition, SessionMetadata, CurrencyItem, Item, Error

# Функция логирования событий
def log_event(event_type: str, message: str):
    """Логирование событий в файл"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{event_type}] {message}\n"

        with open("bot_log.txt", "a", encoding="utf-8") as f:
            f.write(log_message)

        # Выводим в консоль только важные события
        if event_type in ["ERROR", "WARNING", "ADMIN", "MOD"]:
            print(log_message.strip())
    except Exception as e:
        print(f"Error logging event: {e}")

# Глобальные переменные для хранения данных
VIP_USERS = set()
BANNED_USERS = {}
MUTED_USERS = {}
USER_HEARTS = {}
USER_ACTIVITY = {}
USER_INFO = {}
USER_NAMES = {}
TELEPORT_POINTS = {}
ACTIVE_EMOTES = {}
USER_JOIN_TIMES = {}  # Словарь для хранения времени входа пользователей
SAVED_OUTFITS = {}  # Diccionario para almacenar outfits guardados {número: outfit}

# Функции для сохранения данных
def save_user_info():
    """Сохраняет информацию о пользователях"""
    try:
        os.makedirs("data", exist_ok=True)
        with open("data/user_info.json", "w", encoding="utf-8") as f:
            # Преобразуем datetime объекты в строки для сериализации
            serializable_data = {}
            for user_id, data in USER_INFO.items():
                serializable_data[user_id] = {}
                for key, value in data.items():
                    if isinstance(value, datetime):
                        serializable_data[user_id][key] = value.isoformat()
                    else:
                        serializable_data[user_id][key] = value
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        print(f"Información de usuarios guardada: {len(USER_INFO)} usuarios")
    except Exception as e:
        print(f"Error guardando información de usuarios: {e}")

def save_leaderboard_data():
    """Сохраняет данные лидерборда"""
    try:
        os.makedirs("data", exist_ok=True)

        # Сохраняем сердечки
        with open("data/hearts.txt", "w", encoding="utf-8") as f:
            f.write("# Сердечки пользователей (user_id:hearts)\n")
            for user_id, hearts in USER_HEARTS.items():
                username = USER_NAMES.get(user_id, f"User_{user_id[:8]}")
                f.write(f"{user_id}:{hearts}:{username}\n")

        # Сохраняем активность
        with open("data/activity.txt", "w", encoding="utf-8") as f:
            f.write("# Активность пользователей (user_id:messages:last_activity)\n")
            for user_id, data in USER_ACTIVITY.items():
                username = USER_NAMES.get(user_id, f"User_{user_id[:8]}")
                last_activity = data["last_activity"].isoformat() if isinstance(data["last_activity"], datetime) else str(data["last_activity"])
                f.write(f"{user_id}:{data['messages']}:{last_activity}:{username}\n")

        print(f"Datos del leaderboard guardados: {len(USER_HEARTS)} usuarios con corazones, {len(USER_ACTIVITY)} usuarios con actividad")
    except Exception as e:
        print(f"Error guardando datos del leaderboard: {e}")

def load_config():
    """Загружает конфигурацию из файла"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            return json.load(f)
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return {}

# Загружаем конфигурацию
config = load_config()
ADMIN_IDS = config.get("admin_ids", [])
OWNER_ID = config.get("owner_id", "")
MODERATOR_IDS = config.get("moderator_ids", [])
VIP_ZONE = config.get("vip_zone", {"x": 0, "y": 0, "z": 0})
FORBIDDEN_ZONES = config.get("forbidden_zones", [])
BOT_WALLET = config.get("bot_wallet", 0)

# Lista de emotes específica con los 224 emotes solicitados
emotes = {
    "1": {"id": "emote-looping", "name": "fairytwirl", "duration": 9.89, "is_free": True},
    "2": {"id": "idle-floating", "name": "fairyfloat", "duration": 27.60, "is_free": True},
    "3": {"id": "emote-launch", "name": "launch", "duration": 10.88, "is_free": True},
    "4": {"id": "emote-cutesalute", "name": "cutesalute", "duration": 3.79, "is_free": True},
    "5": {"id": "emote-salute", "name": "atattention", "duration": 4.79, "is_free": True},
    "6": {"id": "dance-tiktok11", "name": "tiktok", "duration": 11.37, "is_free": True},
    "7": {"id": "emote-kissing", "name": "smooch", "duration": 6.69, "is_free": True},
    "8": {"id": "dance-employee", "name": "pushit", "duration": 8.55, "is_free": True},
    "9": {"id": "emote-gift", "name": "foryou", "duration": 6.09, "is_free": True},
    "10": {"id": "dance-touch", "name": "touch", "duration": 13.15, "is_free": True},
    "11": {"id": "dance-kawai", "name": "kawaii", "duration": 10.85, "is_free": True},
    "12": {"id": "sit-relaxed", "name": "repose", "duration": 31.21, "is_free": True},
    "13": {"id": "emote-sleigh", "name": "sleigh", "duration": 12.51, "is_free": True},
    "14": {"id": "emote-hyped", "name": "hyped", "duration": 7.62, "is_free": True},
    "15": {"id": "dance-jinglebell", "name": "jingle", "duration": 12.09, "is_free": True},
    "16": {"id": "idle-toilet", "name": "gottago", "duration": 33.48, "is_free": True},
    "17": {"id": "emote-timejump", "name": "timejump", "duration": 5.51, "is_free": True},
    "18": {"id": "idle-wild", "name": "scritchy", "duration": 27.35, "is_free": True},
    "19": {"id": "idle-nervous", "name": "bitnervous", "duration": 22.81, "is_free": True},
    "20": {"id": "emote-iceskating", "name": "iceskating", "duration": 8.41, "is_free": True},
    "21": {"id": "emote-celebrate", "name": "partytime", "duration": 4.35, "is_free": True},
    "22": {"id": "emote-pose10", "name": "arabesque", "duration": 5.00, "is_free": True},
    "23": {"id": "emote-shy2", "name": "bashful", "duration": 6.34, "is_free": True},
    "24": {"id": "emote-headblowup", "name": "revelations", "duration": 13.66, "is_free": True},
    "25": {"id": "emote-creepycute", "name": "watchyourback", "duration": 9.01, "is_free": True},
    "26": {"id": "dance-creepypuppet", "name": "creepypuppet", "duration": 7.79, "is_free": True},
    "27": {"id": "dance-anime", "name": "saunter", "duration": 9.60, "is_free": True},
    "28": {"id": "emote-pose6", "name": "surprise", "duration": 6.46, "is_free": True},
    "29": {"id": "emote-celebrationstep", "name": "celebration", "duration": 5.18, "is_free": True},
    "30": {"id": "dance-pinguin", "name": "penguin", "duration": 12.81, "is_free": True},
    "31": {"id": "emote-boxer", "name": "boxer", "duration": 6.75, "is_free": True},
    "32": {"id": "idle-guitar", "name": "airguitar", "duration": 14.15, "is_free": True},
    "33": {"id": "emote-stargazer", "name": "stargaze", "duration": 7.93, "is_free": True},
    "34": {"id": "emote-pose9", "name": "ditzy", "duration": 6.00, "is_free": True},
    "35": {"id": "idle-uwu", "name": "uwu", "duration": 25.50, "is_free": True},
    "36": {"id": "dance-wrong", "name": "wrong", "duration": 13.60, "is_free": True},
    "37": {"id": "emote-fashionista", "name": "fashion", "duration": 6.33, "is_free": True},
    "38": {"id": "dance-icecream", "name": "icecream", "duration": 16.58, "is_free": True},
    "39": {"id": "idle-dance-tiktok4", "name": "sayso", "duration": 16.55, "is_free": True},
    "40": {"id": "idle_zombie", "name": "zombie", "duration": 31.39, "is_free": True},
    "41": {"id": "emote-astronaut", "name": "astronaut", "duration": 13.93, "is_free": True},
    "42": {"id": "emote-punkguitar", "name": "punk", "duration": 10.59, "is_free": True},
    "43": {"id": "emote-gravity", "name": "zerogravity", "duration": 9.02, "is_free": True},
    "44": {"id": "emote-pose5", "name": "beautiful", "duration": 5.49, "is_free": True},
    "45": {"id": "emote-shocked", "name": "omg", "duration": 5.59, "is_free": False},
    "46": {"id": "idle-dance-casual", "name": "casual", "duration": 9.57, "is_free": True},
    "47": {"id": "emote-pose1", "name": "wink", "duration": 4.71, "is_free": True},
    "48": {"id": "emote-pose3", "name": "fightme", "duration": 5.57, "is_free": True},
    "49": {"id": "emote-superpose", "name": "icon", "duration": 5.43, "is_free": False},
    "50": {"id": "emote-cute", "name": "cute", "duration": 7.20, "is_free": True},
    "51": {"id": "emote-cutey", "name": "cutey", "duration": 4.07, "is_free": True},
    "52": {"id": "emote-greedy", "name": "greedy", "duration": 5.72, "is_free": True},
    "53": {"id": "dance-tiktok9", "name": "viralgroove", "duration": 13.04, "is_free": True},
    "54": {"id": "dance-weird", "name": "weird", "duration": 22.87, "is_free": True},
    "55": {"id": "dance-tiktok10", "name": "shuffle", "duration": 9.41, "is_free": True},
    "56": {"id": "emoji-gagging", "name": "gagging", "duration": 6.84, "is_free": True},
    "57": {"id": "emoji-celebrate", "name": "raise", "duration": 4.78, "is_free": True},
    "58": {"id": "dance-tiktok8", "name": "savage", "duration": 13.10, "is_free": True},
    "59": {"id": "dance-blackpink", "name": "blackpink", "duration": 7.97, "is_free": True},
    "60": {"id": "emote-model", "name": "model", "duration": 7.43, "is_free": True},
    "61": {"id": "dance-tiktok2", "name": "dontstartnow", "duration": 11.37, "is_free": True},
    "62": {"id": "dance-pennywise", "name": "pennywise", "duration": 4.16, "is_free": True},
    "63": {"id": "emote-bow", "name": "bow", "duration": 5.10, "is_free": True},
    "64": {"id": "dance-russian", "name": "russian", "duration": 11.39, "is_free": True},
    "65": {"id": "emote-curtsy", "name": "curtsy", "duration": 3.99, "is_free": True},
    "66": {"id": "emote-snowball", "name": "snowball", "duration": 6.32, "is_free": True},
    "67": {"id": "emote-hot", "name": "hot", "duration": 5.57, "is_free": True},
    "68": {"id": "emote-snowangel", "name": "snowangel", "duration": 7.33, "is_free": True},
    "69": {"id": "emote-charging", "name": "charging", "duration": 9.53, "is_free": True},
    "70": {"id": "dance-shoppingcart", "name": "letsgoshopping", "duration": 5.56, "is_free": True},
    "71": {"id": "emote-confused", "name": "confused", "duration": 9.58, "is_free": True},
    "72": {"id": "idle-enthusiastic", "name": "enthused", "duration": 17.53, "is_free": True},
    "73": {"id": "emote-telekinesis", "name": "telekinesis", "duration": 11.01, "is_free": True},
    "74": {"id": "emote-float", "name": "float", "duration": 9.26, "is_free": True},
    "75": {"id": "emote-teleporting", "name": "teleporting", "duration": 12.89, "is_free": True},
    "76": {"id": "emote-swordfight", "name": "swordfight", "duration": 7.71, "is_free": True},
    "77": {"id": "emote-maniac", "name": "maniac", "duration": 5.94, "is_free": True},
    "78": {"id": "emote-energyball", "name": "energyball", "duration": 8.28, "is_free": True},
    "79": {"id": "emote-snake", "name": "worm", "duration": 6.63, "is_free": True},
    "80": {"id": "idle_singing", "name": "singalong", "duration": 11.31, "is_free": True},
    "81": {"id": "emote-frog", "name": "frog", "duration": 16.14, "is_free": True},
    "82": {"id": "dance-macarena", "name": "macarena", "duration": 15.0, "is_free": True},
    "83": {"id": "emote-kissing-passionate", "name": "kiss", "duration": 10.47, "is_free": True},
    "84": {"id": "emoji-shake-head", "name": "shakehead", "duration": 3.5, "is_free": True},
    "85": {"id": "idle-sad", "name": "sad", "duration": 25.24, "is_free": True},
    "86": {"id": "emoji-nod", "name": "nod", "duration": 2.5, "is_free": True},
    "87": {"id": "emote-laughing2", "name": "laughing", "duration": 6.60, "is_free": True},
    "88": {"id": "emoji-hello", "name": "hello", "duration": 3.0, "is_free": True},
    "89": {"id": "emoji-thumbsup", "name": "thumbsup", "duration": 2.5, "is_free": True},
    "90": {"id": "mining-fail", "name": "miningfail", "duration": 3.41, "is_free": True},
    "91": {"id": "emote-shy", "name": "shy", "duration": 5.15, "is_free": True},
    "92": {"id": "fishing-pull", "name": "fishingpull", "duration": 2.81, "is_free": True},
    "93": {"id": "dance-thewave", "name": "thewave", "duration": 8.0, "is_free": True},
    "94": {"id": "idle-angry", "name": "angry", "duration": 26.07, "is_free": True},
    "95": {"id": "emote-rough", "name": "rough", "duration": 6.0, "is_free": True},
    "96": {"id": "fishing-idle", "name": "fishingidle", "duration": 17.87, "is_free": True},
    "97": {"id": "emote-dropped", "name": "dropped", "duration": 4.5, "is_free": True},
    "98": {"id": "mining-success", "name": "miningsuccess", "duration": 3.11, "is_free": True},
    "99": {"id": "emote-receive-happy", "name": "receivehappy", "duration": 5.0, "is_free": True},
    "100": {"id": "emote-cold", "name": "cold", "duration": 5.17, "is_free": True},
    "101": {"id": "fishing-cast", "name": "fishingcast", "duration": 2.82, "is_free": True},
    "102": {"id": "emote-sit", "name": "sit", "duration": 20.0, "is_free": True},
    "103": {"id": "dance-shuffle", "name": "shuffledance", "duration": 9.0, "is_free": True},
    "104": {"id": "emote-receive-sad", "name": "receivesad", "duration": 5.0, "is_free": True},
    "105": {"id": "idle-loop-tired", "name": "tired", "duration": 11.23, "is_free": True},
    "106": {"id": "dance-hipshake", "name": "hipshake", "duration": 13.38, "is_free": True},
    "107": {"id": "dance-fruity", "name": "fruity", "duration": 18.25, "is_free": True},
    "108": {"id": "dance-cheerleader", "name": "cheerleader", "duration": 17.93, "is_free": True},
    "109": {"id": "dance-tiktok14", "name": "magnetic", "duration": 11.20, "is_free": True},
    "110": {"id": "emote-howl", "name": "nocturnal", "duration": 8.10, "is_free": True},
    "111": {"id": "idle-howl", "name": "moonlit", "duration": 48.62, "is_free": True},
    "112": {"id": "emote-trampoline", "name": "trampoline", "duration": 6.11, "is_free": True},
    "113": {"id": "emote-attention", "name": "attention", "duration": 5.65, "is_free": True},
    "114": {"id": "sit-open", "name": "laidback", "duration": 27.28, "is_free": True},
    "115": {"id": "emote-shrink", "name": "shrink", "duration": 9.99, "is_free": True},
    "116": {"id": "emote-puppet", "name": "puppet", "duration": 17.89, "is_free": True},
    "117": {"id": "dance-aerobics", "name": "pushups", "duration": 9.89, "is_free": True},
    "118": {"id": "dance-duckwalk", "name": "duckwalk", "duration": 12.48, "is_free": True},
    "119": {"id": "dance-handsup", "name": "handsintheair", "duration": 23.18, "is_free": True},
    "120": {"id": "dance-metal", "name": "rockout", "duration": 15.78, "is_free": True},
    "121": {"id": "dance-orangejustice", "name": "orangejuice", "duration": 7.17, "is_free": True},
    "122": {"id": "dance-singleladies", "name": "ringonit", "duration": 22.33, "is_free": True},
    "123": {"id": "dance-smoothwalk", "name": "smoothwalk", "duration": 7.58, "is_free": True},
    "124": {"id": "dance-voguehands", "name": "voguehands", "duration": 10.57, "is_free": True},
    "125": {"id": "emoji-arrogance", "name": "arrogance", "duration": 8.16, "is_free": True},
    "126": {"id": "emoji-give-up", "name": "giveup", "duration": 6.04, "is_free": True},
    "127": {"id": "emoji-hadoken", "name": "fireball", "duration": 4.29, "is_free": True},
    "128": {"id": "emoji-halo", "name": "levitate", "duration": 6.52, "is_free": True},
    "129": {"id": "emoji-lying", "name": "lying", "duration": 7.39, "is_free": True},
    "130": {"id": "emoji-naughty", "name": "naughty", "duration": 5.73, "is_free": True},
    "131": {"id": "emoji-poop", "name": "stinky", "duration": 5.86, "is_free": True},
    "132": {"id": "emoji-pray", "name": "pray", "duration": 6.00, "is_free": True},
    "133": {"id": "emoji-punch", "name": "punch", "duration": 3.36, "is_free": True},
    "134": {"id": "emoji-sick", "name": "sick", "duration": 6.22, "is_free": True},
    "135": {"id": "emoji-smirking", "name": "smirk", "duration": 5.74, "is_free": True},
    "136": {"id": "emoji-sneeze", "name": "sneeze", "duration": 4.33, "is_free": True},
    "137": {"id": "emoji-there", "name": "point", "duration": 3.09, "is_free": True},
    "138": {"id": "emote-death2", "name": "collapse", "duration": 5.54, "is_free": True},
    "139": {"id": "emote-disco", "name": "disco", "duration": 6.14, "is_free": True},
    "140": {"id": "emote-ghost-idle", "name": "ghostfloat", "duration": 20.43, "is_free": True},
    "141": {"id": "emote-handstand", "name": "handstand", "duration": 5.89, "is_free": True},
    "142": {"id": "emote-kicking", "name": "superkick", "duration": 6.21, "is_free": True},
    "143": {"id": "emote-panic", "name": "panic", "duration": 4.5, "is_free": True},
    "144": {"id": "emote-splitsdrop", "name": "splits", "duration": 5.31, "is_free": True},
    "145": {"id": "idle_layingdown", "name": "attentive", "duration": 26.11, "is_free": True},
    "146": {"id": "idle_layingdown2", "name": "relaxed", "duration": 22.59, "is_free": True},
    "147": {"id": "emote-apart", "name": "fallingapart", "duration": 5.98, "is_free": True},
    "148": {"id": "emote-baseball", "name": "homerun", "duration": 8.47, "is_free": True},
    "149": {"id": "emote-boo", "name": "boo", "duration": 5.58, "is_free": True},
    "150": {"id": "emote-bunnyhop", "name": "bunnyhop", "duration": 13.63, "is_free": True},
    "151": {"id": "emote-death", "name": "revival", "duration": 8.00, "is_free": True},
    "152": {"id": "emote-deathdrop", "name": "faintdrop", "duration": 4.18, "is_free": True},
    "153": {"id": "emote-elbowbump", "name": "elbowbump", "duration": 6.44, "is_free": True},
    "154": {"id": "emote-fail1", "name": "fall", "duration": 6.90, "is_free": True},
    "155": {"id": "emote-fail2", "name": "clumsy", "duration": 7.74, "is_free": True},
    "156": {"id": "emote-fainting", "name": "faint", "duration": 18.55, "is_free": True},
    "157": {"id": "emote-hugyourself", "name": "hugyourself", "duration": 6.03, "is_free": True},
    "158": {"id": "emote-jetpack", "name": "jetpack", "duration": 17.77, "is_free": True},
    "159": {"id": "emote-judochop", "name": "judochop", "duration": 5.0, "is_free": True},
    "160": {"id": "emote-jumpb", "name": "jump", "duration": 4.87, "is_free": True},
    "161": {"id": "emote-laughing2", "name": "amused", "duration": 6.60, "is_free": True},
    "162": {"id": "emote-levelup", "name": "levelup", "duration": 7.27, "is_free": True},
    "163": {"id": "emote-monster_fail", "name": "monsterfail", "duration": 5.42, "is_free": True},
    "164": {"id": "idle-dance-headbobbing", "name": "nightfever", "duration": 23.65, "is_free": True},
    "165": {"id": "emote-ninjarun", "name": "ninjarun", "duration": 6.50, "is_free": True},
    "166": {"id": "emoji-peace", "name": "peace", "duration": 3.5, "is_free": True},
    "167": {"id": "emote-peekaboo", "name": "peekaboo", "duration": 4.52, "is_free": True},
    "168": {"id": "emote-proposing", "name": "proposing", "duration": 5.91, "is_free": True},
    "169": {"id": "emote-rainbow", "name": "rainbow", "duration": 8.0, "is_free": True},
    "170": {"id": "emote-robot", "name": "robot", "duration": 10.0, "is_free": True},
    "171": {"id": "emote-rofl", "name": "rofl", "duration": 7.65, "is_free": True},
    "172": {"id": "emote-roll", "name": "roll", "duration": 4.31, "is_free": True},
    "173": {"id": "emote-ropepull", "name": "ropepull", "duration": 10.69, "is_free": True},
    "174": {"id": "emote-secrethandshake", "name": "secrethandshake", "duration": 6.28, "is_free": True},
    "175": {"id": "emote-sumo", "name": "sumofight", "duration": 11.64, "is_free": True},
    "176": {"id": "emote-superpunch", "name": "superpunch", "duration": 5.75, "is_free": True},
    "177": {"id": "emote-superrun", "name": "superrun", "duration": 7.16, "is_free": True},
    "178": {"id": "emote-theatrical", "name": "theatrical", "duration": 11.00, "is_free": True},
    "179": {"id": "emote-wings", "name": "ibelieve", "duration": 14.21, "is_free": True},
    "180": {"id": "emote-frustrated", "name": "irritated", "duration": 6.41, "is_free": True},
    "181": {"id": "idle-floorsleeping", "name": "cozynap", "duration": 14.61, "is_free": True},
    "182": {"id": "idle-floorsleeping2", "name": "relaxing", "duration": 18.83, "is_free": True},
    "183": {"id": "idle-hero", "name": "heropose", "duration": 22.33, "is_free": True},
    "184": {"id": "idle-lookup", "name": "ponder", "duration": 8.75, "is_free": True},
    "185": {"id": "idle-posh", "name": "posh", "duration": 23.29, "is_free": True},
    "186": {"id": "idle-sad", "name": "poutyface", "duration": 25.24, "is_free": True},
    "187": {"id": "emote-dab", "name": "dab", "duration": 3.75, "is_free": True},
    "188": {"id": "dance-gangnamstyle", "name": "gangnamstyle", "duration": 15.0, "is_free": True},
    "189": {"id": "emoji-crying", "name": "sob", "duration": 4.91, "is_free": True},
    "190": {"id": "idle-loop-tapdance", "name": "taploop", "duration": 7.81, "is_free": True},
    "191": {"id": "idle-sleep", "name": "sleepy", "duration": 3.35, "is_free": True},
    "192": {"id": "dance-sexy", "name": "wiggledance", "duration": 13.70, "is_free": True},
    "193": {"id": "emoji-eyeroll", "name": "eyeroll", "duration": 3.75, "is_free": True},
    "194": {"id": "dance-moonwalk", "name": "moonwalk", "duration": 12.0, "is_free": True},
    "195": {"id": "idle-fighter", "name": "fighter", "duration": 18.64, "is_free": True},
    "196": {"id": "idle-dance-tiktok7", "name": "renegade", "duration": 14.05, "is_free": True},
    "197": {"id": "emote-facepalm", "name": "facepalm", "duration": 5.0, "is_free": True},
    "198": {"id": "idle-dance-headbobbing", "name": "feelthebeat", "duration": 23.65, "is_free": True},
    "199": {"id": "emote-pose8", "name": "happy", "duration": 5.62, "is_free": True},
    "200": {"id": "emote-hug", "name": "hug", "duration": 4.53, "is_free": True},
    "201": {"id": "emote-slap", "name": "slap", "duration": 4.06, "is_free": True},
    "202": {"id": "emoji-clapping", "name": "clap", "duration": 2.98, "is_free": True},
    "203": {"id": "emote-exasperated", "name": "exasperated", "duration": 4.10, "is_free": True},
    "204": {"id": "emote-kissing-passionate", "name": "sweetsmooch", "duration": 10.47, "is_free": True},
    "205": {"id": "emote-tapdance", "name": "tapdance", "duration": 6.0, "is_free": True},
    "206": {"id": "emote-suckthumb", "name": "thumbsuck", "duration": 5.23, "is_free": True},
    "207": {"id": "dance-harlemshake", "name": "harlemshake", "duration": 10.0, "is_free": True},
    "208": {"id": "emote-heartfingers", "name": "heartfingers", "duration": 5.18, "is_free": True},
    "209": {"id": "idle-loop-aerobics", "name": "aerobics", "duration": 10.08, "is_free": True},
    "210": {"id": "emote-heartshape", "name": "heartshape", "duration": 7.60, "is_free": True},
    "211": {"id": "emote-hearteyes", "name": "hearteyes", "duration": 5.99, "is_free": True},
    "212": {"id": "dance-wild", "name": "karmadance", "duration": 16.25, "is_free": True},
    "213": {"id": "emoji-scared", "name": "gasp", "duration": 4.06, "is_free": True},
    "214": {"id": "emote-think", "name": "think", "duration": 4.81, "is_free": True},
    "215": {"id": "emoji-dizzy", "name": "stunned", "duration": 5.38, "is_free": True},
    "216": {"id": "emote-embarrassed", "name": "embarrassed", "duration": 9.09, "is_free": True},
    "217": {"id": "emote-disappear", "name": "blastoff", "duration": 5.53, "is_free": True},
    "218": {"id": "idle-loop-annoyed", "name": "annoyed", "duration": 18.62, "is_free": True},
    "219": {"id": "dance-zombie", "name": "dancezombie", "duration": 13.83, "is_free": True},
    "220": {"id": "idle-loop-happy", "name": "chillin", "duration": 19.80, "is_free": True},
    "221": {"id": "emote-frustrated", "name": "frustrated", "duration": 6.41, "is_free": True},
    "222": {"id": "idle-loop-sad", "name": "bummed", "duration": 21.80, "is_free": True},
    "223": {"id": "emoji-ghost", "name": "ghost", "duration": 3.74, "is_free": True},
    "224": {"id": "emoji-mind-blown", "name": "mindblown", "duration": 3.46, "is_free": True}
}

# Добавляем задержку и повторные попытки подключения
MAX_RETRIES = 3
RETRY_DELAY = 5

class Bot(BaseBot):
    def __init__(self):
        super().__init__()
        self.last_announcement = 0
        self.user_positions = {}  # Словарь для хранения последних позиций пользователей
        self.connection_retries = 0
        self.bot_mode = "idle"  # Modo por defecto: idle (sin emotes automáticos)
        self.current_emote_task = None  # Para controlar la tarea actual de emotes

    async def connect_with_retry(self):
        """Подключение к серверу с повторными попытками"""
        # Esta función simplemente retorna True ya que la conexión real
        # es manejada por el framework de Highrise automáticamente
        print("✅ Conexión establecida con High Rise")
        return True

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Inicio del bot"""
        try:
            # Store bot ID from session metadata for reliable identification
            self.bot_id = session_metadata.user_id
            log_event("BOT", f"Bot ID stored: {self.bot_id}")

            if await self.connect_with_retry():
                print("Бот успешно подключен!")
                self.load_data()
                # Запускаем объявления
                asyncio.create_task(self.start_announcements())
                asyncio.create_task(self.check_console_messages())
                # Configurar outfit y emote inicial del bot
                await self.setup_initial_bot_appearance()
                
                # Ejecutar ciclo automático de 224 emotes en bucle infinito
                try:
                    await asyncio.sleep(2)  # Espera breve para estabilizar conexión
                    log_event("BOT", "Preparando ciclo automático de 224 emotes en bucle infinito")
                    await self.highrise.chat("¡El bot ha entrado en la sala! Iniciando CICLO AUTOMÁTICO DE EMOTES...")
                    await self.highrise.chat("🎭 ¡MODO AUTOMÁTICO INFINITO ACTIVADO!")
                    # Iniciar ciclo automático en tarea separada
                    self.bot_mode = "auto"
                    asyncio.create_task(self.start_auto_emote_cycle())
                    log_event("BOT", "Ciclo automático de 224 emotes iniciado")
                except Exception as e:
                    log_event("ERROR", f"Error en ciclo automático: {e}")
                    print(f"⚠️ Error en ciclo automático: {e}")
            else:
                print("Не удалось подключиться к серверу")
                sys.exit(1)
        except Exception as e:
            print(f"Error en on_start: {e}")
        # Bot iniciado - se muestra solo en consola
        print("🤖 ¡Bot iniciado! Usa !help para ver los comandos.")

    def load_data(self):
        """Carga datos desde archivos"""
        try:
            # Carga de usuarios VIP
            if os.path.exists("data/vip.txt"):
                with open("data/vip.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            VIP_USERS.add(line.strip())
            print(f"Datos VIP cargados: {len(VIP_USERS)} usuarios")

            # Carga de puntos de teletransporte
            if os.path.exists("data/teleport_points.txt"):
                with open("data/teleport_points.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            parts = line.strip().split("|")
                            if len(parts) == 4:
                                name = parts[0]
                                x = float(parts[1])
                                y = float(parts[2])
                                z = float(parts[3])
                                TELEPORT_POINTS[name] = {"x": x, "y": y, "z": z}
            print(f"Puntos de teletransporte cargados: {len(TELEPORT_POINTS)} puntos")
        except Exception as e:
            print(f"Error cargando datos: {e}")

    def save_data(self):
        """Guarda datos en archivos"""
        try:
            os.makedirs("data", exist_ok=True)
            with open("data/vip.txt", "w", encoding="utf-8") as f:
                f.write("# Usuarios VIP (un ID por línea)\n")
                for user_id in VIP_USERS:
                    f.write(f"{user_id}\n")
            print(f"Datos VIP guardados: {len(VIP_USERS)} usuarios")

            # Guardar puntos de teletransporte
            with open("data/teleport_points.txt", "w", encoding="utf-8") as f:
                f.write("# Puntos de teletransporte (nombre|x|y|z)\n")
                for name, coords in TELEPORT_POINTS.items():
                    f.write(f"{name}|{coords['x']}|{coords['y']}|{coords['z']}\n")
            print(f"Puntos de teletransporte guardados: {len(TELEPORT_POINTS)} puntos")

            # Salviamo le informazioni sui giocatori
            save_user_info()
            save_leaderboard_data()
        except Exception as e:
            print(f"Error guardando datos: {e}")

    def is_admin(self, user_id: str) -> bool:
        """Verifica si el usuario es administrador"""
        return user_id in ADMIN_IDS or user_id == OWNER_ID

    def is_moderator(self, user_id: str) -> bool:
        """Verifica si el usuario es moderador"""
        return user_id in MODERATOR_IDS or self.is_admin(user_id)

    def is_vip(self, user_id: str) -> bool:
        """Verifica si el usuario es VIP por user_id"""
        # Buscamos el username correspondiente al user_id
        username = USER_NAMES.get(user_id)
        if username:
            return username in VIP_USERS
        return False

    def is_vip_by_username(self, username: str) -> bool:
        """Verifica si el usuario es VIP por username"""
        return username in VIP_USERS

    def is_banned(self, user_id: str) -> bool:
        """Verifica si el usuario está baneado"""
        if user_id in BANNED_USERS:
            ban_data = BANNED_USERS[user_id]
            if isinstance(ban_data, dict) and "time" in ban_data:
                ban_time = ban_data["time"]
                if isinstance(ban_time, str):
                    try:
                        ban_time = datetime.fromisoformat(ban_time.replace('Z', '+00:00'))
                    except:
                        return True
                if datetime.now() > ban_time:
                    del BANNED_USERS[user_id]
                    return False
                return True
            return True
        return False

    def is_muted(self, user_id: str) -> bool:
        """Verifica si el usuario está silenciado"""
        if user_id in MUTED_USERS:
            mute_time = MUTED_USERS[user_id]
            if isinstance(mute_time, str):
                try:
                    mute_time = datetime.fromisoformat(mute_time.replace('Z', '+00:00'))
                except:
                    return True
            if datetime.now() > mute_time:
                del MUTED_USERS[user_id]
                return False
            return True
        return False

    def get_user_hearts(self, user_id: str) -> int:
        """Obtiene la cantidad de corazones del usuario"""
        return USER_HEARTS.get(user_id, 0)

    def get_user_role_info(self, user: User) -> str:
        """Obtiene información sobre el rol del usuario"""
        user_id = user.id
        username = user.username

        if user_id == OWNER_ID:
            return "👑 Propietario del Bot"
        elif self.is_admin(user_id):
            return "🛡️ Administrador"
        elif self.is_moderator(user_id):
            return "⚖️ Moderador"
        elif self.is_vip_by_username(username):
            return "⭐ Usuario VIP"
        else:
            return "👤 Usuario Normal"

    def add_user_hearts(self, user_id: str, hearts: int, username: str | None = None):
        """Añade corazones al usuario"""
        print(f"DEBUG: add_user_hearts вызван с user_id={user_id}, hearts={hearts}, username={username}")

        if user_id not in USER_HEARTS:
            USER_HEARTS[user_id] = 0
        USER_HEARTS[user_id] += hearts

        # Обновляем username если предоставлен или если его нет в USER_NAMES
        if username:
            USER_NAMES[user_id] = username
        elif user_id not in USER_NAMES:
            # Если username не предоставлен, но его нет в USER_NAMES, попробуем найти в текущих пользователях
            print(f"DEBUG: Username не найден для {user_id}, попробуем найти позже")

        print(f"DEBUG: USER_HEARTS после добавления = {USER_HEARTS}")
        print(f"DEBUG: USER_NAMES после добавления = {USER_NAMES}")

        save_leaderboard_data()
        display_username = username if username is not None else f"User_{user_id[:8]}"
        print(f"DEBUG: Добавлено {hearts} сердечек пользователю {display_username}. Всего: {USER_HEARTS[user_id]}")

    def update_activity(self, user_id: str):
        """Actualiza la actividad del usuario"""
        if user_id not in USER_ACTIVITY:
            USER_ACTIVITY[user_id] = {"messages": 0, "last_activity": datetime.now()}
        USER_ACTIVITY[user_id]["messages"] += 1
        USER_ACTIVITY[user_id]["last_activity"] = datetime.now()

        # Aggiorniamo le informazioni sul giocatore
        if user_id in USER_INFO:
            USER_INFO[user_id]["total_messages"] = USER_ACTIVITY[user_id]["messages"]

    def update_user_info(self, user_id: str, username: str):
        """Aggiorna le informazioni sul giocatore"""
        if user_id not in USER_INFO:
            USER_INFO[user_id] = {
                "username": username,
                "first_seen": datetime.now().isoformat(),
                "account_created": None,  # Будет заполнено при получении данных пользователя
                "total_time_in_room": 0,
                "total_messages": 0,
                "time_joined": time.time()  # Используем time.time() как в документации
            }
        else:
            USER_INFO[user_id]["username"] = username
            USER_INFO[user_id]["total_messages"] = USER_ACTIVITY.get(user_id, {}).get("messages", 0)

    def get_user_total_time(self, user_id: str) -> int:
        """Ottiene il tempo totale del giocatore nella stanza in secondi"""
        return USER_INFO.get(user_id, {}).get("total_time_in_room", 0)

    def format_time(self, seconds: int) -> str:
        """Formatta il tempo in formato leggibile"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        if hours > 0:
            return f"{hours}o {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"
        save_leaderboard_data()

    def get_help_for_user(self, user_id: str, username: str) -> str:
        """Retorna comandos disponibles según el rol del usuario"""
        is_owner = (user_id == OWNER_ID)
        is_admin = self.is_admin(user_id)
        is_vip = self.is_vip(user_id)

        if is_owner:
            return ("👑 COMANDOS PROPIETARIO:\n"
                   "📊 !info, !role, !emote list\n"
                   "💖 !heart @user (sin límites)\n"
                   "🎮 Juego amorometro\n"
                   "🎭 Emotes a todos: [emote] all\n"
                   "⚡ !flash [x] [y] [z] - subir/bajar pisos\n"
                   "🎯 !bring @user, !vip @user\n"
                   "🔨 !freeze @user, !mute @user, !ban @user\n"
                   "🗺️ !addzone [nombre] - crear zonas\n"
                   "🤖 !bot @user - hacer punch/revival\n"
                   "🕺 !flossmode - activar modo floss\n"
                   "🎭 !automode - activar ciclo automático\n"
                   "👥 Acceso a todas las zonas")

        elif is_admin:
            return ("⚔️ COMANDOS ADMIN:\n"
                   "📊 !info, !role, !emote list\n"
                   "💖 !heart @user (hasta 100)\n"
                   "🎮 Juego amorometro\n"
                   "🎭 Emotes a todos: [emote] all\n"
                   "⚡ !flash [x] [y] [z] - subir/bajar pisos\n"
                   "🎯 !bring @user, !vip @user\n"
                   "🔨 !freeze @user, !mute @user, !ban @user\n"
                   "🗺️ !addzone [nombre] - crear zonas\n"
                   "🤖 !bot @user - hacer punch/revival\n"
                   "🕺 !flossmode - activar modo floss\n"
                   "🎭 !automode - activar ciclo automático")

        elif is_vip:
            return ("⭐ COMANDOS VIP:\n"
                   "📊 !info, !role, !emote list\n"
                   "💖 !heart @user (limitado)\n"
                   "🎮 Juego amorometro\n"
                   "🎭 Emotes personales únicamente\n"
                   "⚡ !flash [x] [y] [z] - subir/bajar pisos\n"
                   "🔥 vip - acceso a zona VIP")

        else:
            return ("👤 COMANDOS USUARIO:\n"
                   "📊 !info, !role, !emote list\n"
                   "💖 !heart @user (muy limitado)\n"
                   "🎮 Juego amorometro\n"
                   "🎭 Emotes personales únicamente\n"
                   "⚡ !flash [x] [y] [z] - subir/bajar pisos")

    def is_in_forbidden_zone(self, x: float, y: float, z: float) -> bool:
        """Verifica si el punto está en zona prohibida"""
        for zone in FORBIDDEN_ZONES:
            distance = ((x - zone["x"])**2 + (y - zone["y"])**2 + (z - zone["z"])**2)**0.5
            if distance <= zone["radius"]:
                return True
        return False

    def calculate_distance(self, pos1, pos2) -> float:
        """Calcula la distancia entre dos posiciones"""
        return ((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2 + (pos1.z - pos2.z)**2)**0.5

    async def teleport_user(self, user_id: str, x: float, y: float, z: float):
        """Teletransporta al usuario (método obsoleto)"""
        try:

            position = Position(x, y, z)
            await self.highrise.teleport(user_id, position)
            return True
        except Exception:
            return False

    async def send_emote_loop(self, user_id: str, emote_id: str):
        """Inicia la emoción en un bucle infinito"""
        print(f"DEBUG: Iniciando send_emote_loop para usuario {user_id} con emote {emote_id}")
        ACTIVE_EMOTES[user_id] = emote_id
        print(f"DEBUG: ACTIVE_EMOTES después de agregar: {ACTIVE_EMOTES}")

        # Проверяем, что эмоция существует
        if emote_id not in [emote["id"] for emote in emotes.values()]:
            # No hay usuario específico aquí, se mantiene como print
            # Error en animación - este caso no tiene user context
            if user_id in ACTIVE_EMOTES:
                del ACTIVE_EMOTES[user_id]
            return

        # Получаем имя пользователя для сообщений
        username = USER_NAMES.get(user_id, "Usuario")

        while user_id in ACTIVE_EMOTES and ACTIVE_EMOTES[user_id] == emote_id and ACTIVE_EMOTES[user_id] is not None:
            try:
                print(f"DEBUG: Enviando emote {emote_id} a usuario {user_id}")
                await self.highrise.send_emote(emote_id, user_id)
                duration = emotes.get(emote_id, {}).get("duration", 5)
                print(f"DEBUG: Esperando {duration} segundos antes del siguiente emote")
                await asyncio.sleep(duration)
            except Exception as e:
                print(f"DEBUG: Error en send_emote_loop: {e}")
                # Error handling for different types of errors
                if "not found" in str(e).lower() or "invalid" in str(e).lower():
                    print("Error: Animation not found or invalid")
                elif "permission" in str(e).lower() or "access" in str(e).lower():
                    print("Error: Permission or access denied")
                else:
                    print("Error: General error occurred")
                break

        print(f"DEBUG: Bucle terminado para usuario {user_id}")
        # Limpiamos el diccionario si el usuario ya no está activo
        if user_id in ACTIVE_EMOTES and ACTIVE_EMOTES[user_id] is None:
            del ACTIVE_EMOTES[user_id]
            print(f"DEBUG: Usuario {user_id} eliminado de ACTIVE_EMOTES al final del bucle")

    async def stop_emote_loop(self, user_id: str):
        """Detiene la emoción en el bucle"""
        print(f"DEBUG: Intentando detener animación para usuario {user_id}")
        print(f"DEBUG: ACTIVE_EMOTES antes: {ACTIVE_EMOTES}")

        if user_id in ACTIVE_EMOTES:
            print(f"DEBUG: Usuario {user_id} encontrado en ACTIVE_EMOTES")
            # Cambiamos el emote_id a None para forzar la parada del bucle
            ACTIVE_EMOTES[user_id] = None
            print(f"DEBUG: ACTIVE_EMOTES después de None: {ACTIVE_EMOTES}")

            # Enviamos múltiples animaciones de "idle" para asegurar que se detenga
            try:
                # Intentamos con diferentes animaciones de parada
                stop_animations = ["idle", "idle-loop-happy", "idle-loop-sad", "idle-loop-tired"]
                for stop_anim in stop_animations:
                    try:
                        print(f"DEBUG: Intentando enviar animación de parada: {stop_anim}")
                        await self.highrise.send_emote(stop_anim, user_id)
                        print(f"DEBUG: Animación de parada {stop_anim} enviada exitosamente")
                        await asyncio.sleep(0.1)  # Pequeña pausa entre animaciones
                    except Exception as e:
                        print(f"DEBUG: Error enviando {stop_anim}: {e}")
                        continue
            except Exception as e:
                print(f"DEBUG: Error general en stop_animations: {e}")

            # Esperamos más tiempo para que el bucle se detenga completamente
            await asyncio.sleep(1.0)  # Aumentamos el tiempo de espera

            # Luego eliminamos completamente del diccionario
            if user_id in ACTIVE_EMOTES:
                del ACTIVE_EMOTES[user_id]
                print(f"DEBUG: Usuario {user_id} eliminado de ACTIVE_EMOTES")

            print(f"DEBUG: ACTIVE_EMOTES final: {ACTIVE_EMOTES}")
        else:
            print(f"DEBUG: Usuario {user_id} NO encontrado en ACTIVE_EMOTES")

    async def on_chat(self, user: User, message: str) -> None:
        global VIP_ZONE

        msg = message.strip()
        user_id = user.id
        username = user.username

        # Añadimos el username al diccionario USER_NAMES para que funcione is_vip()
        USER_NAMES[user_id] = username

        # Detectar si es comando privado (susurro/whisper)
        is_whisper = hasattr(message, 'is_whisper') and message.is_whisper if hasattr(message, '__dict__') else False
        
        # Registro de todos los mensajes
        log_event("CHAT", f"[{'WHISPER' if is_whisper else 'PUBLIC'}] {user.username}: {msg}")

        # Verificación de ban y mute
        if self.is_banned(user_id):
            log_event("BANNED", f"Mensaje bloqueado de {user.username}")
            await self.highrise.send_whisper(user.id, f"@{user.username} está baneado hasta {BANNED_USERS[user_id]['time'].strftime('%d.%m.%Y %H:%M')}")
            return

        if self.is_muted(user_id):
            log_event("MUTED", f"Mensaje silenciado de {user.username}")
            await self.highrise.send_whisper(user.id, f"@{user.username} está silenciado hasta {MUTED_USERS[user_id].strftime('%H:%M:%S')}")
            return

        # Actualización de actividad
        self.update_activity(user_id)

        # Comando temporal para depurar métodos de Highrise
        if msg == "!methods":
            if self.is_admin(user_id):
                methods = [method for method in dir(self.highrise) if not method.startswith('_')]
                await self.highrise.send_whisper(user.id, f"🔍 Métodos disponibles de Highrise: {', '.join(methods[:10])}")
                if len(methods) > 10:
                    await self.highrise.send_whisper(user.id, f"🔍 ... y {len(methods)-10} métodos más")
                # Buscamos métodos de moderación
                mod_methods = [m for m in methods if any(word in m.lower() for word in ['kick', 'mute', 'ban', 'moderate', 'freeze'])]
                if mod_methods:
                    await self.highrise.send_whisper(user.id, f"🎯 Métodos de moderación: {', '.join(mod_methods)}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ Métodos de moderación no encontrados")
            else:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores pueden usar este comando!")
            return

        # Comando !help - catálogo personalizado por rol
        if msg == "!help":
            help_lines = self.get_help_for_user(user_id, username).split('\n')
            for line in help_lines:
                if line.strip():
                    await self.highrise.send_whisper(user.id, line)
                    await asyncio.sleep(0.2)  # Pequeña pausa entre mensajes
            return

        # Comando !info - informazioni sul giocatore
        if msg == "!info":
            await self.show_user_info(user)
            return

        # Comando !role - mostrar roles de usuario
        if msg == "!role":
            role_info = self.get_user_role_info(user)
            await self.highrise.chat(f"🎭 @{user.username}: {role_info}")
            return
        
        # Comando !role list - mostrar lista de todos los roles (sin restricción)
        if msg == "!role list":
            roles_message = "🎭 LISTA DE ROLES:\n"
            roles_message += "👑 Propietario - Control total\n"
            roles_message += "🛡️ Administrador - Moderación y gestión\n"
            roles_message += "⚖️ Moderador - Moderación básica\n"
            roles_message += "⭐ VIP - Acceso a zonas especiales\n"
            roles_message += "👤 Usuario Normal - Acceso básico"
            await self.highrise.send_whisper(user.id, roles_message)
            return

        # Comando !info @username - informazioni su un altro giocatore
        if msg.startswith("!info @"):
            target_username = msg[7:].strip()
            await self.show_user_info_by_username(target_username)
            return

        # Sección !help interaction
        if msg == "!help interaction":
            await self.highrise.send_whisper(user.id, "🥊 COMANDOS DE INTERACCIÓN:\n!punch @user — golpear (cualquier distancia)\n!slap @user — bofetada (cualquier distancia)\n!flirt @user — coquetear (máx. 3 bloques)\n!scare @user — asustar (máx. 3 bloques)\n!electro @user — electricidad (máx. 3 bloques)\n!hug @user — abrazar (máx. 3 bloques)\n!ninja @user — ninja (máx. 3 bloques)\n!laugh @user — reír (máx. 3 bloques)\n!boom @user — explosión (máx. 3 bloques)")
            return

        # Sección !help teleport
        if msg == "!help teleport":
            await self.highrise.send_whisper(user.id, "📍 COMANDOS DE TELETRANSPORTE:\n!tplist — lista de puntos\n[nombre_punto] — teletransporte al punto\n!tele zonaVIP — zona VIP")
            return



        # Sección !help leaderboard
        if msg == "!help leaderboard":
            await self.highrise.send_whisper(user.id, "🏆 TABLA DE CLASIFICACIÓN:\n!leaderboard heart — top por corazones\n!leaderboard active — top por actividad")
            return

        # Sección !help heart
        if msg == "!help heart":
            await self.highrise.send_whisper(user.id, "❤️ COMANDO DE CORAZONES:\n!heart @usuario [cantidad] — enviar corazones\n\n💖 También puedes enviar corazones con reacciones!")
            return





        # Comando !emote list - Mostrar lista completa de emotes (máximo por mensaje)
        if msg == "!emote list":
            emote_names = []
            for k, v in emotes.items():
                emote_names.append(f"{k}:{v['name']}")

            # Calcular tamaño óptimo por mensaje (máximo ~400 caracteres)
            messages = []
            current_message = "📋 EMOTES:\n"
            
            for emote_entry in emote_names:
                # Si agregar este emote excede el límite, guardar mensaje actual y empezar uno nuevo
                if len(current_message) + len(emote_entry) + 2 > 400:
                    messages.append(current_message)
                    current_message = ""
                
                current_message += emote_entry + ", "
            
            # Agregar último mensaje
            if current_message:
                messages.append(current_message.rstrip(", "))
            
            # Enviar todos los mensajes
            for idx, message in enumerate(messages, 1):
                if idx == 1:
                    await self.highrise.send_whisper(user.id, message)
                else:
                    await self.highrise.send_whisper(user.id, message)
                await asyncio.sleep(0.3)
            
            await self.highrise.send_whisper(user.id, f"✅ Total: {len(emote_names)} emotes")
            return

        # Inicio rápido de animación por número
        if msg.isdigit():
            emote_number = msg
            emote = emotes.get(emote_number)
            if emote and emote["is_free"]:
                try:
                    users = (await self.highrise.get_room_users()).content
                    user_obj = next((u for u, _ in users if u.id == user.id), None)
                    if user_obj:
                        asyncio.create_task(self.send_emote_loop(user.id, emote["id"]))
                        await self.highrise.send_whisper(user.id, f"🎭 Iniciaste la animación: {emote['name']} (#{emote_number})")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ @{user.username}: No estás en la sala.")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error al iniciar animación #{emote_number} - {str(e)[:50]}")
            else:
                if not emote:
                    await self.highrise.send_whisper(user.id, f"❌ Número de animación #{emote_number} no existe. Usa números del 1 al 249.")
                else:
                    await self.highrise.send_whisper(user.id, f"❌ La animación #{emote_number} no es gratuita.")
            return

        # Comando !emote <número o nombre> o !emote @username <número o nombre> (VIP)
        if msg.startswith("!emote"):
            parts = msg.split()
            target_user_id = user.id  # Por defecto, el usuario que ejecuta el comando
            emote_key = msg[7:].strip()  # Por defecto, todo después de "!emote "

            # Verificamos si hay un @username en el comando
            if len(parts) >= 3 and parts[1].startswith("@"):
                target_username = parts[1][1:]  # Removemos el @
                emote_key = " ".join(parts[2:])  # El resto es la animación

                # Solo admin y propietario pueden usar animaciones en otros usuarios
                if not (self.is_admin(user_id) or user_id == OWNER_ID):
                    await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden usar animaciones en otros usuarios!")
                    return

                # Buscamos al usuario objetivo
                try:
                    users = (await self.highrise.get_room_users()).content
                    target_user = None
                    for u, pos in users:
                        if u.username == target_username:
                            target_user = u
                            break

                    if not target_user:
                        await self.highrise.send_whisper(user.id, f"❌ ¡Usuario {target_username} no encontrado en la sala!")
                        return

                    target_user_id = target_user.id

                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error buscando usuario: {e}")
                    return

            # Buscamos la animación
            emote = emotes.get(emote_key)
            if not emote:
                for e in emotes.values():
                    if e["name"].lower() == emote_key.lower() or e["id"].lower() == emote_key.lower():
                        emote = e
                        break

            if emote:
                if emote["is_free"]:
                    try:
                        asyncio.create_task(self.send_emote_loop(target_user_id, emote["id"]))
                        if target_user_id == user.id:
                            await self.highrise.send_whisper(user.id, f"🎭 Iniciaste la animación: {emote['name']}")
                        else:
                            await self.highrise.send_whisper(user.id, f"⭐ Activaste la animación '{emote['name']}' en @{target_username}")
                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ Error al activar animación - {str(e)[:50]}")
                else:
                    await self.highrise.send_whisper(user.id, f"❌ La animación '{emote_key}' no es gratuita.")
            else:
                await self.highrise.send_whisper(user.id, f"❌ No existe la animación '{emote_key}'. Usa !emote list para ver todas.")
            return

        # Inicio rápido de animación por nombre (sin !emote) o animación en otros usuarios (VIP)
        # Проверяем, что сообщение является названием существующей анимации
        emote_found = False
        for e in emotes.values():
            if e["name"].lower() == msg.lower() or e["id"].lower() == msg.lower():
                emote_found = True
                break

        # Проверяем, если сообщение "vip" - телепорт в VIP зону
        if msg.lower() == "vip":
            if self.is_vip_by_username(user.username) or user_id == OWNER_ID:
                try:

                    vip_position = Position(VIP_ZONE["x"], VIP_ZONE["y"], VIP_ZONE["z"])
                    await self.highrise.teleport(user_id, vip_position)
                    await self.highrise.send_whisper(user.id, f"⭐ @{user.username} se teletransportó a la zona VIP!")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error de teletransporte: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ No tienes estatus VIP!")
            return

        # Проверяем, если сообщение "dj" - телепорт в DJ зону (solo admin y propietario)
        if msg.lower() == "dj":
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden usar la zona DJ!")
                return

            try:
                # Cargamos la configuración para obtener la zona DJ
                config = load_config()
                dj_zone = config.get("dj_zone", {})

                if not dj_zone:
                    await self.highrise.send_whisper(user.id, "❌ ¡Zona DJ no establecida! Usa !setdj para establecerla.")
                    return


                dj_position = Position(dj_zone["x"], dj_zone["y"], dj_zone["z"])
                await self.highrise.teleport(user_id, dj_position)
                await self.highrise.send_whisper(user.id, f"🎵 @{user.username} se teletransportó a la zona DJ!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error de teletransporte: {e}")
            return

        # Проверяем, если сообщение "directivo" - телепорт en директорию (solo admin y propietario)
        if msg.lower() == "directivo":
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden usar la zona directiva!")
                return

            try:
                # Cargamos la configuración para obtener la zona directiva
                config = load_config()
                directivo_zone = config.get("directivo_zone", {})

                if not directivo_zone:
                    await self.highrise.send_whisper(user.id, "❌ ¡Zona directiva no establecida! Usa !setdirectivo para establecerla.")
                    return


                directivo_position = Position(directivo_zone["x"], directivo_zone["y"], directivo_zone["z"])
                await self.highrise.teleport(user_id, directivo_position)
                await self.highrise.send_whisper(user.id, f"👑 @{user.username} se teletransportó a la zona directiva!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error de teletransporte: {e}")
            return

        if msg and not msg.startswith("!") and not msg.isdigit() and emote_found:
            parts = msg.split()
            target_user_ids = [user.id]  # Por defecto, el usuario que ejecuta el comando
            emote_name = msg  # Por defecto, todo el mensaje es la animación
            target_usernames = []
            include_self = True  # Por defecto, incluir al usuario que ejecuta el comando

            # Verificamos si hay @usernames o "all" en el mensaje
            if len(parts) >= 2:
                # Verificamos si el primer elemento es @username (formato: @username animación)
                if parts[0].startswith("@"):
                    # Formato: @username animación - solo para el usuario especificado
                    target_username = parts[0][1:]  # Removemos el @
                    emote_name = " ".join(parts[1:])  # El resto es la animación
                    include_self = False  # No incluir al usuario que ejecuta el comando

                    # Solo admin y propietario pueden usar animaciones en otros usuarios
                    if not (self.is_admin(user_id) or user_id == OWNER_ID):
                        await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden usar animaciones en otros usuarios!")
                        return

                    # Buscamos al usuario objetivo
                    try:
                        users = (await self.highrise.get_room_users()).content
                        target_user = None
                        for u, pos in users:
                            if u.username == target_username:
                                target_user = u
                                break

                        if target_user:
                            target_user_ids = [target_user.id]
                            target_usernames = [target_username]
                        else:
                            await self.highrise.send_whisper(user.id, f"❌ ¡Usuario {target_username} no encontrado en la sala!")
                            return

                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ Error buscando usuario: {e}")
                        return
                else:
                    # Formato: animación @username - para ambos usuarios
                    emote_name = parts[0]  # La primera parte es la animación
                    target_parts = parts[1:]  # El resto son objetivos

                    # Solo admin y propietario pueden usar animaciones en otros usuarios
                    if not (self.is_admin(user_id) or user_id == OWNER_ID):
                        await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden usar animaciones en otros usuarios!")
                        return

                    # Buscamos a los usuarios objetivo
                    try:
                        users = (await self.highrise.get_room_users()).content
                        target_user_ids = []
                        target_usernames = []

                        for part in target_parts:
                            if part == "all":
                                # Solo admin y propietario pueden hacer emotes a todos
                                if not (self.is_admin(user_id) or user_id == OWNER_ID):
                                    await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden hacer emotes a todos los usuarios!")
                                    return
                                # Añadimos todos los usuarios excepto el bot
                                for u, pos in users:
                                    if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):  # Excluimos al bot
                                        target_user_ids.append(u.id)
                                        target_usernames.append(u.username)
                            elif part.startswith("@"):
                                target_username = part[1:]  # Removemos el @
                                target_user = None
                                for u, pos in users:
                                    if u.username == target_username:
                                        target_user = u
                                        break

                                if target_user:
                                    target_user_ids.append(target_user.id)
                                    target_usernames.append(target_username)
                                else:
                                    await self.highrise.send_whisper(user.id, f"❌ ¡Usuario {target_username} no encontrado en la sala!")
                                    return

                        if not target_user_ids:
                            await self.highrise.send_whisper(user.id, "❌ ¡No se encontraron usuarios objetivo!")
                            return

                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ Error buscando usuarios: {e}")
                        return

            # Buscamos la animación
            emote = None
            for e in emotes.values():
                if e["name"].lower() == emote_name.lower() or e["id"].lower() == emote_name.lower():
                    emote = e
                    break

            if emote:
                if emote["is_free"]:
                    try:
                        # Si include_self es True, añadimos al usuario que ejecuta el comando
                        if include_self and user.id not in target_user_ids:
                            target_user_ids.append(user.id)

                        # Ejecutamos la animación en todos los usuarios objetivo
                        for target_user_id in target_user_ids:
                            asyncio.create_task(self.send_emote_loop(target_user_id, emote["id"]))

                        # Mostramos mensaje apropiado
                        if len(target_user_ids) == 1 and target_user_ids[0] == user.id:
                            await self.highrise.send_whisper(user.id, f"🎭 Iniciaste la animación: {emote['name']}")
                        elif len(target_user_ids) == 1:
                            await self.highrise.send_whisper(user.id, f"⭐ Activaste la animación '{emote['name']}' en @{target_usernames[0]}")
                        elif len(target_user_ids) == 2:
                            if include_self:
                                await self.highrise.send_whisper(user.id, f"⭐ Activaste la animación '{emote['name']}' en ti mismo y @{target_usernames[0]}")
                            else:
                                await self.highrise.send_whisper(user.id, f"⭐ Activaste la animación '{emote['name']}' en @{target_usernames[0]} y @{target_usernames[1]}")
                        elif len(target_user_ids) == 3:
                            if include_self:
                                await self.highrise.send_whisper(user.id, f"⭐ Activaste la animación '{emote['name']}' en ti mismo, @{target_usernames[0]} y @{target_usernames[1]}")
                            else:
                                await self.highrise.send_whisper(user.id, f"⭐ Activaste la animación '{emote['name']}' en @{target_usernames[0]}, @{target_usernames[1]} y @{target_usernames[2]}")
                        else:
                            if include_self:
                                await self.highrise.send_whisper(user.id, f"⭐ Activaste la animación '{emote['name']}' en ti mismo y {len(target_usernames)} usuarios")
                            else:
                                await self.highrise.send_whisper(user.id, f"⭐ Activaste la animación '{emote['name']}' en {len(target_user_ids)} usuarios")
                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ Error al activar animación '{emote_name}' - {str(e)[:50]}")
                else:
                    await self.highrise.send_whisper(user.id, f"❌ La animación '{emote_name}' no es gratuita.")
            else:
                await self.highrise.send_whisper(user.id, f"❌ No existe la animación '{emote_name}'. Usa !emote list para ver todas.")
            return

        # Comando stop - detener animación (propia o de otro usuario para VIP)
        if msg == "stop" or msg == "!stop" or msg == "0":
            print(f"DEBUG: Comando stop recibido de {user.username} (ID: {user.id})")
            print(f"DEBUG: Mensaje: '{msg}'")
            await self.stop_emote_loop(user.id)
            await self.highrise.send_whisper(user.id, f"🛑 Detuviste tu animación.")
            print(f"DEBUG: Mensaje público enviado para {user.username}")
            return

        # Comando !stop @username - detener animación de otros usuarios (VIP) 
        # Comando !stop all - detener animaciones de todos (solo Admin)
        if msg.startswith("!stop "):
            stop_target = msg[6:].strip()  # Removemos "!stop "

            # Verificar permisos según el comando
            if stop_target == "all":
                # Solo administradores pueden parar todas las animaciones
                if not self.is_admin(user_id):
                    await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores pueden detener todas las animaciones!")
                    return
            else:
                # VIPs y administradores pueden detener animación de un usuario específico
                if not (self.is_vip(user_id) or self.is_admin(user_id)):
                    await self.highrise.send_whisper(user.id, "❌ ¡Solo VIP y administradores pueden detener animaciones de otros usuarios!")
                    return

            try:
                users = (await self.highrise.get_room_users()).content
                target_user_ids = []
                target_usernames = []

                if stop_target == "all":
                    # Detenemos animaciones de todos excepto el bot (solo admin)
                    for u, pos in users:
                        if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):  # Excluimos al bot
                            target_user_ids.append(u.id)
                            target_usernames.append(u.username)
                elif stop_target.startswith("@"):
                    # Detenemos animación de un usuario específico
                    target_username = stop_target[1:]
                    target_user = None
                    for u, pos in users:
                        if u.username == target_username:
                            target_user = u
                            break

                    if target_user:
                        target_user_ids.append(target_user.id)
                        target_usernames.append(target_username)
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ ¡Usuario {target_username} no encontrado en la sala!")
                        return

                if not target_user_ids:
                    await self.highrise.send_whisper(user.id, "❌ ¡No se encontraron usuarios objetivo!")
                    return

                # Detenemos animaciones
                for target_user_id in target_user_ids:
                    await self.stop_emote_loop(target_user_id)

                # Mostramos mensaje apropiado
                if len(target_user_ids) == 1:
                    await self.highrise.send_whisper(user.id, f"🛑 Detuviste la animación de @{target_usernames[0]}")
                elif len(target_user_ids) == 2:
                    await self.highrise.send_whisper(user.id, f"🛑 Detuviste las animaciones de @{target_usernames[0]} y @{target_usernames[1]}")
                elif len(target_user_ids) == 3:
                    await self.highrise.send_whisper(user.id, f"🛑 Detuviste las animaciones de @{target_usernames[0]}, @{target_usernames[1]} y @{target_usernames[2]}")
                else:
                    await self.highrise.send_whisper(user.id, f"🛑 Detuviste las animaciones de {len(target_user_ids)} usuarios")

            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error deteniendo animaciones: {e}")
            return

        # Comando stopall - detener todas las animaciones (solo admin)
        if msg == "!stopall":
            if self.is_admin(user_id):
                # Detenemos todas las animaciones activas
                active_users = list(ACTIVE_EMOTES.keys())
                for active_user_id in active_users:
                    await self.stop_emote_loop(active_user_id)
                await self.highrise.send_whisper(user.id, f"🛑 Detuviste todas las animaciones en la sala.")
            else:
                await self.highrise.send_whisper(user.id, "❌ Solo administradores pueden usar este comando.")
            return

        # Comando temporal para ver ID
        if msg == "!myid":
            await self.highrise.send_whisper(user.id, f"🆔 Tu ID de usuario es: {user_id}")
            return

        # Comando !game love
        if msg.startswith("!game love"):
            parts = msg.split()
            if len(parts) >= 3:
                user1 = parts[2]
                user2 = parts[3] if len(parts) > 3 else "desconocido"
                love_percent = random.randint(1, 100)
                love_emoji = "💘" if love_percent > 80 else "💕" if love_percent > 60 else "💖" if love_percent > 40 else "💔"
                await self.highrise.chat(f"💘 Medidor de amor: {user1} + {user2} = {love_percent}% {love_emoji}")
            return

        # Comando !leaderboard
        if msg.startswith("!leaderboard"):
            print("DEBUG: leaderboard command received:", msg)
            parts = msg.split()
            if len(parts) == 1:
                await self.highrise.send_whisper(user.id, "🏆 !leaderboard heart\n!leaderboard active")
                return
            elif len(parts) > 1:
                lb_type = parts[1].lower()
                if lb_type == "heart":
                    # Top por corazones
                    print(f"DEBUG: USER_HEARTS = {USER_HEARTS}")
                    print(f"DEBUG: USER_NAMES = {USER_NAMES}")

                    # Фильтруем USER_HEARTS, оставляя только записи с ID (длинные строки)
                    valid_hearts = {k: v for k, v in USER_HEARTS.items() if len(k) > 10}  # ID обычно длинные
                    print(f"DEBUG: Валидные записи USER_HEARTS: {valid_hearts}")

                    top = sorted(valid_hearts.items(), key=lambda x: x[1], reverse=True)[:10]
                    users = (await self.highrise.get_room_users()).content
                    id_to_name = {u.id: u.username for u, _ in users}
                    print(f"DEBUG: Пользователи в комнате: {id_to_name}")

                    lines = [f"❤️ Top por corazones:"]
                    count = 0
                    for i, (uid, count_val) in enumerate(top, 1):
                        # Сначала пробуем найти имя в текущих пользователях комнаты
                        uname = id_to_name.get(uid)
                        if not uname:
                            # Если не найден в комнате, пробуем в USER_NAMES
                            uname = USER_NAMES.get(uid)
                        if not uname:
                            # Если все еще не найден, используем ID без обрезки
                            uname = f"User_{uid[:8]}"

                        print(f"DEBUG: Для {uid} найдено имя: {uname}")
                        lines.append(f"{i}. {uname}: {count_val}")
                        count += 1
                    if count == 0:
                        lines.append("Sin datos")
                    await self.highrise.send_whisper(user.id, "\n".join(lines))
                    return
                elif lb_type == "active":
                    # Top por actividad
                    print(f"DEBUG: USER_ACTIVITY = {USER_ACTIVITY}")

                    # Фильтруем USER_ACTIVITY, оставляя только записи с ID (длинные строки)
                    valid_activity = {k: v for k, v in USER_ACTIVITY.items() if len(k) > 10}  # ID обычно длинные
                    print(f"DEBUG: Валидные записи USER_ACTIVITY: {valid_activity}")

                    top = sorted(valid_activity.items(), key=lambda x: x[1]["messages"], reverse=True)[:10]
                    users = (await self.highrise.get_room_users()).content
                    id_to_name = {u.id: u.username for u, _ in users}
                    print(f"DEBUG: Пользователи в комнате для активности: {id_to_name}")

                    lines = [f"💬 Top por actividad:"]
                    count = 0
                    for i, (uid, data) in enumerate(top, 1):
                        # Сначала пробуем найти имя в текущих пользователях комнаты
                        uname = id_to_name.get(uid)
                        if not uname:
                            # Если не найден в комнате, пробуем в USER_NAMES
                            uname = USER_NAMES.get(uid)
                        if not uname:
                            # Если все еще не найден, используем ID без обрезки
                            uname = f"User_{uid[:8]}"

                        print(f"DEBUG: Для активности {uid} найдено имя: {uname}")
                        lines.append(f"{i}. {uname}: {data['messages']}")
                        count += 1
                    if count == 0:
                        lines.append("Sin datos")
                    await self.highrise.send_whisper(user.id, "\n".join(lines))
                    return
            await self.highrise.send_whisper(user.id, "Usa: !leaderboard heart o !leaderboard active")
            return

        # Comando !trackme
        if msg == "!trackme":
            await self.highrise.send_whisper(user.id, f"Activaste seguimiento de actividad!")
            return

        # Comando !heartall - отправить сердечки всем игрокам в комнате (только для Owner)
        if msg == "!heartall":
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede enviar corazones a todos!")
                return

            try:
                users = (await self.highrise.get_room_users()).content
                heart_count = 0

                for u, pos in users:
                    if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):  # Исключаем бота
                        # Добавляем сердечко в счетчик
                        self.add_user_hearts(u.id, 1, u.username)
                        # Отправляем визуальную реакцию сердечка
                        await self.highrise.react("heart", u.id)
                        heart_count += 1
                        await asyncio.sleep(0.1)  # Небольшая задержка между отправками

                await self.highrise.send_whisper(user.id, f"💖 Enviaste ❤️ a todos los {heart_count} jugadores en la sala!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error enviando corazones: {e}")
            return

        # Comando !heart
        if msg.startswith("!heart"):
            print(f"DEBUG: Команда !heart получена: {msg}")
            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                hearts_count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1

                print(f"DEBUG: target_username = {target_username}, hearts_count = {hearts_count}")

                # Buscamos el usuario objetivo
                try:
                    users = (await self.highrise.get_room_users()).content
                    print(f"DEBUG: Пользователи в комнате: {[(u.username, u.id) for u, pos in users]}")

                    target_user_obj = None
                    for u, pos in users:
                        if u.username == target_username:
                            target_user_obj = u
                            break

                    if not target_user_obj:
                        print(f"DEBUG: Пользователь {target_username} не найден")
                        await self.highrise.send_whisper(user.id, f"❌ ¡Usuario {target_username} no encontrado en la sala!")
                        return

                    target_user_id = target_user_obj.id
                    print(f"DEBUG: Найден пользователь {target_username} с ID {target_user_id}")

                    # Проверяем права пользователя
                    is_admin_or_owner = self.is_admin(user_id) or user_id == OWNER_ID
                    is_vip = self.is_vip_by_username(user.username)

                    print(f"DEBUG: Пользователь {user.username} - админ/владелец: {is_admin_or_owner}, VIP: {is_vip}")

                    if is_admin_or_owner:
                        # Администраторы и владелец могут давать до 100 сердечек
                        if hearts_count > 100:
                            await self.highrise.send_whisper(user.id, "❌ ¡Máximo 100 corazones por comando!")
                            return

                        self.add_user_hearts(target_user_id, hearts_count, target_username)
                        await self.highrise.send_whisper(user.id, f"Enviaste {hearts_count} ❤️ a {target_username}")

                        # Отправляем визуальные реакции сердечек (максимум 30 для производительности)
                        visual_hearts = min(hearts_count, 30)  # Ограничиваем визуальные сердечки до 30
                        for _ in range(visual_hearts):
                            await self.highrise.react("heart", target_user_id)
                            await asyncio.sleep(0.05)  # Уменьшаем задержку для быстрой отправки

                    elif is_vip or True:  # VIP и обычные игроки
                        # VIP и обычные игроки могут давать только 1 сердечко
                        if hearts_count > 1:
                            await self.highrise.send_whisper(user.id, "❌ ¡Solo puedes enviar 1 corazón por comando!")
                            return

                        self.add_user_hearts(target_user_id, 1, target_username)
                        await self.highrise.send_whisper(user.id, f"Enviaste ❤️ a {target_username}")
                        # Отправляем визуальную реакцию сердечка
                        await self.highrise.react("heart", target_user_id)

                except Exception as e:
                    print(f"DEBUG: Ошибка в команде !heart: {e}")
                    await self.highrise.send_whisper(user.id, f"❌ Error enviando corazón: {e}")
            else:
                print(f"DEBUG: Недостаточно параметров в команде !heart")
                await self.highrise.send_whisper(user.id, "❌ Usa: !heart @username [cantidad]")
            return

        # Comando !flash [x] [y] [z] - teletransporte solo para subir y bajar entre pisos
        if msg.startswith("!flash"):
            parts = msg.split()
            if len(parts) >= 4:
                try:
                    x = float(parts[1])
                    y = float(parts[2])
                    z = float(parts[3])

                    # Obtener posición actual del usuario
                    users = (await self.highrise.get_room_users()).content
                    current_position = None
                    for u, pos in users:
                        if u.id == user.id:
                            current_position = pos
                            break

                    if current_position:
                        # Verificar que solo sea cambio de altura (subir/bajar pisos)
                        y_difference = abs(current_position.y - y)
                        x_difference = abs(current_position.x - x)
                        z_difference = abs(current_position.z - z)
                        
                        # Flash solo para cambios de piso (Y) con movimiento mínimo en X y Z
                        if y_difference < 1.0:
                            await self.highrise.send_whisper(user.id, "❌ ¡Flash solo para subir/bajar entre pisos! Debe cambiar altura (Y)")
                            return
                        
                        if x_difference > 3.0 or z_difference > 3.0:
                            await self.highrise.send_whisper(user.id, "❌ ¡Flash solo para subir/bajar pisos! No te alejes mucho horizontalmente")
                            return

                        # Verificamos si no está en zona prohibida
                        if not self.is_in_forbidden_zone(x, y, z):
                            pos = Position(x, y, z)
                            await self.highrise.teleport(user.id, pos)
                            await self.highrise.send_whisper(user.id, f"⚡ Flasheaste entre pisos ({x}, {y}, {z})")
                            log_event("FLASHMODE", f"{user.username} usó flash entre pisos a {x}, {y}, {z}")
                        else:
                            await self.highrise.send_whisper(user.id, f"❌ ¡No puedes teletransportarte a una zona prohibida!")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ Error obteniendo tu posición actual")

                except ValueError:
                    await self.highrise.send_whisper(user.id, "❌ Usa: !flash [x] [y] [z] (ejemplo: !flash 5 17 3)")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !flash [x] [y] [z] (ejemplo: !flash 5 17 3)")
            return





        # Comando !inventory - consultar items del bot (solo propietario y admin)
        if msg == "!inventory":
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo propietario y administradores pueden usar este comando!")
                return
            
            try:
                inventory_response = await self.highrise.get_inventory()
                if isinstance(inventory_response, Error):
                    await self.highrise.send_whisper(user.id, f"❌ Error obteniendo inventario: {inventory_response}")
                    return
                
                inventory = inventory_response.items
                if inventory:
                    # Dividir en chunks para no exceder límite de mensaje
                    chunk_size = 10
                    total_items = len(inventory)
                    
                    await self.highrise.send_whisper(user.id, f"👔 INVENTARIO DEL BOT ({total_items} items):")
                    
                    for i in range(0, len(inventory), chunk_size):
                        chunk = inventory[i:i+chunk_size]
                        items_list = []
                        for idx, item in enumerate(chunk, i+1):
                            items_list.append(f"{idx}. {item.type}: {item.id}")
                        
                        await self.highrise.send_whisper(user.id, "\n".join(items_list))
                        await asyncio.sleep(0.3)
                else:
                    await self.highrise.send_whisper(user.id, "📦 El inventario del bot está vacío")
                    
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error consultando inventario: {e}")
            return
        
        # Comando !wallet
        if msg == "!wallet":
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede ver el balance del bot!")
                return
            balance = await self.get_bot_wallet_balance()
            await self.highrise.chat(f"💰 Balance del bot: {balance} oro")
            return

        # Comando !restart - reiniciar bot (solo propietario)
        if msg.startswith("!restart"):
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede reiniciar el bot!")
                return
            await self.highrise.send_whisper(user.id, "🔄 Reiniciando bot...")
            await self.highrise.send_whisper(user.id, "⚠️ El bot se detendrá en 3 segundos!")
            await self.highrise.send_whisper(user.id, "💡 Usa restart_bot.bat para reinicio automático!")
            try:
                asyncio.create_task(self.delayed_restart())
            except Exception as e:
                print(f"Error creando tarea de reinicio: {e}")
            return

        # Comando !say [mensaje] - enviar mensaje a la sala (solo propietario y admin)
        if msg.startswith("!say "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo propietario y administradores pueden usar este comando!")
                return
            
            message_to_send = msg[5:].strip()
            if message_to_send:
                await self.highrise.chat(message_to_send)
                await self.highrise.send_whisper(user.id, f"✅ Mensaje enviado: {message_to_send}")
                log_event("SAY", f"{user.username} envió mensaje: {message_to_send}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !say [mensaje]")
            return
        
        # Comando !tome — teletransportar bot al propietario
        if msg == "!tome":
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede usar este comando!")
                return
            try:
                users = (await self.highrise.get_room_users()).content

                # Debug: mostrar todos los usuarios en la sala
                print(f"DEBUG !tome: Usuarios en sala:")
                for u, pos in users:
                    print(f"  - {u.username} (ID: {u.id})")

                # Busca el bot automáticamente - mejor detección
                bot_user = None

                # Método 1: Buscar por ID específico conocido
                if not bot_user:
                    for u, _ in users:
                        if u.id == "681d54aa4cedce763169580f":
                            bot_user = u
                            print(f"DEBUG !tome: Bot encontrado por ID: {u.username}")
                            break

                # Método 2: Buscar por nombres específicos del bot
                if not bot_user:
                    for u, _ in users:
                        username_upper = u.username.upper()
                        username_lower = u.username.lower()
                        # Buscar nombre exacto primero
                        if u.username == "NOCTURNO_BOT" or username_upper == "NOCTURNO_BOT":
                            bot_user = u
                            print(f"DEBUG !tome: Bot NOCTURNO_BOT encontrado: {u.username}")
                            break
                        # Luego buscar patrones comunes
                        elif any(name in username_lower for name in ["nocturno", "bot", "glux", "highrise"]):
                            bot_user = u
                            print(f"DEBUG !tome: Bot encontrado por patrón: {u.username}")
                            break

                # Método 3: Si no se encuentra, usar el primer usuario que no sea el propietario
                if not bot_user and len(users) > 1:
                    for u, _ in users:
                        if u.id != user_id:  # No el usuario que ejecuta el comando
                            bot_user = u
                            print(f"DEBUG !tome: Usando primer usuario como bot: {u.username}")
                            break

                if bot_user:
                    user_pos = next((pos for u, pos in users if u.id == user_id), None)
                    if user_pos:
                        await self.highrise.teleport(bot_user.id, user_pos)
                        await self.highrise.send_whisper(user.id, f"🤖 Bot {bot_user.username} teletransportado a @{user.username}")
                        print(f"DEBUG !tome: Éxito - {bot_user.username} teletransportado")
                    else:
                        await self.highrise.send_whisper(user.id, "❌ No se pudo obtener tu posición!")
                        print(f"DEBUG !tome: Error - no se pudo obtener posición del propietario")
                else:
                    await self.highrise.send_whisper(user.id, "❌ ¡Bot no encontrado en la sala!")
                    print(f"DEBUG !tome: Error - bot no encontrado")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error de teletransporte: {e}")
                print(f"DEBUG !tome: Excepción: {e}")
            return

        # Comando !outfit [número] - cambio de ropa del bot usando outfits guardados
        if msg.startswith("!outfit"):
            if not (self.is_admin(user_id) or self.is_moderator(user_id)):
                await self.highrise.send_whisper(user.id, "¡No tienes acceso a este comando!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                try:
                    outfit_number = int(parts[1])
                    
                    if outfit_number in SAVED_OUTFITS:
                        # Usar outfit guardado
                        await self.highrise.set_outfit(SAVED_OUTFITS[outfit_number])
                        await self.highrise.send_whisper(user.id, f"👕 Outfit #{outfit_number} aplicado")
                        log_event("OUTFIT", f"Outfit #{outfit_number} aplicado por {user.username}")
                    else:
                        await self.highrise.send_whisper(user.id, f"❌ Outfit #{outfit_number} no existe. Usa !copyoutfit para guardar outfits.")
                        
                except ValueError:
                    await self.highrise.send_whisper(user.id, "❌ Usa: !outfit [número]")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error de cambio de ropa: {e}")
            else:
                # Mostrar lista de outfits guardados
                if SAVED_OUTFITS:
                    outfits_list = ", ".join([f"#{num}" for num in sorted(SAVED_OUTFITS.keys())])
                    await self.highrise.send_whisper(user.id, f"👔 Outfits guardados: {outfits_list}\n❌ Usa: !outfit [número]")
                else:
                    await self.highrise.send_whisper(user.id, "📦 No hay outfits guardados. Usa !copyoutfit para guardar uno.")
            return

        # Comando !flossmode - activar modo floss falso
        if msg == "!flossmode":
            if not (user_id == OWNER_ID or self.is_admin(user_id)):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario y administradores pueden cambiar el modo del bot!")
                return

            try:
                # Detener tarea actual si existe
                if self.current_emote_task and not self.current_emote_task.done():
                    self.current_emote_task.cancel()
                    await asyncio.sleep(0.5)  # Esperar a que se cancele

                # Iniciar modo floss real
                self.current_emote_task = asyncio.create_task(self.start_floss_mode())
                await self.highrise.send_whisper(user.id, "🕺 ¡Modo FLOSS activado! El bot solo hará dance-floss en bucle infinito")
                await self.highrise.chat("🕺 Modo FLOSS activado por admin")
                log_event("BOT", f"Modo floss activado por {user.username}")

            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error activando modo floss: {e}")
                log_event("ERROR", f"Error activando modo floss: {e}")
            return

        # Comando !automode - activar ciclo automático de 224 emotes
        if msg == "!automode":
            if not (user_id == OWNER_ID or self.is_admin(user_id)):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario y administradores pueden cambiar el modo del bot!")
                return

            try:
                # Detener tarea actual si existe
                if self.current_emote_task and not self.current_emote_task.done():
                    self.current_emote_task.cancel()
                    await asyncio.sleep(0.5)  # Esperar a que se cancele

                # Iniciar ciclo automático de 224 emotes
                self.current_emote_task = asyncio.create_task(self.start_auto_emote_cycle())
                await self.highrise.send_whisper(user.id, "🎭 ¡Modo AUTOMÁTICO activado! El bot ejecutará los 224 emotes en secuencia")
                await self.highrise.chat("🎭 Modo AUTOMÁTICO activado por admin")
                log_event("BOT", f"Modo automático activado por {user.username}")

            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error activando modo automático: {e}")
                log_event("ERROR", f"Error activando modo automático: {e}")
            return

        # Comando !mimic [@usuario] - imitar interacción social (solo propietario y admin)
        if msg.startswith("!mimic "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo propietario y administradores pueden usar este comando!")
                return
            
            target_username = msg[7:].strip().replace("@", "")
            try:
                users = (await self.highrise.get_room_users()).content
                target_user = None
                
                for u, pos in users:
                    if u.username == target_username:
                        target_user = u
                        break
                
                if not target_user:
                    await self.highrise.send_whisper(user.id, f"❌ Usuario {target_username} no encontrado")
                    return
                
                # Copiar outfit del usuario objetivo
                target_outfit = await self.highrise.get_user_outfit(target_user.id)
                await self.highrise.set_outfit(target_outfit.outfit)
                
                # Copiar posición del usuario objetivo
                target_position = None
                for u, pos in users:
                    if u.id == target_user.id:
                        target_position = pos
                        break
                
                if target_position and isinstance(target_position, Position):
                    mimic_position = Position(target_position.x + 0.5, target_position.y, target_position.z + 0.5)
                    await self.highrise.teleport(self.bot_id, mimic_position)
                
                await self.highrise.send_whisper(user.id, f"🎭 Bot imitando a @{target_username}")
                await self.highrise.chat(f"🎭 ¡Soy @{target_username}!")
                log_event("MIMIC", f"{user.username} activó mimic de {target_username}")
                
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error en mimic: {e}")
            return
        
        # Comando !copyoutfit - copiar outfit del usuario al bot y guardarlo numerado
        if msg == "!copyoutfit":
            if not (user_id == OWNER_ID or self.is_admin(user_id)):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario y administradores pueden usar este comando!")
                return

            try:
                # Obtener el outfit del usuario que ejecuta el comando
                user_outfit = await self.highrise.get_user_outfit(user.id)

                # Aplicar el outfit al bot
                await self.highrise.set_outfit(user_outfit.outfit)

                # Guardar outfit con número
                outfit_number = len(SAVED_OUTFITS) + 1
                SAVED_OUTFITS[outfit_number] = user_outfit.outfit

                await self.highrise.send_whisper(user.id, f"👔 Outfit copiado y guardado como #{outfit_number}")
                log_event("ADMIN", f"Outfit copiado y guardado #{outfit_number}: {user.username} -> bot")

            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error copiando outfit: {e}")
                log_event("ERROR", f"Error copiando outfit de {user.username}: {e}")
            return

        # Comando !room - cambio de sala del bot
        if msg.startswith("!room"):
            if not (self.is_admin(user_id) or self.is_moderator(user_id)):
                await self.highrise.send_whisper(user.id, "¡No tienes acceso a este comando!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                room_name = parts[1]
                try:
                    # Aquí irá la lógica de cambio de sala del bot
                    await self.highrise.send_whisper(user.id, f"🏠 Transferiste el bot a la sala: {room_name}")
                    log_event("ROOM", f"Cambio de sala: {user.username} -> {room_name}")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error de cambio de sala: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !room [nombre_sala]")
            return

        # Comando !setdirectivo - сохранить точку директории (только для Owner)
        if msg == "!setdirectivo":
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede establecer la zona directiva!")
                return

            try:
                # Obtenemos la posición del usuario
                users = (await self.highrise.get_room_users()).content
                user_obj = None
                user_position = None
                for u, pos in users:
                    if u.id == user_id:
                        user_obj = u
                        user_position = pos
                        break

                if user_obj and user_position:
                    # Actualizamos la zona directiva en la configuración
                    new_directivo_zone = {"x": user_position.x, "y": user_position.y, "z": user_position.z}

                    # Guardamos en config.json
                    config = load_config()
                    config["directivo_zone"] = new_directivo_zone
                    with open("config.json", "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)

                    await self.highrise.send_whisper(user.id, f"👑 Zona directiva establecida en: X={new_directivo_zone['x']}, Y={new_directivo_zone['y']}, Z={new_directivo_zone['z']}")
                else:
                    await self.highrise.send_whisper(user.id, "¡Error obteniendo posición del usuario!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error estableciendo zona directiva: {e}")
            return

        # Comando !dj - acceso al panel DJ
        if msg == "!dj":
            if not (self.is_admin(user_id) or self.is_moderator(user_id)):
                await self.highrise.send_whisper(user.id, "¡No tienes acceso a este comando!")
                return

            try:
                # Aquí irá la lógica de acceso al panel DJ
                await self.highrise.send_whisper(user.id, f"🎵 Obtuviste acceso al panel DJ!")
                log_event("DJ", f"Acceso a DJ: {user.username}")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error de acceso a DJ: {e}")
            return

        # Comando !music - control de música
        if msg.startswith("!music"):
            if not (self.is_admin(user_id) or self.is_moderator(user_id)):
                await self.highrise.send_whisper(user.id, "¡No tienes acceso a este comando!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                action = parts[1].lower()
                if action == "play":
                    await self.highrise.send_whisper(user.id, f"🎵 Reprodujiste música!")
                elif action == "stop":
                    await self.highrise.send_whisper(user.id, f"🔇 Detuviste la música!")
                elif action == "pause":
                    await self.highrise.send_whisper(user.id, f"⏸️ Pausaste la música!")
                else:
                    await self.highrise.send_whisper(user.id, "❌ Usa: !music [play/stop/pause]")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !music [play/stop/pause]")
            return

        # Comando !tip
        if msg.startswith("!tip"):
            global BOT_WALLET

            if not (self.is_admin(user_id) or self.is_moderator(user_id)):
                await self.highrise.send_whisper(user.id, "¡No tienes acceso a este comando!")
                return

            parts = msg.split()
            if len(parts) >= 3:
                tip_type = parts[1]
                try:
                    amount = int(parts[2])
                except ValueError:
                    await self.highrise.send_whisper(user.id, "❌ ¡Cantidad de oro inválida!")
                    return

                if tip_type == "all" and 1 <= amount <= 5:
                    # Dar oro a todos en la sala
                    try:
                        users = (await self.highrise.get_room_users()).content

                        # Encontrar ID del bot (verificar varias opciones de nombres)
                        bot_user = None
                        for u, pos in users:
                            # Verificar nombre específico NOCTURNO_BOT primero
                            if u.username == "NOCTURNO_BOT" or u.username.upper() == "NOCTURNO_BOT":
                                bot_user = u
                                print(f"Bot NOCTURNO_BOT encontrado: {u.username} con ID: {u.id}")
                                break
                            # Verificar diferentes variantes de nombres del bot
                            elif u.username.lower() in ["highrisebot", "gluxbot", "bot"] or any(name in u.username.lower() for name in ["nocturno", "bot", "glux", "highrise"]):
                                bot_user = u
                                print(f"Bot encontrado: {u.username} con ID: {u.id}")
                                break

                        # Si el bot no se encuentra, usar el primer usuario como bot (temporalmente)
                        if bot_user is None:
                            print("Bot no encontrado, usando primer usuario")
                            bot_user = users[0][0] if users else None

                        # Información de depuración
                        print(f"Total de usuarios en sala: {len(users)}")
                        for u, pos in users:
                            print(f"Usuario: {u.username} (ID: {u.id})")

                        # Excluir bot de la lista de destinatarios
                        available_users = [u for u, pos in users if bot_user and u.id != bot_user.id]
                        user_count = len(available_users)
                        total_cost = user_count * amount

                        print(f"Usuarios disponibles (sin bot): {user_count}")
                        print(f"Bot: {bot_user.username if bot_user else 'No encontrado'}")

                        if user_count == 0:
                            await self.highrise.send_whisper(user.id, "❌ ¡No hay usuarios para dar oro!")
                            return

                        # Verificar balance real del bot
                        real_balance = await self.get_bot_wallet_balance()
                        if total_cost > real_balance:
                            await self.highrise.send_whisper(user.id, f"❌ ¡Oro insuficiente! Necesario: {total_cost}, disponible: {real_balance}")
                            return

                        # Dar oro a todos los usuarios (excepto bot)
                        for u in available_users:
                            try:
                                # Convertir cantidad a barras de oro
                                tip_bars = self.convert_to_gold_bars(amount)
                                if tip_bars:
                                    await self.highrise.tip_user(u.id, tip_bars)
                                else:
                                    print(f"No se pudo convertir {amount} a barras de oro")
                            except Exception as e:
                                print(f"Error enviando oro a {u.username}: {e}")

                        await self.highrise.chat(f"💰 ¡Bot dio {amount} oro a todos los {user_count} jugadores en la sala!")

                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ Error dando oro: {e}")

                elif tip_type == "only" and amount > 0:
                    # Dar oro a usuarios aleatorios
                    try:
                        users = (await self.highrise.get_room_users()).content
                        # Encontrar ID del bot (verificar varias opciones de nombres)
                        bot_user = None
                        for u, pos in users:
                            # Verificar nombre específico NOCTURNO_BOT primero
                            if u.username == "NOCTURNO_BOT" or u.username.upper() == "NOCTURNO_BOT":
                                bot_user = u
                                print(f"Bot NOCTURNO_BOT encontrado: {u.username} con ID: {u.id}")
                                break
                            # Verificar diferentes variantes de nombres del bot
                            elif u.username.lower() in ["highrisebot", "gluxbot", "bot"] or any(name in u.username.lower() for name in ["nocturno", "bot", "glux", "highrise"]):
                                bot_user = u
                                print(f"Bot encontrado: {u.username} con ID: {u.id}")
                                break

                        # Si el bot no se encuentra, usar el primer usuario como bot (temporalmente)
                        if bot_user is None:
                            print("Bot no encontrado, usando primer usuario")
                            bot_user = users[0][0] if users else None

                        # Información de depuración
                        print(f"Total de usuarios en sala: {len(users)}")
                        for u, pos in users:
                            print(f"Usuario: {u.username} (ID: {u.id})")

                        # Excluir bot de la lista
                        available_users = [u for u, pos in users if bot_user and u.id != bot_user.id]

                        print(f"Usuarios disponibles (sin bot): {len(available_users)}")
                        print(f"Bot: {bot_user.username if bot_user else 'No encontrado'}")

                        if len(available_users) == 0:
                            await self.highrise.send_whisper(user.id, "❌ ¡No hay usuarios para dar oro!")
                            return

                        # Seleccionar usuarios aleatorios
                        num_users = min(amount, len(available_users))
                        selected_users = random.sample(available_users, num_users)
                        total_cost = num_users * 5  # 5 oro a cada uno

                        # Verificar balance real del bot
                        real_balance = await self.get_bot_wallet_balance()
                        if total_cost > real_balance:
                            await self.highrise.send_whisper(user.id, f"❌ ¡Oro insuficiente! Necesario: {total_cost}, disponible: {real_balance}")
                            return

                        # Dar oro a usuarios seleccionados
                        for u in selected_users:
                            try:
                                # Convertir 5 oro a barras de oro
                                tip_bars = self.convert_to_gold_bars(5)
                                if tip_bars:
                                    await self.highrise.tip_user(u.id, tip_bars)
                                else:
                                    print(f"No se pudo convertir 5 a barras de oro")
                            except Exception as e:
                                print(f"Error enviando oro a {u.username}: {e}")

                        user_names = ", ".join([u.username for u in selected_users])
                        await self.highrise.chat(f"💰 Bot dio 5 oro a {num_users} usuarios aleatorios: {user_names}")

                    except Exception as e:
                        await self.highrise.send_whisper(user.id, f"❌ Error al dar oro: {e}")
                else:
                    await self.highrise.send_whisper(user.id, "❌ ¡Formato de comando inválido! Usa: !tip all [1-5] o !tip only [X]")
            else:
                await self.highrise.send_whisper(user.id, "❌ ¡Formato de comando inválido! Usa: !tip all [1-5] o !tip only [X]")
            return

        # Comandos de moderación
        if msg.startswith("!kick") or msg.startswith("!ban"):
            if not (self.is_admin(user_id) or self.is_moderator(user_id)):
                await self.highrise.send_whisper(user.id, "¡No tienes acceso a este comando!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                command = parts[0]
                try:
                    users = (await self.highrise.get_room_users()).content
                    target_user = None
                    for u, pos in users:
                        if u.username == target_username:
                            target_user = u
                            break
                    if not target_user:
                        await self.highrise.send_whisper(user.id, f"❌ Usuario {target_username} no encontrado en la sala!")
                        return
                    # Moderation through API
                    if command == "!kick":
                        log_event("MODERATION", f"Intento kick: {user.username} -> {target_username}")
                        try:
                            await self.highrise.moderate_room(target_user.id, "kick")
                            await self.highrise.send_whisper(user.id, f"👢 Expulsaste a {target_username} de la sala")
                            log_event("SUCCESS", f"Kick exitoso: {target_username}")
                        except Exception as e:
                            log_event("ERROR", f"Error kick: {e}")
                            await self.highrise.send_whisper(user.id, f"❌ Error kick: {e}")
                    elif command == "!ban":
                        # Real ban through API (1 day = 86400 seconds)
                        log_event("MODERATION", f"Intento ban: {user.username} -> {target_username}")
                        try:
                            await self.highrise.moderate_room(target_user.id, "ban", 86400)
                            await self.highrise.send_whisper(user.id, f"🚫 Baneaste a {target_username} por 1 día")
                            log_event("SUCCESS", f"Ban exitoso: {target_username}")
                        except Exception as e:
                            log_event("ERROR", f"Error ban: {e}")
                            await self.highrise.send_whisper(user.id, f"❌ Error ban: {e}")

                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error de moderación: {e}")
            return

        # Comando !vip - показать comandos para VIP usuarios
        if msg == "!vip":
            if not self.is_vip_by_username(user.username):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo VIP pueden ver esta sección!")
                return
            await self.highrise.send_whisper(user.id, "⭐ COMANDOS VIP:\n!flash [x] [y] [z] - teleport to coordinates\nvip - teleport to VIP zone\n!tele @user - teleport to user\n!emote @user [animation] - animation on user\n[animation] @user - mutual animation\n@user [animation] - animation on user\n!stop @user all - stop user animations")
            return


        # Comando !givevip - dar estatus VIP (mantenido para compatibilidad)
        if msg.startswith("!givevip"):
            # Owner y Admin tienen acceso completo según requerimientos del usuario
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden dar VIP!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                target_user = parts[1].replace("@", "")
                if target_user not in VIP_USERS:
                    VIP_USERS.add(target_user)
                    self.save_data()
                    await self.highrise.send_whisper(user.id, f"🎉 Otorgaste estatus VIP a {target_user}!")
                    log_event("VIP", f"{user.username} otorgó VIP a {target_user}")
                else:
                    await self.highrise.send_whisper(user.id, f"¡Usuario {target_user} ya tiene estatus VIP!")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !givevip @username")
            return

        # Comando !unvip - quitar estatus VIP (solo Admin y Owner)
        if msg.startswith("!unvip"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden quitar VIP!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                target_user = parts[1].replace("@", "")
                if target_user in VIP_USERS:
                    VIP_USERS.remove(target_user)
                    self.save_data()
                    await self.highrise.send_whisper(user.id, f"❌ Removiste estatus VIP de {target_user}!")
                    log_event("VIP", f"{user.username} removió VIP de {target_user}")
                else:
                    await self.highrise.send_whisper(user.id, f"¡Usuario {target_user} no tiene estatus VIP!")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !unvip @username")
            return

        # Comando !freeze - congelar usuario (solo Admin y Owner)
        if msg.startswith("!freeze"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden usar freeze!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                try:
                    # Buscar el usuario en la sala
                    users_response = await self.highrise.get_room_users()
                    if isinstance(users_response, Error):
                        await self.highrise.send_whisper(user.id, f"❌ Error obteniendo usuarios: {users_response}")
                        return
                    users = users_response.content

                    target_user = None
                    for u, pos in users:
                        if u.username == target_username:
                            target_user = u
                            break

                    if not target_user:
                        await self.highrise.send_whisper(user.id, f"❌ Usuario {target_username} no encontrado en la sala!")
                        return

                    # Congelar usando la API de moderación
                    await self.highrise.moderate_room(target_user.id, "mute", 300)  # 5 minutos
                    await self.highrise.send_whisper(user.id, f"🧊 Congelaste a {target_username} por 5 minutos")
                    log_event("FREEZE", f"{user.username} congeló a {target_username}")

                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error en freeze: {e}")
                    log_event("ERROR", f"Error freeze: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !freeze @username")
            return

        # Comando !mute - silenciar usuario (solo Admin y Owner)  
        if msg.startswith("!mute"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden usar mute!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                duration = 600  # 10 minutos por defecto
                if len(parts) >= 3 and parts[2].isdigit():
                    duration = int(parts[2]) * 60  # minutos a segundos

                try:
                    # Buscar el usuario en la sala
                    users_response = await self.highrise.get_room_users()
                    if isinstance(users_response, Error):
                        await self.highrise.send_whisper(user.id, f"❌ Error obteniendo usuarios: {users_response}")
                        return
                    users = users_response.content

                    target_user = None
                    for u, pos in users:
                        if u.username == target_username:
                            target_user = u
                            break

                    if not target_user:
                        await self.highrise.send_whisper(user.id, f"❌ Usuario {target_username} no encontrado en la sala!")
                        return

                    # Silenciar usando la API de moderación
                    await self.highrise.moderate_room(target_user.id, "mute", duration)
                    minutes = duration // 60
                    await self.highrise.send_whisper(user.id, f"🔇 Silenciaste a {target_username} por {minutes} minutos")
                    log_event("MUTE", f"{user.username} silenció a {target_username} por {minutes}min")

                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error en mute: {e}")
                    log_event("ERROR", f"Error mute: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !mute @username [minutos]")
            return

        # Comando !tplist - lista de puntos de teletransporte
        if msg == "!tplist":
            if TELEPORT_POINTS:
                points_list = ", ".join(TELEPORT_POINTS.keys())
                await self.highrise.send_whisper(user.id, f"📍 Puntos de teletransporte disponibles: {points_list}")
            else:
                await self.highrise.send_whisper(user.id, "📍 No hay puntos de teletransporte creados")
            return
        
        # Comando !tele list - lista de ubicaciones de teletransporte (sin restricción)
        if msg == "!tele list":
            if TELEPORT_POINTS:
                tele_message = "🗺️ UBICACIONES DE TELETRANSPORTE:\n"
                for i, (name, coords) in enumerate(TELEPORT_POINTS.items(), 1):
                    tele_message += f"{i}. {name} (X:{coords['x']:.1f}, Y:{coords['y']:.1f}, Z:{coords['z']:.1f})\n"
                await self.highrise.send_whisper(user.id, tele_message)
            else:
                await self.highrise.send_whisper(user.id, "📍 No hay ubicaciones de teletransporte creadas")
            return

        # Comando !delpoint [nombre] — eliminar punto de teletransporte (solo propietario)
        if msg.startswith("!delpoint"):
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede eliminar puntos!")
                return
            parts = msg.split()
            if len(parts) != 2:
                await self.highrise.send_whisper(user.id, "❌ Usa: !delpoint [nombre]")
                return
            point_name = parts[1]
            if point_name in TELEPORT_POINTS:
                del TELEPORT_POINTS[point_name]
                self.save_data()
                await self.highrise.send_whisper(user.id, f"✅ Punto '{point_name}' eliminado!")
            else:
                await self.highrise.send_whisper(user.id, f"❌ Punto '{point_name}' no encontrado!")
            return

        # Comando !checkvip - verificar estatus VIP
        if msg.startswith("!checkvip"):
            parts = msg.split()
            if len(parts) >= 2:
                target_user = parts[1].replace("@", "")
                if target_user in VIP_USERS:
                    await self.highrise.send_whisper(user.id, f"✅ {target_user} tiene estatus VIP!")
                else:
                    await self.highrise.send_whisper(user.id, f"❌ {target_user} no tiene estatus VIP! (VIP_USERS: {list(VIP_USERS)[:3]}...)")
            else:
                # Verificación del propio estatus
                is_vip_status = self.is_vip_by_username(user.username)
                await self.highrise.send_whisper(user.id, f"🔍 Tu verificación VIP: {'✅ VIP' if is_vip_status else '❌ No VIP'}")
                await self.highrise.send_whisper(user.id, f"📋 VIP actuales: {', '.join(list(VIP_USERS)[:3])}...")
            return

        # Comando !setvipzone - establecer zona VIP (mantener para compatibilidad)
        if msg.startswith("!setvipzone"):
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede establecer la zona VIP!")
                return

            try:
                # Obtenemos la posición del usuario
                users = (await self.highrise.get_room_users()).content
                user_obj = None
                user_position = None
                for u, pos in users:
                    if u.id == user_id:
                        user_obj = u
                        user_position = pos
                        break

                if user_obj and user_position:
                    # Actualizamos la zona VIP en la configuración
                    new_vip_zone = {"x": user_position.x, "y": user_position.y, "z": user_position.z}

                    # Guardamos en config.json
                    config = load_config()
                    config["vip_zone"] = new_vip_zone
                    with open("config.json", "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)

                    # Actualizamos la variable global
                    VIP_ZONE.update(new_vip_zone)

                    await self.highrise.send_whisper(user.id, f"🎯 Zona VIP establecida en: X={new_vip_zone['x']}, Y={new_vip_zone['y']}, Z={new_vip_zone['z']}")
                else:
                    await self.highrise.send_whisper(user.id, "¡Error obteniendo posición del usuario!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error estableciendo zona VIP: {e}")
            return

        # Comando !sv - сохранить точку VIP зоны (короткая версия)
        if msg == "!sv":
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede establecer la zona VIP!")
                return

            try:
                # Obtenemos la posición del usuario
                users = (await self.highrise.get_room_users()).content
                user_obj = None
                user_position = None
                for u, pos in users:
                    if u.id == user_id:
                        user_obj = u
                        user_position = pos
                        break

                if user_obj and user_position:
                    # Actualizamos la zona VIP en la configuración
                    new_vip_zone = {"x": user_position.x, "y": user_position.y, "z": user_position.z}

                    # Guardamos en config.json
                    config = load_config()
                    config["vip_zone"] = new_vip_zone
                    with open("config.json", "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)

                    # Actualizamos la variable global
                    VIP_ZONE.update(new_vip_zone)

                    await self.highrise.send_whisper(user.id, f"🎯 Zona VIP establecida en: X={new_vip_zone['x']}, Y={new_vip_zone['y']}, Z={new_vip_zone['z']}")
                else:
                    await self.highrise.send_whisper(user.id, "¡Error obteniendo posición del usuario!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error estableciendo zona VIP: {e}")
            return

        # Comando !setdj - сохранить точку DJ зоны (только для Owner)
        if msg == "!setdj":
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede establecer la zona DJ!")
                return

            try:
                # Obtenemos la posición del usuario
                users = (await self.highrise.get_room_users()).content
                user_obj = None
                user_position = None
                for u, pos in users:
                    if u.id == user_id:
                        user_obj = u
                        user_position = pos
                        break

                if user_obj and user_position:
                    # Actualizamos la zona DJ en la configuración
                    new_dj_zone = {"x": user_position.x, "y": user_position.y, "z": user_position.z}

                    # Guardamos en config.json
                    config = load_config()
                    config["dj_zone"] = new_dj_zone
                    with open("config.json", "w", encoding="utf-8") as f:
                        json.dump(config, f, indent=2, ensure_ascii=False)

                    await self.highrise.send_whisper(user.id, f"🎵 Zona DJ establecida en: X={new_dj_zone['x']}, Y={new_dj_zone['y']}, Z={new_dj_zone['z']}")
                else:
                    await self.highrise.send_whisper(user.id, "¡Error obteniendo posición del usuario!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error estableciendo zona DJ: {e}")
            return



        # Comando !heartall - отправить сердечки всем игрокам в комнате (только для Owner)
        if msg == "!heartall":
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede enviar corazones a todos!")
                return

            try:
                users = (await self.highrise.get_room_users()).content
                heart_count = 0

                for u, pos in users:
                    if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):  # Исключаем бота
                        # Добавляем сердечко в счетчик
                        self.add_user_hearts(u.id, 1, u.username)
                        # Отправляем визуальную реакцию сердечка
                        await self.highrise.react("heart", u.id)
                        heart_count += 1
                        await asyncio.sleep(0.1)  # Небольшая задержка между отправками

                await self.highrise.send_whisper(user.id, f"💖 Enviaste ❤️ a todos los {heart_count} jugadores en la sala!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error enviando corazones: {e}")
            return

        # Comando !heartall - отправить сердечки всем игрокам в комнате (только для Owner)
        if msg == "!heartall":
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede enviar corazones a todos!")
                return

            try:
                users = (await self.highrise.get_room_users()).content
                heart_count = 0

                for u, pos in users:
                    if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):  # Исключаем бота
                        # Добавляем сердечко в счетчик
                        self.add_user_hearts(u.id, 1, u.username)
                        # Отправляем визуальную реакцию сердечка
                        await self.highrise.react("heart", u.id)
                        heart_count += 1
                        await asyncio.sleep(0.1)  # Небольшая задержка между отправками

                await self.highrise.send_whisper(user.id, f"💖 Enviaste ❤️ a todos los {heart_count} jugadores en la sala!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error enviando corazones: {e}")
            return

        # Comando !bring @username - переместить игрока к Admin/Owner
        if msg.startswith("!bring "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden mover jugadores!")
                return

            try:
                target_username = msg[7:].strip().replace("@", "")

                # Obtenemos la posición del usuario que ejecuta el comando
                users = (await self.highrise.get_room_users()).content
                command_user_obj = None
                command_user_position = None
                target_user_obj = None

                for u, pos in users:
                    if u.id == user_id:
                        command_user_obj = u
                        command_user_position = pos
                    elif u.username == target_username:
                        target_user_obj = u

                if not command_user_position:
                    await self.highrise.send_whisper(user.id, "❌ ¡Error obteniendo tu posición!")
                    return

                if not target_user_obj:
                    await self.highrise.send_whisper(user.id, f"❌ ¡Jugador {target_username} no encontrado en la sala!")
                    return

                # Teleportamos al jugador cerca del usuario que ejecuta el comando (desplazamiento de 1 bloque)

                new_position = Position(command_user_position.x + 1, command_user_position.y, command_user_position.z)
                await self.highrise.teleport(target_user_obj.id, new_position)
                await self.highrise.send_whisper(user.id, f"🎯 @{user.username} movió a {target_username} hacia sí mismo!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error moviendo jugador: {e}")
            return

        # Comando !TPus - crear punto de teletransporte
        if msg.startswith("!TPus"):
            if user_id != OWNER_ID:
                await self.highrise.send_whisper(user.id, "❌ ¡Solo el propietario puede crear puntos de teletransporte!")
                return

            parts = msg.split()
            if len(parts) >= 2:
                point_name = parts[1]

                try:
                    # Obtenemos la posición del usuario
                    users = (await self.highrise.get_room_users()).content
                    user_obj = None
                    user_position = None
                    for u, pos in users:
                        if u.id == user_id:
                            user_obj = u
                            user_position = pos
                            break

                    if user_obj and user_position:
                        # Guardamos el punto de teletransporte
                        TELEPORT_POINTS[point_name] = {
                            "x": user_position.x,
                            "y": user_position.y,
                            "z": user_position.z
                        }

                        # Guardamos en el archivo
                        self.save_data()

                        await self.highrise.send_whisper(user.id, f"📍 Punto de teletransporte '{point_name}' creado en posición: X={user_position.x}, Y={user_position.y}, Z={user_position.z}")
                    else:
                        await self.highrise.send_whisper(user.id, "¡Error obteniendo posición del usuario!")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"Error creando punto de teletransporte: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !TPus [nombre]")
            return

        # Comandos de interacción entre usuarios
        if msg.startswith("!punch") or msg.startswith("!slap") or msg.startswith("!flirt") or msg.startswith("!scare") or msg.startswith("!electro") or msg.startswith("!hug") or msg.startswith("!ninja") or msg.startswith("!laugh") or msg.startswith("!boom"):
            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                command = parts[0]

                                            # Encontramos al usuario objetivo
                try:
                    users = (await self.highrise.get_room_users()).content
                    target_user = None
                    sender_pos = None
                    target_pos = None

                    # Buscamos ambos usuarios y sus posiciones
                    for u, pos in users:
                        if u.id == user.id:
                            sender_pos = pos
                        if u.username == target_username:
                            target_user = u
                            target_pos = pos

                    if not target_user:
                        await self.highrise.send_whisper(user.id, f"❌ ¡Usuario {target_username} no encontrado en la sala!")
                        return

                    if not sender_pos or not target_pos:
                        await self.highrise.send_whisper(user.id, f"❌ No se pudo obtener la posición de los usuarios!")
                        return

                    # Verificamos la distancia entre los usuarios
                    distance = self.calculate_distance(sender_pos, target_pos)

                    # !punch y !slap funcionan desde cualquier distancia
                    # Las demás comandos requieren estar a máximo 3 bloques
                    if command not in ["!punch", "!slap"] and distance > 3.0:
                        await self.highrise.send_whisper(user.id, f"❌ ¡{target_username} está muy lejos! Debes estar a máximo 3 bloques de distancia.")
                        return

                    # Determinamos la emoción y mensaje según el comando
                    sender_emote_id = ""
                    receiver_emote_id = ""
                    action_message = ""

                    if command == "!punch":
                        sender_emote_id = "emoji-punch"
                        receiver_emote_id = "emote-death"
                        action_message = f"🥊 @{user.username} golpeó a @{target_username} y lo dejó noqueado!"
                    elif command == "!slap":
                        sender_emote_id = "emote-slap"
                        receiver_emote_id = "emoji-dizzy"
                        action_message = f"👋 @{user.username} dio una bofetada a @{target_username} y lo dejó en shock!"
                    elif command == "!flirt":
                        sender_emote_id = "emote-kissing"
                        receiver_emote_id = "emote-hearteyes"
                        action_message = f"💕 @{user.username} coquetea con @{target_username} y se derrite de amor!"
                    elif command == "!scare":
                        sender_emote_id = "emote-panic"
                        receiver_emote_id = "emoji-scared"
                        action_message = f"😱 @{user.username} asustó a @{target_username} y huyó en pánico!"
                    elif command == "!electro":
                        sender_emote_id = "emote-fail1"
                        receiver_emote_id = "emote-fail2"
                        action_message = f"⚡ @{user.username} electrocutó a @{target_username} y se quemó!"
                    elif command == "!hug":
                        sender_emote_id = "emote-hug"
                        receiver_emote_id = "emote-hugyourself"
                        action_message = f"🤗 @{user.username} abrazó a @{target_username} y lloró de emoción!"
                    elif command == "!ninja":
                        sender_emote_id = "emote-ninjarun"
                        receiver_emote_id = "emote-fail1"
                        action_message = f"🥷 @{user.username} atacó como ninja a @{target_username} y se retuerce de dolor!"
                    elif command == "!laugh":
                        sender_emote_id = "emote-laughing"
                        receiver_emote_id = "emote-laughing2"
                        action_message = f"😂 @{user.username} hizo reír a @{target_username} sin parar!"
                    elif command == "!boom":
                        sender_emote_id = "emote-disappear"
                        receiver_emote_id = "emote-fail1"
                        action_message = f"💥 @{user.username} explotó a @{target_username} y literalmente explotó!"

                    # Enviamos las emociones a ambos usuarios
                    if sender_emote_id and receiver_emote_id:
                        # Animación para el remitente (una sola vez)
                        await self.highrise.send_emote(sender_emote_id, user.id)
                        # Animación para el objetivo (una sola vez)
                        await self.highrise.send_emote(receiver_emote_id, target_user.id)
                        
                        # Si el comando fue privado, responder por privado; si no, por público
                        if is_whisper:
                            await self.highrise.send_whisper(user.id, action_message)
                        else:
                            await self.highrise.chat(action_message)

                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error ejecutando comando: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Usa: !comando @usuario")
            return

        # Verificamos si el mensaje es el nombre de un punto de teletransporte
        if msg in TELEPORT_POINTS:
            point = TELEPORT_POINTS[msg]
            try:

                teleport_position = Position(point["x"], point["y"], point["z"])
                await self.highrise.teleport(user_id, teleport_position)
                await self.highrise.send_whisper(user.id, f"🚀 @{user.username} se teletransportó al punto '{msg}'!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error de teletransporte: {e}")
            return

        # Comando !tele @user - teleport to user (VIP only)
        if msg.startswith("!tele @"):
            if not self.is_vip_by_username(user.username):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo VIP pueden usar este comando!")
                return

            target_username = msg[7:].strip()  # Remove "!tele @"
            try:
                users = (await self.highrise.get_room_users()).content
                target_user = None
                target_position = None

                for u, pos in users:
                    if u.username == target_username:
                        target_user = u
                        target_position = pos
                        break

                if target_user and target_position:
                    # Teleport near the target user (offset by 1 block)

                    new_position = Position(target_position.x + 1, target_position.y, target_position.z)
                    await self.highrise.teleport(user_id, new_position)
                    await self.highrise.send_whisper(user.id, f"🎯 Te has teletransportado a @{target_username}!")
                else:
                    await self.highrise.send_whisper(user.id, f"❌ ¡Usuario {target_username} no encontrado!")
            except Exception as e:
                await self.highrise.send_whisper(user.id, f"Error: {e}")
            return

        # Comando !bot @user - Bot hace punch al usuario, usuario hace revival
        if msg.startswith("!bot "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden usar este comando!")
                return

            target_username = msg[5:].strip().replace("@", "")
            try:
                users = (await self.highrise.get_room_users()).content
                target_user = None
                target_position = None
                bot_user = None
                bot_position = None

                # Buscar usuario objetivo y bot
                for u, pos in users:
                    if u.username == target_username:
                        target_user = u
                        target_position = pos
                    if "bot" in u.username.lower() or "nocturno" in u.username.lower():
                        bot_user = u
                        bot_position = pos

                if not target_user:
                    await self.highrise.send_whisper(user.id, f"❌ ¡Usuario {target_username} no encontrado!")
                    return

                if not bot_user:
                    await self.highrise.send_whisper(user.id, "❌ ¡No se pudo encontrar el bot!")
                    return

                # 1. Bot se mueve cerca del usuario
                move_position = Position(target_position.x + 0.5, target_position.y, target_position.z + 0.5)
                await self.highrise.teleport(bot_user.id, move_position)
                await asyncio.sleep(1)

                # 2. Bot hace punch, usuario hace revival
                await self.highrise.send_emote("emoji-punch", bot_user.id)
                await asyncio.sleep(0.5)
                await self.highrise.send_emote("emote-death", target_user.id)

                # 3. Mensaje global
                await self.highrise.chat("‼️CALLATE‼️")
                await asyncio.sleep(2)

                # 4. Bot regresa a su posición original
                if bot_position:
                    await self.highrise.teleport(bot_user.id, bot_position)

                await self.highrise.send_whisper(user.id, f"🤖 Comando !bot ejecutado en @{target_username}")

            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error ejecutando !bot: {e}")
            return

        # Comando !addzone [nombre] - Crear nueva zona de teletransportación (solo admin/owner)
        if msg.startswith("!addzone "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden crear zonas!")
                return

            zone_name = msg[9:].strip()
            if not zone_name:
                await self.highrise.send_whisper(user.id, "❌ Usa: !addzone [nombre]")
                return

            try:
                # Obtener posición actual del usuario
                users = (await self.highrise.get_room_users()).content
                user_position = None
                for u, pos in users:
                    if u.id == user_id:
                        user_position = pos
                        break

                if user_position:
                    # Guardar nuevo punto de teletransportación
                    TELEPORT_POINTS[zone_name] = {
                        "x": user_position.x,
                        "y": user_position.y,
                        "z": user_position.z
                    }
                    self.save_data()
                    await self.highrise.send_whisper(user.id, f"🗺️ Zona '{zone_name}' creada en posición ({user_position.x}, {user_position.y}, {user_position.z})")
                else:
                    await self.highrise.send_whisper(user.id, "❌ Error obteniendo posición")

            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error creando zona: {e}")
            return

        # Comando !vip @user - Dar estatus VIP (solo admin/owner)
        if msg.startswith("!vip "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await self.highrise.send_whisper(user.id, "❌ ¡Solo administradores y propietario pueden dar VIP!")
                return

            target_username = msg[5:].strip().replace("@", "")
            try:
                # Buscar usuario
                users = (await self.highrise.get_room_users()).content
                target_found = False
                for u, pos in users:
                    if u.username == target_username:
                        target_found = True
                        break

                if target_found:
                    VIP_USERS.add(target_username)  # Añadir por username
                    self.save_data()
                    await self.highrise.send_whisper(user.id, f"⭐ @{target_username} ahora es VIP!")
                    await self.highrise.send_whisper(u.id, f"🎉 ¡Felicitaciones! Ahora eres VIP gracias a @{user.username}")
                else:
                    await self.highrise.send_whisper(user.id, f"❌ Usuario {target_username} no encontrado en la sala")

            except Exception as e:
                await self.highrise.send_whisper(user.id, f"❌ Error dando VIP: {e}")
            return

    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        """Manejador de entrada de usuario"""
        user_id = user.id
        username = user.username

        # Añadimos el username al diccionario USER_NAMES para que funcione is_vip()
        USER_NAMES[user_id] = username

        # Aggiorniamo le informazioni sul giocatore
        self.update_user_info(user_id, username)

        # Registriamo il tempo di ingresso usando time.time() como nella documentazione
        USER_JOIN_TIMES[user_id] = time.time()
        USER_INFO[user_id]["time_joined"] = time.time()

        # Bienvenida privada según solicitud del usuario
        await self.highrise.send_whisper(user_id, "💫🌚Bienvenido a la sala ✓NOCTURNO✓ ponte cómodo y disfruta al máximo🌚💫")

    async def on_user_leave(self, user: User) -> None:
        """Manejador de salida de usuario"""
        user_id = user.id
        username = user.username

        # Calcoliamo il tempo nella stanza e lo aggiungiamo al tempo totale
        if user_id in USER_JOIN_TIMES:
            join_time = USER_JOIN_TIMES[user_id]
            current_time = time.time()
            time_in_room = round(current_time - join_time)  # Используем round() como en la documentación

            if user_id in USER_INFO:
                USER_INFO[user_id]["total_time_in_room"] += time_in_room

            # Rimuoviamo dai giocatori attivi
            del USER_JOIN_TIMES[user_id]

        # Despedida silenciosa (privada) según solicitud del usuario
        # No enviamos mensaje público de despedida

        # Detener emociones al salir
        await self.stop_emote_loop(user_id)

        # Salviamo le informazioni sul giocatore
        save_user_info()

    async def on_tip(self, sender: User, receiver: User, tip: CurrencyItem | Item) -> None:
        """Manejador de propinas"""
        global BOT_WALLET

        print(f"{sender.username} tipped {receiver.username} an amount of {tip.amount}")

                    # Obtenemos el ID del bot
        try:
            room_users_response = await self.highrise.get_room_users()
            if isinstance(room_users_response, Error):
                print(f"Error obteniendo usuarios de la sala: {room_users_response}")
                return
            users = room_users_response.content
            bot_user = None
            for u, pos in users:
                # Buscar NOCTURNO_BOT primero, luego otros nombres
                if u.username == "NOCTURNO_BOT" or u.username.upper() == "NOCTURNO_BOT":
                    bot_user = u
                    break
                elif u.username.lower() in ["highrisebot", "bot"] or any(name in u.username.lower() for name in ["nocturno", "bot", "glux", "highrise"]):
                    bot_user = u
                    break

            # Si el receptor es el bot
            if bot_user and receiver.id == bot_user.id:
                if tip.amount == 100:
                    # VIP por donación
                    VIP_USERS.add(sender.username)  # Usamos username en lugar de id
                    self.save_data()
                    await self.highrise.send_whisper(sender.id, f"🎉 Obtuviste estatus VIP por donación de 100 oro!")
                    await self.highrise.send_whisper(sender.id, f"🌟 ¡Bienvenido al club VIP!")
                else:
                    BOT_WALLET += tip.amount
                    await self.highrise.send_whisper(sender.id, f"💰 Donaste {tip.amount} oro al bot!")
        except Exception as e:
            print(f"Error en on_tip: {e}")

    async def on_emote(self, user: User, emote_id: str, receiver: User | None) -> None:
        """Manejador de emociones"""
        # Se puede agregar lógica para emociones conjuntas
        pass

    async def on_reaction(self, user: User, reaction: Reaction, receiver: User) -> None:
        """Manejador de reacciones"""
        print(f"{user.username} sent the reaction {reaction} to {receiver.username}")
        print(f"DEBUG: reaction = {reaction}")
        print(f"DEBUG: reaction type = {type(reaction)}")
        print(f"DEBUG: reaction attributes = {dir(reaction)}")

        # Agregamos corazones por reacciones - usamos str() para comparar
        if str(reaction) == "heart":
            self.add_user_hearts(receiver.id, 1, receiver.username)
            print(f"💖 {user.username} envió un corazón a {receiver.username}")
            log_event("HEART", f"{user.username} -> {receiver.username}")
            # Отправляем визуальную реакцию сердечка в ответ
            await self.highrise.react("heart", user.id)
        else:
            print(f"DEBUG: Реакция {str(reaction)} не является сердечком")

    async def on_user_move(self, user: User, destination: Position | AnchorPosition) -> None:
        """Manejador de movimiento de usuario - FLASHMODE AUTOMÁTICO"""
        def _coords(p):
            return (p.x, p.y, p.z) if isinstance(p, Position) else None

        try:
            user_id = user.id
            username = user.username
            current_time = time.time()

            # Inicializar cooldown si no existe
            if not hasattr(self, 'flashmode_cooldown'):
                self.flashmode_cooldown = {}

            # Si es el primer movimiento del usuario, solo guardamos la posición
            last_pos = self.user_positions.get(user_id)
            if not last_pos:
                self.user_positions[user_id] = destination
                return

            # Extract coordinates - only proceed with flashmode if both are Position objects
            last_xyz = _coords(last_pos)
            dest_xyz = _coords(destination)

            if not last_xyz or not dest_xyz:
                # Either is AnchorPosition, skip flashmode logic
                self.user_positions[user_id] = destination
                return

            # Detectar cambio de piso (diferencia significativa en Y)
            floor_change_threshold = 1.0  # Umbral para detectar cambio de piso
            y_difference = abs(dest_xyz[1] - last_xyz[1])

            is_floor_change = y_difference >= floor_change_threshold

            # FLASHMODE AUTOMÁTICO - Disponible para TODOS los usuarios sin restricciones
            if is_floor_change:
                # Verificar cooldown (evitar loops)
                cooldown_time = 3.0  # 3 segundos de cooldown
                if user_id in self.flashmode_cooldown:
                    time_since_last = current_time - self.flashmode_cooldown[user_id]
                    if time_since_last < cooldown_time:
                        # En cooldown, actualizar posición sin flashmode
                        self.user_positions[user_id] = destination
                        return

                # Verificar que el destino no esté en zona prohibida
                if not self.is_in_forbidden_zone(dest_xyz[0], dest_xyz[1], dest_xyz[2]):
                    try:
                        # FLASHMODE: Teletransporte automático entre pisos
                        # Verificar que destination sea Position antes de teleport
                        if isinstance(destination, Position):
                            await self.highrise.teleport(user_id, destination)

                        # Actualizar cooldown
                        self.flashmode_cooldown[user_id] = current_time

                        # Log del flashmode
                        log_event("FLASHMODE", f"Auto-flashmode {username}: piso {last_xyz[1]:.1f} → {dest_xyz[1]:.1f}")
                        print(f"🔄 FLASHMODE AUTO: {username} cambió de piso {last_xyz[1]:.1f} → {dest_xyz[1]:.1f}")

                    except Exception as e:
                        print(f"❌ Error en flashmode automático para {username}: {e}")
                else:
                    print(f"❌ Flashmode bloqueado: {username} intentó ir a zona prohibida")

            # Actualizar posición del usuario
            self.user_positions[user_id] = destination

        except Exception as e:
            print(f"Error en on_user_move: {e}")
            print(f"User: {user.username}")
            print(f"Position: {destination}")



    async def start_announcements(self):
        """Inicio de anuncios automáticos"""
        # Приветственное сообщение (разделено на две части)
        welcome_message_1 = "🌌 BIENVENIDO A NOCTURNO ⛈️💙\nUna sala donde lo oculto brilla más que la luz...\n💬 Vive la noche, haz nuevos amigos y deja tu huella👣."
        welcome_message_2 = "✨ Sumérgete en la oscuridad... y descubre lo más brillante de ti💯\n‼️(Cualquier incomodidad o sugerencia comuniqué con @Alber_JG_69 o @Xx__Daikel__xX)‼️"

        # Отправляем приветственные сообщения
        await self.highrise.chat(welcome_message_1)
        await asyncio.sleep(1)  # Небольшая задержка между сообщениями
        await self.highrise.chat(welcome_message_2)

        # Обычные объявления
        announcements = [
            "🎮 Usa !help para ver la lista de todos los comandos",
            "💖 Envía corazones a amigos con !heart @username",
            "🏆 Revisa el ranking con !leaderboard",
            "🎯 Juega al medidor de amor: !game love @user1 @user2"
        ]
        announcement_index = 0
        vip_counter = 0

        while True:
            try:
                current_time = time.time()
                if current_time - self.last_announcement >= 300:  # 5 минут
                    # Отправляем одно сообщение из списка
                    await self.highrise.chat(announcements[announcement_index])
                    announcement_index = (announcement_index + 1) % len(announcements)

                    # Каждое четвертое сообщение - о VIP
                    vip_counter += 1
                    if vip_counter == 4:
                        await self.highrise.chat("💎 ¡Conviértete en VIP por 100 oro y obtén capacidades exclusivas!")
                        vip_counter = 0

                    self.last_announcement = current_time
            except Exception as e:
                print(f"Error en anuncios: {e}")

            await asyncio.sleep(60)  # Проверка каждую минуту

    async def check_console_messages(self):
        """Verificación de mensajes desde la consola"""
        while True:
            try:
                # Verificamos el archivo con mensajes
                if os.path.exists("console_message.txt"):
                    with open("console_message.txt", "r", encoding="utf-8") as f:
                        message = f.read().strip()

                    if message:
                        # Enviamos el mensaje al chat
                        await self.highrise.chat(message)
                        print(f"💬 Mensaje de consola enviado: {message}")

                        # Limpiamos el archivo
                        os.remove("console_message.txt")

            except Exception as e:
                print(f"Error verificando mensajes de consola: {e}")

            await asyncio.sleep(1)  # Verificación cada segundo

    async def delayed_restart(self):
        """Parada retrasada del bot"""
        try:
            await asyncio.sleep(3)  # Esperamos 3 segundos
            # Comentamos esta línea ya que user no está definido en este contexto
            # await self.highrise.send_whisper(user.id, "🛑 ¡Bot detenido!")
            print("🛑 ¡Bot detenido!")

            # Guardamos datos antes de detener
            self.save_data()

            # Terminamos el trabajo del bot
            import os
            os._exit(0)
        except Exception as e:
            print(f"Error al detener: {e}")
            import os
            os._exit(0)

    def convert_to_gold_bars(self, amount: int) -> str:
        """Convierte la cantidad de oro en cadena de barras de oro"""
        bars_dictionary = {
            10000: "gold_bar_10k", 
            5000: "gold_bar_5000",
            1000: "gold_bar_1k",
            500: "gold_bar_500",
            100: "gold_bar_100",
            50: "gold_bar_50",
            10: "gold_bar_10",
            5: "gold_bar_5",
            1: "gold_bar_1"
        }

        tip = []
        remaining_amount = amount

        # Ordenamos las barras por descenso para conversión correcta
        for bar_value in sorted(bars_dictionary.keys(), reverse=True):
            if remaining_amount >= bar_value:
                bar_count = remaining_amount // bar_value
                remaining_amount = remaining_amount % bar_value
                for i in range(bar_count):
                    tip.append(bars_dictionary[bar_value])

        return ",".join(tip) if tip else ""

    async def get_bot_wallet_balance(self):
        """Obtiene el balance real de la billetera del bot"""
        try:
            # Obtenemos el balance real a través de la API
            wallet_response = await self.highrise.get_wallet()
            if isinstance(wallet_response, Error):
                print(f"Error obteniendo wallet: {wallet_response}")
                return BOT_WALLET
            wallet = wallet_response.content
            if wallet and len(wallet) > 0:
                return wallet[0].amount
            else:
                return BOT_WALLET
        except Exception as e:
            print(f"Error obteniendo balance de billetera: {e}")
            return BOT_WALLET

    async def console_chat_input(self):
        """Entrada de consola para enviar mensajes a través del bot"""
        print("💬 ¡Chat de consola iniciado!")
        print("📝 Ingresa un mensaje y presiona Enter para enviar")
        print("❌ Ingresa 'quit' para salir")
        print("-" * 50)

        while True:
            try:
                message = input("> ")
                if message.lower() == 'quit':
                    break
                elif message.strip():
                    await self.highrise.chat(message)
                    print(f"✅ Enviado: {message}")
            except KeyboardInterrupt:
                break
            except Exception as e:
                print(f"❌ Error de envío: {e}")

    async def show_user_info(self, user: User):
        """Mostra informazioni sul giocatore corrente con rol e crew"""
        user_id = user.id
        username = user.username

        # Aggiorniamo le informazioni sul giocatore
        self.update_user_info(user_id, username)

        # Otteniamo i dati del giocatore
        user_data = USER_INFO.get(user_id, {})
        total_time = self.get_user_total_time(user_id)
        messages = USER_ACTIVITY.get(user_id, {}).get("messages", 0)
        hearts = self.get_user_hearts(user_id)

        # Calcoliamo il tempo corrente nella stanza
        current_time_in_room = 0
        if user_id in USER_JOIN_TIMES:
            join_time = USER_JOIN_TIMES[user_id]
            current_time_in_room = round(time.time() - join_time)

        # Formattiamo il tempo
        total_time_str = self.format_time(total_time + current_time_in_room)

        # Determiniamo il rol del giocatore
        if user_id == OWNER_ID:
            rol = "👑 Propietario"
        elif self.is_admin(user_id):
            rol = "🛡️ Administrador"
        elif self.is_moderator(user_id):
            rol = "⚖️ Moderador"
        elif self.is_vip(user_id):
            rol = "⭐ VIP"
        else:
            rol = "👤 Usuario Normal"

        # Otteniamo informazioni dal Web API
        followers = "N/A"
        following = "N/A"
        friends = "N/A"
        account_created = "Sconosciuto"
        crew_info = "Sin crew"

        try:
            # Используем WebAPI para obtener datos del usuario
            user_info = await self.webapi.get_user(user_id)

            # Otteniamo la data di creazione dell'account
            if user_info and hasattr(user_info.user, 'joined_at'):
                account_created = user_info.user.joined_at.strftime("%d.%m.%Y %H:%M")
                # Сохраняем в локальные данные
                USER_INFO[user_id]["account_created"] = user_info.user.joined_at.isoformat()
            elif user_data.get("account_created"):
                # Используем сохраненные данные
                try:
                    created_dt = datetime.fromisoformat(user_data["account_created"].replace('Z', '+00:00'))
                    account_created = created_dt.strftime("%d.%m.%Y %H:%M")
                except:
                    pass

            # Otteniamo informazioni sociali
            if user_info and hasattr(user_info.user, 'num_followers'):
                followers = str(user_info.user.num_followers)
                following = str(user_info.user.num_following)
                friends = str(user_info.user.num_friends)

            # Otteniamo informazioni sulla crew
            if user_info and hasattr(user_info.user, 'crew') and user_info.user.crew:
                crew_name = user_info.user.crew.name if hasattr(user_info.user.crew, 'name') else "Unknown"
                crew_tag = user_info.user.crew.tag if hasattr(user_info.user.crew, 'tag') else ""
                crew_info = f"{crew_name} [{crew_tag}]" if crew_tag else crew_name
                print(f"DEBUG: Crew encontrada para {username}: {crew_info}")

        except Exception as e:
            print(f"Errore nel ottenere dati dal Web API: {e}")
            # Используем сохраненные данные как fallback
            if user_data.get("account_created"):
                try:
                    created_dt = datetime.fromisoformat(user_data["account_created"].replace('Z', '+00:00'))
                    account_created = created_dt.strftime("%d.%m.%Y %H:%M")
                except:
                    pass

        # Calcoliamo il tempo totale in Highrise (dalla registrazione)
        highrise_time = "Sconosciuto"
        try:
            if account_created != "Sconosciuto":
                # Convertiamo la data di registrazione in timestamp
                created_dt = datetime.strptime(account_created, "%d.%m.%Y %H:%M")
                current_dt = datetime.now()
                time_diff = current_dt - created_dt
                days = time_diff.days
                hours = time_diff.seconds // 3600
                minutes = (time_diff.seconds % 3600) // 60
                highrise_time = f"{days}d, {hours}h, {minutes}m"
        except Exception as e:
            print(f"Errore nel calcolare tempo Highrise: {e}")

        # Creiamo il messaggio con le informazioni in colonna
        info_message = f"📊 {username}'s Info:\n"
        info_message += f"🎭 Rol: {rol}\n"
        info_message += f"👥 Crew: {crew_info}\n"
        info_message += f"📅 Registrado: {account_created}\n"
        info_message += f"⏰ Tiempo en HR: {highrise_time}\n"
        info_message += f"👥 Followers: {followers} | Friends: {friends}"

        await self.highrise.chat(info_message)

    async def show_user_role(self, user: User):
        """Mostra il ruolo del giocatore corrente"""
        user_id = user.id
        username = user.username

        # Determiniamo il ruolo del giocatore
        if self.is_admin(user_id):
            role = "Admin"
        elif self.is_moderator(user_id):
            role = "Manager"
        elif self.is_vip(user_id):
            role = "Host"
        else:
            role = "Vip"

        # Creiamo il messaggio del ruolo
        role_message = f"{username} Roles:[{role}]"

        await self.highrise.send_whisper(user_id, role_message)

    async def show_user_role_by_username(self, username: str, requester_id: str):
        """Mostra il ruolo di un giocatore tramite username"""
        # Cerchiamo il giocatore per username
        target_user_id = None

        # Prima cerchiamo nei dati salvati
        for user_id, user_data in USER_INFO.items():
            if user_data.get("username") == username:
                target_user_id = user_id
                break

        # Se non trovato, cerchiamo tra i giocatori attualmente online
        if not target_user_id:
            try:
                room_users_response = await self.highrise.get_room_users()
                if isinstance(room_users_response, Error):
                    print(f"Error obteniendo usuarios: {room_users_response}")
                    return
                users = room_users_response.content
                for user, _ in users:
                    if user.username == username:
                        target_user_id = user.id
                        # Creiamo una voce temporanea per questo giocatore
                        self.update_user_info(target_user_id, username)
                        break
            except Exception as e:
                print(f"Errore nel cercare giocatori online: {e}")

        if not target_user_id:
            await self.highrise.chat(f"❌ Giocatore @{username} non trovato nel database")
            return

        # Determiniamo il ruolo del giocatore
        if self.is_admin(target_user_id):
            role = "Admin"
        elif self.is_moderator(target_user_id):
            role = "Manager"
        elif self.is_vip(target_user_id):
            role = "Host"
        else:
            role = "Vip"

        # Creiamo il messaggio del ruolo
        role_message = f"🔑 {username} Roles:\n"
        role_message += f"Nivel: {role}"

        await self.highrise.send_whisper(requester_id, role_message)

    async def show_all_levels(self, user_id: str):
        """Mostra tutti i livelli disponibili"""
        levels_message = "🔑 Nivel: Vip\n"
        levels_message += "Costo: 100g[Host]\n"
        levels_message += "🔑 Nivel: Host[Manager]\n"
        levels_message += "🔑 Nivel: Manager[Admin]\n"
        levels_message += "🔑 Nivel: Admin"
        await self.highrise.send_whisper(user_id, levels_message)



    def print_highrise_methods(self):
        print(dir(self.highrise))

    async def get_bot_user(self):
        """Obtiene el objeto User del bot usando bot_id almacenado"""
        try:
            if not hasattr(self, 'bot_id'):
                log_event("ERROR", "Bot ID not available - bot may not be properly initialized")
                return None

            room_users_response = await self.highrise.get_room_users()
            if isinstance(room_users_response, Error):
                log_event("ERROR", f"Error obteniendo usuarios: {room_users_response}")
                return None
            users = room_users_response.content
            bot_user = next((u for u, _ in users if u.id == self.bot_id), None)

            if bot_user:
                log_event("BOT", f"Bot user found: {bot_user.username} (ID: {bot_user.id})")
            else:
                log_event("WARNING", f"Bot user not found in room with ID: {self.bot_id}")

            return bot_user
        except Exception as e:
            log_event("ERROR", f"Error obteniendo bot user: {e}")
            return None

    async def change_bot_outfit(self, outfit_id: str):
        """Cambia el outfit del bot usando el ID especificado"""
        try:
            log_event("BOT", f"Attempting to change bot outfit to: {outfit_id}")

            # Outfit personalizado específico solicitado por el usuario
            if outfit_id == "custom_nocturno":
                from highrise.models import Item
                custom_outfit = [
                    # Camisa - Mafia Suit
                    Item(type="clothing", id="shirt-n_guy_rise_par_rewards_2023_mafia_suit", amount=1),
                    # Pantalones - Formal Slacks Black  
                    Item(type="clothing", id="pants-n_room1_2019formalslacksblack", amount=1),
                    # Lentes - Billie Glasses
                    Item(type="clothing", id="glasses-n_registrationavatars2023billieglasses", amount=1),
                    # Zapatos - Knife Boots
                    Item(type="clothing", id="shoes-n_marchscavengerhunt2021knifeboots", amount=1),
                    # Boca - Racer Mouth
                    Item(type="clothing", id="mouth-n_dailyquests2024racermouth", amount=1),
                    # Cabello frontal - Nikana Master Hair
                    Item(type="clothing", id="hair_front-n_winterformaludceventrewards02_2023_nikana_maschair", amount=1),
                    # Sombrero - Angel Halo
                    Item(type="clothing", id="hat-n_fallen_angels_silks_nevs_2024_angel_halo", amount=1),
                    # Piel gris
                    Item(type="clothing", id="skin-s_gray", amount=1)
                ]

                await self.highrise.set_outfit(custom_outfit)
                log_event("BOT", f"✅ Custom NOCTURNO outfit applied successfully")
                print(f"✅ Outfit personalizado NOCTURNO configurado")
                return

            # Get bot's current outfit for other outfit IDs
            current_outfit_response = await self.highrise.get_my_outfit()
            if isinstance(current_outfit_response, Error):
                log_event("ERROR", f"Error obteniendo outfit actual: {current_outfit_response}")
                return
            current_outfit = current_outfit_response.outfit

            # Apply current outfit for backward compatibility
            await self.highrise.set_outfit(current_outfit)

            # Verify the outfit was applied by getting it again
            verification_outfit = await self.highrise.get_my_outfit()

            if verification_outfit:
                log_event("BOT", f"✅ Bot outfit successfully applied for ID: {outfit_id}")
                print(f"✅ Outfit del bot configurado para ID: {outfit_id}")
            else:
                log_event("WARNING", f"Could not verify outfit application for ID: {outfit_id}")

        except Exception as e:
            log_event("ERROR", f"Error cambiando outfit del bot: {e}")
            print(f"❌ Error cambiando outfit del bot: {e}")
            raise e

    async def start_floss_mode(self):
        """Inicia modo floss real - solo emote dance-floss en bucle infinito"""
        try:
            self.bot_mode = "floss"
            log_event("BOT", "Iniciando modo FLOSS REAL en bucle infinito")
            print("🕺 Modo FLOSS REAL activado - bucle infinito")

            while self.bot_mode == "floss":
                try:
                    # EMOTE FLOSS REAL - dance-floss
                    await self.highrise.send_emote("dance-floss", self.bot_id)
                    log_event("BOT", "Emote floss real ejecutado: dance-floss")
                    print("🕺 Bot ejecutando emote floss real (dance-floss)")
                    await asyncio.sleep(6.0)  # Duración del emote floss real

                except Exception as e:
                    log_event("ERROR", f"Error con emote floss real: {e}")
                    print(f"⚠️ Error con emote floss real: {e}")
                    await asyncio.sleep(2)  # Pausa corta antes de reintentar

        except Exception as e:
            log_event("ERROR", f"Error crítico en modo floss: {e}")
            print(f"❌ Error crítico en modo floss: {e}")

    async def fake_floss_acelerado(self, user_id, bucle_infinito=False):
        """
        Simulación del 'Floss Falso' con aceleración progresiva.
        Si bucle_infinito=True, continúa ejecutándose indefinidamente.
        """
        try:
            movimiento_floss = [
                "idle-fighter",      # fighter - Brazo rígido
                "emote-superpunch",  # superpunch - Brazo adelante
                "emote-kicking",     # superkick - Brazo atrás
                "idle-loop-tapdance" # taploop - Ritmo de cadera/reset
            ]
            
            # Fases de aceleración [Tiempo, Número de Veces que Repite la secuencia]
            fases_aceleracion = [
                (0.5, 2),  # Lento
                (0.3, 2),  # Medio
                (0.18, 5)  # Máximo (Velocidad final)
            ]
            
            log_event("BOT", f"Iniciando floss falso acelerado para usuario {user_id} - Bucle infinito: {bucle_infinito}")
            
            # Ejecutamos la secuencia de aceleración inicial
            for tiempo_sleep, num_repeticiones in fases_aceleracion:
                for _ in range(num_repeticiones):
                    for emote_name in movimiento_floss:
                        await self.highrise.send_emote(emote_name, user_id)
                        await asyncio.sleep(tiempo_sleep)
            
            # Si es bucle infinito, continuar con la velocidad máxima
            if bucle_infinito:
                log_event("BOT", f"Iniciando bucle infinito de floss falso para usuario {user_id}")
                print("🕺 FLOSS FALSO - Iniciando bucle infinito a velocidad máxima")
                
                while True:
                    for emote_name in movimiento_floss:
                        await self.highrise.send_emote(emote_name, user_id)
                        await asyncio.sleep(0.18)  # Velocidad máxima constante
            else:
                # El bot termina la aceleración y se pone en pose final
                await self.highrise.send_emote("emote-celebrationstep", user_id)
                log_event("BOT", f"Floss falso completado para usuario {user_id}")
            
        except Exception as e:
            log_event("ERROR", f"Error en floss falso: {e}")
            print(f"⚠️ Error ejecutando floss falso: {e}")

    async def start_auto_emote_cycle(self):
        """Inicia ciclo automático de todos los 224 emotes en secuencia infinita"""
        try:
            self.bot_mode = "auto"
            log_event("BOT", "Iniciando ciclo automático de 224 emotes")
            print("🎭 Modo AUTOMÁTICO activado - ciclo de 224 emotes")

            emote_index = 1  # Empezamos desde el emote #1

            while self.bot_mode == "auto":
                try:
                    # Obtener el emote actual por número
                    emote_key = str(emote_index)
                    if emote_key in emotes:
                        emote_data = emotes[emote_key]
                        emote_id = emote_data["id"]
                        emote_name = emote_data["name"]
                        duration = emote_data["duration"]

                        log_event("BOT", f"Reproduciendo emote #{emote_index}: {emote_name} ({emote_id}) - Duración: {duration}s")
                        print(f"🎭 Bot emote #{emote_index}: {emote_name} - {duration}s")

                        # Reproducir el emote
                        await self.highrise.send_emote(emote_id, self.bot_id)

                        # Esperar la duración del emote
                        await asyncio.sleep(duration)

                        # Avanzar al siguiente emote
                        emote_index += 1

                        # Si llegamos al final, volver al principio (ciclo infinito)
                        if emote_index > 224:
                            emote_index = 1
                            log_event("BOT", "Ciclo de emotes completado, reiniciando desde el principio")
                            print("🔄 Ciclo de emotes completado, reiniciando...")
                    else:
                        log_event("ERROR", f"Emote #{emote_index} no encontrado, saltando al siguiente")
                        emote_index += 1
                        if emote_index > 224:
                            emote_index = 1

                except Exception as e:
                    log_event("ERROR", f"Error reproduciendo emote #{emote_index}: {e}")
                    print(f"⚠️ Error en emote #{emote_index}: {e}")
                    # Continuar con el siguiente emote en caso de error
                    emote_index += 1
                    if emote_index > 224:
                        emote_index = 1
                    await asyncio.sleep(2)  # Pausa corta antes de continuar

        except Exception as e:
            log_event("ERROR", f"Error crítico en ciclo automático de emotes: {e}")
            print(f"❌ Error crítico en ciclo de emotes: {e}")

    async def setup_initial_bot_appearance(self):
        """Configura la apariencia inicial del bot (outfit y emote)"""
        try:
            log_event("BOT", "Starting initial bot appearance setup")
            # Esperar un momento para que el bot se conecte completamente
            await asyncio.sleep(2)

            # Configurar outfit inicial si está especificado en config
            if "bot_initial_outfit" in config:
                outfit_id = config["bot_initial_outfit"]
                try:
                    await self.change_bot_outfit(outfit_id)
                    log_event("BOT", f"Initial bot outfit configured: {outfit_id}")
                    print(f"🎽 Outfit inicial del bot configurado: {outfit_id}")
                except Exception as e:
                    log_event("ERROR", f"Error configurando outfit inicial: {e}")
                    print(f"⚠️  Error configurando outfit inicial: {e}")
            else:
                log_event("BOT", "No initial outfit specified in config")

            # Modo floss deshabilitado por defecto (se puede activar con comando !floss)
            log_event("BOT", f"Bot inicializado en modo idle (bot ID: {self.bot_id})")
            print(f"✅ Bot inicializado en modo idle - usa !floss para activar modo floss")

            log_event("BOT", "Initial bot appearance setup completed")

        except Exception as e:
            log_event("ERROR", f"Error en setup_initial_bot_appearance: {e}")
            print(f"❌ Error en setup_initial_bot_appearance: {e}")

# Обработка сигналов для сохранения данных при завершении
import signal
import sys

def signal_handler(sig, frame):
    """Gestore dei segnali per salvare i dati all'uscita"""
    print("\n🛑 Segnale di uscita ricevuto. Salvataggio dati...")

    # Salviamo il tempo per tutti i giocatori attivi
    current_time = time.time()
    for user_id, join_time in USER_JOIN_TIMES.items():
        if user_id in USER_INFO:
            time_in_room = round(current_time - join_time)
            USER_INFO[user_id]["total_time_in_room"] += time_in_room

    # Salviamo tutti i dati
    try:
        save_leaderboard_data()
        save_user_info()
        print("✅ Dati salvati con successo")
    except Exception as e:
        print(f"❌ Errore nel salvare i dati: {e}")

    print("👋 Arrivederci!")
    sys.exit(0)

# Регистрируем обработчики сигналов
signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# Código principal para ejecutar el bot
if __name__ == "__main__":
    try:
        # Validar configuración necesaria
        if not config.get("api_token"):
            print("❌ Error: No se encontró api_token en config.json")
            sys.exit(1)

        if not config.get("room_id"):
            print("❌ Error: No se encontró room_id en config.json") 
            sys.exit(1)

        api_token = config["api_token"]
        room_id = config["room_id"]

        print("🚀 Iniciando bot High Rise NOCTURNO...")
        print(f"🏠 Room ID: {room_id}")
        print(f"🎭 Emotes disponibles: {len(emotes)}")
        print("=" * 50)

        # Crear instancia del bot
        bot = Bot()

        # Nota: Para ejecutar el bot usa: python -m highrise main:Bot room_id api_token
        print("🔧 Para ejecutar el bot usa: python -m highrise main:Bot", room_id, api_token)

    except KeyboardInterrupt:
        print("\n🛑 Bot detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error crítico ejecutando el bot: {e}")
        log_event("ERROR", f"Error crítico en main: {e}")
        sys.exit(1)