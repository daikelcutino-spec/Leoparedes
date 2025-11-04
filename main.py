import asyncio
import json
import os
import random
import signal
import sys
import time
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Set, Tuple, Union

from highrise import BaseBot, User, Reaction, AnchorPosition
from highrise.models import SessionMetadata, CurrencyItem, Item, Error, Position

# ============================================================================
# CONFIGURACIÓN Y CONSTANTES
# ============================================================================

def load_config():
    """Carga la configuración desde config.json"""
    try:
        with open("config.json", "r", encoding="utf-8") as f:
            config = json.load(f)
        return config
    except Exception as e:
        print(f"Error cargando configuración: {e}")
        return {}

config = load_config()
ADMIN_IDS = config.get("admin_ids", [])
OWNER_ID = config.get("owner_id", "")
MODERATOR_IDS = config.get("moderator_ids", [])
VIP_ZONE = config.get("vip_zone", {"x": 0, "y": 0, "z": 0})
DJ_ZONE = config.get("dj_zone", {"x": 0, "y": 0, "z": 0})
DIRECTIVO_ZONE = config.get("directivo_zone", {"x": 0, "y": 0, "z": 0})
FORBIDDEN_ZONES = config.get("forbidden_zones", [])
BOT_WALLET = config.get("bot_wallet", 0)

# Variables globales
VIP_USERS = set()
BANNED_USERS = {}
MUTED_USERS = {}
USER_HEARTS = {}
USER_ACTIVITY = {}
USER_INFO = {}
USER_NAMES = {}
TELEPORT_POINTS = {}
ACTIVE_EMOTES = {}
USER_JOIN_TIMES = {}
SAVED_OUTFITS = {}
JAIL_USERS = set()  # Usuarios que fueron enviados a la cárcel por admin/owner

# Constantes de reintentos
MAX_RETRIES = 3
RETRY_DELAY = 5

# ============================================================================
# SISTEMA DE LOGGING
# ============================================================================

def log_event(event_type: str, message: str):
    """Sistema de logging de eventos"""
    try:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        log_message = f"[{timestamp}] [{event_type}] {message}\n"

        with open("bot_log.txt", "a", encoding="utf-8") as f:
            f.write(log_message)

        if event_type in ["ERROR", "WARNING", "ADMIN", "MOD"]:
            print(log_message.strip())
    except Exception as e:
        print(f"Error logging event: {e}")

def log_bot_response(message: str):
    """Registra las respuestas del bot para el panel web"""
    try:
        timestamp = datetime.now().strftime("%H:%M:%S")
        with open("bot_responses.txt", "a", encoding="utf-8") as f:
            f.write(f"[{timestamp}] {message}\n")
        
        # Mantener solo las últimas 100 líneas
        try:
            with open("bot_responses.txt", "r", encoding="utf-8") as f:
                lines = f.readlines()
            if len(lines) > 100:
                with open("bot_responses.txt", "w", encoding="utf-8") as f:
                    f.writelines(lines[-100:])
        except:
            pass
    except Exception as e:
        print(f"Error logging bot response: {e}")

def safe_print(message: str):
    """Imprime mensaje de forma segura en Windows, manejando errores de encoding"""
    try:
        print(message)
    except UnicodeEncodeError:
        # Si falla con emojis, imprimir sin ellos
        try:
            print(message.encode('ascii', 'ignore').decode('ascii'))
        except:
            # Si todo falla, usar repr
            print(repr(message))

# ============================================================================
# SISTEMA DE PERSISTENCIA DE DATOS
# ============================================================================

def save_user_info():
    """Guarda información de usuarios"""
    try:
        os.makedirs("data", exist_ok=True)
        serializable_data = {}
        for user_id, data in USER_INFO.items():
            serializable_data[user_id] = {}
            for key, value in data.items():
                if isinstance(value, datetime):
                    serializable_data[user_id][key] = value.isoformat()
                else:
                    serializable_data[user_id][key] = value

        with open("data/user_info.json", "w", encoding="utf-8") as f:
            json.dump(serializable_data, f, indent=2, ensure_ascii=False)
        print(f"Información de usuarios guardada: {len(USER_INFO)} usuarios")
    except Exception as e:
        print(f"Error guardando información de usuarios: {e}")

def save_leaderboard_data():
    """Guarda datos del leaderboard"""
    try:
        os.makedirs("data", exist_ok=True)

        # Guardar corazones
        with open("data/hearts.txt", "w", encoding="utf-8") as f:
            f.write("# Corazones de usuarios (user_id:hearts:username)\n")
            for user_id, hearts in USER_HEARTS.items():
                username = USER_NAMES.get(user_id, f"User_{user_id[:8]}")
                f.write(f"{user_id}:{hearts}:{username}\n")

        # Guardar actividad
        with open("data/activity.txt", "w", encoding="utf-8") as f:
            f.write("# Actividad de usuarios (user_id:messages:last_activity:username)\n")
            for user_id, data in USER_ACTIVITY.items():
                username = USER_NAMES.get(user_id, f"User_{user_id[:8]}")
                last_activity = data["last_activity"].isoformat() if isinstance(data["last_activity"], datetime) else str(data["last_activity"])
                f.write(f"{user_id}:{data['messages']}:{last_activity}:{username}\n")

        print(f"Datos del leaderboard guardados: {len(USER_HEARTS)} corazones, {len(USER_ACTIVITY)} actividad")
    except Exception as e:
        print(f"Error guardando datos del leaderboard: {e}")

async def save_bot_inventory(bot_instance):
    """Guarda el inventario del bot"""
    try:
        inventory_response = await bot_instance.highrise.get_inventory()
        if not isinstance(inventory_response, Error):
            inventory = inventory_response.items
            inventory_data = [
                {
                    "type": item.type,
                    "id": item.id,
                    "amount": item.amount
                }
                for item in inventory
            ]

            os.makedirs("data", exist_ok=True)
            with open("data/bot_inventory.json", "w", encoding="utf-8") as f:
                json.dump(inventory_data, f, indent=2, ensure_ascii=False)

            safe_print(f"✅ Inventario del bot guardado: {len(inventory_data)} items")
    except Exception as e:
        safe_print(f"❌ Error guardando inventario del bot: {e}")

# ============================================================================
# SISTEMA DE GESTIÓN DE SALUD DE EMOTES
# ============================================================================

