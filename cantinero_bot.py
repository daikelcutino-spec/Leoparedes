
from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata
import random
import asyncio
from typing import Union

class BartenderBot(BaseBot):
    """Bot Cantinero NOCTURNO para Highrise - Temática oscura y misteriosa"""
    
    def __init__(self):
        super().__init__()
        
        # IDs de propietario y admin
        self.owner_id = "662aae9b602b4a897557ec18"
        self.admin_id = "669da7b73867bac51391c757"
        
        # Posición del bot
        self.bot_position = None
        
        # Menú de bebidas
        self.menu = {
            "alcoholic": {
                "🍺 cerveza": "Una cerveza bien fría, perfecta para refrescarte!",
                "🍷 vino": "Un exquisito vino tinto de la casa",
                "🍸 martini": "Un martini clásico, agitado no revuelto",
                "🍹 margarita": "Una refrescante margarita con sal en el borde",
                "🥃 whisky": "Whisky añejo, para los conocedores",
                "🍾 champagne": "Champagne para celebrar!",
                "🍺 tequila": "Un shot de tequila con limón y sal",
                "🍷 ron": "Ron añejo de las profundidades",
                "🥃 vodka": "Vodka cristalino de las sombras"
            },
            "non_alcoholic": {
                "☕ café": "Café recién hecho, aromático y caliente",
                "🥤 refresco": "Refresco bien frío de tu sabor favorito",
                "🧃 jugo": "Jugo natural recién exprimido",
                "💧 agua": "Agua fresca y pura",
                "🍵 té": "Té caliente con miel",
                "🥛 batido": "Batido cremoso de frutas",
                "🧋 bubble tea": "Bubble tea con perlas de tapioca"
            }
        }
        
        # Chistes del cantinero
        self.jokes = [
            "¿Por qué el café estaba triste? ¡Porque estaba molido! ☕😄",
            "¿Qué le dice una cerveza a otra? ¡Nos vemos en el bar! 🍺😂",
            "¿Cuál es el colmo de un bartender? ¡Que le sirvan en bandeja de plata! 🍸🤣",
            "¿Por qué el whisky fue al doctor? ¡Porque tenía muchos grados! 🥃😅",
            "¿Qué hace una taza en el gimnasio? ¡Ejercicios de té! 🍵💪"
        ]
        
        # Mensajes automáticos
        self.auto_messages = [
            "‼️¿Sugerencias o incomodidades? Contacta a un miembro superior de la sala: envía un mensaje a @Alber_JG_69 o a @baby__lax. ¡Estamos para ayudarte!‼️",
            "¡Consigue tu VIP Permanente!💎 Para ser un miembro eterno de 🕷️ NOCTURNO 🕷️, Mándale 100 de oro al bot: @NOCTURNO_BOT. ¡Gracias por apoyar la oscuridad!",
            "Acércate a la barra.🥃 Estoy para servirle. ¿Qué deseas hoy?🍻"
        ]
        self.current_message_index = 0

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Se ejecuta cuando el bot se conecta a la sala"""
        print("🕷️ Bot Cantinero NOCTURNO iniciado y listo para servir!")
        
        # Iniciar loops en segundo plano
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
        """Loop que envía mensajes automáticos cada 1.5 minutos"""
        await asyncio.sleep(10)
        
        while True:
            try:
                response = await self.highrise.get_room_users()
                
                message = self.auto_messages[self.current_message_index]
                
                # Enviar mensaje a todos los usuarios excepto bots
                for room_user, _ in response.content:
                    if "bot" in room_user.username.lower():
                        continue
                    
                    try:
                        await self.highrise.send_whisper(room_user.id, message)
                    except Exception as e:
                        print(f"Error enviando mensaje a {room_user.username}: {e}")
                
                # Avanzar al siguiente mensaje
                self.current_message_index = (self.current_message_index + 1) % len(self.auto_messages)
                
            except Exception as e:
                print(f"Error en auto_message_loop: {e}")
            
            # Esperar 1.5 minutos (90 segundos)
            await asyncio.sleep(90)

    async def on_user_join(self, user: User, position: Union[Position, AnchorPosition]) -> None:
        """Se ejecuta cuando un usuario entra a la sala"""
        welcome_message = "Bienvenido a🕷️NOCTURNO 🕷️. El velo se ha abierto solo para ti. Tu presencia es una nueva sombra en nuestra oscuridad."
        
        try:
            await self.highrise.send_whisper(user.id, welcome_message)
            print(f"👋 Mensaje de bienvenida enviado a {user.username}")
        except Exception as e:
            print(f"Error enviando mensaje de bienvenida: {e}")

    async def on_chat(self, user: User, message: str) -> None:
        """Se ejecuta cuando alguien envía un mensaje en el chat"""
        msg = message.lower().strip()
        
        # Comando !menu
        if msg == "!menu":
            menu_text = "🍷 **MENÚ DEL CANTINERO NOCTURNO** 🍷\n\n"
            menu_text += "🥃 **BEBIDAS ALCOHÓLICAS:**\n"
            for drink in self.menu["alcoholic"].keys():
                menu_text += f"  {drink}\n"
            menu_text += "\n☕ **BEBIDAS SIN ALCOHOL:**\n"
            for drink in self.menu["non_alcoholic"].keys():
                menu_text += f"  {drink}\n"
            menu_text += "\n💡 Escribe !bebida [nombre] para pedir una bebida"
            
            await self.highrise.send_whisper(user.id, menu_text)
            return
        
        # Comando !bebida
        if msg.startswith("!bebida "):
            drink_name = msg.replace("!bebida ", "").strip()
            drink_served = False
            
            # Buscar en bebidas alcohólicas
            for drink, description in self.menu["alcoholic"].items():
                if drink_name in drink.lower():
                    response = f"🍷 Aquí tienes tu {drink}! {description}"
                    await self.highrise.send_whisper(user.id, response)
                    drink_served = True
                    break
            
            # Si no se encontró, buscar en no alcohólicas
            if not drink_served:
                for drink, description in self.menu["non_alcoholic"].items():
                    if drink_name in drink.lower():
                        response = f"☕ Aquí tienes tu {drink}! {description}"
                        await self.highrise.send_whisper(user.id, response)
                        drink_served = True
                        break
            
            if not drink_served:
                await self.highrise.send_whisper(user.id, f"❌ Lo siento, no tengo '{drink_name}'. Usa !menu para ver las opciones.")
            return
        
        # Comando !broma o !joke
        if msg in ["!broma", "!joke"]:
            joke = random.choice(self.jokes)
            await self.highrise.send_whisper(user.id, f"😄 {joke}")
            return
        
        # Comando !salud o !cheers
        if msg in ["!salud", "!cheers"]:
            await self.highrise.send_whisper(user.id, "🥂 ¡Salud! ¡Por las sombras y la oscuridad!")
            return
        
        # Comando !ayuda o !help
        if msg in ["!ayuda", "!help"]:
            help_text = "🕷️ **COMANDOS DEL CANTINERO** 🕷️\n\n"
            help_text += "!menu - Ver el menú de bebidas\n"
            help_text += "!bebida [nombre] - Pedir una bebida\n"
            help_text += "!broma o !joke - Escuchar un chiste\n"
            help_text += "!salud o !cheers - Hacer un brindis\n"
            help_text += "!cantinero - Llamar al cantinero\n"
            help_text += "\n💡 También puedes mencionar una bebida directamente!"
            
            await self.highrise.send_whisper(user.id, help_text)
            return
        
        # Comando !cantinero
        if msg == "!cantinero":
            await self.highrise.send_whisper(user.id, "🍷 ¿En qué puedo servirle? Use !menu para ver las opciones.")
            return
        
        # Comando !copy (Admin/Owner)
        if msg == "!copy":
            if user.id == self.owner_id or user.id == self.admin_id:
                try:
                    outfit_response = await self.highrise.get_user_outfit(user.id)
                    await self.highrise.set_outfit(outfit_response.outfit)
                    await self.highrise.send_whisper(user.id, "✅ Outfit copiado con éxito!")
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error copiando outfit: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Solo admin/owner pueden usar este comando.")
            return
        
        # Comando !inicio (Admin/Owner)
        if msg == "!inicio":
            if user.id == self.owner_id or user.id == self.admin_id:
                try:
                    response = await self.highrise.get_room_users()
                    for room_user, pos in response.content:
                        if room_user.id == user.id:
                            self.bot_position = pos
                            if isinstance(pos, Position):
                                coords = f"X:{pos.x}, Y:{pos.y}, Z:{pos.z}"
                            else:
                                coords = "Anchor position"
                            await self.highrise.send_whisper(user.id, f"✅ Posición de inicio establecida: {coords}")
                            break
                except Exception as e:
                    await self.highrise.send_whisper(user.id, f"❌ Error estableciendo posición: {e}")
            else:
                await self.highrise.send_whisper(user.id, "❌ Solo admin/owner pueden usar este comando.")
            return
        
        # Detección automática de bebidas mencionadas
        for drink_category in self.menu.values():
            for drink, description in drink_category.items():
                drink_clean = drink.split()[1] if len(drink.split()) > 1 else drink
                if drink_clean.lower() in msg:
                    response = f"🍷 Aquí tienes tu {drink}! {description}"
                    await self.highrise.send_whisper(user.id, response)
                    return


if __name__ == "__main__":
    # CONFIGURACIÓN - LLENA ESTOS DATOS
    API_TOKEN = ""  # Tu API token aquí
    ROOM_ID = ""    # Tu Room ID aquí
    
    print("🕷️ Iniciando Bot Cantinero NOCTURNO...")
    print("🔧 Asegúrate de llenar API_TOKEN y ROOM_ID")
