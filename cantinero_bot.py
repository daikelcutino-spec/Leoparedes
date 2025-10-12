from keep_alive import keep_alive
keep_alive()
from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata
import random
import asyncio
from typing import Union

class BartenderBot(BaseBot):
    """Bot Cantinero NOCTURNO para Highrise - Temática oscura y misteriosa"""
    
    def __init__(self):
        super().__init__()
        
        self.owner_id = "662aae9b602b4a897557ec18"
        self.admin_id = "669da7b73867bac51391c757"
        
        self.bot_position = None
        
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
        
        self.bartender_phrases = [
            "¡Aquí tienes! 🍺",
            "¡Salud! 🥂",
            "¡Disfrútalo! 😊",
            "¡Que lo disfrutes! 🎉",
            "¡Servido con cariño! ❤️",
            "¡La casa invita! 🎁"
        ]
        
        self.auto_messages = [
            "‼️¿Sugerencias o incomodidades? Contacta a un miembro superior de la sala: envía un mensaje a @Alber_JG_69 o a @baby__lax. ¡Estamos para ayudarte!‼️",
            "¡Consigue tu VIP Permanente!💎 Para ser un miembro eterno de 🕷️ NOCTURNO 🕷️, Mándale 100 de oro al bot: @NOCTURNO_BOT. ¡Gracias por apoyar la oscuridad!",
            "Acércate a la barra.🥃 Estoy para servirle. ¿Qué deseas hoy?🍻"
        ]
        self.current_message_index = 0

    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Se ejecuta cuando el bot se conecta a la sala"""
        print("🕷️ Bot NOCTURNO iniciado y listo para servir!")
        
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

    async def on_chat(self, user: User, message: str) -> None:
        """Maneja los mensajes del chat"""
        message_lower = message.lower().strip()
        
        if message_lower.startswith("!"):
            await self.handle_command(user, message_lower)
        elif any(drink.replace("🍺 ", "").replace("🍷 ", "").replace("🍸 ", "").replace("🍹 ", "").replace("🥃 ", "").replace("🍾 ", "").replace("☕ ", "").replace("🥤 ", "").replace("🧃 ", "").replace("💧 ", "").replace("🍵 ", "").replace("🥛 ", "").replace("🧋 ", "") in message_lower for drink in list(self.menu["alcoholic"].keys()) + list(self.menu["non_alcoholic"].keys())):
            await self.serve_drink_from_message(user, message_lower)

    async def handle_command(self, user: User, message: str) -> None:
        """Maneja los comandos del bot"""
        parts = message.split()
        command = parts[0]
        
        if command == "!menu":
            await self.show_menu(user)
        
        elif command == "!bebida" or command == "!drink":
            if len(parts) > 1:
                drink_name = " ".join(parts[1:])
                await self.serve_drink(user, drink_name)
            else:
                await self.highrise.send_whisper(user.id, "Dime qué bebida quieres! Ej: !bebida cerveza")
        
        elif command == "!ayuda" or command == "!help":
            await self.show_help(user)
        
        elif command == "!broma" or command == "!joke":
            await self.tell_joke(user)
        
        elif command == "!cantinero":
            await self.highrise.send_whisper(user.id, "¡Sí! ¿Qué necesitas? 🍺")
        
        elif command == "!salud" or command == "!cheers":
            await self.highrise.send_whisper(user.id, f"¡Salud @{user.username}! 🥂 ¡Por la amistad!")
        
        elif command == "!copy":
            await self.copy_outfit(user)
        
        elif command == "!inicio":
            await self.set_bot_position(user)
        
        elif command == "!recomendacion" or command == "!recomienda":
            await self.recommend_drink(user)
        
        elif command == "!especial":
            await self.daily_special(user)
        
        elif command == "!brindis":
            await self.make_toast(user)
        
        elif command == "!trivia":
            await self.bar_trivia(user)
        
        elif command == "!barinfo":
            await self.bar_info(user)
        
        elif command == "!shots":
            await self.shot_challenge(user)
        
        elif command == "!mezclar":
            await self.mix_drink(user)
        
        elif command == "!ruleta":
            await self.drink_roulette(user)
        
        elif command == "!cuenta" or command == "!tab":
            await self.user_tab(user)
        
        elif command == "!invitar":
            if len(parts) > 1:
                await self.invite_drink(user, parts[1])
            else:
                await self.highrise.send_whisper(user.id, "Usa: !invitar @usuario")
        
        elif command == "!propina" or command == "!tip":
            await self.give_tip(user)

    async def show_menu(self, user: User) -> None:
        """Muestra el menú de bebidas en whisper"""
        menu_text = "🕷️ === MENÚ DEL BAR NOCTURNO === 🕷️\n\n"
        menu_text += "🍺 BEBIDAS ALCOHÓLICAS:\n"
        for drink in self.menu["alcoholic"].keys():
            menu_text += f"  • {drink}\n"
        
        menu_text += "\n🥤 BEBIDAS SIN ALCOHOL:\n"
        for drink in self.menu["non_alcoholic"].keys():
            menu_text += f"  • {drink}\n"
        
        menu_text += "\nPide con: !bebida [nombre] o solo di el nombre de la bebida!"
        await self.highrise.send_whisper(user.id, menu_text)

    async def show_help(self, user: User) -> None:
        """Muestra la ayuda del bot en whisper"""
        help_text = """🕷️ === COMANDOS DEL CANTINERO NOCTURNO === 🕷️

