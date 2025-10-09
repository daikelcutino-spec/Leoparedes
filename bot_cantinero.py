from highrise import BaseBot, User, Position, AnchorPosition
from highrise.models import SessionMetadata, GetUserOutfitRequest, Error
import asyncio
import json

OWNER_ID = "662aae9b602b4a897557ec18"
ADMIN_ID = "669da7b73867bac51391c757"

class CantineroBot(BaseBot):
    def __init__(self):
        super().__init__()
        self.bot_id = None
        self.floss_task = None
        self.mensaje_task = None
        self.punto_inicio = {"x": 9.5, "y": 0.0, "z": 9.5}
        self.load_config()
        
    def load_config(self):
        """Carga la configuración del bot"""
        try:
            with open("cantinero_config.json", "r") as f:
                config = json.load(f)
                self.punto_inicio = config.get("punto_inicio", self.punto_inicio)
                print(f"✅ Configuración cargada desde archivo:")
                print(f"   📍 X={self.punto_inicio['x']}, Y={self.punto_inicio['y']}, Z={self.punto_inicio['z']}")
        except FileNotFoundError:
            print("⚠️ No se encontró cantinero_config.json, creando con valores por defecto")
            self.save_config()
        except Exception as e:
            print(f"❌ Error leyendo configuración: {e}")
            self.save_config()
    
    def save_config(self):
        """Guarda la configuración del bot"""
        try:
            config_data = {"punto_inicio": self.punto_inicio}
            with open("cantinero_config.json", "w") as f:
                json.dump(config_data, f, indent=2)
            print(f"✅ Configuración guardada en cantinero_config.json:")
            print(f"   📍 X={self.punto_inicio['x']}, Y={self.punto_inicio['y']}, Z={self.punto_inicio['z']}")
            # Verificar que se guardó correctamente
            with open("cantinero_config.json", "r") as f:
                verificacion = json.load(f)
                if verificacion == config_data:
                    print("   ✓ Verificación exitosa: archivo guardado correctamente")
                else:
                    print("   ⚠️ Advertencia: el archivo guardado no coincide")
        except Exception as e:
            print(f"❌ Error guardando configuración: {e}")
    
    def is_admin_or_owner(self, user_id: str) -> bool:
        """Verifica si el usuario es admin o propietario"""
        return user_id == OWNER_ID or user_id == ADMIN_ID
        
    async def on_start(self, session_metadata: SessionMetadata) -> None:
        """Inicialización del bot cantinero"""
        print("🍷 Bot Cantinero iniciando...")
        self.bot_id = session_metadata.user_id
        
        # Recargar configuración para asegurar que tenemos la última posición guardada
        self.load_config()
        
        await asyncio.sleep(2)
        
        try:
            position = Position(
                float(self.punto_inicio["x"]), 
                float(self.punto_inicio["y"]), 
                float(self.punto_inicio["z"])
            )
            await self.highrise.teleport(self.bot_id, position)
            print(f"📍 Bot teletransportado a punto de inicio: X={self.punto_inicio['x']}, Y={self.punto_inicio['y']}, Z={self.punto_inicio['z']}")
        except Exception as e:
            print(f"❌ Error al teletransportar: {e}")
            print(f"   Punto de inicio configurado: {self.punto_inicio}")
        
        print("🕺 Iniciando emote floss continuo...")
        self.floss_task = asyncio.create_task(self.floss_continuo())
        
        print("📢 Iniciando mensajes automáticos...")
        self.mensaje_task = asyncio.create_task(self.mensajes_automaticos())
        
        print("🍷 ¡Bot Cantinero listo para servir!")
    
    async def floss_continuo(self):
        """Ejecuta el emote floss continuamente sin parar"""
        emotes_disponibles = ["emote-float", "emote-gravity", "idle-dance-casual", "dance-tiktok8"]
        emote_actual = 0
        
        while True:
            try:
                await self.highrise.send_emote(emotes_disponibles[emote_actual], self.bot_id)
                await asyncio.sleep(4)
            except Exception as e:
                emote_actual = (emote_actual + 1) % len(emotes_disponibles)
                if emote_actual == 0:
                    await asyncio.sleep(5)
    
    async def mensajes_automaticos(self):
        """Envía 1 mensaje automático cada 3 minutos, alternando entre los 3 mensajes"""
        mensajes = [
            "‼️¿Sugerencias o incomodidades? Contacta a un miembro superior de la sala: envía un mensaje a @Alber_JG_69 o a @baby__lax. ¡Estamos para ayudarte!‼️",
            "¡Consigue tu VIP Permanente!💎 Para ser un miembro eterno de 🕷️ NOCTURNO 🕷️, Mándale 100 de oro al bot: @NOCTURNO_BOT. ¡Gracias por apoyar la oscuridad!",
            "Acércate a la barra.🥃 Estoy para servirle. ¿Qué deseas hoy?🍻"
        ]
        indice = 0
        
        while True:
            try:
                await asyncio.sleep(180)
                
                mensaje_actual = mensajes[indice]
                
                response = await self.highrise.get_room_users()
                if not isinstance(response, Error):
                    for user, _ in response.content:
                        if user.id != self.bot_id:
                            try:
                                await self.highrise.send_whisper(user.id, mensaje_actual)
                            except Exception as e:
                                print(f"Error enviando mensaje a {user.username}: {e}")
                
                print(f"📢 Mensaje automático #{indice + 1} enviado: {mensaje_actual[:50]}...")
                indice = (indice + 1) % len(mensajes)
                
            except Exception as e:
                print(f"Error en mensajes automáticos: {e}")
                await asyncio.sleep(60)
    
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
    
    async def procesar_comando(self, user: User, message: str) -> None:
        """Procesa comandos del usuario (desde chat o whisper)"""
        msg = message.lower().strip()
        user_id = user.id
        
        if msg == "!menu" or msg == "!carta":
            await self.mostrar_menu(user)
            return
        
        if msg.startswith("!servir"):
            await self.servir_bebida(user, message)
            return
        
        if msg == "!cantinero":
            await self.highrise.send_whisper(user_id, "🍷 A tus órdenes. Usa !menu para ver la carta")
            return
        
        if msg == "!copy":
            if not self.is_admin_or_owner(user_id):
                await self.highrise.send_whisper(user_id, "❌ Solo admin y propietario pueden usar este comando")
                return
            
            try:
                outfit_request = await self.highrise.get_user_outfit(user_id)
                if outfit_request and not isinstance(outfit_request, Error):
                    await self.highrise.set_outfit(outfit_request.outfit)
                    await self.highrise.send_whisper(user_id, f"✅ Outfit copiado exitosamente de @{user.username}!")
                    print(f"👔 Outfit copiado de {user.username}")
            except Exception as e:
                await self.highrise.send_whisper(user_id, f"❌ Error al copiar outfit: {e}")
                print(f"Error copiando outfit: {e}")
            return
        
        if msg == "!inicio":
            if not self.is_admin_or_owner(user_id):
                await self.highrise.send_whisper(user_id, "❌ Solo admin y propietario pueden usar este comando")
                return
            
            try:
                response = await self.highrise.get_room_users()
                bot_position = None
                
                if not isinstance(response, Error):
                    for u, pos in response.content:
                        if u.id == self.bot_id:
                            bot_position = pos
                            break
                
                if bot_position and isinstance(bot_position, Position):
                    # Guardar coordenadas actuales
                    self.punto_inicio = {
                        "x": float(bot_position.x),
                        "y": float(bot_position.y),
                        "z": float(bot_position.z)
                    }
                    
                    # Guardar en archivo
                    self.save_config()
                    
                    # Esperar un momento y recargar para verificar
                    await asyncio.sleep(0.5)
                    self.load_config()
                    
                    # Confirmar al usuario
                    await self.highrise.send_whisper(user_id, "✅ PUNTO DE INICIO GUARDADO")
                    await self.highrise.send_whisper(user_id, f"📍 X={self.punto_inicio['x']:.2f}")
                    await self.highrise.send_whisper(user_id, f"📍 Y={self.punto_inicio['y']:.2f}")
                    await self.highrise.send_whisper(user_id, f"📍 Z={self.punto_inicio['z']:.2f}")
                    await self.highrise.send_whisper(user_id, "")
                    await self.highrise.send_whisper(user_id, "🔄 Reinicia el bot para verificar")
                    await self.highrise.send_whisper(user_id, "💡 Usa el workflow 'Bot Cantinero'")
                    
                    print(f"📍 PUNTO DE INICIO ACTUALIZADO:")
                    print(f"   X={self.punto_inicio['x']}, Y={self.punto_inicio['y']}, Z={self.punto_inicio['z']}")
                    
                elif bot_position and isinstance(bot_position, AnchorPosition):
                    await self.highrise.send_whisper(user_id, "⚠️ Posición tipo AnchorPosition detectada")
                    if bot_position.anchor:
                        await self.highrise.send_whisper(user_id, f"📍 Anchor: {bot_position.anchor}")
                    if bot_position.offset:
                        self.punto_inicio = {
                            "x": float(bot_position.offset.x),
                            "y": float(bot_position.offset.y),
                            "z": float(bot_position.offset.z)
                        }
                        self.save_config()
                        await asyncio.sleep(0.5)
                        self.load_config()
                        await self.highrise.send_whisper(user_id, "✅ Punto guardado usando offset")
                        await self.highrise.send_whisper(user_id, f"📍 X={self.punto_inicio['x']:.2f}, Y={self.punto_inicio['y']:.2f}, Z={self.punto_inicio['z']:.2f}")
                else:
                    await self.highrise.send_whisper(user_id, "❌ No se pudo obtener la posición del bot")
                    await self.highrise.send_whisper(user_id, f"Tipo de posición: {type(bot_position).__name__}")
                    print(f"❌ Bot position: {bot_position}, type: {type(bot_position)}")
            except Exception as e:
                await self.highrise.send_whisper(user_id, f"❌ Error: {str(e)[:100]}")
                print(f"❌ Error en !inicio: {e}")
                import traceback
                traceback.print_exc()
            return
        
        await self.detectar_bebida(user, msg)
    
    async def on_chat(self, user: User, message: str) -> None:
        """Maneja mensajes del chat público"""
        await self.procesar_comando(user, message)
    
    async def on_whisper(self, user: User, message: str) -> None:
        """Maneja mensajes whisper (privados)"""
        await self.procesar_comando(user, message)
    
    async def detectar_bebida(self, user: User, msg: str):
        """Detecta si el mensaje contiene el nombre de una bebida y la sirve automáticamente"""
        bebidas_respuestas = {
            "cerveza": "🍺 Aquí tienes una cerveza bien fría, @{user}! Salud! 🍻",
            "vino": "🍷 Un excelente vino tinto para ti, @{user}. ¡Buen provecho!",
            "whisky": "🥃 Whisky en las rocas para @{user}. Con clase! 🎩",
            "coctel": "🍹 Un cóctel especial de la casa para @{user}! 🌟",
            "cóctel": "🍹 Un cóctel especial de la casa para @{user}! 🌟",
            "champagne": "🍾 Champagne! Algo que celebrar, @{user}? 🎉",
            "cafe": "☕ Café recién hecho para @{user}. ¡Energía pura! ⚡",
            "café": "☕ Café recién hecho para @{user}. ¡Energía pura! ⚡",
            "refresco": "🥤 Refresco bien frío para @{user}! 🧊",
            "sombra": "🖤 Sombra Líquida... la especialidad NOCTURNO para @{user}. Oscuro y misterioso... 🕷️",
            "sangre": "🦇 Sangre de Murciélago para @{user}... dulce con un toque salvaje 🌙",
            "eclipse": "🌑 Eclipse Negro... la bebida más oscura para @{user}. Solo para los más valientes 🕸️"
        }
        
        for bebida, respuesta in bebidas_respuestas.items():
            if bebida in msg:
                respuesta_final = respuesta.replace("{user}", user.username)
                await self.highrise.send_whisper(user.id, respuesta_final)
                return
    
    async def mostrar_menu(self, user: User):
        """Muestra el menú de bebidas"""
        menu = [
            "🍷 === CARTA DEL CANTINERO === 🍷",
            "",
            "🍺 Cerveza",
            "🍷 Vino",
            "🥃 Whisky",
            "🍹 Cóctel",
            "🍾 Champagne",
            "☕ Café",
            "🥤 Refresco",
            "",
            "🕷️ Bebidas especiales NOCTURNO:",
            "🖤 Sombra Líquida",
            "🦇 Sangre de Murciélago",
            "🌑 Eclipse Negro",
            "",
            "💡 Solo di el nombre de la bebida o usa !servir [bebida]"
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
            await self.highrise.send_whisper(user.id, respuesta)
        elif bebida == "":
            await self.highrise.send_whisper(user.id, "¿Qué bebida deseas? Usa !menu para ver la carta")
        else:
            await self.highrise.send_whisper(user.id, f"No tengo '{bebida}' en la carta. Usa !menu para ver opciones")

if __name__ == "__main__":
    import sys
    
    print("🍷 Iniciando Bot Cantinero NOCTURNO...")
    print("🕺 Emote floss continuo activado")
    print("📢 Mensajes automáticos cada 3 minutos")
    print("🕷️ Listo para servir en la oscuridad...")
    print("=" * 50)
    
    bot = CantineroBot()
    print("🔧 Bot Cantinero inicializado. Esperando conexión...")
