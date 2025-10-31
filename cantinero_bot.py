
from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata, Error
import asyncio
from typing import Union
from datetime import datetime
import sys

class BartenderBot(BaseBot):
    """Bot Cantinero NOCTURNO - Floss continuo y mensajes automáticos"""

    def __init__(self):
        super().__init__()
        self.current_message_index = 0
        self.bot_id = None
        self.is_in_call = False
        self.call_partner = None

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
            "‼️¿Sugerencias o incomodidades? Contacta a un miembro superior de la sala: envía un mensaje a @Alber_JG_69 o a @baby__lax. ¡Estamos para ayudarte!‼️",
            "¡Consigue tu VIP Permanente!💎 Para ser un miembro eterno de 🕷️ NOCTURNO 🕷️, Mándale 100 de oro al bot: @NOCTURNO_BOT. ¡Gracias por apoyar la oscuridad!",
            "👉🏼PIDE TU CANCIÓN FAVORITA EN LA JARRITA DE TIP👈🏼",
            "Acércate a la barra.🥃 Estoy para servirle. ¿Qué deseas hoy?🍻"
        ]

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Se ejecuta cuando el bot se conecta a la sala"""
        self.bot_id = session_metadata.user_id
        print(f"🕷️ Bot Cantinero NOCTURNO iniciado! ID: {self.bot_id}")
        
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
                print(f"📍 Bot cantinero teletransportado al punto de inicio: X={punto_inicio['x']}, Y={punto_inicio['y']}, Z={punto_inicio['z']}")
        except Exception as e:
            print(f"⚠️ No se pudo teletransportar al punto de inicio: {e}")

        asyncio.create_task(self.floss_loop())
        asyncio.create_task(self.auto_message_loop())
        asyncio.create_task(self.auto_reconnect_loop())

    async def floss_loop(self) -> None:
        """Loop infinito que ejecuta el emote floss continuamente"""
        await asyncio.sleep(2)

        while True:
            try:
                if not self.is_in_call:
                    await self.highrise.send_emote("dance-floss")
                    print("💃 Ejecutando emote floss")
                await asyncio.sleep(12)
            except Exception as e:
                print(f"⚠️ Error al enviar emote floss: {e}")
                await asyncio.sleep(5)

    async def auto_message_loop(self) -> None:
        """Loop que envía mensajes automáticos públicos cada 2 minutos"""
        await asyncio.sleep(120)

        while True:
            try:
                auto_messages = self.get_auto_messages()
                message = auto_messages[self.current_message_index]

                # Enviar mensaje público en el chat
                await self.highrise.chat(message)


    async def auto_reconnect_loop(self):
        """Sistema de reconexión automática"""
        while True:
            try:
                await asyncio.sleep(30)
                
                # Verificar si el bot está en la sala
                try:
                    room_users = await self.highrise.get_room_users()
                    if isinstance(room_users, Error):
                        raise Exception("Error obteniendo usuarios de la sala")
                    
                    users = room_users.content
                    bot_in_room = any(u.id == self.bot_id for u, _ in users)
                    
                    if not bot_in_room:
                        print("⚠️ Bot cantinero desconectado de la sala, reconectando...")
                        await self.attempt_reconnection()
                        
                except Exception as e:
                    print(f"❌ Error verificando presencia del bot cantinero: {e}")
                    await self.attempt_reconnection()
                    
            except Exception as e:
                print(f"❌ Error en auto_reconnect_loop: {e}")
                await asyncio.sleep(5)

    async def attempt_reconnection(self):
        """Intenta reconectar el bot cantinero"""
        max_attempts = 5
        for attempt in range(1, max_attempts + 1):
            try:
                print(f"🔄 Intento de reconexión {attempt}/{max_attempts}...")
                
                await asyncio.sleep(attempt * 2)
                
                room_users = await self.highrise.get_room_users()
                if not isinstance(room_users, Error):
                    print("✅ Reconexión exitosa del bot cantinero!")
                    
                    # Reiniciar tareas
                    asyncio.create_task(self.floss_loop())
                    asyncio.create_task(self.auto_message_loop())
                    
                    return True
                    
            except Exception as e:
                print(f"❌ Fallo en intento {attempt}: {e}")
                
        print("❌ No se pudo reconectar después de varios intentos")
        return False

    async def on_chat(self, user: User, message: str) -> None:
        """Detectar cuando mencionan al bot cantinero"""
        msg = message.strip()
        
        # Detectar mención @CANTINERO_BOT
        if "@CANTINERO_BOT" in msg or "@cantinero" in msg.lower():
            # Notificar que recibió la llamada
            await asyncio.sleep(0.5)
            await self.highrise.chat("📞 *contesta el teléfono* ¿Sí? Dime, ¿en qué te puedo servir?")
            self.is_in_call = True
            self.call_partner = user.username
            
            # Detener floss durante la llamada
            await asyncio.sleep(3)
            await self.highrise.send_emote("emote-telekinesis")
            
            # Finalizar llamada después de 10 segundos
            await asyncio.sleep(10)
            await self.highrise.chat("📞 *cuelga* ¡Que tengas buen día! 🍻")
            self.is_in_call = False
            self.call_partner = None

                
                self.current_message_index = (self.current_message_index + 1) % len(auto_messages)
                print(f"📢 Mensaje automático público enviado: {message[:50]}...")
            except Exception as e:
                print(f"Error en auto_message_loop: {e}")

            # Esperar 2 minutos (120 segundos) para el siguiente mensaje
            await asyncio.sleep(120)

    async def on_user_join(self, user: User, position: Union[Position, AnchorPosition]) -> None:
        """Saluda a los usuarios cuando entran a la sala"""
        greeting = "Bienvenido a🕷️NOCTURNO 🕷️. El velo se ha abierto solo para ti. Tu presencia es una nueva sombra en nuestra oscuridad."
        try:
            await self.highrise.send_whisper(user.id, greeting)
            print(f"✅ Saludo enviado a {user.username}")
        except Exception as e:
            print(f"Error al saludar a {user.username}: {e}")
