from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata, Error
import asyncio
from typing import Union
from datetime import datetime
import sys

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

class BartenderBot(BaseBot):
    """Bot Cantinero NOCTURNO - Floss continuo y mensajes automáticos"""

    def __init__(self):
        super().__init__()
        self.current_message_index = 0
        self.bot_id = None
        self.is_in_call = False
        self.call_partner = None
        self.users_called = set()  # Usuarios que ya llamaron (solo pueden llamar 1 vez)
        self.users_blocked_notified = set()  # Usuarios que ya recibieron mensaje de bloqueo
        
        # Sistema de emotes en bucle
        self.current_emote = "emote-ghost-idle"  # ghostfloat - emote por defecto
        self.emote_loop_active = True  # Activado por defecto
        
        # Lista de bebidas para el comando !trago
        self.bebidas = [
            "🍺 Una cerveza bien fría",
            "🍷 Una copa de vino tinto",
            "🍸 Un martini shaken, not stirred",
            "🥃 Un whisky en las rocas",
            "🍹 Un mojito refrescante",
            "🍾 Champagne de celebración",
            "🧃 Un tequila shot",
            "🥂 Un cóctel de la casa",
            "☕ Un café irlandés",
            "🍻 Una jarra de cerveza artesanal"
        ]

    def get_day_message(self):
        """Obtiene el mensaje según el día de la semana"""
        days = {
            0: "¡Que pasen un feliz Lunes! 🌙",
            1: "¡Que pasen un feliz Martes! 🌙",
            2: "¡Que pasen un feliz Miércoles! 🌙",
            3: "¡Que pasen un feliz Jueves! 🌙",
            4: "¡Que pasen un feliz Viernes! 🌙",
            5: "¡Que pasen un feliz Sábado! 🌙",
            6: "¡Que pasen un feliz Domingo! 🌙"
        }
        # Usar hora UTC-5 (ajustar según tu zona horaria)
        from datetime import timedelta
        local_time = datetime.utcnow() - timedelta(hours=5)
        weekday = local_time.weekday()
        return days[weekday]

    def get_auto_messages(self):
        """Lista de mensajes automáticos incluyendo el día de la semana"""
        return [
            self.get_day_message(),
            "‼️¿Sugerencias o incomodidades? Contacta a un miembro superior de la sala: envía un mensaje a @Alber_JG_69 o a @_Kmi.77. ¡Estamos para ayudarte!‼️",
            "¡Consigue tu VIP Permanente!💎 Para ser un miembro eterno de 🕷️ NOCTURNO 🕷️, Mándale 100 de oro al bot: @NOCTURNO_BOT. ¡Gracias por apoyar la oscuridad!",
            "👉🏼PIDE TU CANCIÓN FAVORITA EN LA JARRITA DE TIP👈🏼",
            "Acércate a la barra.🥃 Estoy para servirle. ¿Qué deseas hoy?🍻"
        ]

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Se ejecuta cuando el bot se conecta a la sala"""
        self.bot_id = session_metadata.user_id
        safe_print(f"🕷️ Bot Cantinero NOCTURNO iniciado! ID: {self.bot_id}")
        safe_print(f"🕷️ User ID: {session_metadata.user_id}")

        # Teletransportar al punto de inicio si está configurado
        try:
            import json
            with open("cantinero_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)

            punto_inicio = config.get("punto_inicio")
            if punto_inicio:
                from highrise import Position
                spawn_position = Position(punto_inicio["x"], punto_inicio["y"], punto_inicio["z"])
                await self.highrise.teleport(self.bot_id, spawn_position)
                safe_print(f"📍 Bot cantinero teletransportado al punto de inicio: X={punto_inicio['x']}, Y={punto_inicio['y']}, Z={punto_inicio['z']}")
        except Exception as e:
            safe_print(f"⚠️ No se pudo teletransportar al punto de inicio: {e}")

        # Iniciar todos los loops con manejo de errores
        try:
            asyncio.create_task(self.emote_loop())
            safe_print(f"✅ Emote loop iniciado con: {self.current_emote} (ghostfloat)")
        except Exception as e:
            safe_print(f"❌ Error iniciando emote_loop: {e}")
        
        try:
            asyncio.create_task(self.auto_message_loop())
            safe_print("✅ Auto message loop iniciado")
        except Exception as e:
            safe_print(f"❌ Error iniciando auto_message_loop: {e}")
        
        try:
            asyncio.create_task(self.auto_reconnect_loop())
            safe_print("✅ Auto reconnect loop iniciado")
        except Exception as e:
            safe_print(f"❌ Error iniciando auto_reconnect_loop: {e}")

    async def emote_loop(self) -> None:
        """Loop infinito que ejecuta el emote configurado en bucle"""
        await asyncio.sleep(5)  # Esperar al inicio
        consecutive_errors = 0
        max_consecutive_errors = 3
        
        # Duraciones aproximadas de emotes comunes (en segundos)
        emote_durations = {
            "emote-ghost-idle": 20.43,  # ghostfloat
            "emote-dab": 3.75,
            "dance-gangnamstyle": 15.0,
            "idle-floating": 27.60,  # fairyfloat
            "emote-looping": 9.89,  # fairytwirl
        }

        while True:
            try:
                # Solo ejecutar si el loop está activo y no está en llamada
                if self.emote_loop_active and not self.is_in_call:
                    await self.highrise.send_emote(self.current_emote)
                    consecutive_errors = 0  # Resetear contador en caso de éxito
                    
                    # Obtener duración del emote actual
                    emote_duration = emote_durations.get(self.current_emote, 10.0)
                    
                    # Esperar la duración del emote menos un pequeño margen
                    # para que se repita de forma continua pero completa
                    await asyncio.sleep(max(0.5, emote_duration - 0.3))
                else:
                    # Si está desactivado o en llamada, esperar
                    await asyncio.sleep(2)
            except Exception as e:
                consecutive_errors += 1
                safe_print(f"⚠️ Error emote loop ({consecutive_errors}/{max_consecutive_errors}): {type(e).__name__}: {e}")
                
                # Backoff exponencial: 10s, 20s, 40s
                wait_time = min(10 * (2 ** (consecutive_errors - 1)), 60)
                safe_print(f"⏳ Esperando {wait_time}s antes de reintentar emote...")
                await asyncio.sleep(wait_time)
                
                # Si hay demasiados errores, resetear después de espera larga
                if consecutive_errors >= max_consecutive_errors:
                    consecutive_errors = 0

    async def auto_message_loop(self) -> None:
        """Loop que envía mensajes automáticos públicos cada 2 minutos"""
        await asyncio.sleep(120)
        consecutive_errors = 0
        max_consecutive_errors = 3

        while True:
            try:
                auto_messages = self.get_auto_messages()
                message = auto_messages[self.current_message_index]

                # Enviar mensaje público en el chat
                await self.highrise.chat(message)

                self.current_message_index = (self.current_message_index + 1) % len(auto_messages)
                consecutive_errors = 0  # Resetear en caso de éxito
                safe_print(f"📢 Mensaje automático público enviado: {message[:50]}...")
            except Exception as e:
                consecutive_errors += 1
                safe_print(f"❌ Error en auto_message_loop ({consecutive_errors}/{max_consecutive_errors}): {type(e).__name__}: {e}")
                
                # Si hay muchos errores, esperar más
                if consecutive_errors >= max_consecutive_errors:
                    safe_print(f"⚠️ Demasiados errores en mensajes automáticos, pausando 5 minutos...")
                    await asyncio.sleep(300)  # 5 minutos
                    consecutive_errors = 0

            # Esperar 2 minutos (120 segundos) para el siguiente mensaje
            await asyncio.sleep(120)

    async def start_auto_emote_cycle(self):
        """Ciclo automático de todos los emotes"""
        await asyncio.sleep(2)
        
        # Cargar emotes completos
        emotes = {
            "1": {"id": "emote-looping", "name": "fairytwirl", "duration": 9.89},
            "2": {"id": "idle-floating", "name": "fairyfloat", "duration": 27.60},
            "3": {"id": "emote-launch", "name": "launch", "duration": 10.88},
            "4": {"id": "emote-cutesalute", "name": "cutesalute", "duration": 3.79},
            "5": {"id": "emote-salute", "name": "atattention", "duration": 4.79},
            "6": {"id": "dance-tiktok11", "name": "tiktok", "duration": 11.37},
            "7": {"id": "emote-kissing", "name": "smooch", "duration": 6.69},
            "8": {"id": "dance-employee", "name": "pushit", "duration": 8.55},
            "9": {"id": "emote-gift", "name": "foryou", "duration": 6.09},
            "10": {"id": "dance-touch", "name": "touch", "duration": 13.15},
            "11": {"id": "dance-kawai", "name": "kawaii", "duration": 10.85},
            "12": {"id": "sit-relaxed", "name": "repose", "duration": 31.21},
            "13": {"id": "emote-sleigh", "name": "sleigh", "duration": 12.51},
            "14": {"id": "emote-hyped", "name": "hyped", "duration": 7.62},
            "15": {"id": "dance-jinglebell", "name": "jingle", "duration": 12.09},
            "16": {"id": "idle-toilet", "name": "gottago", "duration": 33.48},
            "17": {"id": "emote-timejump", "name": "timejump", "duration": 5.51},
            "18": {"id": "idle-wild", "name": "scritchy", "duration": 27.35},
            "19": {"id": "idle-nervous", "name": "bitnervous", "duration": 22.81},
            "20": {"id": "emote-iceskating", "name": "iceskating", "duration": 8.41},
            "21": {"id": "emote-celebrate", "name": "partytime", "duration": 4.35},
            "22": {"id": "emote-pose10", "name": "arabesque", "duration": 5.00},
            "23": {"id": "emote-shy2", "name": "bashful", "duration": 6.34},
            "24": {"id": "emote-headblowup", "name": "revelations", "duration": 13.66},
            "25": {"id": "emote-creepycute", "name": "watchyourback", "duration": 9.01},
            "26": {"id": "dance-creepypuppet", "name": "creepypuppet", "duration": 7.79},
            "27": {"id": "dance-anime", "name": "saunter", "duration": 9.60},
            "28": {"id": "emote-pose6", "name": "surprise", "duration": 6.46},
            "29": {"id": "emote-celebrationstep", "name": "celebration", "duration": 5.18},
            "30": {"id": "dance-pinguin", "name": "penguin", "duration": 12.81},
            "31": {"id": "emote-boxer", "name": "boxer", "duration": 6.75},
            "32": {"id": "idle-guitar", "name": "airguitar", "duration": 14.15},
            "33": {"id": "emote-stargazer", "name": "stargaze", "duration": 7.93},
            "34": {"id": "emote-pose9", "name": "ditzy", "duration": 6.00},
            "35": {"id": "idle-uwu", "name": "uwu", "duration": 25.50},
            "36": {"id": "dance-wrong", "name": "wrong", "duration": 13.60},
            "37": {"id": "emote-fashionista", "name": "fashion", "duration": 6.33},
            "38": {"id": "dance-icecream", "name": "icecream", "duration": 16.58},
            "39": {"id": "idle-dance-tiktok4", "name": "sayso", "duration": 16.55},
            "40": {"id": "idle_zombie", "name": "zombie", "duration": 31.39},
            "41": {"id": "emote-astronaut", "name": "astronaut", "duration": 13.93},
            "42": {"id": "emote-punkguitar", "name": "punk", "duration": 10.59},
            "43": {"id": "emote-gravity", "name": "zerogravity", "duration": 9.02},
            "44": {"id": "emote-pose5", "name": "beautiful", "duration": 5.49},
            "46": {"id": "idle-dance-casual", "name": "casual", "duration": 9.57},
            "47": {"id": "emote-pose1", "name": "wink", "duration": 4.71},
            "48": {"id": "emote-pose3", "name": "fightme", "duration": 5.57},
            "50": {"id": "emote-cute", "name": "cute", "duration": 7.20},
            "51": {"id": "emote-cutey", "name": "cutey", "duration": 4.07},
            "52": {"id": "emote-greedy", "name": "greedy", "duration": 5.72},
            "53": {"id": "dance-tiktok9", "name": "viralgroove", "duration": 13.04},
            "54": {"id": "dance-weird", "name": "weird", "duration": 22.87},
            "55": {"id": "dance-tiktok10", "name": "shuffle", "duration": 9.41},
            "56": {"id": "emoji-gagging", "name": "gagging", "duration": 6.84},
            "57": {"id": "emoji-celebrate", "name": "raise", "duration": 4.78},
            "58": {"id": "dance-tiktok8", "name": "savage", "duration": 13.10},
            "59": {"id": "dance-blackpink", "name": "blackpink", "duration": 7.97},
            "60": {"id": "emote-model", "name": "model", "duration": 7.43},
            "61": {"id": "dance-tiktok2", "name": "dontstartnow", "duration": 11.37},
            "62": {"id": "dance-pennywise", "name": "pennywise", "duration": 4.16},
            "63": {"id": "emote-bow", "name": "bow", "duration": 5.10},
            "64": {"id": "dance-russian", "name": "russian", "duration": 11.39},
            "65": {"id": "emote-curtsy", "name": "curtsy", "duration": 3.99},
            "66": {"id": "emote-snowball", "name": "snowball", "duration": 6.32},
            "67": {"id": "emote-hot", "name": "hot", "duration": 5.57},
            "68": {"id": "emote-snowangel", "name": "snowangel", "duration": 7.33},
            "69": {"id": "emote-charging", "name": "charging", "duration": 9.53},
            "70": {"id": "dance-shoppingcart", "name": "letsgoshopping", "duration": 5.56},
            "71": {"id": "emote-confused", "name": "confused", "duration": 9.58},
            "72": {"id": "idle-enthusiastic", "name": "enthused", "duration": 17.53},
            "73": {"id": "emote-telekinesis", "name": "telekinesis", "duration": 11.01},
            "74": {"id": "emote-float", "name": "float", "duration": 9.26},
            "75": {"id": "emote-teleporting", "name": "teleporting", "duration": 12.89},
            "76": {"id": "emote-swordfight", "name": "swordfight", "duration": 7.71},
            "77": {"id": "emote-maniac", "name": "maniac", "duration": 5.94},
            "78": {"id": "emote-energyball", "name": "energyball", "duration": 8.28},
            "79": {"id": "emote-snake", "name": "worm", "duration": 6.63},
            "80": {"id": "idle_singing", "name": "singalong", "duration": 11.31},
            "81": {"id": "emote-frog", "name": "frog", "duration": 16.14},
            "82": {"id": "dance-macarena", "name": "macarena", "duration": 15.0},
            "83": {"id": "emote-kissing-passionate", "name": "kiss", "duration": 10.47},
            "84": {"id": "emoji-shake-head", "name": "shakehead", "duration": 3.5},
            "85": {"id": "idle-sad", "name": "sad", "duration": 25.24},
            "86": {"id": "emoji-nod", "name": "nod", "duration": 2.5},
            "87": {"id": "emote-laughing2", "name": "laughing", "duration": 6.60},
            "88": {"id": "emoji-hello", "name": "hello", "duration": 3.0},
            "89": {"id": "emoji-thumbsup", "name": "thumbsup", "duration": 2.5},
            "90": {"id": "mining-fail", "name": "miningfail", "duration": 3.41},
            "91": {"id": "emote-shy", "name": "shy", "duration": 5.15},
            "92": {"id": "fishing-pull", "name": "fishingpull", "duration": 2.81},
            "93": {"id": "dance-thewave", "name": "thewave", "duration": 8.0},
            "94": {"id": "idle-angry", "name": "angry", "duration": 26.07},
            "95": {"id": "emote-rough", "name": "rough", "duration": 6.0},
            "96": {"id": "fishing-idle", "name": "fishingidle", "duration": 17.87},
            "97": {"id": "emote-dropped", "name": "dropped", "duration": 4.5},
            "98": {"id": "mining-success", "name": "miningsuccess", "duration": 3.11},
            "99": {"id": "emote-receive-happy", "name": "receivehappy", "duration": 5.0},
            "100": {"id": "emote-cold", "name": "cold", "duration": 5.17},
            "101": {"id": "fishing-cast", "name": "fishingcast", "duration": 2.82},
            "102": {"id": "emote-sit", "name": "sit", "duration": 20.0},
            "103": {"id": "dance-shuffle", "name": "shuffledance", "duration": 9.0},
            "104": {"id": "emote-receive-sad", "name": "receivesad", "duration": 5.0},
            "105": {"id": "idle-loop-tired", "name": "tired", "duration": 11.23},
            "106": {"id": "dance-hipshake", "name": "hipshake", "duration": 13.38},
            "107": {"id": "dance-fruity", "name": "fruity", "duration": 18.25},
            "108": {"id": "dance-cheerleader", "name": "cheerleader", "duration": 17.93},
            "109": {"id": "dance-tiktok14", "name": "magnetic", "duration": 11.20},
            "110": {"id": "emote-howl", "name": "nocturnal", "duration": 8.10},
            "111": {"id": "idle-howl", "name": "moonlit", "duration": 48.62},
            "112": {"id": "emote-trampoline", "name": "trampoline", "duration": 6.11},
            "113": {"id": "emote-attention", "name": "attention", "duration": 5.65},
            "114": {"id": "sit-open", "name": "laidback", "duration": 27.28},
            "115": {"id": "emote-shrink", "name": "shrink", "duration": 9.99},
            "116": {"id": "emote-puppet", "name": "puppet", "duration": 17.89},
            "117": {"id": "dance-aerobics", "name": "pushups", "duration": 9.89},
            "118": {"id": "dance-duckwalk", "name": "duckwalk", "duration": 12.48},
            "119": {"id": "dance-handsup", "name": "handsintheair", "duration": 23.18},
            "120": {"id": "dance-metal", "name": "rockout", "duration": 15.78},
            "121": {"id": "dance-orangejustice", "name": "orangejuice", "duration": 7.17},
            "122": {"id": "dance-singleladies", "name": "ringonit", "duration": 22.33},
            "123": {"id": "dance-smoothwalk", "name": "smoothwalk", "duration": 7.58},
            "124": {"id": "dance-voguehands", "name": "voguehands", "duration": 10.57},
            "125": {"id": "emoji-arrogance", "name": "arrogance", "duration": 8.16},
            "126": {"id": "emoji-give-up", "name": "giveup", "duration": 6.04},
            "127": {"id": "emoji-hadoken", "name": "fireball", "duration": 4.29},
            "128": {"id": "emoji-halo", "name": "levitate", "duration": 6.52},
            "129": {"id": "emoji-lying", "name": "lying", "duration": 7.39},
            "130": {"id": "emoji-naughty", "name": "naughty", "duration": 5.73},
            "131": {"id": "emoji-poop", "name": "stinky", "duration": 5.86},
            "132": {"id": "emoji-pray", "name": "pray", "duration": 6.00},
            "133": {"id": "emoji-punch", "name": "punch", "duration": 3.36},
            "134": {"id": "emoji-sick", "name": "sick", "duration": 6.22},
            "135": {"id": "emoji-smirking", "name": "smirk", "duration": 5.74},
            "136": {"id": "emoji-sneeze", "name": "sneeze", "duration": 4.33},
            "137": {"id": "emoji-there", "name": "point", "duration": 3.09},
            "138": {"id": "emote-death2", "name": "collapse", "duration": 5.54},
            "139": {"id": "emote-disco", "name": "disco", "duration": 6.14},
            "140": {"id": "emote-ghost-idle", "name": "ghostfloat", "duration": 20.43},
            "141": {"id": "emote-handstand", "name": "handstand", "duration": 5.89},
            "142": {"id": "emote-kicking", "name": "superkick", "duration": 6.21},
            "143": {"id": "emote-panic", "name": "panic", "duration": 4.5},
            "144": {"id": "emote-splitsdrop", "name": "splits", "duration": 5.31},
            "145": {"id": "idle_layingdown", "name": "attentive", "duration": 26.11},
            "146": {"id": "idle_layingdown2", "name": "relaxed", "duration": 22.59},
            "147": {"id": "emote-apart", "name": "fallingapart", "duration": 5.98},
            "148": {"id": "emote-baseball", "name": "homerun", "duration": 8.47},
            "149": {"id": "emote-boo", "name": "boo", "duration": 5.58},
            "150": {"id": "emote-bunnyhop", "name": "bunnyhop", "duration": 13.63},
            "151": {"id": "emote-death", "name": "revival", "duration": 8.00},
            "152": {"id": "emote-deathdrop", "name": "faintdrop", "duration": 4.18},
            "153": {"id": "emote-elbowbump", "name": "elbowbump", "duration": 6.44},
            "154": {"id": "emote-fail1", "name": "fall", "duration": 6.90},
            "155": {"id": "emote-fail2", "name": "clumsy", "duration": 7.74},
            "156": {"id": "emote-fainting", "name": "faint", "duration": 18.55},
            "157": {"id": "emote-hugyourself", "name": "hugyourself", "duration": 6.03},
            "158": {"id": "emote-jetpack", "name": "jetpack", "duration": 17.77},
            "159": {"id": "emote-judochop", "name": "judochop", "duration": 5.0},
            "160": {"id": "emote-jumpb", "name": "jump", "duration": 4.87},
            "161": {"id": "emote-laughing2", "name": "amused", "duration": 6.60},
            "162": {"id": "emote-levelup", "name": "levelup", "duration": 7.27},
            "163": {"id": "emote-monster_fail", "name": "monsterfail", "duration": 5.42},
            "164": {"id": "idle-dance-headbobbing", "name": "nightfever", "duration": 23.65},
            "165": {"id": "emote-ninjarun", "name": "ninjarun", "duration": 6.50},
            "166": {"id": "emoji-peace", "name": "peace", "duration": 3.5},
            "167": {"id": "emote-peekaboo", "name": "peekaboo", "duration": 4.52},
            "168": {"id": "emote-proposing", "name": "proposing", "duration": 5.91},
            "169": {"id": "emote-rainbow", "name": "rainbow", "duration": 8.0},
            "170": {"id": "emote-robot", "name": "robot", "duration": 10.0},
            "171": {"id": "emote-rofl", "name": "rofl", "duration": 7.65},
            "172": {"id": "emote-roll", "name": "roll", "duration": 4.31},
            "173": {"id": "emote-ropepull", "name": "ropepull", "duration": 10.69},
            "174": {"id": "emote-secrethandshake", "name": "secrethandshake", "duration": 6.28},
            "175": {"id": "emote-sumo", "name": "sumofight", "duration": 11.64},
            "176": {"id": "emote-superpunch", "name": "superpunch", "duration": 5.75},
            "177": {"id": "emote-superrun", "name": "superrun", "duration": 7.16},
            "178": {"id": "emote-theatrical", "name": "theatrical", "duration": 11.00},
            "179": {"id": "emote-wings", "name": "ibelieve", "duration": 14.21},
            "180": {"id": "emote-frustrated", "name": "irritated", "duration": 6.41},
            "181": {"id": "idle-floorsleeping", "name": "cozynap", "duration": 14.61},
            "182": {"id": "idle-floorsleeping2", "name": "relaxing", "duration": 18.83},
            "183": {"id": "idle-hero", "name": "heropose", "duration": 22.33},
            "184": {"id": "idle-lookup", "name": "ponder", "duration": 8.75},
            "185": {"id": "idle-posh", "name": "posh", "duration": 23.29},
            "186": {"id": "idle-sad", "name": "poutyface", "duration": 25.24},
            "187": {"id": "emote-dab", "name": "dab", "duration": 3.75},
            "188": {"id": "dance-gangnamstyle", "name": "gangnamstyle", "duration": 15.0},
            "189": {"id": "emoji-crying", "name": "sob", "duration": 4.91},
            "190": {"id": "idle-loop-tapdance", "name": "taploop", "duration": 7.81},
            "191": {"id": "idle-sleep", "name": "sleepy", "duration": 3.35},
            "192": {"id": "dance-sexy", "name": "wiggledance", "duration": 13.70},
            "193": {"id": "emoji-eyeroll", "name": "eyeroll", "duration": 3.75},
            "194": {"id": "dance-moonwalk", "name": "moonwalk", "duration": 12.0},
            "195": {"id": "idle-fighter", "name": "fighter", "duration": 18.64},
            "196": {"id": "idle-dance-tiktok7", "name": "renegade", "duration": 14.05},
            "197": {"id": "emote-facepalm", "name": "facepalm", "duration": 5.0},
            "198": {"id": "idle-dance-headbobbing", "name": "feelthebeat", "duration": 23.65},
            "199": {"id": "emote-pose8", "name": "happy", "duration": 5.62},
            "200": {"id": "emote-hug", "name": "hug", "duration": 4.53},
            "201": {"id": "emote-slap", "name": "slap", "duration": 4.06},
            "202": {"id": "emoji-clapping", "name": "clap", "duration": 2.98},
            "203": {"id": "emote-exasperated", "name": "exasperated", "duration": 4.10},
            "204": {"id": "emote-kissing-passionate", "name": "sweetsmooch", "duration": 10.47},
            "205": {"id": "emote-tapdance", "name": "tapdance", "duration": 6.0},
            "206": {"id": "emote-suckthumb", "name": "thumbsuck", "duration": 5.23},
            "207": {"id": "dance-harlemshake", "name": "harlemshake", "duration": 10.0},
            "208": {"id": "emote-heartfingers", "name": "heartfingers", "duration": 5.18},
            "209": {"id": "idle-loop-aerobics", "name": "aerobics", "duration": 10.08},
            "210": {"id": "emote-heartshape", "name": "heartshape", "duration": 7.60},
            "211": {"id": "emote-hearteyes", "name": "hearteyes", "duration": 5.99},
            "212": {"id": "dance-wild", "name": "karmadance", "duration": 16.25},
            "213": {"id": "emoji-scared", "name": "gasp", "duration": 4.06},
            "214": {"id": "emote-think", "name": "think", "duration": 4.81},
            "215": {"id": "emoji-dizzy", "name": "stunned", "duration": 5.38},
            "216": {"id": "emote-embarrassed", "name": "embarrassed", "duration": 9.09},
            "217": {"id": "emote-disappear", "name": "blastoff", "duration": 5.53},
            "218": {"id": "idle-loop-annoyed", "name": "annoyed", "duration": 18.62},
            "219": {"id": "dance-zombie", "name": "dancezombie", "duration": 13.83},
            "220": {"id": "idle-loop-happy", "name": "chillin", "duration": 19.80},
            "221": {"id": "emote-frustrated", "name": "frustrated", "duration": 6.41},
            "222": {"id": "idle-loop-sad", "name": "bummed", "duration": 21.80},
            "223": {"id": "emoji-ghost", "name": "ghost", "duration": 3.74},
            "224": {"id": "emoji-mind-blown", "name": "mindblown", "duration": 3.46}
        }
        
        safe_print(f"🎭 INICIANDO CICLO AUTOMÁTICO DE {len(emotes)} EMOTES...")
        
        # Desactivar loop único
        self.emote_loop_active = False
        
        try:
            cycle_count = 0
            while True:
                cycle_count += 1
                safe_print(f"🔄 Ciclo #{cycle_count} - Iniciando secuencia de {len(emotes)} emotes")
                
                for number, emote_data in emotes.items():
                    emote_id = emote_data["id"]
                    emote_name = emote_data["name"]
                    emote_duration = emote_data.get("duration", 5.0)
                    
                    try:
                        await self.highrise.send_emote(emote_id, self.bot_id)
                        if int(number) % 20 == 0:
                            safe_print(f"🎭 Emote #{number}/{len(emotes)}: {emote_name}")
                        await asyncio.sleep(max(0.1, emote_duration - 0.3))
                    except Exception as e:
                        safe_print(f"❌ Error emote #{number} ({emote_name}): {e}")
                        await asyncio.sleep(0.5)
                        continue
                
                safe_print(f"✅ Ciclo #{cycle_count} completado. Esperando 2 segundos...")
                await asyncio.sleep(2.0)
        except Exception as e:
            safe_print(f"❌ ERROR en ciclo automático: {e}")
    
    async def auto_reconnect_loop(self):
        """Sistema de reconexión automática mejorado con mejor logging"""
        consecutive_failures = 0
        last_check_time = None
        
        while True:
            try:
                await asyncio.sleep(30)  # Verificar cada 30 segundos para reducir carga en API
                
                from datetime import datetime
                current_time = datetime.now().strftime("%H:%M:%S")
                last_check_time = current_time

                # Verificar si el bot está en la sala
                try:
                    room_users = await self.highrise.get_room_users()
                    if isinstance(room_users, Error):
                        safe_print(f"[{current_time}] ❌ Error API: {room_users.message}")
                        raise Exception(f"Error API obteniendo usuarios: {room_users.message}")

                    users = room_users.content
                    bot_in_room = any(u.id == self.bot_id for u, _ in users)

                    if bot_in_room:
                        consecutive_failures = 0  # Resetear contador si está conectado
                        # Logging solo cada 10 minutos para no saturar
                        minute = int(current_time.split(':')[1])
                        if minute % 10 == 0 and int(current_time.split(':')[2]) < 30:
                            safe_print(f"[{current_time}] ✅ Bot cantinero conectado OK ({len(users)} usuarios en sala)")
                    else:
                        consecutive_failures += 1
                        safe_print(f"[{current_time}] ⚠️ Bot cantinero NO encontrado en sala ({consecutive_failures}/3)")
                        
                        if consecutive_failures >= 3:
                            safe_print(f"[{current_time}] 🔄 Iniciando reconexión automática...")
                            await self.attempt_reconnection()
                            consecutive_failures = 0

                except Exception as e:
                    consecutive_failures += 1
                    safe_print(f"[{current_time}] ❌ Error verificando presencia ({consecutive_failures}/3)")
                    safe_print(f"[{current_time}] Detalle del error: {type(e).__name__}: {str(e)}")
                    
                    if consecutive_failures >= 3:
                        safe_print(f"[{current_time}] 🔄 Intentando reconexión tras {consecutive_failures} fallos...")
                        await self.attempt_reconnection()
                        consecutive_failures = 0

            except Exception as e:
                safe_print(f"❌ Error crítico en auto_reconnect_loop: {type(e).__name__}: {str(e)}")
                import traceback
                safe_print(f"Traceback: {traceback.format_exc()}")
                await asyncio.sleep(5)

    async def attempt_reconnection(self):
        """Intenta reconectar el bot cantinero"""
        max_attempts = 10
        for attempt in range(1, max_attempts + 1):
            try:
                safe_print(f"🔄 Intento de reconexión {attempt}/{max_attempts}...")

                # Esperar tiempo incremental
                await asyncio.sleep(min(attempt * 3, 30))

                room_users = await self.highrise.get_room_users()
                if not isinstance(room_users, Error):
                    safe_print("✅ Reconexión exitosa del bot cantinero!")
                    
                    # Esperar antes de reiniciar tareas
                    await asyncio.sleep(2)
                    
                    # Teletransportar al punto de inicio
                    try:
                        if self.bot_id:
                            import json
                            with open("cantinero_config.json", "r", encoding="utf-8") as f:
                                config = json.load(f)
                            punto_inicio = config.get("punto_inicio")
                            if punto_inicio:
                                spawn_position = Position(punto_inicio["x"], punto_inicio["y"], punto_inicio["z"])
                                await self.highrise.teleport(self.bot_id, spawn_position)
                    except:
                        pass

                    return True

            except Exception as e:
                safe_print(f"❌ Fallo en intento {attempt}: {e}")

        safe_print("❌ No se pudo reconectar después de varios intentos")
        safe_print("🔄 El bot seguirá intentando reconectar...")
        return False

    async def on_chat(self, user: User, message: str) -> None:
        """Detectar cuando mencionan al bot cantinero o usan comando !trago"""
        msg = message.strip()
        user_id = user.id
        username = user.username

        # Cargar configuración para verificar admin/owner
        import json
        try:
            with open("config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            owner_id = config.get("owner_id", "")
            admin_ids = config.get("admin_ids", [])
        except:
            owner_id = ""
            admin_ids = []

        is_admin_or_owner = (user_id == owner_id or user_id in admin_ids)

        # Comando !copy - Copiar outfit del usuario que usa el comando
        if msg.lower() == "!copy":
            if not is_admin_or_owner:
                await self.highrise.chat("❌ Solo admin y propietario pueden copiar outfits")
                return

            try:
                # Obtener el outfit del usuario que ejecuta el comando
                user_outfit_response = await self.highrise.get_user_outfit(user_id)
                
                if isinstance(user_outfit_response, Error):
                    await self.highrise.chat("❌ Error obteniendo tu outfit")
                    safe_print(f"❌ Error obteniendo outfit: {user_outfit_response.message}")
                    return
                
                # Copiar el outfit al bot cantinero
                await self.highrise.set_outfit(user_outfit_response.outfit)
                
                await self.highrise.chat(f"👔 ¡Outfit de @{username} copiado exitosamente!")
                safe_print(f"✅ Bot cantinero copió el outfit de {username}")
            except Exception as e:
                await self.highrise.chat(f"❌ Error copiando outfit: {e}")
                safe_print(f"❌ Error en !copy: {e}")
            return

        # Catálogo completo de 224 emotes (mismo que bot principal)
        emotes = {
            "1": {"id": "emote-looping", "name": "fairytwirl", "duration": 9.89},
            "2": {"id": "idle-floating", "name": "fairyfloat", "duration": 27.60},
            "3": {"id": "emote-launch", "name": "launch", "duration": 10.88},
            "4": {"id": "emote-cutesalute", "name": "cutesalute", "duration": 3.79},
            "5": {"id": "emote-salute", "name": "atattention", "duration": 4.79},
            "6": {"id": "dance-tiktok11", "name": "tiktok", "duration": 11.37},
            "7": {"id": "emote-kissing", "name": "smooch", "duration": 6.69},
            "8": {"id": "dance-employee", "name": "pushit", "duration": 8.55},
            "9": {"id": "emote-gift", "name": "foryou", "duration": 6.09},
            "10": {"id": "dance-touch", "name": "touch", "duration": 13.15},
            "11": {"id": "dance-kawai", "name": "kawaii", "duration": 10.85},
            "12": {"id": "sit-relaxed", "name": "repose", "duration": 31.21},
            "13": {"id": "emote-sleigh", "name": "sleigh", "duration": 12.51},
            "14": {"id": "emote-hyped", "name": "hyped", "duration": 7.62},
            "15": {"id": "dance-jinglebell", "name": "jingle", "duration": 12.09},
            "16": {"id": "idle-toilet", "name": "gottago", "duration": 33.48},
            "17": {"id": "emote-timejump", "name": "timejump", "duration": 5.51},
            "18": {"id": "idle-wild", "name": "scritchy", "duration": 27.35},
            "19": {"id": "idle-nervous", "name": "bitnervous", "duration": 22.81},
            "20": {"id": "emote-iceskating", "name": "iceskating", "duration": 8.41},
            "21": {"id": "emote-celebrate", "name": "partytime", "duration": 4.35},
            "22": {"id": "emote-pose10", "name": "arabesque", "duration": 5.00},
            "23": {"id": "emote-shy2", "name": "bashful", "duration": 6.34},
            "24": {"id": "emote-headblowup", "name": "revelations", "duration": 13.66},
            "25": {"id": "emote-creepycute", "name": "watchyourback", "duration": 9.01},
            "26": {"id": "dance-creepypuppet", "name": "creepypuppet", "duration": 7.79},
            "27": {"id": "dance-anime", "name": "saunter", "duration": 9.60},
            "28": {"id": "emote-pose6", "name": "surprise", "duration": 6.46},
            "29": {"id": "emote-celebrationstep", "name": "celebration", "duration": 5.18},
            "30": {"id": "dance-pinguin", "name": "penguin", "duration": 12.81},
            "31": {"id": "emote-boxer", "name": "boxer", "duration": 6.75},
            "32": {"id": "idle-guitar", "name": "airguitar", "duration": 14.15},
            "33": {"id": "emote-stargazer", "name": "stargaze", "duration": 7.93},
            "34": {"id": "emote-pose9", "name": "ditzy", "duration": 6.00},
            "35": {"id": "idle-uwu", "name": "uwu", "duration": 25.50},
            "36": {"id": "dance-wrong", "name": "wrong", "duration": 13.60},
            "37": {"id": "emote-fashionista", "name": "fashion", "duration": 6.33},
            "38": {"id": "dance-icecream", "name": "icecream", "duration": 16.58},
            "39": {"id": "idle-dance-tiktok4", "name": "sayso", "duration": 16.55},
            "40": {"id": "idle_zombie", "name": "zombie", "duration": 31.39},
            "41": {"id": "emote-astronaut", "name": "astronaut", "duration": 13.93},
            "42": {"id": "emote-punkguitar", "name": "punk", "duration": 10.59},
            "43": {"id": "emote-gravity", "name": "zerogravity", "duration": 9.02},
            "44": {"id": "emote-pose5", "name": "beautiful", "duration": 5.49},
            "46": {"id": "idle-dance-casual", "name": "casual", "duration": 9.57},
            "47": {"id": "emote-pose1", "name": "wink", "duration": 4.71},
            "48": {"id": "emote-pose3", "name": "fightme", "duration": 5.57},
            "50": {"id": "emote-cute", "name": "cute", "duration": 7.20},
            "51": {"id": "emote-cutey", "name": "cutey", "duration": 4.07},
            "52": {"id": "emote-greedy", "name": "greedy", "duration": 5.72},
            "53": {"id": "dance-tiktok9", "name": "viralgroove", "duration": 13.04},
            "54": {"id": "dance-weird", "name": "weird", "duration": 22.87},
            "55": {"id": "dance-tiktok10", "name": "shuffle", "duration": 9.41},
            "56": {"id": "emoji-gagging", "name": "gagging", "duration": 6.84},
            "57": {"id": "emoji-celebrate", "name": "raise", "duration": 4.78},
            "58": {"id": "dance-tiktok8", "name": "savage", "duration": 13.10},
            "59": {"id": "dance-blackpink", "name": "blackpink", "duration": 7.97},
            "60": {"id": "emote-model", "name": "model", "duration": 7.43},
            "61": {"id": "dance-tiktok2", "name": "dontstartnow", "duration": 11.37},
            "62": {"id": "dance-pennywise", "name": "pennywise", "duration": 4.16},
            "63": {"id": "emote-bow", "name": "bow", "duration": 5.10},
            "64": {"id": "dance-russian", "name": "russian", "duration": 11.39},
            "65": {"id": "emote-curtsy", "name": "curtsy", "duration": 3.99},
            "66": {"id": "emote-snowball", "name": "snowball", "duration": 6.32},
            "67": {"id": "emote-hot", "name": "hot", "duration": 5.57},
            "68": {"id": "emote-snowangel", "name": "snowangel", "duration": 7.33},
            "69": {"id": "emote-charging", "name": "charging", "duration": 9.53},
            "70": {"id": "dance-shoppingcart", "name": "letsgoshopping", "duration": 5.56},
            "71": {"id": "emote-confused", "name": "confused", "duration": 9.58},
            "72": {"id": "idle-enthusiastic", "name": "enthused", "duration": 17.53},
            "73": {"id": "emote-telekinesis", "name": "telekinesis", "duration": 11.01},
            "74": {"id": "emote-float", "name": "float", "duration": 9.26},
            "75": {"id": "emote-teleporting", "name": "teleporting", "duration": 12.89},
            "76": {"id": "emote-swordfight", "name": "swordfight", "duration": 7.71},
            "77": {"id": "emote-maniac", "name": "maniac", "duration": 5.94},
            "78": {"id": "emote-energyball", "name": "energyball", "duration": 8.28},
            "79": {"id": "emote-snake", "name": "worm", "duration": 6.63},
            "80": {"id": "idle_singing", "name": "singalong", "duration": 11.31},
            "81": {"id": "emote-frog", "name": "frog", "duration": 16.14},
            "82": {"id": "dance-macarena", "name": "macarena", "duration": 15.0},
            "83": {"id": "emote-kissing-passionate", "name": "kiss", "duration": 10.47},
            "84": {"id": "emoji-shake-head", "name": "shakehead", "duration": 3.5},
            "85": {"id": "idle-sad", "name": "sad", "duration": 25.24},
            "86": {"id": "emoji-nod", "name": "nod", "duration": 2.5},
            "87": {"id": "emote-laughing2", "name": "laughing", "duration": 6.60},
            "88": {"id": "emoji-hello", "name": "hello", "duration": 3.0},
            "89": {"id": "emoji-thumbsup", "name": "thumbsup", "duration": 2.5},
            "90": {"id": "mining-fail", "name": "miningfail", "duration": 3.41},
            "91": {"id": "emote-shy", "name": "shy", "duration": 5.15},
            "92": {"id": "fishing-pull", "name": "fishingpull", "duration": 2.81},
            "93": {"id": "dance-thewave", "name": "thewave", "duration": 8.0},
            "94": {"id": "idle-angry", "name": "angry", "duration": 26.07},
            "95": {"id": "emote-rough", "name": "rough", "duration": 6.0},
            "96": {"id": "fishing-idle", "name": "fishingidle", "duration": 17.87},
            "97": {"id": "emote-dropped", "name": "dropped", "duration": 4.5},
            "98": {"id": "mining-success", "name": "miningsuccess", "duration": 3.11},
            "99": {"id": "emote-receive-happy", "name": "receivehappy", "duration": 5.0},
            "100": {"id": "emote-cold", "name": "cold", "duration": 5.17},
            "101": {"id": "fishing-cast", "name": "fishingcast", "duration": 2.82},
            "102": {"id": "emote-sit", "name": "sit", "duration": 20.0},
            "103": {"id": "dance-shuffle", "name": "shuffledance", "duration": 9.0},
            "104": {"id": "emote-receive-sad", "name": "receivesad", "duration": 5.0},
            "105": {"id": "idle-loop-tired", "name": "tired", "duration": 11.23},
            "106": {"id": "dance-hipshake", "name": "hipshake", "duration": 13.38},
            "107": {"id": "dance-fruity", "name": "fruity", "duration": 18.25},
            "108": {"id": "dance-cheerleader", "name": "cheerleader", "duration": 17.93},
            "109": {"id": "dance-tiktok14", "name": "magnetic", "duration": 11.20},
            "110": {"id": "emote-howl", "name": "nocturnal", "duration": 8.10},
            "111": {"id": "idle-howl", "name": "moonlit", "duration": 48.62},
            "112": {"id": "emote-trampoline", "name": "trampoline", "duration": 6.11},
            "113": {"id": "emote-attention", "name": "attention", "duration": 5.65},
            "114": {"id": "sit-open", "name": "laidback", "duration": 27.28},
            "115": {"id": "emote-shrink", "name": "shrink", "duration": 9.99},
            "116": {"id": "emote-puppet", "name": "puppet", "duration": 17.89},
            "117": {"id": "dance-aerobics", "name": "pushups", "duration": 9.89},
            "118": {"id": "dance-duckwalk", "name": "duckwalk", "duration": 12.48},
            "119": {"id": "dance-handsup", "name": "handsintheair", "duration": 23.18},
            "120": {"id": "dance-metal", "name": "rockout", "duration": 15.78},
            "121": {"id": "dance-orangejustice", "name": "orangejuice", "duration": 7.17},
            "122": {"id": "dance-singleladies", "name": "ringonit", "duration": 22.33},
            "123": {"id": "dance-smoothwalk", "name": "smoothwalk", "duration": 7.58},
            "124": {"id": "dance-voguehands", "name": "voguehands", "duration": 10.57},
            "125": {"id": "emoji-arrogance", "name": "arrogance", "duration": 8.16},
            "126": {"id": "emoji-give-up", "name": "giveup", "duration": 6.04},
            "127": {"id": "emoji-hadoken", "name": "fireball", "duration": 4.29},
            "128": {"id": "emoji-halo", "name": "levitate", "duration": 6.52},
            "129": {"id": "emoji-lying", "name": "lying", "duration": 7.39},
            "130": {"id": "emoji-naughty", "name": "naughty", "duration": 5.73},
            "131": {"id": "emoji-poop", "name": "stinky", "duration": 5.86},
            "132": {"id": "emoji-pray", "name": "pray", "duration": 6.00},
            "133": {"id": "emoji-punch", "name": "punch", "duration": 3.36},
            "134": {"id": "emoji-sick", "name": "sick", "duration": 6.22},
            "135": {"id": "emoji-smirking", "name": "smirk", "duration": 5.74},
            "136": {"id": "emoji-sneeze", "name": "sneeze", "duration": 4.33},
            "137": {"id": "emoji-there", "name": "point", "duration": 3.09},
            "138": {"id": "emote-death2", "name": "collapse", "duration": 5.54},
            "139": {"id": "emote-disco", "name": "disco", "duration": 6.14},
            "140": {"id": "emote-ghost-idle", "name": "ghostfloat", "duration": 20.43},
            "141": {"id": "emote-handstand", "name": "handstand", "duration": 5.89},
            "142": {"id": "emote-kicking", "name": "superkick", "duration": 6.21},
            "143": {"id": "emote-panic", "name": "panic", "duration": 4.5},
            "144": {"id": "emote-splitsdrop", "name": "splits", "duration": 5.31},
            "145": {"id": "idle_layingdown", "name": "attentive", "duration": 26.11},
            "146": {"id": "idle_layingdown2", "name": "relaxed", "duration": 22.59},
            "147": {"id": "emote-apart", "name": "fallingapart", "duration": 5.98},
            "148": {"id": "emote-baseball", "name": "homerun", "duration": 8.47},
            "149": {"id": "emote-boo", "name": "boo", "duration": 5.58},
            "150": {"id": "emote-bunnyhop", "name": "bunnyhop", "duration": 13.63},
            "151": {"id": "emote-death", "name": "revival", "duration": 8.00},
            "152": {"id": "emote-deathdrop", "name": "faintdrop", "duration": 4.18},
            "153": {"id": "emote-elbowbump", "name": "elbowbump", "duration": 6.44},
            "154": {"id": "emote-fail1", "name": "fall", "duration": 6.90},
            "155": {"id": "emote-fail2", "name": "clumsy", "duration": 7.74},
            "156": {"id": "emote-fainting", "name": "faint", "duration": 18.55},
            "157": {"id": "emote-hugyourself", "name": "hugyourself", "duration": 6.03},
            "158": {"id": "emote-jetpack", "name": "jetpack", "duration": 17.77},
            "159": {"id": "emote-judochop", "name": "judochop", "duration": 5.0},
            "160": {"id": "emote-jumpb", "name": "jump", "duration": 4.87},
            "161": {"id": "emote-laughing2", "name": "amused", "duration": 6.60},
            "162": {"id": "emote-levelup", "name": "levelup", "duration": 7.27},
            "163": {"id": "emote-monster_fail", "name": "monsterfail", "duration": 5.42},
            "164": {"id": "idle-dance-headbobbing", "name": "nightfever", "duration": 23.65},
            "165": {"id": "emote-ninjarun", "name": "ninjarun", "duration": 6.50},
            "166": {"id": "emoji-peace", "name": "peace", "duration": 3.5},
            "167": {"id": "emote-peekaboo", "name": "peekaboo", "duration": 4.52},
            "168": {"id": "emote-proposing", "name": "proposing", "duration": 5.91},
            "169": {"id": "emote-rainbow", "name": "rainbow", "duration": 8.0},
            "170": {"id": "emote-robot", "name": "robot", "duration": 10.0},
            "171": {"id": "emote-rofl", "name": "rofl", "duration": 7.65},
            "172": {"id": "emote-roll", "name": "roll", "duration": 4.31},
            "173": {"id": "emote-ropepull", "name": "ropepull", "duration": 10.69},
            "174": {"id": "emote-secrethandshake", "name": "secrethandshake", "duration": 6.28},
            "175": {"id": "emote-sumo", "name": "sumofight", "duration": 11.64},
            "176": {"id": "emote-superpunch", "name": "superpunch", "duration": 5.75},
            "177": {"id": "emote-superrun", "name": "superrun", "duration": 7.16},
            "178": {"id": "emote-theatrical", "name": "theatrical", "duration": 11.00},
            "179": {"id": "emote-wings", "name": "ibelieve", "duration": 14.21},
            "180": {"id": "emote-frustrated", "name": "irritated", "duration": 6.41},
            "181": {"id": "idle-floorsleeping", "name": "cozynap", "duration": 14.61},
            "182": {"id": "idle-floorsleeping2", "name": "relaxing", "duration": 18.83},
            "183": {"id": "idle-hero", "name": "heropose", "duration": 22.33},
            "184": {"id": "idle-lookup", "name": "ponder", "duration": 8.75},
            "185": {"id": "idle-posh", "name": "posh", "duration": 23.29},
            "186": {"id": "idle-sad", "name": "poutyface", "duration": 25.24},
            "187": {"id": "emote-dab", "name": "dab", "duration": 3.75},
            "188": {"id": "dance-gangnamstyle", "name": "gangnamstyle", "duration": 15.0},
            "189": {"id": "emoji-crying", "name": "sob", "duration": 4.91},
            "190": {"id": "idle-loop-tapdance", "name": "taploop", "duration": 7.81},
            "191": {"id": "idle-sleep", "name": "sleepy", "duration": 3.35},
            "192": {"id": "dance-sexy", "name": "wiggledance", "duration": 13.70},
            "193": {"id": "emoji-eyeroll", "name": "eyeroll", "duration": 3.75},
            "194": {"id": "dance-moonwalk", "name": "moonwalk", "duration": 12.0},
            "195": {"id": "idle-fighter", "name": "fighter", "duration": 18.64},
            "196": {"id": "idle-dance-tiktok7", "name": "renegade", "duration": 14.05},
            "197": {"id": "emote-facepalm", "name": "facepalm", "duration": 5.0},
            "198": {"id": "idle-dance-headbobbing", "name": "feelthebeat", "duration": 23.65},
            "199": {"id": "emote-pose8", "name": "happy", "duration": 5.62},
            "200": {"id": "emote-hug", "name": "hug", "duration": 4.53},
            "201": {"id": "emote-slap", "name": "slap", "duration": 4.06},
            "202": {"id": "emoji-clapping", "name": "clap", "duration": 2.98},
            "203": {"id": "emote-exasperated", "name": "exasperated", "duration": 4.10},
            "204": {"id": "emote-kissing-passionate", "name": "sweetsmooch", "duration": 10.47},
            "205": {"id": "emote-tapdance", "name": "tapdance", "duration": 6.0},
            "206": {"id": "emote-suckthumb", "name": "thumbsuck", "duration": 5.23},
            "207": {"id": "dance-harlemshake", "name": "harlemshake", "duration": 10.0},
            "208": {"id": "emote-heartfingers", "name": "heartfingers", "duration": 5.18},
            "209": {"id": "idle-loop-aerobics", "name": "aerobics", "duration": 10.08},
            "210": {"id": "emote-heartshape", "name": "heartshape", "duration": 7.60},
            "211": {"id": "emote-hearteyes", "name": "hearteyes", "duration": 5.99},
            "212": {"id": "dance-wild", "name": "karmadance", "duration": 16.25},
            "213": {"id": "emoji-scared", "name": "gasp", "duration": 4.06},
            "214": {"id": "emote-think", "name": "think", "duration": 4.81},
            "215": {"id": "emoji-dizzy", "name": "stunned", "duration": 5.38},
            "216": {"id": "emote-embarrassed", "name": "embarrassed", "duration": 9.09},
            "217": {"id": "emote-disappear", "name": "blastoff", "duration": 5.53},
            "218": {"id": "idle-loop-annoyed", "name": "annoyed", "duration": 18.62},
            "219": {"id": "dance-zombie", "name": "dancezombie", "duration": 13.83},
            "220": {"id": "idle-loop-happy", "name": "chillin", "duration": 19.80},
            "221": {"id": "emote-frustrated", "name": "frustrated", "duration": 6.41},
            "222": {"id": "idle-loop-sad", "name": "bummed", "duration": 21.80},
            "223": {"id": "emoji-ghost", "name": "ghost", "duration": 3.74},
            "224": {"id": "emoji-mind-blown", "name": "mindblown", "duration": 3.46}
        }
        
        # Comando por número: !1, !2, etc.
        if msg.startswith("!") and msg[1:].isdigit():
            if not is_admin_or_owner:
                await self.highrise.chat("❌ Solo admin y propietario pueden cambiar emotes")
                return
            
            emote_num = msg[1:]
            if emote_num in emotes:
                emote_data = emotes[emote_num]
                self.current_emote = emote_data["id"]
                self.emote_loop_active = True
                await self.highrise.chat(f"🎭 Emote cambiado a #{emote_num}: {emote_data['name']} (bucle infinito)")
                safe_print(f"✅ Emote #{emote_num} ({emote_data['name']}) activado por {username}")
            else:
                await self.highrise.chat(f"❌ Emote #{emote_num} no existe")
            return
        
        # Comando por nombre: !ghostfloat, !dab, etc.
        if msg.startswith("!") and not msg[1:].isdigit() and msg.lower() != "!trago" and msg.lower() != "!copy" and msg.lower() != "!canstop" and msg.lower() != "!canstart" and msg.lower() != "!canstatus":
            if not is_admin_or_owner:
                return
            
            emote_name = msg[1:].lower().strip()
            emote_found = None
            emote_number = None
            
            # Buscar por nombre
            for num, data in emotes.items():
                if data["name"].lower() == emote_name or data["id"].lower() == emote_name:
                    emote_found = data
                    emote_number = num
                    break
            
            if emote_found:
                self.current_emote = emote_found["id"]
                self.emote_loop_active = True
                await self.highrise.chat(f"🎭 Emote cambiado a: {emote_found['name']} (#{emote_number}, bucle infinito)")
                safe_print(f"✅ Emote '{emote_found['name']}' activado por {username}")
            return
        
        # Comando !canstop - Detener emote en bucle (Solo Admin/Owner)
        if msg.lower() == "!canstop":
            if not is_admin_or_owner:
                await self.highrise.chat("❌ Solo admin y propietario pueden detener el emote")
                return
            
            self.emote_loop_active = False
            await self.highrise.chat("⏸️ Emote detenido")
            safe_print(f"⏸️ Emote detenido por {username}")
            return
        
        # Comando !canstart - Reanudar emote en bucle (Solo Admin/Owner)
        if msg.lower() == "!canstart":
            if not is_admin_or_owner:
                await self.highrise.chat("❌ Solo admin y propietario pueden iniciar el emote")
                return
            
            self.emote_loop_active = True
            await self.highrise.chat(f"▶️ Emote reanudado: {self.current_emote}")
            safe_print(f"▶️ Emote reanudado por {username}: {self.current_emote}")
            return
        
        # Comando !canstatus - Ver estado actual del emote (Solo Admin/Owner)
        if msg.lower() == "!canstatus":
            if not is_admin_or_owner:
                return
            
            status = "🟢 Activo" if self.emote_loop_active else "🔴 Detenido"
            await self.highrise.chat(f"📊 Estado:\nEmote: {self.current_emote}\nEstado: {status}")
            return
        
        # Comando !automode - Ciclo infinito de todos los emotes (Solo Admin/Owner)
        if msg.lower() == "!automode":
            if not is_admin_or_owner:
                await self.highrise.chat("❌ Solo admin y propietario pueden activar modo automático")
                return
            
            # Iniciar ciclo automático
            asyncio.create_task(self.start_auto_emote_cycle())
            await self.highrise.chat(f"🎭 ¡Modo automático activado!\n📊 Ciclo de {len(emotes)} emotes iniciado")
            safe_print(f"🎭 Modo automático activado por {username}")
            return

        # Comando !trago @user
        if msg.startswith("!trago"):
            parts = msg.split()
            if len(parts) >= 2:
                target_username = parts[1].replace("@", "")
                import random
                bebida = random.choice(self.bebidas)
                await self.highrise.chat(f"🍹 Para @{target_username}: {bebida}. ¡Salud! 🥂")
                safe_print(f"🍹 Bebida servida a {target_username}: {bebida}")
            else:
                await self.highrise.chat("❌ Usa: !trago @usuario")
            return

        # Detectar mención @CANTINERO_BOT
        if "@CANTINERO_BOT" in msg or "@cantinero" in msg.lower():
            # Verificar si el usuario ya llamó (excepto admin/owner)
            if not is_admin_or_owner and user_id in self.users_called:
                # Mostrar mensaje de bloqueo solo la primera vez
                if user_id not in self.users_blocked_notified:
                    await self.highrise.chat(f"📞 @{username} te ha bloqueado de sus contactos 🚫")
                    self.users_blocked_notified.add(user_id)
                    safe_print(f"🚫 {username} intentó llamar nuevamente - Mensaje de bloqueo enviado")
                return

            # Agregar usuario a la lista de llamadas (solo si no es admin/owner)
            if not is_admin_or_owner:
                self.users_called.add(user_id)

            # Iniciar llamada extendida
            self.is_in_call = True
            self.call_partner = username

            # Fase 1: Contestar teléfono
            await asyncio.sleep(0.5)
            await self.highrise.chat(f"📞 *suena el teléfono* ¡Un momento!")

            # Fase 2: Detener floss y atender
            await asyncio.sleep(2)
            await self.highrise.send_emote("emote-telekinesis")
            await asyncio.sleep(1)
            await self.highrise.chat(f"📞 *contesta* ¿Sí? Habla @{username}, ¿en qué te puedo servir?")

            # Fase 3: Conversación
            await asyncio.sleep(4)
            await self.highrise.chat("🤔 Ajá... entiendo, entiendo...")

            await asyncio.sleep(3)
            await self.highrise.chat("😊 ¡Claro que sí! Con gusto te atiendo.")

            # Fase 4: Despedida
            await asyncio.sleep(3)
            await self.highrise.chat(f"📞 Perfecto @{username}, ya voy para allá. *cuelga*")

            await asyncio.sleep(2)
            await self.highrise.chat("¡Que tengas excelente día! 🍻✨")

            # Finalizar llamada
            self.is_in_call = False
            self.call_partner = None

            safe_print(f"📞 Llamada completada con {username} (Admin/Owner: {is_admin_or_owner})")

    async def on_user_join(self, user: User, position: Union[Position, AnchorPosition]) -> None:
        """Saluda a los usuarios cuando entran a la sala con reintentos"""
        greeting = "Bienvenido a🕷️NOCTURNO 🕷️. El velo se ha abierto solo para ti. Tu presencia es una nueva sombra en nuestra oscuridad."
        max_attempts = 3
        
        for attempt in range(1, max_attempts + 1):
            try:
                await asyncio.sleep(0.5 * attempt)  # Delay incremental para evitar rate limiting
                await self.highrise.send_whisper(user.id, greeting)
                safe_print(f"✅ Saludo cantinero enviado a {user.username} (intento {attempt})")
                break  # Éxito, salir del loop
            except Exception as e:
                if attempt < max_attempts:
                    safe_print(f"⚠️ Cantinero intento {attempt} fallido para {user.username}: {e}. Reintentando...")
                else:
                    safe_print(f"❌ Cantinero no pudo saludar a {user.username} después de {max_attempts} intentos: {e}")

    