
# 📋 COMANDOS DE LOS BOTS NOCTURNO

Este archivo contiene la documentación completa de todos los comandos disponibles en ambos bots: **Bot Principal** y **Bot Cantinero**.

---

## 🤖 BOT PRINCIPAL (NOCTURNO_BOT)

### 📊 INFORMACIÓN
- `!info` - Mostrar tu información
- `!info @user` - Ver información de un usuario
- `!role` - Ver tu rol
- `!role list` - Lista de roles disponibles
- `!stats` - Estadísticas de la sala
- `!online` - Usuarios online
- `!myid` - Ver tu ID de usuario
- `!position` o `!pos` - Ver tu posición actual

### 💖 CORAZONES & REACCIONES
- `!heart @user [cantidad]` - Dar corazones (Admin/Owner: hasta 100, VIP: hasta 5)
- `!heartall` - Dar corazones a todos (Solo Owner)
- `!thumbs @user [cantidad]` - Pulgar arriba
- `!clap @user [cantidad]` - Aplaudir
- `!wave @user [cantidad]` - Saludar
- `!reactions` - Ver lista de reacciones disponibles
- `!game love @user1 @user2` - Medidor de amor

### 🎭 EMOTES
- `!emote list` - Lista de emotes (224 emotes disponibles)
- `[número]` - Hacer emote por número (ej: `1`)
- `[nombre]` - Hacer emote por nombre (ej: `fairytwirl`)
- `!emote @user [emote]` - Emote a usuario (Admin/Owner)
- `!emote all [emote]` - Emote a todos (Admin/Owner)
- `[emote] all` - Emote a todos (Admin/Owner)
- `!stop` - Detener tu emote
- `!stop @user` - Detener emote de usuario (VIP+)
- `!stop all` - Detener todos los emotes (Admin/Owner)
- `!stopall` - Detener todos los emotes (Admin/Owner)
- `!automode` - Modo automático (Admin/Owner) - Ciclo de 224 emotes
- `(emote) @user` - Emote mutuo (Solo VIP+)

### 📋 SISTEMA DE COPIA DE EMOTES (Admin/Owner)
- `!copyemote @user` o `!copyemote [user_id]` - Copiar emote de otro usuario
- `!listemotes` - Ver lista de emotes copiados
- `!emotecopy [número]` - Usar emote copiado en bucle infinito

### ⚡ TELETRANSPORTE
- `!flash [x] [y] [z]` - Flash entre pisos (altura >= 10 bloques)
- `!anchor [x] [y] [z]` - Teleporte sin restricciones (Admin/Owner)
- `!bring @user` - Traer usuario (Admin/Owner)
- `!goto @user [punto]` - Enviar usuario a punto (Admin/Owner)
- `!sendall [zona]` - Enviar todos a una zona (Admin/Owner)
- `!tplist` - Lista de puntos de teletransporte
- `!tp [nombre]` - Ir a punto guardado
- `[nombre_punto]` - Ir a punto (escribir nombre directamente)
- `!tele list` - Lista de ubicaciones
- `!tele @user` - Ir a usuario (VIP+)
- `vip` o `!vip` - Zona VIP (Solo VIP+)
- `dj` o `!dj` - Zona DJ (Admin/Owner)
- `directivo` o `!directivo` - Zona directivo (Admin/Owner)
- `carcel` o `!carcel` - Zona cárcel (Admin/Owner)
- `!addzone [nombre]` - Crear zona (Admin/Owner)
- `!TPus [nombre]` - Crear punto TP (Owner)
- `!delpoint [nombre]` - Eliminar punto (Owner)

### 🔨 MODERACIÓN (Admin/Owner)
- `!vip @user` - Dar VIP
- `!givevip @user` - Dar VIP
- `!unvip @user` - Quitar VIP
- `!checkvip [@user]` - Verificar VIP
- `!kick @user` - Expulsar
- `!ban @user` - Banear
- `!unban @user` - Desbanear
- `!freeze @user` - Congelar
- `!mute @user [seg]` - Silenciar
- `!unmute @user` - Quitar silencio
- `!jail @user` - Enviar a cárcel (impide escape automático)
- `!unjail @user` - Liberar de cárcel
- `!banlist` - Lista de baneados
- `!mutelist` - Lista de silenciados
- `!privilege @user` - Ver privilegios

### 🤖 BOT (Admin/Owner)
- `!bot @user` - Atacar con bot
- `!tome` - Bot a ti (Owner)
- `!say [mensaje]` - Bot habla
- `!mimic @user` - Imitar usuario
- `!copyoutfit` - Copiar tu outfit y guardarlo

### 👔 APARIENCIA (Admin/Owner)
- `!outfit [número]` - Cambiar outfit guardado
- `!inventory` - Ver inventario del bot
- `!inventory @user` - Ver outfit de usuario
- `!give @user [item]` - Dar item (deshabilitado)