🍺 BEBIDAS:
!menu - Ver todas las bebidas
!bebida [nombre] - Pedir bebida
!recomendacion - Sugerencia del cantinero
!especial - Ver especial del día
!mezclar - Crear bebida personalizada
!ruleta - Bebida sorpresa al azar

🎉 DIVERSIÓN:
!broma - Chiste del cantinero
!trivia - Datos curiosos sobre bebidas
!shots - Reto de shots
!brindis - Hacer un brindis público

💰 SOCIAL:
!salud - Hacer un brindis personal
!invitar @user - Invitar bebida a alguien
!cuenta - Ver tu consumo del día
!propina - Dar propina al cantinero
!barinfo - Info sobre el bar

🔧 UTILIDAD:
!ayuda - Mostrar esta ayuda

💡 También puedes pedir bebidas directamente:
Ejemplo: "quiero una cerveza" """
        await self.highrise.send_whisper(user.id, help_text)

    async def serve_drink(self, user: User, drink_name: str) -> None:
        """Sirve una bebida al usuario en whisper"""
        drink_name = drink_name.lower().strip()
        
        for drink, description in {**self.menu["alcoholic"], **self.menu["non_alcoholic"]}.items():
            if drink_name in drink.lower():
                phrase = random.choice(self.bartender_phrases)
                await self.highrise.send_whisper(user.id, f"{phrase} {drink}\n{description}")
                print(f"🍺 Servido {drink} a {user.username}")
                return
        
        await self.highrise.send_whisper(user.id, f"Lo siento, no tengo esa bebida. Usa !menu para ver el menú 📋")

    async def serve_drink_from_message(self, user: User, message: str) -> None:
        """Detecta y sirve bebidas mencionadas en mensajes normales"""
        for drink in list(self.menu["alcoholic"].keys()) + list(self.menu["non_alcoholic"].keys()):
            drink_clean = drink.split()[-1].lower()
            if drink_clean in message:
                await self.serve_drink(user, drink_clean)
                return

    async def tell_joke(self, user: User) -> None:
        """Cuenta un chiste en whisper"""
        jokes = [
            "¿Qué le dice un tequila a otro? ¿Tequila o te mata? 😂",
            "¿Por qué el café fue al psicólogo? Porque tenía muchos problemas sin filtrar! ☕",
            "¿Qué le dice una cerveza a otra? ¡Nos vemos en el bar! 🍺",
            "¿Cuál es el colmo de un cantinero? Servir a la mesa sin estar casado! 🤣",
            "¿Por qué el vino no puede guardar secretos? Porque siempre se va de la lengua! 🍷",
            "Un cliente entra al bar con un cocodrilo. El cantinero dice: ¡Hey! ¿Sirves bebidas aquí? 🐊",
            "En el bar nocturno, hasta las sombras piden un trago 🌙🍸"
        ]
        joke = random.choice(jokes)
        await self.highrise.send_whisper(user.id, joke)
    
    async def copy_outfit(self, user: User) -> None:
        """Copia el outfit del usuario - Solo admin y propietario"""
        if user.id != self.owner_id and user.id != self.admin_id:
            await self.highrise.send_whisper(user.id, "❌ Solo el propietario o admin pueden usar este comando.")
            return
        
        try:
            response = await self.highrise.get_user_outfit(user.id)
            user_outfit = response.outfit
            
            await self.highrise.set_outfit(user_outfit)
            await self.highrise.send_whisper(user.id, f"✅ ¡Outfit copiado exitosamente de {user.username}!")
            print(f"👔 Outfit copiado de {user.username}")
        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Error al copiar outfit: {e}")
            print(f"Error copiando outfit: {e}")
    
    async def set_bot_position(self, user: User) -> None:
        """Establece la posición inicial del bot - Solo admin y propietario"""
        if user.id != self.owner_id and user.id != self.admin_id:
            await self.highrise.send_whisper(user.id, "❌ Solo el propietario o admin pueden usar este comando.")
            return
        
        try:
            response = await self.highrise.get_room_users()
            
            for room_user, pos in response.content:
                if room_user.id == user.id:
                    self.bot_position = pos
                    await self.highrise.walk_to(pos)
                    await self.highrise.send_whisper(user.id, f"✅ Posición inicial establecida en: {pos}")
                    print(f"📍 Posición del bot establecida: {pos}")
                    return
            
            await self.highrise.send_whisper(user.id, "❌ No se pudo obtener tu posición")
        except Exception as e:
            await self.highrise.send_whisper(user.id, f"❌ Error al establecer posición: {e}")
            print(f"Error estableciendo posición: {e}")
    
    async def shot_challenge(self, user: User) -> None:
        """Reto de shots"""
        shots = ["🥃 Tequila", "🥃 Vodka", "🥃 Ron", "🥃 Whisky"]
        shot = random.choice(shots)
        challenges = [
            f"🔥 RETO: 3 {shot} seguidos! ¿Te atreves?",
            f"💪 DESAFÍO: {shot} doble shot! ¡Sin hacer cara!",
            f"⚡ CHALLENGE: {shot} al estilo NOCTURNO... ¡sin respirar!",
            f"🎯 PRUEBA: {shot} mientras bailas floss!"
        ]
        await self.highrise.send_whisper(user.id, random.choice(challenges))
        await self.highrise.chat(f"🔥 @{user.username} acepta el reto de shots!")
    
    async def recommend_drink(self, user: User) -> None:
        """Recomienda una bebida al azar"""
        all_drinks = list(self.menu["alcoholic"].keys()) + list(self.menu["non_alcoholic"].keys())
        drink = random.choice(all_drinks)
        description = self.menu["alcoholic"].get(drink) or self.menu["non_alcoholic"].get(drink)
        recommendation = f"🍸 Te recomiendo {drink}\n{description}\n\n¿Te la sirvo?"
        await self.highrise.send_whisper(user.id, recommendation)
    
    async def daily_special(self, user: User) -> None:
        """Muestra el especial del día"""
        specials = [
            "🍷 HOY: Sangría NOCTURNA - Vino tinto con frutas de la oscuridad 🌙",
            "🍹 ESPECIAL: Cóctel Eclipse - Mezcla misteriosa de licores exóticos 🌑",
            "🥃 DEL DÍA: Whisky Sombra - Añejado en barriles de roble negro 🕷️",
            "🍸 PROMOCIÓN: Martini Lunático - Con un toque de misterio 🌒",
            "🍺 OFERTA: Cerveza de la Medianoche - Oscura y refrescante 🦇"
        ]
        await self.highrise.send_whisper(user.id, random.choice(specials))
    
    async def mix_drink(self, user: User) -> None:
        """Crea una bebida personalizada mezclando ingredientes"""
        ingredients = ["limón", "menta", "jengibre", "canela", "vainilla", "chocolate", "fresa", "mango"]
        bases = ["vodka", "ron", "tequila", "jugo", "té", "café"]
        
        ingredient1 = random.choice(ingredients)
        ingredient2 = random.choice([i for i in ingredients if i != ingredient1])
        base = random.choice(bases)
        
        custom_drink = f"🍹 MEZCLA NOCTURNA:\n✨ Base de {base}\n🌿 Con {ingredient1} y {ingredient2}\n\n¡Tu bebida personalizada está lista!"
        await self.highrise.send_whisper(user.id, custom_drink)
    
    async def make_toast(self, user: User) -> None:
        """Hace un brindis especial"""
        toasts = [
            "🥂 ¡Por las noches eternas y las amistades que nacen en la oscuridad!",
            "🍷 ¡Brindemos por los misterios sin resolver y las aventuras por vivir!",
            "🍺 ¡Salud por los que están y los que vendrán al NOCTURNO!",
            "🍸 ¡Por las sombras que nos protegen y la luna que nos guía!",
            "🥃 ¡Por cada alma valiente que se adentra en la oscuridad del bar!",
            "🍾 ¡Brindis por la noche, nuestra eterna compañera!"
        ]
        toast = random.choice(toasts)
        await self.highrise.send_whisper(user.id, f"{toast} 🎉")
        await self.highrise.chat(f"🥂 Brindis NOCTURNO: {toast}")
    
    async def bar_trivia(self, user: User) -> None:
        """Comparte datos curiosos sobre bebidas"""
        trivias = [
            "💡 ¿Sabías que? El cóctel más antiguo registrado es el 'Sazerac', de Nueva Orleans (1838)",
            "💡 Dato curioso: El champagne tiene aproximadamente 49 millones de burbujas por botella 🍾",
            "💡 Curiosidad: El whisky más caro del mundo se vendió por $1.9 millones 🥃",
            "💡 ¿Sabías que? La palabra 'cocktail' apareció por primera vez en 1806 🍸",
            "💡 Dato interesante: El café es la segunda bebida más consumida después del agua ☕",
            "💡 Trivia: En la Edad Media, el agua era peligrosa, así que todos bebían cerveza... ¡hasta los niños! 🍺"
        ]
        await self.highrise.send_whisper(user.id, random.choice(trivias))
    
    async def bar_info(self, user: User) -> None:
        """Información sobre el bar NOCTURNO"""
        info = """🕷️ === BAR NOCTURNO === 🕷️

