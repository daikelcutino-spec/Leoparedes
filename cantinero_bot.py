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

        # Sistema simplificado de emotes - cargar del main.py
        emotes = {
            "1": {"id": "emote-looping", "name": "fairytwirl"},
            "2": {"id": "idle-floating", "name": "fairyfloat"},
            "3": {"id": "emote-launch", "name": "launch"},
            "4": {"id": "emote-cutesalute", "name": "cutesalute"},
            "5": {"id": "emote-salute", "name": "atattention"},
            "6": {"id": "dance-tiktok11", "name": "tiktok"},
            "7": {"id": "emote-kissing", "name": "smooch"},
            "8": {"id": "dance-employee", "name": "pushit"},
            "9": {"id": "emote-gift", "name": "foryou"},
            "10": {"id": "dance-touch", "name": "touch"},
            "11": {"id": "dance-kawai", "name": "kawaii"},
            "12": {"id": "sit-relaxed", "name": "repose"},
            "13": {"id": "emote-sleigh", "name": "sleigh"},
            "14": {"id": "emote-hyped", "name": "hyped"},
            "15": {"id": "dance-jinglebell", "name": "jingle"},
            "16": {"id": "idle-toilet", "name": "gottago"},
            "17": {"id": "emote-timejump", "name": "timejump"},
            "18": {"id": "idle-wild", "name": "scritchy"},
            "19": {"id": "idle-nervous", "name": "bitnervous"},
            "20": {"id": "emote-iceskating", "name": "iceskating"},
            "140": {"id": "emote-ghost-idle", "name": "ghostfloat"},
            "187": {"id": "emote-dab", "name": "dab"},
            "188": {"id": "dance-gangnamstyle", "name": "gangnamstyle"}
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

    