### 🎵 DJ & MÚSICA (Admin/Moderator)
- `!dj` - Panel DJ
- `!music play` - Reproducir
- `!music stop` - Detener
- `!music pause` - Pausar

### 💰 DINERO (Admin/Moderator)
- `!tip all [1-5]` - Dar oro a todos
- `!tip only [X]` - Dar oro a X usuarios aleatorios
- `!wallet` - Balance del bot (Owner)

### 🏆 LOGROS & RANKING
- `!leaderboard heart` - Top corazones
- `!leaderboard active` - Top actividad
- `!achievements` - Tus logros
- `!rank` - Tu rango
- `!daily` - Recompensa diaria
- `!trackme` - Seguimiento de actividad

### ⚙️ ZONAS (Owner)
- `!setvipzone` o `!sv` - Establecer zona VIP
- `!setdj` - Establecer zona DJ
- `!setdirectivo` - Establecer zona directivo
- `!setspawn` - Establecer punto de inicio del bot

### 🥊 INTERACCIONES (VIP+)
- `!punch @user` - Golpear
- `!slap @user` - Bofetada
- `!flirt @user` - Coquetear
- `!scare @user` - Asustar
- `!electro @user` - Electrocutar
- `!hug @user` - Abrazar
- `!ninja @user` - Ataque ninja
- `!laugh @user` - Reír
- `!boom @user` - Explotar

### 🔧 SISTEMA
- `!restart` - Reiniciar bot (Owner)
- `!help` - Ver comandos disponibles según rol
- `!help interaction` - Ayuda de interacciones
- `!help teleport` - Ayuda de teletransporte
- `!help leaderboard` - Ayuda de ranking
- `!help heart` - Ayuda de corazones

---

## 🍷 BOT CANTINERO (CANTINERO_BOT)

### 🎭 EMOTES (Solo Admin/Owner)
El bot cantinero tiene acceso completo a los **224 emotes** del bot principal.

#### Comandos de Emote Individual:
- `!1`, `!2`, `!3`, ... `!224` - Cambiar a emote por número
- `!fairytwirl`, `!ghostfloat`, `!dab`, etc. - Cambiar a emote por nombre
- `!canstop` - Detener emote en bucle
- `!canstart` - Reanudar emote en bucle
- `!canstatus` - Ver estado actual del emote

#### Modo Automático:
- `!automode` - Iniciar ciclo infinito de todos los 224 emotes

**Nota:** Solo Admin y Owner pueden cambiar emotes del bot cantinero.

### 👔 OUTFIT (Admin/Owner)
- `!copy` - Copiar outfit del usuario que ejecuta el comando

### 🍹 BEBIDAS
- `!trago @user` - Servir bebida aleatoria a un usuario

### 📞 SISTEMA DE LLAMADAS
- Mencionar `@CANTINERO_BOT` o `@cantinero` en el chat
  - Usuarios normales: Solo pueden llamar 1 vez
  - Admin/Owner: Llamadas ilimitadas

### 💬 MENSAJES AUTOMÁTICOS
El bot cantinero envía mensajes automáticos cada **2 minutos**:
1. Mensaje del día de la semana
2. Información de contacto para sugerencias
3. Información de VIP
4. Solicitud de canciones
5. Invitación a la barra

### 🎯 EMOTES POR DEFECTO
- Emote inicial: **ghostfloat** (emote-ghost-idle)
- Ejecuta el emote configurado cada 18 segundos en bucle

---

## 🌟 SISTEMA VIP

### Obtener VIP
- **Donación automática:** Enviar exactamente **100 oro** al bot principal
- **Asignación manual:** Admin/Owner puede dar VIP con `!vip @user` o `!givevip @user`

### Beneficios VIP
✅ Acceso a comandos de emotes mutuos  
✅ Detener emotes de otros usuarios  
✅ Teletransporte a zona VIP  
✅ Enviar hasta 5 corazones por comando  
✅ Comandos de interacción  

---

## 📝 NOTAS IMPORTANTES

### Permisos
- **Owner (Propietario):** Acceso total a todos los comandos
- **Admin (Administrador):** Mayoría de comandos menos algunos exclusivos del Owner
- **Moderator (Moderador):** Comandos de moderación básica
- **VIP:** Comandos especiales limitados
- **Usuario Normal:** Comandos básicos de información y emotes

### Flashmode Automático
El bot principal detecta automáticamente cuando subes/bajas >= 10 bloques de altura y activa el flashmode.

### Sistema Anti-Escape
Los usuarios enviados a la cárcel con `!jail` no pueden escapar. El bot los devuelve automáticamente si intentan alejarse.

### Sistema de Reconexión
Ambos bots tienen sistema de reconexión automática que verifica la conexión cada 30 segundos y reintenta conectar si es necesario.

---

**Última actualización:** Noviembre 2025  
**Versión:** 2.0 - Sistema completo de 224 emotes
