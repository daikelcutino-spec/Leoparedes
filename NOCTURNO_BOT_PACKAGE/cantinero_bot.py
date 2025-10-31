
from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata
import asyncio
from typing import Union
from datetime import datetime

class BartenderBot(BaseBot):
    """Bot Cantinero NOCTURNO - Floss continuo y mensajes automáticos"""

    def __init__(self):
        super().__init__()
        self.current_message_index = 0

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
        print("🕷️ Bot Cantinero NOCTURNO iniciado!")
        
        # Teletransportar al punto de inicio si está configurado
        try:
            import json
            with open("cantinero_config.json", "r", encoding="utf-8") as f:
                config = json.load(f)
            
            punto_inicio = config.get("punto_inicio")
            if punto_inicio:
                from highrise import Position
                spawn_position = Position(punto_inicio["x"], punto_inicio["y"], punto_inicio["z"])
                await self.highrise.teleport(session_metadata.user_id, spawn_position)
                print(f"📍 Bot cantinero teletransportado al punto de inicio: X={punto_inicio['x']}, Y={punto_inicio['y']}, Z={punto_inicio['z']}")
        except Exception as e:
            print(f"⚠️ No se pudo teletransportar al punto de inicio: {e}")

        asyncio.create_task(self.floss_loop())
        asyncio.create_task(self.auto_message_loop())

    async def floss_loop(self) -> None:
        """Loop infinito que ejecuta el emote floss continuamente"""
        await asyncio.sleep(2)

        while True:
            try:
                await self.highrise.send_emote("dance-floss")
                print("💃 Ejecutando emote floss")
                # Esperar 12 segundos para que el floss se complete totalmente
                await asyncio.sleep(12)
            except Exception as e:
                print(f"Error al enviar emote floss: {e}")
                await asyncio.sleep(1)

    async def auto_message_loop(self) -> None:
        """Loop que envía mensajes automáticos públicos cada 2 minutos"""
        await asyncio.sleep(120)

        while True:
            try:
                auto_messages = self.get_auto_messages()
                message = auto_messages[self.current_message_index]

                # Enviar mensaje público en el chat
                await self.highrise.chat(message)
                
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
