from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata
import asyncio

class CantineroBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.bot_id = None
        self.floss_task = None
        
    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Inicialización del bot cantinero"""
        print("🍷 Bot Cantinero iniciando...")
        self.bot_id = session_metadata.user_id
        
        await asyncio.sleep(2)
        
        print("🕺 Iniciando emote floss continuo...")
        self.floss_task = asyncio.create_task(self.floss_continuo())
        
        print("🍷 ¡Bot Cantinero listo para servir!")
    
    async def floss_continuo(self):
        """Ejecuta el emote floss continuamente sin parar"""
        while True:
            try:
                await self.highrise.send_emote("emote-floss", self.bot_id)
                await asyncio.sleep(4)
            except Exception as e:
                print(f"Error en floss: {e}")
                await asyncio.sleep(5)
    
    async def on_user_join(self, user: User, position: Position | AnchorPosition) -> None:
        """Mensaje de bienvenida personalizado"""
        try:
            mensaje_bienvenida = (
                "Bienvenido a🕷️NOCTURNO 🕷️. "
                "El velo se ha abierto solo para ti. "
                "Tu presencia es una nueva sombra en nuestra oscuridad."
            )
            await self.highrise.send_whisper(user.id, mensaje_bienvenida)
            print(f"👤 {user.username} entró a la sala")
        except Exception as e:
            print(f"Error al enviar bienvenida: {e}")
    
    async def on_chat(self, user: User, message: str) -> None:
        """Comandos del cantinero"""
        msg = message.lower().strip()
        
        if msg == "!menu" or msg == "!carta":
            await self.mostrar_menu(user)
        elif msg.startswith("!servir"):
            await self.servir_bebida(user, message)
        elif msg == "!cantinero":
            await self.highrise.chat(f"🍷 A tus órdenes @{user.username}. Usa !menu para ver la carta")
    
    async def mostrar_menu(self, user: User):
        """Muestra el menú de bebidas"""
        menu = [
            "🍷 === CARTA DEL CANTINERO === 🍷",
            "",
            "🍺 Cerveza - !servir cerveza",
            "🍷 Vino - !servir vino",
            "🥃 Whisky - !servir whisky",
            "🍹 Cóctel - !servir coctel",
            "🍾 Champagne - !servir champagne",
            "☕ Café - !servir cafe",
            "🥤 Refresco - !servir refresco",
            "",
            "🕷️ Bebidas especiales NOCTURNO:",
            "🖤 Sombra Líquida - !servir sombra",
            "🦇 Sangre de Murciélago - !servir sangre",
            "🌑 Eclipse Negro - !servir eclipse"
        ]
        
        for linea in menu:
            await self.highrise.send_whisper(user.id, linea)
    
    async def servir_bebida(self, user: User, mensaje: str):
        """Sirve la bebida solicitada"""
        bebida = mensaje[7:].strip().lower()
        
        bebidas = {
            "cerveza": "🍺 Aquí tienes una cerveza bien fría, @{user}! Salud! 🍻",
            "vino": "🍷 Un excelente vino tinto para ti, @{user}. ¡Buen provecho!",
            "whisky": "🥃 Whisky en las rocas para @{user}. Con clase! 🎩",
            "coctel": "🍹 Un cóctel especial de la casa para @{user}! 🌟",
            "champagne": "🍾 Champagne! Algo que celebrar, @{user}? 🎉",
            "cafe": "☕ Café recién hecho para @{user}. ¡Energía pura! ⚡",
            "refresco": "🥤 Refresco bien frío para @{user}! 🧊",
            "sombra": "🖤 Sombra Líquida... la especialidad NOCTURNO para @{user}. Oscuro y misterioso... 🕷️",
            "sangre": "🦇 Sangre de Murciélago para @{user}... dulce con un toque salvaje 🌙",
            "eclipse": "🌑 Eclipse Negro... la bebida más oscura para @{user}. Solo para los más valientes 🕸️"
        }
        
        if bebida in bebidas:
            respuesta = bebidas[bebida].replace("{user}", user.username)
            await self.highrise.chat(respuesta)
        elif bebida == "":
            await self.highrise.send_whisper(user.id, "¿Qué bebida deseas? Usa !menu para ver la carta")
        else:
            await self.highrise.send_whisper(user.id, f"No tengo '{bebida}' en la carta. Usa !menu para ver opciones")

if __name__ == "__main__":
    import sys
    
    print("🍷 Iniciando Bot Cantinero NOCTURNO...")
    print("🕺 Emote floss continuo activado")
    print("🕷️ Listo para servir en la oscuridad...")
    print("=" * 50)
    
    bot = CantineroBot()
    print("🔧 Bot Cantinero inicializado. Esperando conexión...")