class EmoteHealthManager:
    """Gestiona la salud de los emotes, detectando y deshabilitando emotes problemáticos"""
    
    HEALTH_FILE = "data/emote_health.json"
    SOFT_FAILURE_THRESHOLD = 3
    HARD_FAILURE_THRESHOLD = 5
    COOLDOWN_HOURS = 24
    
    def __init__(self):
        self.emote_stats = {}
        self.disabled_emotes = set()
        self.load_health_data()
    
    def load_health_data(self):
        """Carga datos de salud de emotes desde el archivo"""
        try:
            if os.path.exists(self.HEALTH_FILE):
                with open(self.HEALTH_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                    self.emote_stats = data.get("stats", {})
                    self.disabled_emotes = set(data.get("disabled", []))
                    safe_print(f"📊 Datos de salud de emotes cargados: {len(self.disabled_emotes)} deshabilitados")
        except Exception as e:
            safe_print(f"⚠️ Error cargando datos de salud de emotes: {e}")
            self.emote_stats = {}
            self.disabled_emotes = set()
    
    def save_health_data(self):
        """Guarda datos de salud de emotes al archivo"""
        try:
            os.makedirs("data", exist_ok=True)
            data = {
                "stats": self.emote_stats,
                "disabled": list(self.disabled_emotes),
                "last_update": datetime.now().isoformat()
            }
            with open(self.HEALTH_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=2, ensure_ascii=False)
        except Exception as e:
            safe_print(f"❌ Error guardando datos de salud de emotes: {e}")
    
    def should_run(self, emote_id: str, emote_name: str = "") -> bool:
        """Determina si un emote debe ejecutarse"""
        if emote_id in self.disabled_emotes:
            return False
        
        if emote_id in self.emote_stats:
            stats = self.emote_stats[emote_id]
            
            if stats.get("hard_disabled", False):
                return False
            
            if stats.get("soft_disabled", False):
                disabled_at = stats.get("disabled_at")
                if disabled_at:
                    try:
                        disabled_time = datetime.fromisoformat(disabled_at)
                        cooldown_end = disabled_time + timedelta(hours=self.COOLDOWN_HOURS)
                        if datetime.now() < cooldown_end:
                            return False
                        else:
                            stats["soft_disabled"] = False
                            stats["failures"] = 0
                            safe_print(f"♻️ Emote {emote_name} ({emote_id}) salió de cooldown")
                            self.save_health_data()
                    except:
                        pass
        
        return True
    
    def record_success(self, emote_id: str, emote_name: str = ""):
        """Registra una ejecución exitosa del emote"""
        is_new_entry = emote_id not in self.emote_stats
        was_soft_disabled = False
        
        if is_new_entry:
            self.emote_stats[emote_id] = {
                "name": emote_name,
                "successes": 0,
                "failures": 0,
                "last_success": None,
                "last_failure": None,
                "soft_disabled": False,
                "hard_disabled": False
            }
        else:
            was_soft_disabled = self.emote_stats[emote_id].get("soft_disabled", False)
        
        self.emote_stats[emote_id]["successes"] += 1
        self.emote_stats[emote_id]["last_success"] = datetime.now().isoformat()
        
        should_save = (
            is_new_entry or 
            was_soft_disabled or 
            self.emote_stats[emote_id]["successes"] % 20 == 0
        )
        
        if should_save:
            self.save_health_data()
    
    def record_failure(self, emote_id: str, emote_name: str, exception: str) -> bool:
        """Registra un fallo del emote. Retorna True si es error de transporte."""
        is_transport_error = self._is_transport_error(exception)
        
        if emote_id not in self.emote_stats:
            self.emote_stats[emote_id] = {
                "name": emote_name,
                "successes": 0,
                "failures": 0,
                "last_success": None,
                "last_failure": None,
                "last_exception": None,
                "soft_disabled": False,
                "hard_disabled": False
            }
        
        stats = self.emote_stats[emote_id]
        stats["failures"] += 1
        stats["last_failure"] = datetime.now().isoformat()
        stats["last_exception"] = str(exception)
        
        if stats["failures"] >= self.HARD_FAILURE_THRESHOLD:
            if not stats.get("hard_disabled", False):
                stats["hard_disabled"] = True
                stats["disabled_at"] = datetime.now().isoformat()
                self.disabled_emotes.add(emote_id)
                safe_print(f"🚫 Emote {emote_name} ({emote_id}) DESHABILITADO PERMANENTEMENTE - {stats['failures']} fallos")
                log_event("EMOTE", f"Emote {emote_name} deshabilitado permanentemente: {stats['failures']} fallos - Último error: {exception}")
        
        elif stats["failures"] >= self.SOFT_FAILURE_THRESHOLD:
            if not stats.get("soft_disabled", False):
                stats["soft_disabled"] = True
                stats["disabled_at"] = datetime.now().isoformat()
                safe_print(f"⚠️ Emote {emote_name} ({emote_id}) en COOLDOWN por {self.COOLDOWN_HOURS}h - {stats['failures']} fallos")
                log_event("EMOTE", f"Emote {emote_name} en cooldown: {stats['failures']} fallos - Último error: {exception}")
        
        self.save_health_data()
        return is_transport_error
    
    def _is_transport_error(self, exception_str: str) -> bool:
        """Detecta si el error es relacionado con el transporte/conexión"""
        transport_keywords = [
            "transport",
            "closing",
            "connection",
            "websocket",
            "disconnect",
            "closed",
            "write to closing"
        ]
        exception_lower = str(exception_str).lower()
        return any(keyword in exception_lower for keyword in transport_keywords)
    
    def get_disabled_count(self) -> int:
        """Retorna el número de emotes deshabilitados"""
        return len(self.disabled_emotes)
    
    def get_stats_summary(self) -> str:
        """Retorna un resumen de las estadísticas"""
        total = len(self.emote_stats)
        disabled = len(self.disabled_emotes)
        soft_disabled = sum(1 for s in self.emote_stats.values() if s.get("soft_disabled", False))
        return f"Total: {total} | Deshabilitados: {disabled} | En cooldown: {soft_disabled}"

# Instancia global del gestor de salud
emote_health_manager = EmoteHealthManager()

# ============================================================================
# CATÁLOGO DE EMOTES
# ============================================================================

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
    "46": {"id": "idle-dance-casual", "name": "casual", "duration": 9.57, "is_free": True},
    "47": {"id": "emote-pose1", "name": "wink", "duration": 4.71, "is_free": True},
    "48": {"id": "emote-pose3", "name": "fightme", "duration": 5.57, "is_free": True},
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

# ============================================================================
# CLASE PRINCIPAL DEL BOT
# ============================================================================

class Bot(BaseBot):
    def __init__(self):
        super().__init__()
        self.last_announcement = 0
        self.user_positions = {}
        self.connection_retries = 0
        self.bot_mode = "idle"
        self.current_emote_task = None
        self.flashmode_cooldown = {}
        self.session_active = False
        self.reconnection_in_progress = False
        self.copied_emotes = {}  # {número: {"emote_id": str, "name": str, "from_user": str}}
        self.copied_emote_mode = False
        self.current_copied_emote = None

    # ========================================================================
    # MÉTODOS DE INICIALIZACIÓN Y CONEXIÓN
    # ========================================================================

    async def connect_with_retry(self):
        """Conexión con reintentos"""
        safe_print("✅ Conexión establecida con High Rise")
        return True

    async def auto_reconnect_loop(self):
        """Sistema de reconexión automática"""
        while True:
            try:
                await asyncio.sleep(30)  # Verificar cada 30 segundos
                
                # Verificar si el bot está en la sala
                try:
                    room_users = await self.highrise.get_room_users()
                    if isinstance(room_users, Error):
                        raise Exception("Error obteniendo usuarios de la sala")
                    
                    # Verificar si el bot está en la lista de usuarios
                    users = room_users.content
                    bot_in_room = any(u.id == self.bot_id for u, _ in users)
                    
                    if not bot_in_room:
                        log_event("WARNING", "Bot no encontrado en la sala, intentando reconectar...")
                        safe_print("⚠️ Bot desconectado de la sala, reconectando...")
                        await self.attempt_reconnection()
                        
                except Exception as e:
                    log_event("ERROR", f"Error verificando presencia del bot: {e}")
                    safe_print(f"❌ Error verificando conexión: {e}")
                    await self.attempt_reconnection()
                    
            except Exception as e:
                log_event("ERROR", f"Error en auto_reconnect_loop: {e}")
                await asyncio.sleep(5)

    async def attempt_reconnection(self):
        """Intenta reconectar el bot"""
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            try:
                safe_print(f"🔄 Intento de reconexión {attempt}/{max_attempts}...")
                log_event("BOT", f"Intento de reconexión {attempt}/{max_attempts}")
                
                # Esperar antes de reintentar
                await asyncio.sleep(attempt * 2)
                
                # Intentar obtener usuarios de la sala como prueba de conexión
                room_users = await self.highrise.get_room_users()
                if not isinstance(room_users, Error):
                    safe_print("✅ Reconexión exitosa!")
                    log_event("BOT", "Reconexión exitosa")
                    
                    # Reiniciar tareas en segundo plano si es necesario
                    asyncio.create_task(self.start_announcements())
                    asyncio.create_task(self.check_console_messages())
                    asyncio.create_task(self.periodic_inventory_save())
                    
                    if self.bot_mode == "auto":
                        asyncio.create_task(self.start_auto_emote_cycle())
                        
                    return True
                    
            except Exception as e:
                log_event("ERROR", f"Fallo en intento {attempt}: {e}")
                safe_print(f"❌ Fallo en intento {attempt}: {e}")
                
        safe_print("❌ No se pudo reconectar después de varios intentos")
        log_event("ERROR", "Reconexión fallida después de múltiples intentos")
        return False

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Inicio del bot"""
        try:
            self.bot_id = session_metadata.user_id
            self.session_active = True
            log_event("BOT", f"Bot ID almacenado: {self.bot_id}")

            if await self.connect_with_retry():
                safe_print("Bot conectado exitosamente!")
                self.load_data()

                # Iniciar tareas en segundo plano
                asyncio.create_task(self.start_announcements())
                asyncio.create_task(self.check_console_messages())
                asyncio.create_task(self.periodic_inventory_save())
                asyncio.create_task(self.auto_reconnect_loop())

                # Configurar apariencia inicial
                await self.setup_initial_bot_appearance()
                await save_bot_inventory(self)

                # Iniciar ciclo automático de emotes (sin esperar a que termine)
                self.bot_mode = "auto"
                asyncio.create_task(self.start_auto_emote_cycle())
                safe_print("🎭 Ciclo automático de 224 emotes iniciado")
                log_event("BOT", "Ciclo automático de 224 emotes iniciado")
            else:
                print("No se pudo conectar al servidor")
                sys.exit(1)
        except Exception as e:
            print(f"Error en on_start: {e}")

        safe_print("🤖 ¡Bot iniciado! Usa !help para ver los comandos.")

    # ========================================================================
    # SISTEMA DE CARGA Y GUARDADO DE DATOS
    # ========================================================================

    def load_data(self):
        """Carga datos desde archivos"""
        try:
            # Crear directorio data si no existe
            os.makedirs("data", exist_ok=True)
            
            # Cargar VIP
            if os.path.exists("data/vip.txt"):
                with open("data/vip.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            VIP_USERS.add(line.strip())
            safe_print(f"✅ Datos VIP cargados: {len(VIP_USERS)} usuarios")

            # Cargar puntos de teletransporte
            if os.path.exists("data/teleport_points.txt"):
                with open("data/teleport_points.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            try:
                                parts = line.strip().split("|")
                                if len(parts) == 4:
                                    name = parts[0]
                                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                                    TELEPORT_POINTS[name] = {"x": x, "y": y, "z": z}
                            except ValueError as e:
                                safe_print(f"⚠️ Error parseando punto: {line.strip()} - {e}")
            safe_print(f"✅ Puntos de teletransporte cargados: {len(TELEPORT_POINTS)} puntos")
            
            # Cargar corazones
            if os.path.exists("data/hearts.txt"):
                with open("data/hearts.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            try:
                                parts = line.strip().split(":")
                                if len(parts) >= 2:
                                    user_id = parts[0]
                                    hearts = int(parts[1])
                                    USER_HEARTS[user_id] = hearts
                                    if len(parts) >= 3:
                                        USER_NAMES[user_id] = parts[2]
                            except ValueError as e:
                                safe_print(f"⚠️ Error parseando corazones: {line.strip()} - {e}")
            safe_print(f"✅ Corazones cargados: {len(USER_HEARTS)} usuarios")
            
            # Cargar actividad
            if os.path.exists("data/activity.txt"):
                with open("data/activity.txt", "r", encoding="utf-8") as f:
                    for line in f:
                        if line.strip() and not line.startswith("#"):
                            try:
                                parts = line.strip().split(":")
                                if len(parts) >= 3:
                                    user_id = parts[0]
                                    messages = int(parts[1])
                                    last_activity = parts[2]
                                    USER_ACTIVITY[user_id] = {
                                        "messages": messages,
                                        "last_activity": datetime.fromisoformat(last_activity)
                                    }
                                    if len(parts) >= 4:
                                        USER_NAMES[user_id] = parts[3]
                            except (ValueError, IndexError) as e:
                                safe_print(f"⚠️ Error parseando actividad: {line.strip()} - {e}")
            safe_print(f"✅ Actividad cargada: {len(USER_ACTIVITY)} usuarios")
            
            # Cargar información de usuarios
            if os.path.exists("data/user_info.json"):
                with open("data/user_info.json", "r", encoding="utf-8") as f:
                    loaded_data = json.load(f)
                    for user_id, data in loaded_data.items():
                        USER_INFO[user_id] = data
                        # Convertir fechas ISO a datetime
                        for key in ["first_seen", "account_created"]:
                            if key in data and data[key]:
                                try:
                                    USER_INFO[user_id][key] = datetime.fromisoformat(data[key].replace('Z', '+00:00'))
                                except:
                                    pass
            safe_print(f"✅ Info de usuarios cargada: {len(USER_INFO)} usuarios")
            
            # Cargar outfits guardados
            if os.path.exists("data/saved_outfits.json"):
                from highrise.models import Item
                with open("data/saved_outfits.json", "r", encoding="utf-8") as f:
                    outfits_data = json.load(f)
                    for num_str, items_data in outfits_data.items():
                        outfit_items = [Item(type=item["type"], id=item["id"], amount=item.get("amount", 1)) for item in items_data]
                        SAVED_OUTFITS[int(num_str)] = outfit_items
            safe_print(f"✅ Outfits guardados cargados: {len(SAVED_OUTFITS)} outfits")
            
        except Exception as e:
            safe_print(f"❌ Error cargando datos: {e}")
            import traceback
            traceback.print_exc()

    def save_data(self):
        """Guarda datos en archivos"""
        try:
            os.makedirs("data", exist_ok=True)

            # Guardar VIP
            with open("data/vip.txt", "w", encoding="utf-8") as f:
                f.write("# Usuarios VIP (un username por línea)\n")
                for username in sorted(VIP_USERS):
                    f.write(f"{username}\n")
            safe_print(f"✅ Datos VIP guardados: {len(VIP_USERS)} usuarios")

            # Guardar puntos de teletransporte
            with open("data/teleport_points.txt", "w", encoding="utf-8") as f:
                f.write("# Puntos de teletransporte (nombre|x|y|z)\n")
                for name, coords in sorted(TELEPORT_POINTS.items()):
                    f.write(f"{name}|{coords['x']}|{coords['y']}|{coords['z']}\n")
            safe_print(f"✅ Puntos de teletransporte guardados: {len(TELEPORT_POINTS)}")

            # Guardar outfits
            if SAVED_OUTFITS:
                outfits_data = {}
                for num, outfit in SAVED_OUTFITS.items():
                    outfits_data[str(num)] = [{"type": item.type, "id": item.id, "amount": item.amount} for item in outfit]
                
                with open("data/saved_outfits.json", "w", encoding="utf-8") as f:
                    json.dump(outfits_data, f, indent=2, ensure_ascii=False)
                safe_print(f"✅ Outfits guardados: {len(SAVED_OUTFITS)}")

            save_user_info()
            save_leaderboard_data()
            
        except Exception as e:
            safe_print(f"❌ Error guardando datos: {e}")
            import traceback
            traceback.print_exc()

    # ========================================================================
    # SISTEMA DE VERIFICACIÓN DE PERMISOS
    # ========================================================================

    def is_admin(self, user_id: str) -> bool:
        """Verifica si es administrador"""
        return user_id in ADMIN_IDS or user_id == OWNER_ID

    def is_moderator(self, user_id: str) -> bool:
        """Verifica si es moderador"""
        return user_id in MODERATOR_IDS or self.is_admin(user_id)

    def is_vip(self, user_id: str) -> bool:
        """Verifica si es VIP por user_id"""
        username = USER_NAMES.get(user_id)
        if username:
            return username in VIP_USERS
        return False

    def is_vip_by_username(self, username: str) -> bool:
        """Verifica si es VIP por username"""
        return username in VIP_USERS

    def is_banned(self, user_id: str) -> bool:
        """Verifica si está baneado"""
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
        """Verifica si está silenciado"""
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

    # ========================================================================
    # SISTEMA DE GESTIÓN DE USUARIOS
    # ========================================================================

    def get_user_hearts(self, user_id: str) -> int:
        """Obtiene corazones del usuario"""
        return USER_HEARTS.get(user_id, 0)

    def add_user_hearts(self, user_id: str, hearts: int, username: str | None = None):
        """Añade corazones al usuario"""
        if user_id not in USER_HEARTS:
            USER_HEARTS[user_id] = 0
        USER_HEARTS[user_id] += hearts

        if username:
            USER_NAMES[user_id] = username

        save_leaderboard_data()

    def update_activity(self, user_id: str):
        """Actualiza actividad del usuario"""
        if user_id not in USER_ACTIVITY:
            USER_ACTIVITY[user_id] = {"messages": 0, "last_activity": datetime.now()}
        USER_ACTIVITY[user_id]["messages"] += 1
        USER_ACTIVITY[user_id]["last_activity"] = datetime.now()

        if user_id in USER_INFO:
            USER_INFO[user_id]["total_messages"] = USER_ACTIVITY[user_id]["messages"]

    def update_user_info(self, user_id: str, username: str):
        """Actualiza información del usuario"""
        if user_id not in USER_INFO:
            USER_INFO[user_id] = {
                "username": username,
                "first_seen": datetime.now().isoformat(),
                "account_created": None,
                "total_time_in_room": 0,
                "total_messages": 0,
                "time_joined": time.time()
            }
        else:
            USER_INFO[user_id]["username"] = username
            USER_INFO[user_id]["total_messages"] = USER_ACTIVITY.get(user_id, {}).get("messages", 0)

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

    def format_time(self, seconds: int) -> str:
        """Formatea el tiempo en formato legible"""
        hours = seconds // 3600
        minutes = (seconds % 3600) // 60
        seconds = seconds % 60

        if hours > 0:
            return f"{hours}h {minutes}m {seconds}s"
        elif minutes > 0:
            return f"{minutes}m {seconds}s"
        else:
            return f"{seconds}s"

    def get_user_total_time(self, user_id: str) -> int:
        """Obtiene el tiempo total del usuario en la sala"""
        if user_id in USER_INFO:
            return USER_INFO[user_id].get("total_time_in_room", 0)
        return 0

    def get_help_for_user(self, user_id: str, username: str) -> str:
        """Retorna comandos disponibles según el rol del usuario"""
        is_owner = (user_id == OWNER_ID)
        is_admin = self.is_admin(user_id)
        is_vip = self.is_vip(user_id)

        if is_owner or is_admin:
            return ("👑 COMANDOS PROPIETARIO/ADMIN:\n"
                    "📊 INFORMACIÓN:\n"
                    "!info - Tu información\n"
                    "!info @user - Info de usuario\n"
                    "!role - Tu rol\n"
                    "!role list - Lista roles\n"
                    "!stats - Estadísticas sala\n"
                    "!online - Usuarios online\n"
                    "!myid - Tu ID|||"
                    "💖 CORAZONES & REACCIONES:\n"
                    "!heart @user [cantidad] - Dar corazones\n"
                    "!heartall - Corazones a todos\n"
                    "!thumbs @user [cantidad] - Pulgar arriba\n"
                    "!clap @user [cantidad] - Aplaudir\n"
                    "!wave @user [cantidad] - Saludar\n"
                    "!game love @user1 @user2 - Amorómetro|||"
                    "🎭 EMOTES:\n"
                    "!emote list - Lista emotes\n"
                    "[número] - Hacer emote\n"
                    "[emote] - Hacer emote\n"
                    "!emote @user [emote] - Emote a usuario\n"
                    "!emote all [emote] - Emote a todos\n"
                    "[emote] all - Emote a todos\n"
                    "!stop - Detener tu emote\n"
                    "!stop @user - Detener emote usuario\n"
                    "!stop all - Detener todos emotes\n"
                    "!stopall - Detener todos emotes|||"
                    "⚡ TELETRANSPORTE:\n"
                    "!flash [x] [y] [z] - Flash entre pisos\n"
                    "!bring @user - Traer usuario\n"
                    "!goto @user [punto] - Enviar usuario a punto\n"
                    "!tplist - Puntos de teleporte\n"
                    "!tp [nombre] - Ir a punto\n"
                    "[nombre_punto] - Ir a punto\n"
                    "!tele list - Lista ubicaciones\n"
                    "!tele @user - Ir a usuario\n"
                    "!addzone [nombre] - Crear zona\n"
                    "!TPus [nombre] - Crear punto TP\n"
                    "!delpoint [nombre] - Eliminar punto|||"
                    "🔨 MODERACIÓN:\n"
                    "!vip @user - Dar VIP\n"
                    "!givevip @user - Dar VIP\n"
                    "!unvip @user - Quitar VIP\n"
                    "!checkvip [@user] - Verificar VIP\n"
                    "!kick @user - Expulsar\n"
                    "!ban @user - Banear\n"
                    "!unban @user - Desbanear\n"
                    "!freeze @user - Congelar\n"
                    "!mute @user [seg] - Silenciar\n"
                    "!unmute @user - Quitar silencio\n"
                    "!jail @user - Enviar a cárcel\n"
                    "!unjail @user - Liberar de cárcel\n"
                    "!banlist - Lista baneados\n"
                    "!mutelist - Lista silenciados\n"
                    "!privilege @user - Ver privilegios|||"
                    "🤖 BOT:\n"
                    "!bot @user - Atacar con bot\n"
                    "!tome - Bot a ti\n"
                    "!automode - Modo automático\n"
                    "!say [mensaje] - Bot habla\n"
                    "!mimic @user - Imitar usuario\n"
                    "!copyoutfit - Copiar tu outfit|||"
                    "👔 APARIENCIA:\n"
                    "!outfit [número] - Cambiar outfit\n"
                    "!inventory - Ver inventario\n"
                    "!inventory @user - Ver outfit usuario\n"
                    "!give @user [item] - Dar item|||"
                    "🎵 DJ & MÚSICA:\n"
                    "!dj - Panel DJ\n"
                    "!music play - Reproducir\n"
                    "!music stop - Detener\n"
                    "!music pause - Pausar|||"
                    "💰 DINERO:\n"
                    "!tip all [1-5] - Dar oro a todos\n"
                    "!tip only [X] - Dar oro a X usuarios\n"
                    "!wallet - Balance bot|||"
                    "🏆 LOGROS & RANKING:\n"
                    "!leaderboard heart - Top corazones\n"
                    "!leaderboard active - Top actividad\n"
                    "!achievements - Tus logros\n"
                    "!rank - Tu rango\n"
                    "!daily - Recompensa diaria\n"
                    "!trackme - Seguimiento actividad|||"
                    "⚙️ ZONAS:\n"
                    "!setvipzone / !sv - Establecer zona VIP\n"
                    "!setdj - Establecer zona DJ\n"
                    "!setdirectivo - Establecer zona directivo\n"
                    "!setspawn - Establecer punto de inicio del bot|||"
                    "🥊 INTERACCIONES:\n"
                    "!punch @user - Golpear\n"
                    "!slap @user - Bofetada\n"
                    "!flirt @user - Coquetear\n"
                    "!scare @user - Asustar\n"
                    "!electro @user - Electrocutar\n"
                    "!hug @user - Abrazar\n"
                    "!ninja @user - Ataque ninja\n"
                    "!laugh @user - Reír\n"
                    "!boom @user - Explotar|||"
                    "🔧 SISTEMA:\n"
                    "!restart - Reiniciar bot\n"
                    "!help - Ver comandos\n"
                    "!help interaction - Ayuda interacción\n"
                    "!help teleport - Ayuda teleporte\n"
                    "!help leaderboard - Ayuda ranking\n"
                    "!help heart - Ayuda corazones")

        elif is_vip:
            return ("⭐ COMANDOS VIP:\n"
                    "📊 INFORMACIÓN:\n"
                    "!info - Tu información\n"
                    "!info @user - Info de usuario\n"
                    "!role - Tu rol\n"
                    "!role list - Lista roles\n"
                    "!stats - Estadísticas sala\n"
                    "!online - Usuarios online\n"
                    "!myid - Tu ID|||"
                    "💖 CORAZONES & REACCIONES:\n"
                    "!heart @user - Dar corazón\n"
                    "!thumbs @user - Pulgar arriba\n"
                    "!clap @user - Aplaudir\n"
                    "!wave @user - Saludar\n"
                    "!game love @user1 @user2 - Amorómetro|||"
                    "🎭 EMOTES:\n"
                    "!emote list - Lista emotes\n"
                    "[número] - Hacer emote\n"
                    "[emote] - Hacer emote\n"
                    "!stop - Detener tu emote\n"
                    "!stop @user - Detener emote usuario|||"
                    "⚡ TELETRANSPORTE:\n"
                    "!flash [x] [y] [z] - Flash entre pisos\n"
                    "!tplist - Puntos de teleporte\n"
                    "!tp [nombre] - Ir a punto\n"
                    "[nombre_punto] - Ir a punto\n"
                    "!tele list - Lista ubicaciones\n"
                    "!tele @user - Ir a usuario|||"
                    "🏆 LOGROS & RANKING:\n"
                    "!leaderboard heart - Top corazones\n"
                    "!leaderboard active - Top actividad\n"
                    "!achievements - Tus logros\n"
                    "!rank - Tu rango\n"
                    "!daily - Recompensa diaria\n"
                    "!trackme - Seguimiento actividad|||"
                    "🥊 INTERACCIONES:\n"
                    "!punch @user - Golpear\n"
                    "!slap @user - Bofetada\n"
                    "!flirt @user - Coquetear\n"
                    "!scare @user - Asustar\n"
                    "!electro @user - Electrocutar\n"
                    "!hug @user - Abrazar\n"
                    "!ninja @user - Ataque ninja\n"
                    "!laugh @user - Reír\n"
                    "!boom @user - Explotar|||"
                    "🔧 AYUDA:\n"
                    "!help - Ver comandos\n"
                    "!help interaction - Ayuda interacción\n"
                    "!help teleport - Ayuda teleporte\n"
                    "!help leaderboard - Ayuda ranking\n"
                    "!help heart - Ayuda corazones")

        else:
            return ("👤 COMANDOS USUARIO:\n"
                    "📊 INFORMACIÓN:\n"
                    "!info - Tu información\n"
                    "!info @user - Info de usuario\n"
                    "!role - Tu rol\n"
                    "!role list - Lista roles\n"
                    "!stats - Estadísticas sala\n"
                    "!online - Usuarios online\n"
                    "!myid - Tu ID|||"
                    "💖 CORAZONES & REACCIONES:\n"
                    "!heart @user - Dar corazón\n"
                    "!thumbs @user - Pulgar arriba\n"
                    "!clap @user - Aplaudir\n"
                    "!wave @user - Saludar\n"
                    "!game love @user1 @user2 - Amorómetro|||"
                    "🎭 EMOTES:\n"
                    "!emote list - Lista emotes\n"
                    "[número] - Hacer emote\n"
                    "[emote] - Hacer emote\n"
                    "!stop - Detener tu emote|||"
                    "⚡ TELETRANSPORTE:\n"
                    "!flash [x] [y] [z] - Flash entre pisos\n"
                    "!tplist - Puntos de teleporte\n"
                    "!tp [nombre] - Ir a punto\n"
                    "[nombre_punto] - Ir a punto\n"
                    "!tele list - Lista ubicaciones|||"
                    "🏆 LOGROS & RANKING:\n"
                    "!leaderboard heart - Top corazones\n"
                    "!leaderboard active - Top actividad\n"
                    "!achievements - Tus logros\n"
                    "!rank - Tu rango\n"
                    "!daily - Recompensa diaria\n"
                    "!trackme - Seguimiento actividad|||"
                    "🥊 INTERACCIONES:\n"
                    "!punch @user - Golpear\n"
                    "!slap @user - Bofetada\n"
                    "!flirt @user - Coquetear\n"
                    "!scare @user - Asustar\n"
                    "!electro @user - Electrocutar\n"
                    "!hug @user - Abrazar\n"
                    "!ninja @user - Ataque ninja\n"
                    "!laugh @user - Reír\n"
                    "!boom @user - Explotar|||"
                    "🔧 AYUDA:\n"
                    "!help - Ver comandos\n"
                    "!help interaction - Ayuda interacción\n"
                    "!help teleport - Ayuda teleporte\n"
                    "!help leaderboard - Ayuda ranking\n"
                    "!help heart - Ayuda corazones")

    def is_in_forbidden_zone(self, x: float, y: float, z: float, user_id: Optional[str] = None) -> bool:
        """Verifica si el punto está en zona prohibida
        Admin y owner tienen acceso completo a todas las zonas"""
        # Admin y owner pueden acceder a cualquier zona
        if user_id and (self.is_admin(user_id) or user_id == OWNER_ID):
            return False
        
        for zone in FORBIDDEN_ZONES:
            distance = ((x - zone["x"])**2 + (y - zone["y"])**2 + (z - zone["z"])**2)**0.5
            if distance <= zone["radius"]:
                return True
        return False

    def calculate_distance(self, pos1, pos2) -> float:
        """Calcula la distancia entre dos posiciones"""
        return ((pos1.x - pos2.x)**2 + (pos1.y - pos2.y)**2 + (pos1.z - pos2.z)**2)**0.5

    async def teleport_user(self, user_id: str, x: float, y: float, z: float):
        """Teletransporta al usuario"""
        try:
            position = Position(x, y, z)
            await self.highrise.teleport(user_id, position)
            return True
        except Exception as e:
            print(f"Error en teleport_user: {e}")
            return False

    async def send_emote_loop(self, user_id: str, emote_id: str):
        """Inicia la emoción en un bucle infinito"""
        ACTIVE_EMOTES[user_id] = emote_id

        emote_info = next((e for e in emotes.values() if e["id"] == emote_id), None)
        if not emote_info:
            if user_id in ACTIVE_EMOTES: del ACTIVE_EMOTES[user_id]
            return

        while user_id in ACTIVE_EMOTES and ACTIVE_EMOTES[user_id] == emote_id and ACTIVE_EMOTES[user_id] is not None:
            try:
                await self.highrise.send_emote(emote_id, user_id)
                duration = emote_info.get("duration", 5)
                await asyncio.sleep(max(0.1, duration - 0.3))
            except Exception as e:
                print(f"Error en send_emote_loop: {e}")
                break

        if user_id in ACTIVE_EMOTES and ACTIVE_EMOTES[user_id] is None:
            del ACTIVE_EMOTES[user_id]

    async def stop_emote_loop(self, user_id: str):
        """Detiene la emoción en el bucle"""
        if user_id in ACTIVE_EMOTES:
            ACTIVE_EMOTES[user_id] = None
            try:
                stop_animations = ["idle", "idle-loop-happy", "idle-loop-sad", "idle-loop-tired"]
                for stop_anim in stop_animations:
                    try:
                        await self.highrise.send_emote(stop_anim, user_id)
                        await asyncio.sleep(0.1)
                    except Exception:
                        continue
            except Exception as e:
                print(f"Error general en stop_animations: {e}")

            await asyncio.sleep(1.0)
            if user_id in ACTIVE_EMOTES:
                del ACTIVE_EMOTES[user_id]

    async def handle_command(self, user: User, message: str, is_whisper: bool) -> None:
        """Procesa comandos del usuario"""
        global VIP_ZONE
        msg = message.strip()
        user_id = user.id
        username = user.username

        public_commands = [
            "!game love", "!stats", "!online", "!info", "!role"
        ]
        force_public = any(msg.startswith(cmd) for cmd in public_commands)

        context_dependent_commands = [
            "!heart", "!heartall", "!thumbs", "!clap", "!wave",
            "!punch", "!slap", "!flirt", "!scare", "!electro", 
            "!hug", "!ninja", "!laugh", "!boom"
        ]
        is_context_dependent = any(msg.startswith(cmd) for cmd in context_dependent_commands)

        async def send_response(text: str):
            # Registrar comando y respuesta en formato claro
            if msg.startswith("!"):
                log_bot_response(f"@{username}: {msg}")
                log_bot_response(f"BOT → {text}")
            
            # Si es un comando que debe ser público, siempre enviar al chat
            if force_public:
                await self.highrise.chat(text)
            # Si es un comando que depende del contexto (reacciones/interacciones)
            elif is_context_dependent:
                if is_whisper:
                    await self.highrise.send_whisper(user.id, text)
                else:
                    await self.highrise.chat(text)
            # Todos los demás comandos siempre por whisper
            else:
                await self.highrise.send_whisper(user.id, text)

        # Comando !help
        if msg == "!help":
            help_text = self.get_help_for_user(user_id, username)
            help_groups = help_text.split('|||')
            
            # Enviar cada grupo de comandos por separado con delay
            for group in help_groups:
                if group.strip():
                    # Dividir grupos muy largos en sub-mensajes si exceden ~250 caracteres
                    group_text = group.strip()
                    if len(group_text) > 250:
                        lines = group_text.split('\n')
                        current_msg = ""
                        for line in lines:
                            if len(current_msg) + len(line) + 1 > 250:
                                if current_msg:
                                    await self.highrise.send_whisper(user.id, current_msg)
                                    await asyncio.sleep(0.5)
                                current_msg = line
                            else:
                                current_msg += ("\n" if current_msg else "") + line
                        if current_msg:
                            await self.highrise.send_whisper(user.id, current_msg)
                            await asyncio.sleep(0.5)
                    else:
                        await self.highrise.send_whisper(user.id, group_text)
                        await asyncio.sleep(0.5)
            return

        # Comando !info
        if msg == "!info":
            await self.show_user_info(user, public_response=True)
            return
        if msg.startswith("!info @"):
            target_username = msg[7:].strip()
            await self.show_user_info_by_username(target_username)
            return

        # Comando !role
        if msg == "!role":
            role_info = self.get_user_role_info(user)
            await self.highrise.chat(f"🎭 {role_info}")
            return
        if msg.startswith("!role @"):
            target_username = msg[7:].strip()
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await self.highrise.chat("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            target_user = next((u for u, _ in users if u.username == target_username), None)
            if not target_user:
                await self.highrise.chat(f"❌ Usuario {target_username} no encontrado!")
                return
            role_info = self.get_user_role_info(target_user)
            await self.highrise.chat(f"🎭 {role_info}")
            return
        if msg == "!role list":
            await self.highrise.chat("🎭 LISTA DE ROLES:\n👑 Propietario\n🛡️ Administrador\n⚖️ Moderador\n⭐ VIP\n👤 Usuario Normal")
            return

        # Ayuda para secciones
        if msg == "!help interaction": await send_response("🥊 COMANDOS DE INTERACCIÓN:\n!punch @user — golpear\n!slap @user — bofetada\n!flirt @user — coquetear\n!scare @user — asustar\n!electro @user — electricidad\n!hug @user — abrazar\n!ninja @user — ninja\n!laugh @user — reír\n!boom @user — explosión")
        if msg == "!help teleport": await send_response("📍 COMANDOS DE TELETRANSPORTE:\n!tplist — lista de puntos\n[nombre_punto] — teletransporte al punto\n!tele zonaVIP — zona VIP")
        if msg == "!help leaderboard": await send_response("🏆 TABLA DE CLASIFICACIÓN:\n!leaderboard heart — top por corazones\n!leaderboard active — top por actividad")
        if msg == "!help heart": await send_response("❤️ COMANDO DE CORAZONES:\n!heart @usuario [cantidad] — enviar corazones\n💖 También puedes enviar corazones con reacciones!")

        # Comando !copyemote @user o !copyemote [user_id]
        if msg.startswith("!copyemote "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await send_response("❌ ¡Solo propietario y administradores pueden copiar emotes!")
                return
            
            parts = msg.split()
            if len(parts) < 2:
                await send_response("❌ Usa: !copyemote @usuario o !copyemote [user_id]")
                return
            
            target_identifier = parts[1].replace("@", "")
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                return
            
            users = response.content
            # Buscar por username o user_id
            target_user = next((u for u, _ in users if u.username == target_identifier or u.id == target_identifier), None)
            
            if not target_user:
                await send_response(f"❌ Usuario/Bot {target_identifier} no encontrado en la sala!")
                return
            
            # Verificar si el usuario tiene un emote activo
            if target_user.id not in ACTIVE_EMOTES or ACTIVE_EMOTES[target_user.id] is None:
                await send_response(f"❌ {target_user.username} no está ejecutando ningún emote!")
                return
            
            emote_id = ACTIVE_EMOTES[target_user.id]
            emote_name = next((e["name"] for e in emotes.values() if e["id"] == emote_id), emote_id)
            
            # Guardar emote copiado con número incremental (SIN outfit)
            emote_number = len(self.copied_emotes) + 1
            self.copied_emotes[emote_number] = {
                "emote_id": emote_id,
                "name": emote_name,
                "from_user": target_user.username,
                "from_user_id": target_user.id
            }
            
            await send_response(f"✅ Emote '{emote_name}' copiado de @{target_user.username}\n📋 Guardado como #{emote_number}\n💡 Usa: !emotecopy {emote_number}")
            log_event("EMOTE", f"Emote '{emote_name}' copiado de {target_user.username} (ID: {target_user.id[:8]}...) como #{emote_number}")
            return

        # Comando !listemotes - listar emotes copiados
        if msg == "!listemotes":
            if not self.copied_emotes:
                await send_response("📋 No hay emotes copiados")
                return
            
            emote_list = "📋 EMOTES COPIADOS:\n"
            for num, data in self.copied_emotes.items():
                emote_list += f"#{num} - {data['name']} (de @{data['from_user']})\n"
            emote_list += "\n💡 Usa: !emotecopy [número]"
            await send_response(emote_list)
            return

        # Comando !emotecopy [número]
        if msg.startswith("!emotecopy "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await send_response("❌ ¡Solo propietario y administradores pueden usar emotes copiados!")
                return
            
            parts = msg.split()
            if len(parts) < 2:
                await send_response("❌ Usa: !emotecopy [número]")
                return
            
            try:
                emote_num = int(parts[1])
            except ValueError:
                await send_response("❌ Número inválido")
                return
            
            if emote_num not in self.copied_emotes:
                await send_response(f"❌ Emote #{emote_num} no existe. Usa !listemotes")
                return
            
            # Detener ciclo automático si está activo
            if self.current_emote_task and not self.current_emote_task.done():
                self.current_emote_task.cancel()
                await asyncio.sleep(0.5)
            
            # Activar modo de emote copiado
            emote_data = self.copied_emotes[emote_num]
            self.copied_emote_mode = True
            self.current_copied_emote = emote_data["emote_id"]
            self.bot_mode = "copied"
            
            # Iniciar bucle infinito del emote copiado
            self.current_emote_task = asyncio.create_task(self.start_copied_emote_loop(emote_data["emote_id"]))
            
            await send_response(f"🎭 Emote '{emote_data['name']}' activado en bucle infinito\n💡 Para cambiar, usa !automode o !emotecopy con otro número")
            await self.highrise.chat(f"🎭 Bot ejecutando emote '{emote_data['name']}' en bucle")
            log_event("BOT", f"Modo emote copiado activado: '{emote_data['name']}'")
            return

        # Comando !emote list
        if msg == "!emote list":
            total_emotes = len(emotes)
            free_emotes = sum(1 for e in emotes.values() if e["is_free"])
            emote_list = f"🎭 LISTA DE EMOTES ({total_emotes} total, {free_emotes} gratuitos):\n\n"
            
            # Mostrar en grupos de 10
            emote_items = list(emotes.items())
            for i in range(0, len(emote_items), 10):
                batch = emote_items[i:i+10]
                batch_text = ""
                for num, data in batch:
                    status = "✅" if data["is_free"] else "🔒"
                    batch_text += f"{status} #{num} - {data['name']}\n"
                await send_response(emote_list + batch_text if i == 0 else batch_text)
                await asyncio.sleep(0.3)
            
            await send_response("💡 Usa: [número] o [nombre] para hacer un emote")
            return

        # Ejecución de emotes
        if msg.isdigit():
            emote_number = msg
            emote = emotes.get(emote_number)
            if emote and emote["is_free"]:
                try:
                    response = await self.highrise.get_room_users()
                    if isinstance(response, Error):
                        await send_response("❌ Error obteniendo usuarios")
                        log_event("ERROR", f"get_room_users failed: {response.message}")
                        return
                    users = response.content
                    user_obj = next((u for u, _ in users if u.id == user.id), None)
                    if user_obj:
                        asyncio.create_task(self.send_emote_loop(user.id, emote["id"]))
                        await send_response( f"🎭 Iniciaste la animación: {emote['name']} (#{emote_number})")
                    else:
                        await send_response( f"❌ @{user.username}: No estás en la sala.")
                except Exception as e:
                    await send_response( f"❌ Error al iniciar animación #{emote_number} - {str(e)[:50]}")
            else:
                await send_response( f"❌ Número de animación #{emote_number} no existe o no es gratuito.")
            return
        if msg.startswith("!emote"):
            parts = msg.split()
            target_user_ids = [user.id]
            emote_key = msg[7:].strip()
            apply_to_all = False

            if len(parts) >= 3 and parts[1].lower() == "all":
                if not (self.is_admin(user_id) or user_id == OWNER_ID):
                    await send_response( "❌ ¡Solo administradores y propietario pueden usar !emote all!")
                    return
                apply_to_all = True
                emote_key = " ".join(parts[2:])
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                target_user_ids = [u.id for u, _ in users if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"])]

            elif len(parts) >= 3 and parts[1].startswith("@"):
                if not (self.is_admin(user_id) or user_id == OWNER_ID):
                    await send_response( "❌ ¡Solo administradores y propietario pueden usar animaciones en otros usuarios!")
                    return
                target_username = parts[1][1:]
                emote_key = " ".join(parts[2:])
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                target_user = next((u for u, _ in users if u.username == target_username), None)
                if not target_user: await send_response( f"❌ ¡Usuario {target_username} no encontrado!"); return
                target_user_ids = [target_user.id]

            emote = emotes.get(emote_key)
            if not emote:
                for e in emotes.values():
                    if e["name"].lower() == emote_key.lower() or e["id"].lower() == emote_key.lower():
                        emote = e
                        break

            if emote:
                if emote["is_free"]:
                    for target_id in target_user_ids:
                        asyncio.create_task(self.send_emote_loop(target_id, emote["id"]))
                    await send_response( f"🎭 Animación '{emote['name']}' activada")
                else:
                    await send_response( f"❌ La animación '{emote_key}' no es gratuita.")
            else:
                await send_response( f"❌ No existe la animación '{emote_key}'. Usa !emote list.")
            return

        # Ejecución rápida de emotes sin !emote
        emote_found = False
        for e in emotes.values():
            if e["name"].lower() == msg.lower() or e["id"].lower() == msg.lower():
                emote_found = True
                break
        if msg and not msg.startswith("!") and not msg.isdigit() and emote_found:
            parts = msg.split()
            target_user_ids = [user.id]
            emote_name = msg
            include_self = True

            if len(parts) >= 2:
                if parts[0].startswith("@"):
                    if not (self.is_admin(user_id) or user_id == OWNER_ID):
                        await send_response( "❌ ¡Solo administradores y propietario pueden usar animaciones en otros usuarios!")
                        return
                    target_username = parts[0][1:]
                    emote_name = " ".join(parts[1:])
                    include_self = False
                    response = await self.highrise.get_room_users()
                    if isinstance(response, Error):
                        await send_response("❌ Error obteniendo usuarios")
                        log_event("ERROR", f"get_room_users failed: {response.message}")
                        return
                    users = response.content
                    target_user = next((u for u, _ in users if u.username == target_username), None)
                    if not target_user: await send_response( f"❌ ¡Usuario {target_username} no encontrado!"); return
                    target_user_ids = [target_user.id]
                else:
                    if not (self.is_admin(user_id) or user_id == OWNER_ID):
                        await send_response( "❌ ¡Solo administradores y propietario pueden usar animaciones en otros usuarios!")
                        return
                    emote_name = parts[0]
                    target_parts = parts[1:]
                    response = await self.highrise.get_room_users()
                    if isinstance(response, Error):
                        await send_response("❌ Error obteniendo usuarios")
                        log_event("ERROR", f"get_room_users failed: {response.message}")
                        return
                    users = response.content
                    target_user_ids = []
                    for part in target_parts:
                        if part == "all":
                            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden hacer emotes a todos!"); return
                            target_user_ids.extend([u.id for u, _ in users if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"])])
                        elif part.startswith("@"):
                            target_username = part[1:]
                            target_user = next((u for u, _ in users if u.username == target_username), None)
                            if target_user: target_user_ids.append(target_user.id)
                            else: await send_response( f"❌ ¡Usuario {target_username} no encontrado!"); return
                    if not target_user_ids: await send_response("❌ ¡No se encontraron usuarios objetivo!"); return

            emote = next((e for e in emotes.values() if e["name"].lower() == emote_name.lower() or e["id"].lower() == emote_name.lower()), None)
            if emote:
                if emote["is_free"]:
                    if include_self and user.id not in target_user_ids:
                        target_user_ids.append(user.id)
                    for target_user_id in target_user_ids:
                        asyncio.create_task(self.send_emote_loop(target_user_id, emote["id"]))
                    await send_response( f"🎭 Animación '{emote_name}' activada")
                else:
                    await send_response( f"❌ La animación '{emote_name}' no es gratuita.")
            else:
                await send_response( f"❌ No existe la animación '{emote_name}'. Usa !emote list.")
            return

        # Comando stop
        if msg == "stop" or msg == "!stop" or msg == "0":
            await self.stop_emote_loop(user.id)
            await send_response( f"🛑 Detuviste tu animación.")
            return
        if msg.startswith("!stop "):
            stop_target = msg[6:].strip()
            if stop_target == "all":
                if not self.is_admin(user_id): await send_response("❌ ¡Solo administradores pueden detener todas las animaciones!"); return
                active_users = list(ACTIVE_EMOTES.keys())
                for active_user_id in active_users: await self.stop_emote_loop(active_user_id)
                await send_response( f"🛑 Detuviste todas las animaciones en la sala.")
            elif stop_target.startswith("@"):
                if not (self.is_vip(user_id) or self.is_admin(user_id)): await send_response("❌ ¡Solo VIP y administradores pueden detener animaciones de otros!"); return
                target_username = stop_target[1:]
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                target_user = next((u for u, _ in users if u.username == target_username), None)
                if not target_user: await send_response( f"❌ ¡Usuario {target_username} no encontrado!"); return
                await self.stop_emote_loop(target_user.id)
                await send_response( f"🛑 Detuviste la animación de @{target_username}")
            return
        if msg == "!stopall":
            if self.is_admin(user_id):
                active_users = list(ACTIVE_EMOTES.keys())
                for active_user_id in active_users: await self.stop_emote_loop(active_user_id)
                await send_response( f"🛑 Detuviste todas las animaciones en la sala.")
            else: await send_response("❌ Solo administradores pueden usar este comando.")
            return

        # Comando !myid
        if msg == "!myid": await send_response( f"🆔 Tu ID de usuario es: {user_id}")

        # Comando !position (nuevo - muestra posición actual)
        if msg == "!position" or msg == "!pos":
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            user_position = next((pos for u, pos in users if u.id == user_id), None)
            if user_position:
                if isinstance(user_position, Position):
                    await send_response(f"📍 Tu posición:\nX: {user_position.x:.2f}\nY: {user_position.y:.2f}\nZ: {user_position.z:.2f}")
                elif isinstance(user_position, AnchorPosition):
                    if user_position.offset:
                        await send_response(f"📍 Tu posición:\nX: {user_position.offset.x:.2f}\nY: {user_position.offset.y:.2f}\nZ: {user_position.offset.z:.2f}")
                    else:
                        await send_response("❌ No se pudo obtener tu posición (sin offset)")
                else:
                    await send_response("❌ No se pudo obtener tu posición")
            else:
                await send_response("❌ No se pudo obtener tu posición")
            return

        # Comando !reactions (nuevo - lista de reacciones disponibles)
        if msg == "!reactions":
            reactions_list = "💫 REACCIONES DISPONIBLES:\n"
            reactions_list += "❤️ heart - Corazón\n"
            reactions_list += "👍 thumbs - Pulgar arriba\n"
            reactions_list += "👏 clap - Aplauso\n"
            reactions_list += "👋 wave - Saludo\n"
            reactions_list += "😂 laugh - Risa\n"
            reactions_list += "😮 wink - Guiño\n"
            reactions_list += "\n💡 Usa: !heart @user, !thumbs @user, etc."
            await send_response(reactions_list)
            return

        # Comando !game love
        if msg.startswith("!game love"):
            parts = msg.split()
            if len(parts) >= 3:
                user1, user2 = parts[2], parts[3] if len(parts) > 3 else "desconocido"
                love_percent = random.randint(1, 100)
                love_emoji = "💘" if love_percent > 80 else "💕" if love_percent > 60 else "💖" if love_percent > 40 else "💔"
                await self.highrise.chat(f"💘 Medidor de amor: {user1} + {user2} = {love_percent}% {love_emoji}")
            return

        # Comando !leaderboard
        if msg.startswith("!leaderboard"):
            parts = msg.split()
            if len(parts) == 1: await send_response("🏆 !leaderboard heart\n!leaderboard active")
            elif len(parts) > 1:
                lb_type = parts[1].lower()
                if lb_type == "heart":
                    top = sorted(USER_HEARTS.items(), key=lambda x: x[1], reverse=True)[:10]
                    response = await self.highrise.get_room_users()
                    if isinstance(response, Error):
                        await send_response("❌ Error obteniendo usuarios")
                        log_event("ERROR", f"get_room_users failed: {response.message}")
                        return
                    id_to_name = {u.id: u.username for u, _ in response.content}
                    lines = ["❤️ Top por corazones:"]
                    count = 0
                    for i, (uid, count_val) in enumerate(top, 1):
                        uname = id_to_name.get(uid) or USER_NAMES.get(uid) or f"User_{uid[:8]}"
                        lines.append(f"{i}. {uname}: {count_val}")
                        count += 1
                    if count == 0: lines.append("Sin datos")
                    await send_response("\n".join(lines))
                elif lb_type == "active":
                    top = sorted(USER_ACTIVITY.items(), key=lambda x: x[1]["messages"], reverse=True)[:10]
                    response = await self.highrise.get_room_users()
                    if isinstance(response, Error):
                        await send_response("❌ Error obteniendo usuarios")
                        log_event("ERROR", f"get_room_users failed: {response.message}")
                        return
                    id_to_name = {u.id: u.username for u, _ in response.content}
                    lines = ["💬 Top por actividad:"]
                    count = 0
                    for i, (uid, data) in enumerate(top, 1):
                        uname = id_to_name.get(uid) or USER_NAMES.get(uid) or f"User_{uid[:8]}"
                        lines.append(f"{i}. {uname}: {data['messages']}")
                        count += 1
                    if count == 0: lines.append("Sin datos")
                    await send_response("\n".join(lines))
            return

        # Comando !trackme
        if msg == "!trackme": await send_response("Activaste seguimiento de actividad!")

        # Comando !heartall (Owner)
        if msg == "!heartall":
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede enviar corazones a todos!"); return
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            heart_count = 0
            for u, _ in users:
                if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):
                    self.add_user_hearts(u.id, 1, u.username)
                    await self.highrise.react("heart", u.id)
                    heart_count += 1
                    await asyncio.sleep(0.1)
            await send_response(f"💖 Enviaste ❤️ a todos los {heart_count} jugadores en la sala!")

        # Comando !heart
        if msg.startswith("!heart"):
            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                hearts_count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                target_user_obj = next((u for u, _ in users if u.username == target_username), None)
                if not target_user_obj: await send_response( f"❌ ¡Usuario {target_username} no encontrado!"); return

                is_admin_or_owner = self.is_admin(user_id) or user_id == OWNER_ID
                is_vip = self.is_vip_by_username(user.username)

                if is_admin_or_owner:
                    if hearts_count > 100: await send_response("❌ ¡Máximo 100 corazones por comando!"); return
                    self.add_user_hearts(target_user_obj.id, hearts_count, target_username)
                    heart_message = f"💖 {username} envió {hearts_count} ❤️ a {target_username}"
                    await send_response(heart_message)
                    for _ in range(hearts_count):
                        await self.highrise.react("heart", target_user_obj.id)
                        await asyncio.sleep(0.05)
                elif is_vip:
                    # VIP puede enviar máximo 5 corazones
                    if hearts_count > 5:
                        await send_response("❌ ¡Los VIP pueden enviar máximo 5 corazones por comando!")
                        return
                    self.add_user_hearts(target_user_obj.id, hearts_count, target_username)
                    heart_message = f"💖 {username} envió {hearts_count} ❤️ a {target_username}"
                    await send_response(heart_message)
                    for _ in range(hearts_count):
                        await self.highrise.react("heart", target_user_obj.id)
                        await asyncio.sleep(0.05)
                else:
                    await send_response("🔒 ¡Solo VIP, administradores y propietario pueden enviar corazones!")
            else:
                await send_response( "❌ Usa: !heart @username [cantidad]")
            return

        # Comando !thumbs
        if msg.startswith("!thumbs"):
            parts = msg.split()
            if len(parts) >= 2:
                target = parts[1].replace("@", "")
                thumbs_count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                
                if target.lower() == "all":
                    count = 0
                    for u, _ in users:
                        if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):
                            await self.highrise.react("thumbs", u.id)
                            count += 1
                            await asyncio.sleep(0.1)
                    await send_response(f"👍 Enviaste pulgar arriba a todos los {count} usuarios!")
                else:
                    target_user = next((u for u, _ in users if u.username == target), None)
                    if not target_user: await send_response( f"❌ Usuario {target} no encontrado!"); return
                    for _ in range(min(thumbs_count, 30)):
                        await self.highrise.react("thumbs", target_user.id)
                        await asyncio.sleep(0.05)
                    await send_response( f"👍 Enviaste {thumbs_count} pulgar(es) arriba a @{target}")
            else:
                await send_response( "❌ Usa: !thumbs @username [cantidad] o !thumbs all")
            return

        # Comando !clap
        if msg.startswith("!clap"):
            parts = msg.split()
            if len(parts) >= 2:
                target = parts[1].replace("@", "")
                clap_count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                
                if target.lower() == "all":
                    count = 0
                    for u, _ in users:
                        if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):
                            await self.highrise.react("clap", u.id)
                            count += 1
                            await asyncio.sleep(0.1)
                    await send_response(f"👏 Enviaste aplauso a todos los {count} usuarios!")
                else:
                    target_user = next((u for u, _ in users if u.username == target), None)
                    if not target_user: await send_response( f"❌ Usuario {target} no encontrado!"); return
                    for _ in range(min(clap_count, 30)):
                        await self.highrise.react("clap", target_user.id)
                        await asyncio.sleep(0.05)
                    await send_response( f"👏 Enviaste {clap_count} aplauso(s) a @{target}")
            else:
                await send_response( "❌ Usa: !clap @username [cantidad] o !clap all")
            return

        # Comando !wave
        if msg.startswith("!wave"):
            parts = msg.split()
            if len(parts) >= 2:
                target = parts[1].replace("@", "")
                wave_count = int(parts[2]) if len(parts) > 2 and parts[2].isdigit() else 1
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                
                if target.lower() == "all":
                    count = 0
                    for u, _ in users:
                        if not any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):
                            await self.highrise.react("wave", u.id)
                            count += 1
                            await asyncio.sleep(0.1)
                    await send_response(f"👋 Enviaste ola a todos los {count} usuarios!")
                else:
                    target_user = next((u for u, _ in users if u.username == target), None)
                    if not target_user: await send_response( f"❌ Usuario {target} no encontrado!"); return
                    for _ in range(min(wave_count, 30)):
                        await self.highrise.react("wave", target_user.id)
                        await asyncio.sleep(0.05)
                    await send_response( f"👋 Enviaste {wave_count} ola(s) a @{target}")
            else:
                await send_response( "❌ Usa: !wave @username [cantidad] o !wave all")
            return

        # Comando !anchor (nuevo - teleporte sin restricciones para admin/owner)
        if msg.startswith("!anchor "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await send_response("❌ ¡Solo administradores y propietario pueden usar anchor!")
                return
            parts = msg.split()
            if len(parts) >= 4:
                try:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    pos = Position(x, y, z)
                    await self.highrise.teleport(user_id, pos)
                    await send_response(f"⚓ Anclado a posición ({x}, {y}, {z})")
                except ValueError:
                    await send_response("❌ Usa: !anchor [x] [y] [z]")
            else:
                await send_response("❌ Usa: !anchor [x] [y] [z]")
            return

        # Comando !flash
        if msg.startswith("!flash"):
            parts = msg.split()
            if len(parts) >= 4:
                try:
                    x, y, z = float(parts[1]), float(parts[2]), float(parts[3])
                    response = await self.highrise.get_room_users()
                    if isinstance(response, Error):
                        await send_response("❌ Error obteniendo usuarios")
                        log_event("ERROR", f"get_room_users failed: {response.message}")
                        return
                    users = response.content
                    current_position = next((pos for u, pos in users if u.id == user.id), None)
                    if current_position:
                        current_y = current_position.y if isinstance(current_position, Position) else (current_position.offset.y if current_position.offset else 0)
                        current_x = current_position.x if isinstance(current_position, Position) else (current_position.offset.x if current_position.offset else 0)
                        current_z = current_position.z if isinstance(current_position, Position) else (current_position.offset.z if current_position.offset else 0)
                        if abs(current_y - y) < 1.0: await send_response("❌ ¡Flash solo para subir/bajar pisos!"); return
                        if abs(current_x - x) > 3.0 or abs(current_z - z) > 3.0: await send_response("❌ ¡Flash solo para subir/bajar pisos!"); return
                        if not self.is_in_forbidden_zone(x, y, z, user.id):
                            pos = Position(x, y, z)
                            await self.highrise.teleport(user.id, pos)
                            await send_response( f"⚡ Flasheaste entre pisos ({x}, {y}, {z})")
                        else:
                            await send_response( f"❌ ¡No puedes teletransportarte a una zona prohibida!")
                    else:
                        await send_response( "❌ Error obteniendo tu posición actual")
                except ValueError:
                    await send_response( "❌ Usa: !flash [x] [y] [z] (ejemplo: !flash 5 17 3)")
            else:
                await send_response( "❌ Usa: !flash [x] [y] [z] (ejemplo: !flash 5 17 3)")
            return

        # Comando !inventory
        if msg.startswith("!inventory"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo propietario y administradores pueden usar este comando!"); return
            parts = msg.split()
            if len(parts) == 2 and parts[1].startswith("@"):
                target_username = parts[1].replace("@", "")
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                target_user = next((u for u, _ in users if u.username == target_username), None)
                if not target_user: await send_response( f"❌ Usuario {target_username} no encontrado!"); return
                inv_response = await self.highrise.get_user_outfit(target_user.id)
                if isinstance(inv_response, Error):
                    await send_response( f"❌ Error obteniendo outfit de {target_username}")
                    log_event("ERROR", f"get_user_outfit failed: {inv_response.message}")
                    return
                outfit = inv_response.outfit
                if outfit:
                    await send_response( f"👔 OUTFIT de {target_username}:")
                    for i, item in enumerate(outfit, 1): await send_response( f"{i}. {item.type}: {item.id}"); await asyncio.sleep(0.2)
                else: await send_response( f"👔 {target_username} no tiene outfit equipado")
            else:
                inventory_response = await self.highrise.get_inventory()
                if isinstance(inventory_response, Error):
                    await send_response( f"❌ Error obteniendo inventario")
                    log_event("ERROR", f"get_inventory failed: {inventory_response.message}")
                    return
                inventory = inventory_response.items
                if inventory:
                    total_items = len(inventory)
                    await send_response( f"👔 INVENTARIO: {total_items} items")
                    for i, item in enumerate(inventory, 1): await send_response( f"{i}. {item.type}: {item.id}"); await asyncio.sleep(0.2)
                else: await send_response("📦 Inventario vacío")
            return

        # Comando !give
        if msg.startswith("!give "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo propietario y administradores pueden dar items!"); return
            parts = msg.split()
            if len(parts) >= 3:
                target_username = parts[1].replace("@", "")
                item_id = " ".join(parts[2:])
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                target_user = next((u for u, _ in users if u.username == target_username), None)
                if not target_user: await send_response( f"❌ Usuario {target_username} no encontrado!"); return
                await send_response( f"⚠️ Comando !give deshabilitado (set_inventory no disponible)")
            else: await send_response("❌ Usa: !give @user [item_id]")
            return

        # Comando !wallet (Owner)
        if msg == "!wallet":
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede ver el balance del bot!"); return
            balance = await self.get_bot_wallet_balance()
            await self.highrise.chat(f"💰 Balance del bot: {balance} oro")
            return

        # Comando !restart (Owner)
        if msg.startswith("!restart"):
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede reiniciar el bot!"); return
            await send_response("🔄 Reiniciando bot..."); await send_response("⚠️ El bot se detendrá en 3 segundos!"); await send_response("💡 Usa restart_bot.bat para reinicio automático!")
            asyncio.create_task(self.delayed_restart())
            return

        # Comando !say (Admin/Owner)
        if msg.startswith("!say "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo propietario y administradores pueden usar este comando!"); return
            message_to_send = msg[5:].strip()
            if message_to_send:
                await self.highrise.chat(message_to_send)
                await send_response( f"✅ Mensaje enviado: {message_to_send}")
            else: await send_response("❌ Usa: !say [mensaje]")
            return

        # Comando !tome (Owner)
        if msg == "!tome":
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede usar este comando!"); return
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            bot_user, bot_pos, user_pos = None, None, None
            for u, pos in users:
                if hasattr(self, 'bot_id') and u.id == self.bot_id: bot_user, bot_pos = u, pos
                if u.id == user_id: user_pos = pos
            if bot_user and user_pos:
                if isinstance(user_pos, Position):
                    target_pos = Position(user_pos.x + 1.0, user_pos.y, user_pos.z)
                elif isinstance(user_pos, AnchorPosition) and user_pos.offset:
                    target_pos = Position(user_pos.offset.x + 1.0, user_pos.offset.y, user_pos.offset.z)
                else:
                    await send_response("❌ No se pudo obtener tu posición!")
                    return
                await self.highrise.teleport(bot_user.id, target_pos)
                await send_response( f"🤖 Bot teletransportado a @{user.username}")
            elif not bot_user: await send_response("❌ ¡Bot no encontrado en la sala!")
            else: await send_response("❌ No se pudo obtener tu posición!")
            return

        # Comando !outfit
        if msg.startswith("!outfit"):
            if not (self.is_admin(user_id) or self.is_moderator(user_id)): await send_response("¡No tienes acceso a este comando!"); return
            parts = msg.split()
            if len(parts) >= 2:
                try:
                    outfit_number = int(parts[1])
                    if outfit_number in SAVED_OUTFITS:
                        await self.highrise.set_outfit(SAVED_OUTFITS[outfit_number])
                        await send_response( f"👕 Outfit #{outfit_number} aplicado")
                    else: await send_response( f"❌ Outfit #{outfit_number} no existe.")
                except ValueError: await send_response("❌ Usa: !outfit [número]")
                except Exception as e: await send_response( f"❌ Error de cambio de ropa: {e}")
            else:
                if SAVED_OUTFITS:
                    outfits_list = ", ".join([f"#{num}" for num in sorted(SAVED_OUTFITS.keys())])
                    await send_response( f"👔 Outfits guardados: {outfits_list}\n❌ Usa: !outfit [número]")
                else: await send_response("📦 No hay outfits guardados.")
            return

        # Comando !automode (Admin/Owner)
        if msg == "!automode":
            if not (user_id == OWNER_ID or self.is_admin(user_id)): await send_response("❌ ¡Solo propietario y administradores pueden cambiar el modo del bot!"); return
            try:
                # Detener cualquier tarea activa
                if self.current_emote_task and not self.current_emote_task.done(): 
                    self.current_emote_task.cancel()
                    await asyncio.sleep(0.5)
                
                # Desactivar modo de emote copiado
                self.copied_emote_mode = False
                self.current_copied_emote = None
                
                # Iniciar ciclo automático
                self.current_emote_task = asyncio.create_task(self.start_auto_emote_cycle())
                await send_response("🎭 ¡Modo AUTOMÁTICO activado!\n📊 Ejecutando 224 emotes en ciclo")
                await self.highrise.chat("🎭 Modo AUTOMÁTICO activado por admin")
                log_event("BOT", f"Modo automático activado por {user.username}")
            except Exception as e:
                await send_response( f"❌ Error activando modo automático: {e}")
            return

        # Comando !mimic (Admin/Owner)
        if msg.startswith("!mimic "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo propietario y administradores pueden usar este comando!"); return
            target_username = msg[7:].strip().replace("@", "")
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            target_user = next((u for u, _ in users if u.username == target_username), None)
            if not target_user: await send_response( f"❌ Usuario {target_username} no encontrado"); return
            target_outfit_response = await self.highrise.get_user_outfit(target_user.id)
            if isinstance(target_outfit_response, Error):
                await send_response(f"❌ Error obteniendo outfit de {target_username}")
                log_event("ERROR", f"get_user_outfit failed: {target_outfit_response.message}")
                return
            await self.highrise.set_outfit(target_outfit_response.outfit)
            target_position = next((pos for u, pos in users if u.id == target_user.id), None)
            if target_position:
                if isinstance(target_position, Position):
                    mimic_position = Position(target_position.x + 0.5, target_position.y, target_position.z + 0.5)
                elif isinstance(target_position, AnchorPosition) and target_position.offset:
                    mimic_position = Position(target_position.offset.x + 0.5, target_position.offset.y, target_position.offset.z + 0.5)
                else:
                    await send_response("❌ No se pudo obtener la posición")
                    return
                await self.highrise.teleport(self.bot_id, mimic_position)
            await send_response( f"🎭 Bot imitando a @{target_username}"); await self.highrise.chat(f"🎭 ¡Soy @{target_username}!")
            return

        # Comando !copyoutfit (Admin/Owner)
        if msg == "!copyoutfit":
            if not (user_id == OWNER_ID or self.is_admin(user_id)): await send_response("❌ ¡Solo propietario y administradores pueden usar este comando!"); return
            user_outfit_response = await self.highrise.get_user_outfit(user.id)
            if isinstance(user_outfit_response, Error):
                await send_response("❌ Error obteniendo outfit")
                log_event("ERROR", f"get_user_outfit failed: {user_outfit_response.message}")
                return
            
            # Guardar outfit en el bot
            await self.highrise.set_outfit(user_outfit_response.outfit)
            
            # Guardar en SAVED_OUTFITS y persistir
            outfit_number = len(SAVED_OUTFITS) + 1
            SAVED_OUTFITS[outfit_number] = user_outfit_response.outfit
            
            # Guardar a archivo JSON
            try:
                import os
                os.makedirs("data", exist_ok=True)
                import json
                outfits_data = {}
                for num, outfit in SAVED_OUTFITS.items():
                    outfits_data[num] = [{"type": item.type, "id": item.id, "amount": item.amount} for item in outfit]
                
                with open("data/saved_outfits.json", "w", encoding="utf-8") as f:
                    json.dump(outfits_data, f, indent=2, ensure_ascii=False)
                
                safe_print(f"✅ Outfit #{outfit_number} guardado en archivo")
                log_event("OUTFIT", f"Outfit #{outfit_number} guardado por {username}")
            except Exception as e:
                safe_print(f"❌ Error guardando outfit a archivo: {e}")
                log_event("ERROR", f"Error guardando outfit: {e}")
            
            await send_response(f"👔 Outfit copiado y guardado como #{outfit_number}")
            return

        # Comando !setdirectivo (Owner)
        if msg == "!setdirectivo":
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede establecer la zona directiva!"); return
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            user_position = next((pos for u, pos in users if u.id == user_id), None)
            if user_position:
                if isinstance(user_position, Position):
                    new_directivo_zone = {"x": user_position.x, "y": user_position.y, "z": user_position.z}
                elif isinstance(user_position, AnchorPosition) and user_position.offset:
                    new_directivo_zone = {"x": user_position.offset.x, "y": user_position.offset.y, "z": user_position.offset.z}
                else:
                    await send_response("¡Error obteniendo posición del usuario!")
                    return
                # Cargar config actual
                config = load_config()
                config["directivo_zone"] = new_directivo_zone
                # Guardar a archivo
                with open("config.json", "w", encoding="utf-8") as f: 
                    json.dump(config, f, indent=2, ensure_ascii=False)
                # Actualizar variable global
                global DIRECTIVO_ZONE
                DIRECTIVO_ZONE = new_directivo_zone
                await send_response( f"👑 Zona directiva establecida en: X={new_directivo_zone['x']}, Y={new_directivo_zone['y']}, Z={new_directivo_zone['z']}")
                log_event("CONFIG", f"Zona directiva actualizada: {new_directivo_zone}")
            else: await send_response("¡Error obteniendo posición del usuario!")
            return

        # Comando !dj (Admin/Moderator)
        if msg == "!dj":
            if not (self.is_admin(user_id) or self.is_moderator(user_id)): await send_response("¡No tienes acceso a este comando!"); return
            await send_response("🎵 Acceso al panel DJ concedido!")
            return

        # Comando !music
        if msg.startswith("!music"):
            if not (self.is_admin(user_id) or self.is_moderator(user_id)): await send_response("¡No tienes acceso a este comando!"); return
            parts = msg.split()
            if len(parts) >= 2:
                action = parts[1].lower()
                if action == "play": await send_response(f"🎵 Reprodujiste música!")
                elif action == "stop": await send_response(f"🔇 Detuviste la música!")
                elif action == "pause": await send_response(f"⏸️ Pausaste la música!")
                else: await send_response("❌ Usa: !music [play/stop/pause]")
            else: await send_response("❌ Usa: !music [play/stop/pause]")
            return

        # Comando !tip
        if msg.startswith("!tip"):
            if not (self.is_admin(user_id) or self.is_moderator(user_id)): await send_response("¡No tienes acceso a este comando!"); return
            parts = msg.split()
            if len(parts) >= 3:
                tip_type = parts[1]
                try:
                    amount = int(parts[2])
                except ValueError: await send_response("❌ ¡Cantidad de oro inválida!"); return

                if tip_type == "all" and 1 <= amount <= 5:
                    try:
                        response = await self.highrise.get_room_users()
                        if isinstance(response, Error):
                            await send_response("❌ Error obteniendo usuarios")
                            log_event("ERROR", f"get_room_users failed: {response.message}")
                            return
                        users = response.content
                        bot_user = next((u for u, _ in users if u.username == "NOCTURNO_BOT" or u.username.upper() == "NOCTURNO_BOT" or u.username.lower() in ["highrisebot", "gluxbot", "bot"] or any(name in u.username.lower() for name in ["nocturno", "bot", "glux", "highrise"])), None)
                        available_users = [u for u, _ in users if bot_user and u.id != bot_user.id]
                        user_count = len(available_users)
                        total_cost = user_count * amount
                        real_balance = await self.get_bot_wallet_balance()
                        if total_cost > real_balance: await send_response( f"❌ ¡Oro insuficiente! Necesario: {total_cost}, disponible: {real_balance}"); return

                        valid_tips = ["gold_bar_1", "gold_bar_5", "gold_bar_10", "gold_bar_50", "gold_bar_100", "gold_bar_500", "gold_bar_1k", "gold_bar_5000", "gold_bar_10k"]
                        for u in available_users:
                            tip_bars = self.convert_to_gold_bars(amount)
                            if tip_bars and tip_bars in valid_tips:
                                await self.highrise.tip_user(u.id, tip_bars)
                        await self.highrise.chat(f"💰 ¡Bot dio {amount} oro a todos los {user_count} jugadores en la sala!")
                    except Exception as e: await send_response( f"❌ Error dando oro: {e}")

                elif tip_type == "only" and amount > 0:
                    try:
                        response = await self.highrise.get_room_users()
                        if isinstance(response, Error):
                            await send_response("❌ Error obteniendo usuarios")
                            log_event("ERROR", f"get_room_users failed: {response.message}")
                            return
                        users = response.content
                        bot_user = next((u for u, _ in users if u.username == "NOCTURNO_BOT" or u.username.upper() == "NOCTURNO_BOT" or u.username.lower() in ["highrisebot", "gluxbot", "bot"] or any(name in u.username.lower() for name in ["nocturno", "bot", "glux", "highrise"])), None)
                        available_users = [u for u, _ in users if bot_user and u.id != bot_user.id]
                        num_users = min(amount, len(available_users))
                        selected_users = random.sample(available_users, num_users)
                        total_cost = num_users * 5
                        real_balance = await self.get_bot_wallet_balance()
                        if total_cost > real_balance: await send_response( f"❌ ¡Oro insuficiente! Necesario: {total_cost}, disponible: {real_balance}"); return
                        valid_tips = ["gold_bar_1", "gold_bar_5", "gold_bar_10", "gold_bar_50", "gold_bar_100", "gold_bar_500", "gold_bar_1k", "gold_bar_5000", "gold_bar_10k"]
                        for u in selected_users:
                            tip_bars = self.convert_to_gold_bars(5)
                            if tip_bars and tip_bars in valid_tips:
                                await self.highrise.tip_user(u.id, tip_bars)
                        user_names = ", ".join([u.username for u in selected_users])
                        await self.highrise.chat(f"💰 Bot dio 5 oro a {num_users} usuarios aleatorios: {user_names}")
                    except Exception as e: await send_response( f"❌ Error al dar oro: {e}")
                else: await send_response("❌ ¡Formato de comando inválido! Usa: !tip all [1-5] o !tip only [X]")
            else: await send_response("❌ ¡Formato de comando inválido! Usa: !tip all [1-5] o !tip only [X]")
            return

        # Comandos de moderación
        if msg.startswith("!kick") or msg.startswith("!ban"):
            if not (self.is_admin(user_id) or self.is_moderator(user_id)): await send_response("¡No tienes acceso a este comando!"); return
            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                command = parts[0]
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                target_user = next((u for u, _ in users if u.username == target_username), None)
                if not target_user: await send_response( f"❌ Usuario {target_username} no encontrado en la sala!"); return
                if command == "!kick":
                    await self.highrise.moderate_room(target_user.id, "kick")
                    await send_response( f"👢 Expulsaste a {target_username} de la sala")
                elif command == "!ban":
                    await self.highrise.moderate_room(target_user.id, "ban", 86400)
                    await send_response( f"🚫 Baneaste a {target_username} por 1 día")
            return

        

        # Comando !givevip (Admin/Owner)
        if msg.startswith("!givevip"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden dar VIP!"); return
            target_user = msg[8:].strip().replace("@", "")
            if target_user not in VIP_USERS:
                VIP_USERS.add(target_user)
                self.save_data()
                await send_response( f"🎉 Otorgaste estatus VIP a {target_user}!")
                response = await self.highrise.get_room_users()
                if not isinstance(response, Error):
                    target_user_id = next((u.id for u, _ in response.content if u.username == target_user), None)
                    if target_user_id: await self.highrise.send_whisper(target_user_id, f"🎉 ¡Felicitaciones! Ahora eres VIP gracias a @{user.username}")
            else: await send_response( f"¡Usuario {target_user} ya tiene estatus VIP!")
            return

        # Comando !unvip (Admin/Owner)
        if msg.startswith("!unvip"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden quitar VIP!"); return
            target_user = msg[6:].strip().replace("@", "")
            if target_user in VIP_USERS:
                VIP_USERS.remove(target_user)
                self.save_data()
                await send_response( f"❌ Removiste estatus VIP de {target_user}!")
            else: await send_response( f"¡Usuario {target_user} no tiene estatus VIP!")
            return

        # Comando !freeze (Admin/Owner)
        if msg.startswith("!freeze"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden usar freeze!"); return
            target_username = msg[7:].strip().replace("@", "")
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            target_user = next((u for u, _ in users if u.username == target_username), None)
            if not target_user: await send_response( f"❌ Usuario {target_username} no encontrado en la sala!"); return
            await self.highrise.moderate_room(target_user.id, "mute", 300)
            await send_response( f"🧊 Congelaste a {target_username} por 5 minutos")
            return

        # Comando !mute
        if msg.startswith("!mute"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden usar mute!"); return
            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                duration = int(parts[2]) if len(parts) >= 3 and parts[2].isdigit() else 60
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                target_user = next((u for u, _ in users if u.username == target_username), None)
                if not target_user: await send_response( f"❌ Usuario {target_username} no encontrado!"); return
                await self.highrise.moderate_room(target_user.id, "mute", duration)
                await send_response( f"🔇 Silenciaste a {target_username} por {duration} segundos")
            else: await send_response("❌ Usa: !mute @username [segundos]")
            return

        # Comando !unmute
        if msg.startswith("!unmute"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden usar unmute!"); return
            target_username = msg[7:].strip().replace("@", "")
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            target_user = next((u for u, _ in users if u.username == target_username), None)
            if not target_user: await send_response( f"❌ Usuario {target_username} no encontrado!"); return
            await self.highrise.moderate_room(target_user.id, "mute", 0)
            await send_response( f"🔊 Quitaste el silencio a {target_username}")
            return

        # Comando !jail - Enviar usuario a la cárcel (Admin/Owner)
        if msg.startswith("!jail "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await send_response("❌ ¡Solo administradores y propietario pueden enviar a la cárcel!")
                return
            
            target_username = msg[6:].strip().replace("@", "")
            
            # Buscar al usuario
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            target_user = next((u for u, _ in users if u.username == target_username), None)
            
            if not target_user:
                await send_response(f"❌ Usuario {target_username} no encontrado en la sala!")
                return
            
            # Crear zona cárcel automáticamente si no existe (muy alto, Y=100.0)
            if "carcel" not in TELEPORT_POINTS:
                # Posición muy alta fuera de la sala normal
                TELEPORT_POINTS["carcel"] = {"x": 0.0, "y": 100.0, "z": 0.0}
                self.save_data()
                safe_print(f"🔒 Zona cárcel creada automáticamente en Y=100.0")
                log_event("JAIL", "Zona cárcel creada automáticamente en altura Y=100.0")
            
            # Agregar al usuario a la lista de cárcel
            JAIL_USERS.add(target_user.id)
            
            # Teletransportar a la cárcel (altura muy elevada)
            point = TELEPORT_POINTS["carcel"]
            try:
                carcel_position = Position(point["x"], point["y"], point["z"])
                await self.highrise.teleport(target_user.id, carcel_position)
                await send_response(f"⛓️ {target_username} fue enviado a la cárcel en altura Y={point['y']}!")
                await self.highrise.send_whisper(target_user.id, f"⛓️ Fuiste enviado a la cárcel por @{username}.\n⚠️ No puedes escapar hasta que un admin te libere.")
                await self.highrise.chat(f"🚨 @{target_username} fue enviado a la cárcel por @{username}")
                log_event("JAIL", f"{username} envió a {target_username} a la cárcel (Y={point['y']})")
            except Exception as e:
                await send_response(f"❌ Error enviando a la cárcel: {e}")
                JAIL_USERS.discard(target_user.id)
            return

        # Comando !unjail - Liberar usuario de la cárcel (Admin/Owner)
        if msg.startswith("!unjail "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await send_response("❌ ¡Solo administradores y propietario pueden liberar de la cárcel!")
                return
            
            target_username = msg[8:].strip().replace("@", "")
            
            # Buscar al usuario
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                return
            users = response.content
            target_user = next((u for u, _ in users if u.username == target_username), None)
            
            if not target_user:
                await send_response(f"❌ Usuario {target_username} no encontrado en la sala!")
                return
            
            if target_user.id in JAIL_USERS:
                JAIL_USERS.discard(target_user.id)
                
                # Teletransportar a un punto seguro (entrada de la sala)
                try:
                    # Usar spawn point si existe, sino posición por defecto
                    spawn = config.get("spawn_point", {"x": 0.0, "y": 0.0, "z": 0.0})
                    spawn_position = Position(spawn["x"], spawn["y"], spawn["z"])
                    await self.highrise.teleport(target_user.id, spawn_position)
                except Exception as e:
                    safe_print(f"⚠️ Error teletransportando a spawn: {e}")
                
                await send_response(f"✅ {target_username} fue liberado de la cárcel!")
                await self.highrise.send_whisper(target_user.id, f"✅ Fuiste liberado de la cárcel por @{username}!")
                await self.highrise.chat(f"🔓 @{target_username} fue liberado de la cárcel por @{username}")
                log_event("JAIL", f"{username} liberó a {target_username} de la cárcel")
            else:
                await send_response(f"ℹ️ {target_username} no está en la cárcel")
            return

        # Comando !unban
        if msg.startswith("!unban"):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden desbanear!"); return
            target_username = msg[6:].strip().replace("@", "")
            target_id = next((uid for uid, uname in USER_NAMES.items() if uname == target_username), None)
            if target_id and target_id in BANNED_USERS:
                del BANNED_USERS[target_id]
                await send_response( f"✅ Desbaneaste a {target_username}")
            else: await send_response( f"❌ {target_username} no está baneado")
            return

        # Comando !banlist
        if msg == "!banlist":
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden ver banlist!"); return
            if BANNED_USERS:
                ban_list = "🚫 USUARIOS BANEADOS:\n"
                for i, (uid, ban_data) in enumerate(BANNED_USERS.items(), 1):
                    username = USER_NAMES.get(uid, f"User_{uid[:8]}")
                    ban_time = ban_data.get("time", "indefinido")
                    ban_list += f"{i}. {username} (hasta {ban_time})\n"
                await send_response(ban_list)
            else:
                await send_response("✅ No hay usuarios baneados")
            return

        # Sistema de emotes mutuos (VIP) - formato: (emote) @user
        if msg.startswith("(") and ")" in msg and "@" in msg:
            # Verificar que sea VIP o superior
            is_vip = self.is_vip_by_username(username)
            is_admin_or_owner = self.is_admin(user_id) or user_id == OWNER_ID
            
            if not (is_vip or is_admin_or_owner):
                await send_response("🔒 Solo usuarios VIP pueden usar emotes mutuos!")
                return
            
            try:
                # Extraer emote y usuario
                emote_part = msg[msg.index("(")+1:msg.index(")")]
                target_username = msg[msg.index("@")+1:].strip().split()[0]
                
                # Buscar el emote
                emote = None
                emote_key = emote_part.strip().lower()
                
                if emote_key.isdigit() and emote_key in emotes:
                    emote = emotes[emote_key]
                else:
                    for e in emotes.values():
                        if e["name"].lower() == emote_key or e["id"].lower() == emote_key:
                            emote = e
                            break
                
                if not emote:
                    await send_response(f"❌ Emote '{emote_part}' no encontrado. Usa !emote list")
                    return
                
                if not emote["is_free"]:
                    await send_response(f"❌ El emote '{emote['name']}' no es gratuito")
                    return
                
                # Buscar usuario objetivo
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    return
                
                users = response.content
                target_user = next((u for u, _ in users if u.username == target_username), None)
                
                if not target_user:
                    await send_response(f"❌ Usuario {target_username} no encontrado")
                    return
                
                # Ejecutar emote en ambos usuarios
                await self.highrise.send_emote(emote["id"], user.id)
                await self.highrise.send_emote(emote["id"], target_user.id)
                
                await send_response(f"🎭 Emote mutuo '{emote['name']}' entre @{username} y @{target_username}")
                
            except Exception as e:
                await send_response(f"❌ Error: Usa el formato: (nombre_emote) @usuario")
                log_event("ERROR", f"Error en emote mutuo: {e}")
            return

        # Comando !mutelist
        if msg == "!mutelist":
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden ver mutelist!"); return
            if MUTED_USERS:
                mute_list = "🔇 USUARIOS SILENCIADOS:\n"
                for i, (uid, mute_time) in enumerate(MUTED_USERS.items(), 1):
                    username = USER_NAMES.get(uid, f"User_{uid[:8]}")
                    mute_list += f"{i}. {username} (hasta {mute_time})\n"
                await send_response( mute_list)
            else: await send_response("✅ No hay usuarios silenciados")
            return

        # Comando !privilege
        if msg.startswith("!privilege "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden ver privilegios!"); return
            target_username = msg[11:].strip().replace("@", "")
            target_user_id = next((uid for uid, uname in USER_NAMES.items() if uname == target_username), None)
            if not target_user_id: await send_response(f"❌ Usuario {target_username} no encontrado!"); return
            status = "👤 Usuario normal"
            if self.is_admin(target_user_id): status = "⚔️ Administrador"
            elif self.is_moderator(target_user_id): status = "👮 Moderador"
            await send_response( f"🔍 Privilegios de @{target_username}: {status}")
            return

        # Comando !tplist
        if msg == "!tplist":
            if TELEPORT_POINTS:
                tele_message = "📍 PUNTOS DE TELETRANSPORTE:\n"
                for name in TELEPORT_POINTS.keys():
                    tele_message += f"🔹 {name}\n"
                tele_message += "\n💡 Usa: !tp [nombre] o escribe el nombre directamente"
                await send_response(tele_message)
            else: await send_response("📍 No hay puntos de teletransporte creados")
            return
        if msg == "!tele list":
            if TELEPORT_POINTS:
                tele_message = "🗺️ UBICACIONES DE TELETRANSPORTE:\n"
                for i, (name, coords) in enumerate(TELEPORT_POINTS.items(), 1):
                    tele_message += f"{i}. {name} (X:{coords['x']:.1f}, Y:{coords['y']:.1f}, Z:{coords['z']:.1f})\n"
                tele_message += "\n💡 Usa: !tp [nombre]"
                await send_response( tele_message)
            else: await send_response("📍 No hay ubicaciones de teletransporte creadas")
            return

        # Comando !delpoint (Owner)
        if msg.startswith("!delpoint"):
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede eliminar puntos!"); return
            parts = msg.split()
            if len(parts) != 2: await send_response("❌ Usa: !delpoint [nombre]"); return
            point_name = parts[1]
            if point_name in TELEPORT_POINTS:
                del TELEPORT_POINTS[point_name]
                self.save_data()
                await send_response( f"✅ Punto '{point_name}' eliminado!")
            else: await send_response( f"❌ Punto '{point_name}' no encontrado!")
            return

        # Comando !checkvip
        if msg.startswith("!checkvip"):
            parts = msg.split()
            if len(parts) >= 2:
                target_user = parts[1].replace("@", "")
                if target_user in VIP_USERS: await send_response( f"✅ {target_user} tiene estatus VIP!")
                else: await send_response( f"❌ {target_user} no tiene estatus VIP!")
            else:
                is_vip_status = self.is_vip_by_username(user.username)
                await send_response( f"🔍 Tu verificación VIP: {'✅ VIP' if is_vip_status else '❌ No VIP'}")
                await send_response( f"📋 VIP actuales: {', '.join(list(VIP_USERS)[:3])}...")
            return

        # Comando !setvipzone (Owner)
        if msg.startswith("!setvipzone") or msg == "!sv":
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede establecer la zona VIP!"); return
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            user_position = next((pos for u, pos in users if u.id == user_id), None)
            if user_position:
                if isinstance(user_position, Position):
                    new_vip_zone = {"x": user_position.x, "y": user_position.y, "z": user_position.z}
                elif isinstance(user_position, AnchorPosition) and user_position.offset:
                    new_vip_zone = {"x": user_position.offset.x, "y": user_position.offset.y, "z": user_position.offset.z}
                else:
                    await send_response("¡Error obteniendo posición del usuario!")
                    return
                # Cargar config actual
                config = load_config()
                config["vip_zone"] = new_vip_zone
                # Guardar a archivo
                with open("config.json", "w", encoding="utf-8") as f: 
                    json.dump(config, f, indent=2, ensure_ascii=False)
                # Actualizar variable global
                global VIP_ZONE
                VIP_ZONE = new_vip_zone
                await send_response( f"🎯 Zona VIP establecida en: X={new_vip_zone['x']}, Y={new_vip_zone['y']}, Z={new_vip_zone['z']}")
                log_event("CONFIG", f"Zona VIP actualizada: {new_vip_zone}")
            else: await send_response("¡Error obteniendo posición del usuario!")
            return

        # Comando !setdj (Owner)
        if msg == "!setdj":
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede establecer la zona DJ!"); return
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            user_position = next((pos for u, pos in users if u.id == user_id), None)
            if user_position:
                if isinstance(user_position, Position):
                    new_dj_zone = {"x": user_position.x, "y": user_position.y, "z": user_position.z}
                elif isinstance(user_position, AnchorPosition) and user_position.offset:
                    new_dj_zone = {"x": user_position.offset.x, "y": user_position.offset.y, "z": user_position.offset.z}
                else:
                    await send_response("¡Error obteniendo posición del usuario!")
                    return
                # Cargar config actual
                config = load_config()
                config["dj_zone"] = new_dj_zone
                # Guardar a archivo
                with open("config.json", "w", encoding="utf-8") as f: 
                    json.dump(config, f, indent=2, ensure_ascii=False)
                # Actualizar variable global
                global DJ_ZONE
                DJ_ZONE = new_dj_zone
                await send_response( f"🎵 Zona DJ establecida en: X={new_dj_zone['x']}, Y={new_dj_zone['y']}, Z={new_dj_zone['z']}")
                log_event("CONFIG", f"Zona DJ actualizada: {new_dj_zone}")
            else: await send_response("¡Error obteniendo posición del usuario!")
            return

        # Comando !setspawn (Owner)
        if msg == "!setspawn":
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede establecer el punto de inicio del bot!"); return
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            user_position = next((pos for u, pos in users if u.id == user_id), None)
            if user_position:
                if isinstance(user_position, Position):
                    spawn_point = {"x": user_position.x, "y": user_position.y, "z": user_position.z}
                elif isinstance(user_position, AnchorPosition) and user_position.offset:
                    spawn_point = {"x": user_position.offset.x, "y": user_position.offset.y, "z": user_position.offset.z}
                else:
                    await send_response("¡Error obteniendo posición del usuario!")
                    return
                config = load_config()
                config["spawn_point"] = spawn_point
                with open("config.json", "w", encoding="utf-8") as f: json.dump(config, f, indent=2, ensure_ascii=False)
                await send_response( f"📍 Punto de inicio del bot establecido en: X={spawn_point['x']}, Y={spawn_point['y']}, Z={spawn_point['z']}")
            else: await send_response("¡Error obteniendo posición del usuario!")
            return

        # Comando !bot (Admin/Owner)
        if msg.startswith("!bot "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden usar este comando!"); return
            target_username = msg[5:].strip().replace("@", "")
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            bot_user, bot_pos, target_user, target_pos = None, None, None, None
            for u, pos in users:
                if hasattr(self, 'bot_id') and u.id == self.bot_id: bot_user, bot_pos = u, pos
                if u.username == target_username: target_user, target_pos = u, pos
            if not bot_user: await send_response("❌ Bot no encontrado!"); return
            if not target_user: await send_response(f"❌ ¡Usuario {target_username} no encontrado!"); return
            if not bot_pos or not target_pos: await send_response("❌ Error: No se pudieron obtener las posiciones"); return
            if isinstance(bot_pos, Position):
                original_x, original_y, original_z = bot_pos.x, bot_pos.y, bot_pos.z
            elif isinstance(bot_pos, AnchorPosition) and bot_pos.offset:
                original_x, original_y, original_z = bot_pos.offset.x, bot_pos.offset.y, bot_pos.offset.z
            else:
                await send_response("❌ Error obteniendo posición del bot")
                return
            if isinstance(target_pos, Position):
                new_position = Position(target_pos.x + 1.0, target_pos.y, target_pos.z)
            elif isinstance(target_pos, AnchorPosition) and target_pos.offset:
                new_position = Position(target_pos.offset.x + 1.0, target_pos.offset.y, target_pos.offset.z)
            else:
                await send_response("❌ Error obteniendo posición del objetivo")
                return
            await self.highrise.teleport(bot_user.id, new_position)
            await send_response(f"🤖 Bot teletransportado a @{target_username}!")
            try:
                await self.highrise.send_emote("emoji-punch", bot_user.id)
                await asyncio.sleep(0.5)
                await self.highrise.send_emote("emote-death", target_user.id)
                await send_response(f"🥊 Bot golpeó a @{target_username}!")
            except Exception as emote_error: log_event("WARNING", f"No se pudo hacer emote: {emote_error}")
            await asyncio.sleep(3)
            original_position = Position(original_x, original_y, original_z)
            await self.highrise.teleport(bot_user.id, original_position)
            await send_response("✅ Bot retornó a su posición original")
            return

        # Comando !bring (Admin/Owner)
        if msg.startswith("!bring "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden mover jugadores!"); return
            target_username = msg[7:].strip().replace("@", "")
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            command_user_position = next((pos for u, pos in users if u.id == user_id), None)
            target_user_obj = next((u for u, _ in users if u.username == target_username), None)
            if not command_user_position: await send_response("❌ ¡Error obteniendo tu posición!"); return
            if not target_user_obj: await send_response( f"❌ ¡Jugador {target_username} no encontrado en la sala!"); return
            if isinstance(command_user_position, Position):
                new_position = Position(command_user_position.x + 1, command_user_position.y, command_user_position.z)
            elif isinstance(command_user_position, AnchorPosition) and command_user_position.offset:
                new_position = Position(command_user_position.offset.x + 1, command_user_position.offset.y, command_user_position.offset.z)
            else:
                await send_response("❌ ¡Error obteniendo tu posición!")
                return
            await self.highrise.teleport(target_user_obj.id, new_position)
            await send_response( f"🎯 @{user.username} movió a {target_username} hacia sí mismo!")
            return

        # Comando !stats
        if msg == "!stats":
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            total_users = len(users)
            admin_count = sum(1 for u, _ in users if self.is_admin(u.id))
            mod_count = sum(1 for u, _ in users if self.is_moderator(u.id) and not self.is_admin(u.id))
            vip_count = sum(1 for u, _ in users if self.is_vip_by_username(u.username))
            total_messages = sum(data.get("messages", 0) for data in USER_ACTIVITY.values())
            total_hearts = sum(USER_HEARTS.values())
            stats_msg = f"📊 ESTADÍSTICAS DE LA SALA:\n👥 Usuarios: {total_users}\n🛡️ Admins: {admin_count}\n⚖️ Mods: {mod_count}\n⭐ VIPs: {vip_count}\n💬 Mensajes: {total_messages}\n💖 Corazones: {total_hearts}"
            await self.highrise.chat(stats_msg)
            return

        # Comando !online
        if msg == "!online":
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                log_event("ERROR", f"get_room_users failed: {response.message}")
                return
            users = response.content
            admins, mods, vips, regular = [], [], [], []
            for u, _ in users:
                if self.is_admin(u.id): admins.append(u.username)
                elif self.is_moderator(u.id): mods.append(u.username)
                elif self.is_vip_by_username(u.username): vips.append(u.username)
                else: regular.append(u.username)
            online_msg = f"👥 USUARIOS ONLINE ({len(users)}):\n"
            if admins: online_msg += f"🛡️ Admins: {', '.join(admins)}\n"
            if mods: online_msg += f"⚖️ Mods: {', '.join(mods)}\n"
            if vips:
                online_msg += f"⭐ VIPs: {', '.join(vips[:5])}"
                if len(vips) > 5: online_msg += f" (+{len(vips)-5} más)"
                online_msg += "\n"
            online_msg += f"👤 Usuarios: {len(regular)}"
            await self.highrise.chat(online_msg)
            return

        # Comando !achievements
        if msg == "!achievements":
            user_hearts = self.get_user_hearts(user_id)
            user_messages = USER_ACTIVITY.get(user_id, {}).get("messages", 0)
            user_time = self.get_user_total_time(user_id)
            achievements = []
            if user_hearts >= 1000: achievements.append("💎 Maestro del Amor")
            elif user_hearts >= 500: achievements.append("💖 Coleccionista de Corazones")
            elif user_hearts >= 100: achievements.append("❤️ Amante")
            if user_messages >= 1000: achievements.append("📢 Locutor Profesional")
            elif user_messages >= 500: achievements.append("💬 Conversador Activo")
            elif user_messages >= 100: achievements.append("✍️ Participante")
            if user_time >= 36000: achievements.append("⏰ Veterano de la Sala")
            elif user_time >= 18000: achievements.append("🕐 Residente Frecuente")
            if self.is_vip_by_username(user.username): achievements.append("⭐ Miembro VIP")
            if self.is_admin(user_id): achievements.append("🛡️ Administrador")
            ach_msg = f"🏆 LOGROS DE @{user.username}:\n" + "\n".join(f"• {ach}" for ach in achievements) if achievements else f"🎯 @{user.username} aún no ha desbloqueado logros\n💡 Sé activo para conseguirlos!"
            await send_response(ach_msg)
            return

        # Comando !rank
        if msg == "!rank":
            user_hearts = self.get_user_hearts(user_id)
            user_messages = USER_ACTIVITY.get(user_id, {}).get("messages", 0)
            total_score = user_hearts + (user_messages * 2)
            if total_score >= 5000: rank = "💎 Diamante"
            elif total_score >= 2000: rank = "🥇 Oro"
            elif total_score >= 1000: rank = "🥈 Plata"
            elif total_score >= 500: rank = "🥉 Bronce"
            else: rank = "🌱 Novato"
            rank_msg = f"🎖️ RANGO DE @{user.username}:\n{rank}\nPuntuación: {total_score}\n💖 Corazones: {user_hearts}\n💬 Mensajes: {user_messages}"
            await send_response(rank_msg)
            return

        # Comando !daily
        if msg == "!daily":
            current_time = datetime.now()
            last_daily_key = f"{user_id}_last_daily"
            if last_daily_key in USER_INFO.get(user_id, {}):
                last_claim_str = USER_INFO[user_id][last_daily_key]
                last_claim = datetime.fromisoformat(last_claim_str.replace('Z', '+00:00'))
                if (current_time - last_claim).days < 1:
                    hours_left = 24 - (current_time - last_claim).seconds // 3600
                    await send_response(f"⏰ Ya reclamaste tu recompensa diaria\n🕐 Vuelve en {hours_left}h")
                    return
            daily_hearts = 10
            self.add_user_hearts(user_id, daily_hearts, user.username)
            if user_id not in USER_INFO: USER_INFO[user_id] = {}
            USER_INFO[user_id][last_daily_key] = current_time.isoformat()
            save_user_info()
            await send_response(f"🎁 ¡Recompensa diaria reclamada!\n💖 +{daily_hearts} corazones")
            return

        # Comando !TPus (Owner)
        if msg.startswith("!TPus"):
            if user_id != OWNER_ID: await send_response("❌ ¡Solo el propietario puede crear puntos de teletransporte!"); return
            parts = msg.split()
            if len(parts) >= 2:
                point_name = parts[1]
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    log_event("ERROR", f"get_room_users failed: {response.message}")
                    return
                users = response.content
                user_position = next((pos for u, pos in users if u.id == user_id), None)
                if user_position:
                    if isinstance(user_position, Position):
                        TELEPORT_POINTS[point_name] = {"x": user_position.x, "y": user_position.y, "z": user_position.z}
                        self.save_data()
                        await send_response( f"📍 Punto de teletransporte '{point_name}' creado en posición: X={user_position.x}, Y={user_position.y}, Z={user_position.z}")
                    elif isinstance(user_position, AnchorPosition) and user_position.offset:
                        TELEPORT_POINTS[point_name] = {"x": user_position.offset.x, "y": user_position.offset.y, "z": user_position.offset.z}
                        save_leaderboard_data()
                        self.save_data()
                        await send_response( f"📍 Punto de teletransporte '{point_name}' creado en posición: X={user_position.offset.x}, Y={user_position.offset.y}, Z={user_position.offset.z}")
                    else:
                        await send_response("¡Error obteniendo posición del usuario!")
                else: await send_response("¡Error obteniendo posición del usuario!")
            else: await send_response("❌ Usa: !TPus [nombre]")
            return

        # Comandos de interacción (Solo VIP+)
        if msg.startswith("!punch") or msg.startswith("!slap") or msg.startswith("!flirt") or msg.startswith("!scare") or msg.startswith("!electro") or msg.startswith("!hug") or msg.startswith("!ninja") or msg.startswith("!laugh") or msg.startswith("!boom"):
            # Verificar permisos: Solo VIP, Admin y Owner pueden usar interacciones
            is_vip = self.is_vip_by_username(username)
            is_admin_or_owner = self.is_admin(user_id) or user_id == OWNER_ID
            
            if not (is_vip or is_admin_or_owner):
                await send_response("🔒 Solo usuarios VIP, Admins y el Propietario pueden usar comandos de interacción!")
                return
            
            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                command = parts[0]
                users = (await self.highrise.get_room_users()).content
                sender_pos, target_user, target_pos = None, None, None
                for u, pos in users:
                    if u.id == user.id: sender_pos = pos
                    if u.username == target_username: target_user, target_pos = u, pos
                if not target_user: await send_response( f"❌ ¡Usuario {target_username} no encontrado!"); return
                if not sender_pos or not target_pos: await send_response( f"❌ No se pudo obtener la posición de los usuarios!"); return
                distance = self.calculate_distance(sender_pos, target_pos)

                if command not in ["!punch", "!slap"] and distance > 3.0: await send_response( f"❌ ¡{target_username} está muy lejos!"); return

                sender_emote_id, receiver_emote_id, action_message = "", "", ""
                if command == "!punch": sender_emote_id, receiver_emote_id, action_message = "emoji-punch", "emote-death", f"🥊 @{user.username} golpeó a @{target_username} y lo dejó noqueado!"
                elif command == "!slap": sender_emote_id, receiver_emote_id, action_message = "emote-slap", "emoji-dizzy", f"👋 @{user.username} dio una bofetada a @{target_username} y lo dejó en shock!"
                elif command == "!flirt": sender_emote_id, receiver_emote_id, action_message = "emote-kissing", "emote-hearteyes", f"💕 @{user.username} coquetea con @{target_username} y se derrite de amor!"
                elif command == "!scare": sender_emote_id, receiver_emote_id, action_message = "emote-panic", "emoji-scared", f"😱 @{user.username} asustó a @{target_username} y huyó en pánico!"
                elif command == "!electro": sender_emote_id, receiver_emote_id, action_message = "emote-fail1", "emote-fail2", f"⚡ @{user.username} electrocutó a @{target_username} y se quemó!"
                elif command == "!hug": sender_emote_id, receiver_emote_id, action_message = "emote-hug", "emote-hugyourself", f"🤗 @{user.username} abrazó a @{target_username} y lloró de emoción!"
                elif command == "!ninja": sender_emote_id, receiver_emote_id, action_message = "emote-ninjarun", "emote-fail1", f"🥷 @{user.username} atacó como ninja a @{target_username} y se retuerce de dolor!"
                elif command == "!laugh": sender_emote_id, receiver_emote_id, action_message = "emote-laughing", "emote-laughing2", f"😂 @{user.username} hizo reír a @{target_username} sin parar!"
                elif command == "!boom": sender_emote_id, receiver_emote_id, action_message = "emote-disappear", "emote-fail1", f"💥 @{user.username} explotó a @{target_username} y literalmente explotó!"

                if sender_emote_id and receiver_emote_id:
                    await self.highrise.send_emote(sender_emote_id, user.id)
                    await self.highrise.send_emote(receiver_emote_id, target_user.id)
                    await send_response(action_message)
            else: await send_response("❌ Usa: !comando @usuario")
            return

        # Comando !sendall [zona] - Enviar a todos los usuarios a una zona (Admin/Owner)
        if msg.startswith("!sendall "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await send_response("❌ ¡Solo admins y propietario pueden usar !sendall!")
                return
            
            parts = msg.split()
            if len(parts) < 2:
                await send_response("❌ Usa: !sendall [zona]\n💡 Usa !tplist para ver zonas disponibles")
                return
            
            zone_name = parts[1].lower()
            
            if zone_name not in TELEPORT_POINTS:
                await send_response(f"❌ Zona '{zone_name}' no encontrada. Usa !tplist")
                return
            
            point = TELEPORT_POINTS[zone_name]
            
            try:
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    return
                
                users = response.content
                moved_count = 0
                
                for u, _ in users:
                    # Saltar admin, owner y bots
                    if u.id == OWNER_ID or self.is_admin(u.id):
                        continue
                    if any(name in u.username.lower() for name in ["bot", "glux", "highrise"]):
                        continue
                    
                    try:
                        teleport_position = Position(point["x"], point["y"], point["z"])
                        await self.highrise.teleport(u.id, teleport_position)
                        moved_count += 1
                        await asyncio.sleep(0.2)  # Delay para evitar rate limit
                    except Exception as e:
                        safe_print(f"⚠️ Error moviendo a {u.username}: {e}")
                        continue
                
                await self.highrise.chat(f"🚁 {moved_count} usuarios fueron enviados a '{zone_name}' por @{username}")
                await send_response(f"✅ {moved_count} usuarios enviados a '{zone_name}'")
                log_event("TELEPORT", f"{username} envió {moved_count} usuarios a '{zone_name}'")
            except Exception as e:
                await send_response(f"❌ Error: {e}")
                log_event("ERROR", f"Error en !sendall: {e}")
            return

        # Comando !goto @user [punto] - Teletransportar usuario a punto guardado (Admin/Owner)
        if msg.startswith("!goto "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await send_response("❌ ¡Solo admins y propietario pueden usar !goto!")
                return
            
            parts = msg.split()
            if len(parts) < 3:
                await send_response("❌ Usa: !goto @usuario [punto]")
                return
            
            target_username = parts[1].replace("@", "")
            point_name = parts[2].lower()
            
            if point_name not in TELEPORT_POINTS:
                await send_response(f"❌ Punto '{point_name}' no encontrado. Usa !tplist")
                return
            
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                await send_response("❌ Error obteniendo usuarios")
                return
            
            users = response.content
            target_user = next((u for u, _ in users if u.username == target_username), None)
            
            if not target_user:
                await send_response(f"❌ Usuario {target_username} no encontrado!")
                return
            
            point = TELEPORT_POINTS[point_name]
            try:
                teleport_position = Position(point["x"], point["y"], point["z"])
                await self.highrise.teleport(target_user.id, teleport_position)
                await send_response(f"🚁 Teletransportaste a @{target_username} a '{point_name}'!")
                await self.highrise.send_whisper(target_user.id, f"📍 Fuiste teletransportado a '{point_name}' por @{username}")
                log_event("TELEPORT", f"{username} envió a {target_username} a '{point_name}' - X:{point['x']}, Y:{point['y']}, Z:{point['z']}")
            except Exception as e:
                await send_response(f"❌ Error: {e}")
                log_event("ERROR", f"Error en !goto: {e}")
            return

        # Comando !estadoemotes - Muestra estadísticas de salud de emotes (Admin/Owner)
        if msg == "!estadoemotes":
            if not (self.is_admin(user_id) or user_id == OWNER_ID):
                await send_response("❌ ¡Solo admins y propietario pueden ver las estadísticas de emotes!")
                return
            
            stats_summary = emote_health_manager.get_stats_summary()
            disabled_count = emote_health_manager.get_disabled_count()
            
            message = f"📊 ESTADÍSTICAS DE SALUD DE EMOTES\n"
            message += f"{stats_summary}\n\n"
            
            if disabled_count > 0:
                message += "🚫 Emotes deshabilitados:\n"
                for emote_id in emote_health_manager.disabled_emotes:
                    if emote_id in emote_health_manager.emote_stats:
                        stats = emote_health_manager.emote_stats[emote_id]
                        name = stats.get("name", "desconocido")
                        failures = stats.get("failures", 0)
                        last_error = stats.get("last_exception", "N/A")[:50]
                        message += f"• {name} ({emote_id[:15]}...): {failures} fallos\n"
                        message += f"  Último error: {last_error}\n"
            else:
                message += "✅ No hay emotes deshabilitados\n\n"
                message += "💡 El sistema está monitoreando activamente todos los emotes.\n"
                message += "Si algún emote falla, será deshabilitado automáticamente."
            
            # Siempre enviar por whisper para comandos de estadísticas
            await self.highrise.send_whisper(user_id, message)
            log_event("ADMIN", f"{username} consultó estadísticas de emotes")
            return

        # Comando !reiniciaremote [emote_id] - Reinicia estado de emote(s) (Owner)
        if msg.startswith("!reiniciaremote"):
            if user_id != OWNER_ID:
                await send_response("❌ ¡Solo el propietario puede reiniciar el estado de emotes!")
                return
            
            parts = msg.split()
            if len(parts) > 1:
                emote_id = parts[1]
                if emote_id in emote_health_manager.emote_stats:
                    del emote_health_manager.emote_stats[emote_id]
                    if emote_id in emote_health_manager.disabled_emotes:
                        emote_health_manager.disabled_emotes.remove(emote_id)
                    emote_health_manager.save_health_data()
                    await self.highrise.send_whisper(user_id, f"♻️ Estado del emote {emote_id} reiniciado")
                    log_event("ADMIN", f"{username} reinició estado del emote {emote_id}")
                else:
                    await self.highrise.send_whisper(user_id, f"❌ Emote {emote_id} no encontrado en estadísticas")
            else:
                emote_health_manager.emote_stats = {}
                emote_health_manager.disabled_emotes = set()
                emote_health_manager.save_health_data()
                await self.highrise.send_whisper(user_id, "♻️ Todas las estadísticas de emotes han sido reiniciadas")
                log_event("ADMIN", f"{username} reinició todas las estadísticas de emotes")
            return

        # Comando !tp [punto]
        if msg.startswith("!tp "):
            point_name = msg[4:].strip().lower()
            if point_name in TELEPORT_POINTS:
                # Verificar permisos para zonas restringidas
                if point_name in ["vip", "pv"]:
                    has_permission = (
                        user_id == OWNER_ID or 
                        self.is_admin(user_id) or 
                        username in VIP_USERS
                    )
                    if not has_permission:
                        await send_response(f"🔒 '{point_name}' es zona VIP. ¡Solo VIP, admins y el propietario pueden acceder!")
                        return
                
                elif point_name in ["directivo", "dj", "carcel"]:
                    has_permission = (
                        user_id == OWNER_ID or 
                        self.is_admin(user_id)
                    )
                    if not has_permission:
                        await send_response(f"🔒 '{point_name}' es zona exclusiva. ¡Solo admins y el propietario pueden acceder!")
                        return
                
                point = TELEPORT_POINTS[point_name]
                try:
                    teleport_position = Position(point["x"], point["y"], point["z"])
                    await self.highrise.teleport(user_id, teleport_position)
                    await send_response(f"🚀 Te teletransportaste a '{point_name}'!")
                    log_event("TELEPORT", f"{username} fue a zona '{point_name}' - X:{point['x']}, Y:{point['y']}, Z:{point['z']}")
                except Exception as e: 
                    await send_response(f"❌ Error de teletransporte: {e}")
                    log_event("ERROR", f"Error teletransporte {username} a '{point_name}': {e}")
            else:
                await send_response(f"❌ Punto '{point_name}' no encontrado. Usa !tplist para ver los disponibles")
            return

        # Comando vip (teletransporte a zona VIP usando VIP_ZONE del config)
        if msg == "vip" or msg == "!vip":
            has_permission = (
                user_id == OWNER_ID or 
                self.is_admin(user_id) or 
                username in VIP_USERS
            )
            if not has_permission:
                await send_response("🔒 Zona VIP solo para VIP, admins y propietario!")
                return
            
            if VIP_ZONE and VIP_ZONE.get("x") is not None:
                try:
                    vip_position = Position(VIP_ZONE["x"], VIP_ZONE["y"], VIP_ZONE["z"])
                    await self.highrise.teleport(user_id, vip_position)
                    await send_response(f"⭐ Te teletransportaste a la zona VIP!")
                    log_event("TELEPORT", f"{username} accedió a zona VIP - X:{VIP_ZONE['x']}, Y:{VIP_ZONE['y']}, Z:{VIP_ZONE['z']}")
                except Exception as e:
                    await send_response(f"❌ Error de teletransporte: {e}")
                    log_event("ERROR", f"Error teletransporte {username} a zona VIP: {e}")
            else:
                await send_response("❌ Zona VIP no configurada. Usa !setvipzone para establecerla")
            return

        # Comando dj (teletransporte a zona DJ)
        if msg == "dj" or msg == "!dj":
            has_permission = (user_id == OWNER_ID or self.is_admin(user_id))
            if not has_permission:
                await send_response("🔒 Zona DJ solo para admins y propietario!")
                return
            
            if DJ_ZONE and DJ_ZONE.get("x") is not None:
                try:
                    dj_position = Position(DJ_ZONE["x"], DJ_ZONE["y"], DJ_ZONE["z"])
                    await self.highrise.teleport(user_id, dj_position)
                    await send_response(f"🎵 Te teletransportaste a la zona DJ!")
                    log_event("TELEPORT", f"{username} accedió a zona DJ - X:{DJ_ZONE['x']}, Y:{DJ_ZONE['y']}, Z:{DJ_ZONE['z']}")
                except Exception as e:
                    await send_response(f"❌ Error de teletransporte: {e}")
            else:
                await send_response("❌ Zona DJ no configurada. Usa !setdj para establecerla")
            return

        # Comando directivo (teletransporte a zona directivo)
        if msg == "directivo" or msg == "!directivo":
            has_permission = (user_id == OWNER_ID or self.is_admin(user_id))
            if not has_permission:
                await send_response("🔒 Zona directivo solo para admins y propietario!")
                return
            
            if DIRECTIVO_ZONE and DIRECTIVO_ZONE.get("x") is not None:
                try:
                    directivo_position = Position(DIRECTIVO_ZONE["x"], DIRECTIVO_ZONE["y"], DIRECTIVO_ZONE["z"])
                    await self.highrise.teleport(user_id, directivo_position)
                    await send_response(f"👑 Te teletransportaste a la zona directivo!")
                    log_event("TELEPORT", f"{username} accedió a zona directivo - X:{DIRECTIVO_ZONE['x']}, Y:{DIRECTIVO_ZONE['y']}, Z:{DIRECTIVO_ZONE['z']}")
                except Exception as e:
                    await send_response(f"❌ Error de teletransporte: {e}")
            else:
                await send_response("❌ Zona directivo no configurada. Usa !setdirectivo para establecerla")
            return

        # Comando carcel (teletransporte a carcel - solo admin/owner pueden ir voluntariamente)
        if msg == "carcel" or msg == "!carcel":
            has_permission = (user_id == OWNER_ID or self.is_admin(user_id))
            if not has_permission:
                await send_response("🔒 ¡La cárcel es solo para prisioneros!\n⚠️ Solo admin/owner pueden visitarla voluntariamente")
                return
            
            # Crear cárcel automáticamente si no existe
            if "carcel" not in TELEPORT_POINTS:
                TELEPORT_POINTS["carcel"] = {"x": 0.0, "y": 100.0, "z": 0.0}
                self.save_data()
                safe_print(f"🔒 Zona cárcel creada automáticamente en Y=100.0")
            
            point = TELEPORT_POINTS["carcel"]
            try:
                carcel_position = Position(point["x"], point["y"], point["z"])
                await self.highrise.teleport(user_id, carcel_position)
                await send_response(f"⛓️ Visitaste la cárcel en altura Y={point['y']}")
                log_event("TELEPORT", f"{username} visitó la cárcel - X:{point['x']}, Y:{point['y']}, Z:{point['z']}")
            except Exception as e:
                await send_response(f"❌ Error de teletransporte: {e}")
            return

        # Teletransporte a puntos (escribiendo el nombre directamente)
        if msg.lower() in TELEPORT_POINTS:
            point_name = msg.lower()
            
            # Verificar permisos para zonas restringidas
            if point_name in ["vip", "pv"]:
                has_permission = (
                    user_id == OWNER_ID or 
                    self.is_admin(user_id) or 
                    username in VIP_USERS
                )
                if not has_permission:
                    await send_response(f"🔒 '{point_name}' es zona VIP. ¡Solo VIP, admins y el propietario pueden acceder!")
                    log_event("TELEPORT", f"{username} intentó acceder a '{point_name}' sin permisos")
                    return
            
            elif point_name in ["directivo", "dj"]:
                has_permission = (
                    user_id == OWNER_ID or 
                    self.is_admin(user_id)
                )
                if not has_permission:
                    await send_response(f"🔒 '{point_name}' es zona exclusiva. ¡Solo admins y el propietario pueden acceder!")
                    log_event("TELEPORT", f"{username} intentó acceder a '{point_name}' sin permisos")
                    return
            
            elif point_name == "carcel":
                # La cárcel solo puede ser accedida por admin/owner
                is_admin_or_owner = (user_id == OWNER_ID or self.is_admin(user_id))
                
                if not is_admin_or_owner:
                    await send_response(f"🔒 ¡Solo admins y propietario pueden ir a la cárcel!")
                    log_event("TELEPORT", f"{username} intentó acceder a cárcel sin autorización")
                    return
            
            point = TELEPORT_POINTS[point_name]
            try:
                teleport_position = Position(point["x"], point["y"], point["z"])
                await self.highrise.teleport(user_id, teleport_position)
                await send_response(f"🚀 @{username} se teletransportó al punto '{point_name}'!")
                log_event("TELEPORT", f"{username} accedió a '{point_name}' - X:{point['x']}, Y:{point['y']}, Z:{point['z']}")
            except Exception as e: 
                await send_response(f"❌ Error de teletransporte: {e}")
                log_event("ERROR", f"Error teletransporte {username} a '{point_name}': {e}")
            return

        # Comando !tele @user (VIP)
        if msg.startswith("!tele @"):
            if not self.is_vip_by_username(user.username): await send_response("❌ ¡Solo VIP pueden usar este comando!"); return
            target_username = msg[7:].strip()
            try:
                response = await self.highrise.get_room_users()
                if isinstance(response, Error):
                    await send_response("❌ Error obteniendo usuarios")
                    return
                users = response.content
                target_user = None
                target_position = None
                for u, pos in users:
                    if u.username.lower() == target_username.lower():
                        target_user = u
                        target_position = pos
                        break
                if target_user and target_position:
                    # Manejar tanto Position como AnchorPosition
                    if isinstance(target_position, Position):
                        new_position = Position(target_position.x + 1, target_position.y, target_position.z)
                    elif isinstance(target_position, AnchorPosition) and target_position.offset:
                        new_position = Position(target_position.offset.x + 1, target_position.offset.y, target_position.offset.z)
                    else:
                        await send_response("❌ No se pudo obtener la posición del usuario")
                        return
                    await self.highrise.teleport(user_id, new_position)
                    await send_response( f"🎯 Te has teletransportado a @{target_username}!")
                else: await send_response( f"❌ ¡Usuario {target_username} no encontrado!")
            except Exception as e: await send_response( f"❌ Error: {e}")
            return

        # Comando !addzone (Admin/Owner)
        if msg.startswith("!addzone "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden crear zonas!"); return
            zone_name = msg[9:].strip()
            if not zone_name: await send_response("❌ Usa: !addzone [nombre]"); return
            users = (await self.highrise.get_room_users()).content
            user_position = next((pos for u, pos in users if u.id == user_id), None)
            if user_position:
                if isinstance(user_position, Position):
                    TELEPORT_POINTS[zone_name] = {"x": user_position.x, "y": user_position.y, "z": user_position.z}
                elif isinstance(user_position, AnchorPosition) and user_position.offset:
                    TELEPORT_POINTS[zone_name] = {"x": user_position.offset.x, "y": user_position.offset.y, "z": user_position.offset.z}
                else:
                    await send_response("❌ Error obteniendo posición")
                    return
                save_leaderboard_data()
                self.save_data()
                await send_response( f"🗺️ Zona '{zone_name}' creada en posición ({TELEPORT_POINTS[zone_name]['x']}, {TELEPORT_POINTS[zone_name]['y']}, {TELEPORT_POINTS[zone_name]['z']})")
            else: await send_response("❌ Error obteniendo posición")
            return

        # Comando !vip @user (Admin/Owner)
        if msg.startswith("!vip "):
            if not (self.is_admin(user_id) or user_id == OWNER_ID): await send_response("❌ ¡Solo administradores y propietario pueden dar VIP!"); return
            target_username = msg[5:].strip().replace("@", "")
            users = (await self.highrise.get_room_users()).content
            target_found = False
            target_user_id = None
            for u, pos in users:
                if u.username == target_username:
                    target_found = True
                    target_user_id = u.id
                    break
            if target_found:
                VIP_USERS.add(target_username)
                self.save_data()
                await send_response( f"⭐ @{target_username} ahora es VIP!")
                if target_user_id: await self.highrise.send_whisper(target_user_id, f"🎉 ¡Felicitaciones! Ahora eres VIP gracias a @{user.username}")
            else: await send_response( f"❌ Usuario {target_username} no encontrado en la sala")
            return

    async def on_chat(self, user: User, message: str) -> None:
        """Manejador de mensajes públicos"""
        msg = message.strip()
        user_id = user.id
        username = user.username

        USER_NAMES[user_id] = username

        # Detectar mención al bot cantinero
        if "@CANTINERO_BOT" in msg or "@cantinero" in msg.lower():
            await asyncio.sleep(0.3)
            await self.highrise.chat(f"📞 *marcando al cantinero* ¡@{username} está llamando a la barra!")
            log_event("CALL", f"{username} mencionó al bot cantinero")
            # El bot cantinero responderá automáticamente con sistema extendido
            return

        bot_username = "NOCTURNO_BOT"
        is_bot_mention = False
        treat_as_whisper = False
        
        # Detectar si mencionan al bot
        if f"@{bot_username}" in msg or "@nocturno" in msg.lower() or "@bot" in msg.lower():
            is_bot_mention = True
            treat_as_whisper = True
            msg = msg.replace(f"@{bot_username}", "").replace("@nocturno", "").replace("@bot", "").strip()

        log_event("CHAT", f"[PUBLIC] {username}: {message}" + (" [BOT_MENTION]" if is_bot_mention else ""))

        if is_bot_mention:
            await self.highrise.send_whisper(user_id, f"👋 ¡Hola @{username}! Me mencionaste.")
            await self.highrise.send_whisper(user_id, "💡 Usa !help en privado para ver todos los comandos")
            if not msg or msg.isspace(): return

        if self.is_banned(user_id) or self.is_muted(user_id):
            return

        self.update_activity(user_id)
        await self.handle_command(user, msg, is_whisper=treat_as_whisper)

    async def on_whisper(self, user: User, message: str) -> None:
        """Manejador de susurros"""
        msg = message.strip()
        user_id = user.id
        username = user.username

        USER_NAMES[user_id] = username

        if self.is_banned(user_id) or self.is_muted(user_id):
            return

        self.update_activity(user_id)
        log_event("WHISPER", f"{username}: {message}")
        await self.handle_command(user, msg, is_whisper=True)

    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        """Usuario entra a la sala"""
        user_id = user.id
        username = user.username

        USER_NAMES[user_id] = username
        self.update_user_info(user_id, username)

        USER_JOIN_TIMES[user_id] = time.time()
        USER_INFO[user_id]["time_joined"] = time.time()

        # Enviar bienvenida con reintentos
        welcome_message = "💫🌚Bienvenido a la sala ✓NOCTURNO✓ ponte cómodo y disfruta al máximo🌚💫"
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                await asyncio.sleep(0.5 * attempt)  # Delay incremental para evitar rate limiting
                await self.highrise.send_whisper(user_id, welcome_message)
                safe_print(f"✅ Bienvenida enviada a {username} (intento {attempt})")
                break  # Éxito, salir del loop
            except Exception as e:
                if attempt < max_attempts:
                    safe_print(f"⚠️ Intento {attempt} fallido para {username}: {e}. Reintentando...")
                else:
                    safe_print(f"❌ Error enviando bienvenida a {username} después de {max_attempts} intentos: {e}")
                    log_event("WARNING", f"Fallo bienvenida a {username}: {e}")

    async def on_user_leave(self, user: User) -> None:
        """Usuario sale de la sala"""
        user_id = user.id

        if user_id in USER_JOIN_TIMES:
            join_time = USER_JOIN_TIMES[user_id]
            current_time = time.time()
            time_in_room = round(current_time - join_time)
            if user_id in USER_INFO:
                USER_INFO[user_id]["total_time_in_room"] += time_in_room
            del USER_JOIN_TIMES[user_id]

        await self.stop_emote_loop(user_id)
        save_user_info()

    async def on_tip(self, sender: User, receiver: User, tip: CurrencyItem | Item) -> None:
        """Manejador de propinas - Sistema VIP automático por donación"""
        global BOT_WALLET
        
        if receiver.id == self.bot_id:
            # Verificar que sea una propina de oro (CurrencyItem) y no un item regular
            if isinstance(tip, CurrencyItem):
                tip_amount = tip.amount
                
                # Sistema VIP: Donación de exactamente 100 oro otorga VIP permanente
                if tip_amount == 100:
                    if sender.username not in VIP_USERS:
                        VIP_USERS.add(sender.username)
                        self.save_data()
                        await self.highrise.send_whisper(sender.id, "✨ ¡Ahora eres VIP permanente en la sala 🕷️NOCTURNO🕷️!")
                        await self.highrise.chat(f"🌟 ¡@{sender.username} se unió al club VIP con 100 oro! 🌟")
                        log_event("VIP", f"{sender.username} obtuvo VIP por donación de 100 oro")
                    else:
                        await self.highrise.send_whisper(sender.id, "💖 ¡Gracias por tu donación de 100 oro!")
                        await self.highrise.send_whisper(sender.id, "⭐ Ya eres VIP en la sala, esta donación apoya al bot")
                else:
                    # Cualquier otra cantidad de oro
                    await self.highrise.send_whisper(sender.id, f"💰 ¡Gracias por donar {tip_amount} oro al bot!")
                    await self.highrise.send_whisper(sender.id, f"💡 Dona exactamente 100 oro para obtener VIP automáticamente")
                
                # Actualizar balance del bot
                BOT_WALLET += tip_amount
                log_event("TIP", f"{sender.username} donó {tip_amount} oro al bot (Balance: {BOT_WALLET})")
            else:
                # Si es un Item regular (no oro)
                log_event("TIP", f"{sender.username} envió un item al bot (no oro)")
                await self.highrise.send_whisper(sender.id, "💝 ¡Gracias por el regalo!")

    async def on_emote(self, user: User, emote_id: str, receiver: User | None) -> None:
        """Manejador de emotes"""
        pass

    async def on_user_move(self, user: User, destination: Position | AnchorPosition) -> None:
        """Manejador de movimiento de usuario para flashmode automático y sistema anti-escape de cárcel
        Activa flashmode cuando el usuario sube o baja desde/hacia altura Y >= 10.0 bloques
        Previene que usuarios en la cárcel escapen teletransportándolos de vuelta
        """
        def _coords(p):
            return (p.x, p.y, p.z) if isinstance(p, Position) else None

        try:
            user_id = user.id
            username = user.username
            current_time = time.time()

            if not hasattr(self, 'flashmode_cooldown'): 
                self.flashmode_cooldown = {}

            # SISTEMA ANTI-ESCAPE DE CÁRCEL
            # Si el usuario está en la cárcel y NO es admin/owner, devolverlo a la cárcel
            if user_id in JAIL_USERS:
                is_admin_or_owner = (user_id == OWNER_ID or self.is_admin(user_id))
                
                if not is_admin_or_owner:
                    # Verificar si están intentando escapar de la cárcel
                    if "carcel" in TELEPORT_POINTS:
                        jail_point = TELEPORT_POINTS["carcel"]
                        dest_xyz = _coords(destination)
                        
                        if dest_xyz:
                            # Si intentan alejarse más de 3 bloques de la cárcel, devolverlos
                            distance_from_jail = ((dest_xyz[0] - jail_point["x"])**2 + 
                                                 (dest_xyz[1] - jail_point["y"])**2 + 
                                                 (dest_xyz[2] - jail_point["z"])**2)**0.5
                            
                            if distance_from_jail > 3.0:
                                # Devolverlos a la cárcel
                                jail_position = Position(jail_point["x"], jail_point["y"], jail_point["z"])
                                await self.highrise.teleport(user_id, jail_position)
                                await self.highrise.send_whisper(user_id, "⛓️ ¡No puedes escapar de la cárcel!\n⚠️ Solo un admin puede liberarte con !unjail")
                                safe_print(f"🔒 Intento de escape bloqueado: {username} devuelto a la cárcel")
                                log_event("JAIL", f"Intento de escape bloqueado: {username}")
                                return

            last_pos = self.user_positions.get(user_id)
            if not last_pos:
                self.user_positions[user_id] = destination
                return

            last_xyz = _coords(last_pos)
            dest_xyz = _coords(destination)

            if not last_xyz or not dest_xyz:
                self.user_positions[user_id] = destination
                return

            floor_change_threshold = 1.0
            y_change = abs(dest_xyz[1] - last_xyz[1])
            minimum_height = 10.0

            if y_change >= floor_change_threshold and (dest_xyz[1] >= minimum_height or last_xyz[1] >= minimum_height):
                cooldown_time = 3.0
                if user_id in self.flashmode_cooldown:
                    time_since_last = current_time - self.flashmode_cooldown[user_id]
                    if time_since_last < cooldown_time:
                        self.user_positions[user_id] = destination
                        return

                if not self.is_in_forbidden_zone(dest_xyz[0], dest_xyz[1], dest_xyz[2], user_id):
                    if isinstance(destination, Position):
                        await self.highrise.teleport(user_id, destination)
                        self.flashmode_cooldown[user_id] = current_time
                        direction = "subió" if dest_xyz[1] > last_xyz[1] else "bajó"
                        log_event("FLASHMODE", f"Auto-flashmode {username}: Y:{last_xyz[1]:.1f}→{dest_xyz[1]:.1f}")
                        safe_print(f"⚡ FLASHMODE: {username} {direction} de/a altura >= 10 bloques ({last_xyz[1]:.1f} → {dest_xyz[1]:.1f})")
                else:
                    safe_print(f"❌ Flashmode bloqueado: {username} intentó zona prohibida")

            self.user_positions[user_id] = destination

        except Exception as e:
            safe_print(f"❌ Error en on_user_move: {e}")

    # ========================================================================
    # TAREAS EN SEGUNDO PLANO
    # ========================================================================

    async def start_announcements(self):
        """Sistema de anuncios automáticos públicos"""
        welcome_message_1 = "🌌 BIENVENIDO A NOCTURNO ⛈️💙\nUna sala donde lo oculto brilla más que la luz...\n💬 Vive la noche, haz nuevos amigos y deja tu huella👣."
        welcome_message_2 = "✨ Sumérgete en la oscuridad... y descubre lo más brillante de ti💯\n‼️(Cualquier incomodidad o sugerencia comuniqué con @Alber_JG_69 o @Xx__Daikel__xX)‼️"
        await self.highrise.chat(welcome_message_1)
        await asyncio.sleep(1)
        await self.highrise.chat(welcome_message_2)

        announcements = [
            "🎮 Usa !help para ver la lista de todos los comandos",
            "💖 Envía corazones a amigos con !heart @username",
            "🏆 Revisa el ranking con !leaderboard",
            "🎯 Juega al medidor de amor: !game love @user1 @user2"
        ]
        announcement_index = 0
        vip_counter = 0

        # Esperar 60 segundos para alternar con bot cantinero
        await asyncio.sleep(60)

        while True:
            try:
                await self.highrise.chat(announcements[announcement_index])
                safe_print(f"📢 Anuncio público enviado: {announcements[announcement_index][:50]}...")
                announcement_index = (announcement_index + 1) % len(announcements)

                vip_counter += 1
                if vip_counter == 4:
                    await self.highrise.chat("💎 ¡Conviértete en VIP por 100 oro y obtén capacidades exclusivas!")
                    vip_counter = 0
                
                self.last_announcement = time.time()
            except Exception as e:
                print(f"Error en anuncios: {e}")
            
            # Esperar 2 minutos (120 segundos) para el siguiente mensaje
            await asyncio.sleep(120)

    async def check_console_messages(self):
        """Verifica mensajes desde consola"""
        while True:
            try:
                if os.path.exists("console_message.txt"):
                    with open("console_message.txt", "r", encoding="utf-8") as f:
                        message = f.read().strip()
                    if message:
                        await self.highrise.chat(message)
                        print(f"💬 Mensaje de consola enviado: {message}")
                        os.remove("console_message.txt")
            except Exception as e:
                print(f"Error verificando mensajes de consola: {e}")
            await asyncio.sleep(1)

    async def periodic_inventory_save(self):
        """Guarda inventario periódicamente"""
        while True:
            await asyncio.sleep(300)
            await save_bot_inventory(self)

    async def start_copied_emote_loop(self, emote_id: str):
        """Bucle infinito de emote copiado"""
        safe_print(f"🎭 INICIANDO BUCLE INFINITO DE EMOTE COPIADO: {emote_id}")
        log_event("BOT", f"Bucle infinito de emote copiado iniciado: {emote_id}")
        
        # Obtener duración del emote
        emote_duration = 5.0
        for e in emotes.values():
            if e["id"] == emote_id:
                emote_duration = e.get("duration", 5.0)
                break
        
        try:
            while self.bot_mode == "copied" and self.copied_emote_mode:
                try:
                    await self.highrise.send_emote(emote_id, self.bot_id)
                    await asyncio.sleep(max(0.1, emote_duration - 0.3))
                except Exception as e:
                    safe_print(f"❌ Error ejecutando emote copiado: {e}")
                    await asyncio.sleep(1.0)
                    continue
        except Exception as e:
            safe_print(f"❌ ERROR en bucle de emote copiado: {e}")
            log_event("ERROR", f"Error en bucle de emote copiado: {e}")

    async def start_auto_emote_cycle(self):
        """Ciclo automático de emotes con gestión de salud"""
        await asyncio.sleep(3)
        
        # Desactivar modo de emote copiado si estaba activo
        self.copied_emote_mode = False
        self.current_copied_emote = None
        self.bot_mode = "auto"
        
        # Filtrar solo emotes gratuitos
        free_emotes = {num: data for num, data in emotes.items() if data.get("is_free", True)}
        
        # Mostrar estadísticas de salud de emotes
        stats_summary = emote_health_manager.get_stats_summary()
        safe_print(f"🎭 INICIANDO CICLO AUTOMÁTICO DE {len(free_emotes)} EMOTES GRATUITOS...")
        safe_print(f"📊 Estado de salud: {stats_summary}")
        log_event("BOT", f"Iniciando ciclo automático de {len(free_emotes)} emotes gratuitos - {stats_summary}")
        
        consecutive_transport_errors = 0
        max_transport_errors = 3
        
        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                emotes_run = 0
                emotes_skipped = 0
                
                safe_print(f"🔄 Ciclo #{cycle_count} - Iniciando secuencia de {len(free_emotes)} emotes")
                
                for number, emote_data in free_emotes.items():
                    if self.bot_mode != "auto":
                        safe_print("⏸️ Ciclo automático detenido (modo cambiado)")
                        return
                    
                    emote_id = emote_data["id"]
                    emote_name = emote_data["name"]
                    emote_duration = emote_data.get("duration", 5.0)
                    
                    # Verificar si el emote debe ejecutarse
                    if not emote_health_manager.should_run(emote_id, emote_name):
                        emotes_skipped += 1
                        continue
                    
                    try:
                        await self.highrise.send_emote(emote_id, self.bot_id)
                        emote_health_manager.record_success(emote_id, emote_name)
                        consecutive_transport_errors = 0
                        emotes_run += 1
                        
                        if emotes_run % 20 == 0:
                            safe_print(f"🎭 Emote #{emotes_run}/{len(free_emotes)}: {emote_name}")
                        
                        await asyncio.sleep(max(0.1, emote_duration - 0.3))
                        
                    except Exception as e:
                        error_msg = str(e)
                        is_transport_error = emote_health_manager.record_failure(emote_id, emote_name, error_msg)
                        
                        if is_transport_error:
                            consecutive_transport_errors += 1
                            safe_print(f"🔴 Error de transporte #{consecutive_transport_errors} con emote {emote_name}: {error_msg}")
                            log_event("ERROR", f"Error de transporte con emote {emote_name}: {error_msg}")
                            
                            # Si hay demasiados errores de transporte consecutivos, abortar ciclo
                            if consecutive_transport_errors >= max_transport_errors:
                                safe_print(f"🛑 ABORTANDO CICLO: {consecutive_transport_errors} errores de transporte consecutivos")
                                log_event("ERROR", f"Ciclo abortado por {consecutive_transport_errors} errores de transporte")
                                
                                # Esperar con backoff exponencial antes de reintentar
                                backoff_time = min(2 ** consecutive_transport_errors, 60)
                                safe_print(f"⏱️ Esperando {backoff_time}s antes de reintentar...")
                                await asyncio.sleep(backoff_time)
                                
                                # Reiniciar contador para el siguiente ciclo
                                consecutive_transport_errors = 0
                                break
                        else:
                            safe_print(f"⚠️ Error con emote {emote_name}: {error_msg}")
                        
                        await asyncio.sleep(1.0)
                        continue
                
                if emotes_skipped > 0:
                    safe_print(f"⏭️ Emotes omitidos por problemas: {emotes_skipped}")
                
                safe_print(f"✅ Ciclo #{cycle_count} completado. Ejecutados: {emotes_run}, Omitidos: {emotes_skipped}")
                await asyncio.sleep(2.0)
                
        except Exception as e:
            safe_print(f"❌ ERROR CRÍTICO en ciclo automático: {e}")
            log_event("ERROR", f"Error crítico en ciclo automático: {e}")

    async def setup_initial_bot_appearance(self):
        """Configura apariencia inicial del bot"""
        try:
            await asyncio.sleep(2)
            if "bot_initial_outfit" in config:
                outfit_id = config["bot_initial_outfit"]
                await self.change_bot_outfit(outfit_id)
                safe_print(f"🎽 Outfit inicial configurado: {outfit_id}")
            
            if "spawn_point" in config and config["spawn_point"]:
                spawn = config["spawn_point"]
                try:
                    spawn_position = Position(spawn["x"], spawn["y"], spawn["z"])
                    await self.highrise.teleport(self.bot_id, spawn_position)
                    safe_print(f"📍 Bot teletransportado al punto de inicio: X={spawn['x']}, Y={spawn['y']}, Z={spawn['z']}")
                    log_event("BOT", f"Bot posicionado en spawn point: {spawn}")
                except Exception as e:
                    safe_print(f"⚠️ Error teletransportando al spawn: {e}")
            
            log_event("BOT", f"Bot inicializado en modo idle (ID: {self.bot_id})")
        except Exception as e:
            log_event("ERROR", f"Error en setup: {e}")

    async def change_bot_outfit(self, outfit_id: str):
        """Cambia outfit del bot"""
        try:
            if outfit_id == "custom_nocturno":
                from highrise.models import Item
                custom_outfit = [
                    Item(type="clothing", id="shirt-n_guy_rise_par_rewards_2023_mafia_suit", amount=1),
                    Item(type="clothing", id="pants-n_room1_2019formalslacksblack", amount=1),
                    Item(type="clothing", id="glasses-n_registrationavatars2023billieglasses", amount=1),
                    Item(type="clothing", id="shoes-n_marchscavengerhunt2021knifeboots", amount=1),
                    Item(type="clothing", id="mouth-n_dailyquests2024racermouth", amount=1),
                    Item(type="clothing", id="hair_front-n_winterformaludceventrewards02_2023_nikana_maschair", amount=1),
                    Item(type="clothing", id="hat-n_fallen_angels_silks_nevs_2024_angel_halo", amount=1),
                    Item(type="clothing", id="skin-s_gray", amount=1)
                ]
                await self.highrise.set_outfit(custom_outfit)
                log_event("BOT", "Outfit NOCTURNO aplicado")
            else:
                current_outfit_response = await self.highrise.get_my_outfit()
                if not isinstance(current_outfit_response, Error):
                    await self.highrise.set_outfit(current_outfit_response.outfit)
            print(f"✅ Outfit del bot configurado para ID: {outfit_id}")
        except Exception as e:
            log_event("ERROR", f"Error cambiando outfit: {e}")

    async def delayed_restart(self):
        """Parada retrasada del bot"""
        await asyncio.sleep(3)
        print("🛑 ¡Bot detenido!")
        self.save_data()
        sys.exit(0)

    def convert_to_gold_bars(self, amount: int) -> str:
        """Convierte la cantidad de oro en barras de oro para tips"""
        bars_dictionary = {
            10000: "gold_bar_10k", 5000: "gold_bar_5000", 1000: "gold_bar_1k",
            500: "gold_bar_500", 100: "gold_bar_100", 50: "gold_bar_50",
            10: "gold_bar_10", 5: "gold_bar_5", 1: "gold_bar_1"
        }
        tip = []
        remaining_amount = amount
        for bar_value in sorted(bars_dictionary.keys(), reverse=True):
            if remaining_amount >= bar_value:
                bar_count = remaining_amount // bar_value
                remaining_amount %= bar_value
                tip.extend([bars_dictionary[bar_value]] * bar_count)
        return ",".join(tip) if tip else ""

    async def get_bot_wallet_balance(self):
        """Obtiene el balance real de la billetera del bot"""
        try:
            wallet_response = await self.highrise.get_wallet()
            if isinstance(wallet_response, Error):
                print(f"Error obteniendo wallet: {wallet_response}")
                return BOT_WALLET
            wallet = wallet_response.content
            return wallet[0].amount if wallet else BOT_WALLET
        except Exception as e:
            print(f"Error obteniendo balance de billetera: {e}")
            return BOT_WALLET

    async def show_user_info(self, user: User, public_response: bool = False):
        """Muestra información del jugador"""
        user_id = user.id
        username = user.username
        self.update_user_info(user_id, username)
        user_data = USER_INFO.get(user_id, {})
        total_time = self.get_user_total_time(user_id)
        messages = USER_ACTIVITY.get(user_id, {}).get("messages", 0)
        hearts = self.get_user_hearts(user_id)
        current_time_in_room = round(time.time() - USER_JOIN_TIMES.get(user_id, time.time()))
        total_time_str = self.format_time(total_time + current_time_in_room)

        if user_id == OWNER_ID: rol = "👑 Propietario"
        elif self.is_admin(user_id): rol = "🛡️ Administrador"
        elif self.is_moderator(user_id): rol = "⚖️ Moderador"
        elif self.is_vip(user_id): rol = "⭐ VIP"
        else: rol = "👤 Usuario Normal"

        followers, following, friends, account_created, crew_info = "N/A", "N/A", "N/A", "Sconosciuto", "Sin crew"
        try:
            user_info = await self.webapi.get_user(user_id) if hasattr(self, 'webapi') and self.webapi else None
            if user_info:
                account_created = user_info.user.joined_at.strftime("%d.%m.%Y %H:%M")
                USER_INFO[user_id]["account_created"] = user_info.user.joined_at.isoformat()
                followers, following, friends = str(user_info.user.num_followers), str(user_info.user.num_following), str(user_info.user.num_friends)
                if hasattr(user_info.user, 'crew') and user_info.user.crew:
                    crew_name = user_info.user.crew.name if hasattr(user_info.user.crew, 'name') else "Unknown"
                    crew_info = crew_name
            elif user_data.get("account_created"):
                try:
                    created_dt = datetime.fromisoformat(user_data["account_created"].replace('Z', '+00:00'))
                    account_created = created_dt.strftime("%d.%m.%Y %H:%M")
                except: pass
        except Exception as e: print(f"Errore Web API: {e}")

        highrise_time = "Sconosciuto"
        try:
            if account_created != "Sconosciuto":
                created_dt = datetime.strptime(account_created, "%d.%m.%Y %H:%M")
                time_diff = datetime.now() - created_dt
                days, hours, minutes = time_diff.days, time_diff.seconds // 3600, (time_diff.seconds % 3600) // 60
                highrise_time = f"{days}d, {hours}h, {minutes}m"
        except Exception as e: print(f"Errore calcolo tempo Highrise: {e}")

        info_message = f"📊 {username}'s Info:\n🎭 Rol: {rol}\n👥 Crew: {crew_info}\n📅 Registrado: {account_created}\n⏰ Tiempo en HR: {highrise_time}\n💖 Corazones: {hearts}\n💬 Mensajes: {messages}\n👥 Followers: {followers} | Following: {following} | Friends: {friends}"
        if public_response: await self.highrise.chat(info_message)
        else: await self.highrise.send_whisper(user_id, info_message)

    async def show_user_info_by_username(self, username: str):
        """Muestra información de usuario por nombre de usuario"""
        target_user_id = None
        response = await self.highrise.get_room_users()
        if isinstance(response, Error):
            await self.highrise.chat("❌ Error obteniendo usuarios")
            log_event("ERROR", f"get_room_users failed: {response.message}")
            return
        users = response.content
        for u, _ in users:
            if u.username == username:
                target_user_id = u.id
                self.update_user_info(target_user_id, username)
                break
        if not target_user_id:
            await self.highrise.chat(f"❌ ¡Usuario {username} no encontrado!")
            return
        await self.show_user_info(User(id=target_user_id, username=username), public_response=True)

    async def show_user_role(self, user: User):
        """Muestra el rol del jugador actual"""
        user_id = user.id
        username = user.username
        if self.is_admin(user_id): role = "Admin"
        elif self.is_moderator(user_id): role = "Manager"
        elif self.is_vip(user_id): role = "Host"
        else: role = "Vip"
        await self.highrise.send_whisper(user_id, f"{username} Roles:[{role}]")

    async def show_user_role_by_username(self, username: str):
        """Muestra el rol de un jugador por nombre de usuario"""
        target_user_id = None
        response = await self.highrise.get_room_users()
        if isinstance(response, Error):
            await self.highrise.chat("❌ Error obteniendo usuarios")
            return
        users = response.content
        for u, _ in users:
            if u.username == username:
                target_user_id = u.id
                self.update_user_info(target_user_id, username)
                break
        if not target_user_id: await self.highrise.chat(f"❌ Giocatore @{username} non trovato"); return
        if self.is_admin(target_user_id): role = "Admin"
        elif self.is_moderator(target_user_id): role = "Manager"
        elif self.is_vip(target_user_id): role = "Host"
        else: role = "Vip"
        await self.highrise.send_whisper(target_user_id, f"🔑 {username} Roles:\nNivel: {role}")

    async def get_bot_user(self):
        """Obtiene el objeto User del bot usando bot_id almacenado"""
        try:
            if not hasattr(self, 'bot_id'): log_event("ERROR", "Bot ID no disponible"); return None
            response = await self.highrise.get_room_users()
            if isinstance(response, Error):
                log_event("ERROR", f"Error obteniendo usuarios de sala: {response.message}")
                return None
            users = response.content
            bot_user = next((u for u, _ in users if u.id == self.bot_id), None)
            if bot_user: log_event("BOT", f"Bot encontrado: {bot_user.username}")
            else: log_event("WARNING", f"Bot no encontrado en sala con ID: {self.bot_id}")
            return bot_user
        except Exception as e: log_event("ERROR", f"Error obteniendo bot user: {e}"); return None

    async def console_chat_input(self):
        """Entrada de consola para enviar mensajes"""
        print("💬 Chat de consola iniciado! Ingresa 'quit' para salir.")
        while True:
            try:
                message = input("> ")
                if message.lower() == 'quit': break
                elif message.strip(): await self.highrise.chat(message); print(f"✅ Enviado: {message}")
            except KeyboardInterrupt: break
            except Exception as e: print(f"❌ Error de envío: {e}")

# ============================================================================
# MANEJADOR DE SEÑALES
# ============================================================================

def signal_handler(sig, frame):
    """Guarda datos al salir"""
    print("\n🛑 Señal de salida recibida. Guardando datos...")
    current_time = time.time()
    for user_id, join_time in USER_JOIN_TIMES.items():
        if user_id in USER_INFO:
            time_in_room = round(current_time - join_time)
            USER_INFO[user_id]["total_time_in_room"] += time_in_room
    try:
        # Guardar puntos de teletransporte
        os.makedirs("data", exist_ok=True)
        with open("data/teleport_points.txt", "w", encoding="utf-8") as f:
            f.write("# Puntos de teletransporte (nombre|x|y|z)\n")
            for name, coords in TELEPORT_POINTS.items():
                f.write(f"{name}|{coords['x']}|{coords['y']}|{coords['z']}\n")
        
        save_leaderboard_data()
        save_user_info()
        safe_print("✅ Datos guardados con éxito (incluidos puntos de teletransporte)")
    except Exception as e: print(f"❌ Error guardando datos: {e}")
    print("👋 ¡Adiós!")
    sys.exit(0)

signal.signal(signal.SIGINT, signal_handler)
signal.signal(signal.SIGTERM, signal_handler)

# ============================================================================
# PUNTO DE ENTRADA
# ============================================================================

if __name__ == "__main__":
    try:
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

        bot = Bot()
        print("🔧 Para ejecutar el bot usa: python -m highrise main:Bot", room_id, api_token)

    except KeyboardInterrupt:
        print("\n🛑 Bot detenido por el usuario")
        sys.exit(0)
    except Exception as e:
        print(f"❌ Error crítico: {e}")
        log_event("ERROR", f"Error crítico en main: {e}")
        sys.exit(1)