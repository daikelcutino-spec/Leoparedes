from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata
import asyncio
from typing import Union

class BartenderBot(BaseBot):
    """Bot Cantinero NOCTURNO - Solo mensajes automáticos"""

    def __init__(self):
        super().__init__()

        self.auto_messages = [
            "‼️¿Sugerencias o incomodidades? Contacta a un miembro superior de la sala: envía un mensaje a @Alber_JG_69 o a @baby__lax. ¡Estamos para ayudarte!‼️",
            "¡Consigue tu VIP Permanente!💎 Para ser un miembro eterno de 🕷️ NOCTURNO 🕷️, Mándale 100 de oro al bot: @NOCTURNO_BOT. ¡Gracias por apoyar la oscuridad!",
            "Acércate a la barra.🥃 Estoy para servirle. ¿Qué deseas hoy?🍻"
        ]
        self.current_message_index = 0

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Se ejecuta cuando el bot se conecta a la sala"""
        print("🕷️ Bot Cantinero NOCTURNO iniciado!")

        asyncio.create_task(self.floss_loop())
        asyncio.create_task(self.auto_message_loop())

    async def floss_loop(self) -> None:
        """Loop infinito que ejecuta el emote floss de forma continua"""
        await asyncio.sleep(2)

        while True:
            try:
                await self.highrise.send_emote("dance-floss")
                print("💃 Ejecutando emote floss continuo")
            except Exception as e:
                print(f"Error al enviar emote floss: {e}")

            await asyncio.sleep(22)

    async def auto_message_loop(self) -> None:
        """Loop que envía mensajes automáticos cada 4 minutos (alternando con bot NOCTURNO cada 2 min)"""
        # Esperar 2 minutos (120 segundos) para alternar con el bot NOCTURNO
        await asyncio.sleep(120)

        while True:
            try:
                response = await self.highrise.get_room_users()

                message = self.auto_messages[self.current_message_index]

                for room_user, _ in response.content:
                    if room_user.username.lower() == "cantinero_bot" or room_user.username.lower() == "nocturno_bot":
                        continue
                    try:
                        await self.highrise.send_whisper(room_user.id, message)
                    except Exception as e:
                        print(f"Error enviando whisper a {room_user.username}: {e}")

                self.current_message_index = (self.current_message_index + 1) % len(self.auto_messages)

                print(f"📢 Mensaje automático enviado a todos los usuarios")
            except Exception as e:
                print(f"Error en auto_message_loop: {e}")

            # Esperar 4 minutos (240 segundos) para el siguiente mensaje
            await asyncio.sleep(240)

    async def on_user_join(self, user: User, position: Union[Position, AnchorPosition]) -> None:
        """Saluda a los usuarios cuando entran a la sala"""
        greeting = "Bienvenido a🕷️NOCTURNO 🕷️. El velo se ha abierto solo para ti. Tu presencia es una nueva sombra en nuestra oscuridad."
        try:
            await self.highrise.send_whisper(user.id, greeting)
            print(f"✅ Saludo enviado a {user.username}")
        except Exception as e:
            print(f"Error al saludar a {user.username}: {e}")