📍 Ubicación: En el corazón de la oscuridad
🕐 Horario: Siempre abierto (24/7)
🎭 Ambiente: Místico y acogedor
👔 Código de vestimenta: La oscuridad te acepta tal como eres

🍺 Especialidad: Bebidas con alma
🎵 Música: Ecos de la medianoche
✨ Magia: En cada trago servido

¡Bienvenido a tu refugio en las sombras!"""
        await self.highrise.send_whisper(user.id, info)
    
    async def drink_roulette(self, user: User) -> None:
        """Ruleta de bebidas - bebida sorpresa al azar"""
        all_drinks = list(self.menu["alcoholic"].keys()) + list(self.menu["non_alcoholic"].keys())
        drink = random.choice(all_drinks)
        description = self.menu["alcoholic"].get(drink) or self.menu["non_alcoholic"].get(drink)
        
        await self.highrise.send_whisper(user.id, f"🎰 RULETA NOCTURNA GIRÓ...\n🍸 Tu bebida sorpresa: {drink}\n{description}")
        await self.highrise.chat(f"🎰 @{user.username} probó suerte en la ruleta!")
    
    async def user_tab(self, user: User) -> None:
        """Muestra la cuenta ficticia del usuario"""
        drinks_count = random.randint(1, 8)
        total = drinks_count * random.randint(5, 15)
        
        tab_info = f"🧾 TU CUENTA NOCTURNA:\n🍺 Bebidas consumidas: {drinks_count}\n💰 Total: {total} monedas\n\n🎁 Primera ronda: ¡Cortesía de la casa!"
        await self.highrise.send_whisper(user.id, tab_info)
    
    async def invite_drink(self, user: User, target_username: str) -> None:
        """Invita una bebida a otro usuario"""
        target_username = target_username.replace("@", "")
        drink = random.choice(list(self.menu["alcoholic"].keys()) + list(self.menu["non_alcoholic"].keys()))
        
        await self.highrise.chat(f"🎁 @{user.username} invita {drink} a @{target_username}! 🥂")
        await self.highrise.send_whisper(user.id, f"✅ Has invitado {drink} a @{target_username}")
    
    async def give_tip(self, user: User) -> None:
        """Recibe propina del usuario (simbólica)"""
        tips = [
            f"🙏 Gracias por la propina @{user.username}! Eres muy generoso 💰",
            f"⭐ Wow! Gracias @{user.username}! El servicio siempre será mejor para ti 🍺",
            f"❤️ Aprecio tu gesto @{user.username}! La próxima bebida tiene descuento 🎁",
            f"🎉 Muchas gracias @{user.username}! Eres cliente VIP del bar 👑"
        ]
        response = random.choice(tips)
        await self.highrise.send_whisper(user.id, response)
        await self.highrise.chat(f"💝 @{user.username} dejó propina al cantinero!")