# Configuración 24/7 para Bots de Highrise

## ✅ Sistema Configurado

Tu proyecto ahora está configurado para mantener **ambos bots activos 24/7** usando Flask y UptimeRobot.

## 📋 Archivos Creados/Actualizados

### 1. **start.py** - Lanzador Principal
- Ejecuta ambos bots simultáneamente en hilos separados
- Bot principal (`main.py`) usa `HIGHRISE_API_TOKEN`
- Bot cantinero (`cantinero_bot.py`) usa `CANTINERO_API_TOKEN`
- Ambos comparten el mismo `HIGHRISE_ROOM_ID`
- Servidor Flask en puerto 5000 con endpoint `/` que responde "¡Bots vivos!"

### 2. **pyproject.toml** - Dependencias
```toml
dependencies = [
    "asyncio>=4.0.0",
    "flask>=3.1.2",
    "highrise-bot-sdk>=24.1.0",
]
```

### 3. **Workflow "Bots 24/7"** - Auto-ejecución
- Se ejecuta automáticamente al iniciar el proyecto
- Espera a que el puerto 5000 esté listo antes de mostrar la URL pública

## 🔐 Secrets Necesarios

Asegúrate de tener configurados estos secrets en Replit:

| Secret | Descripción | Ejemplo |
|--------|-------------|---------|
| `HIGHRISE_API_TOKEN` | Token del bot principal | `b0c7b29926...` |
| `CANTINERO_API_TOKEN` | Token del bot cantinero | `e85f532a8d...` |
| `HIGHRISE_ROOM_ID` | ID de la sala compartida | `686c527e9668a3cb40e1f58d` |
| `OWNER_ID` | ID del propietario | `662aae9b602b4a897557ec18` |
| `ADMIN_IDS` | IDs de admins (separados por comas) | `id1,id2,id3` |
| `MODERATOR_IDS` | IDs de moderadores (separados por comas) | `id1,id2,id3` |

## 🌐 URL Pública

Una vez que el proyecto esté corriendo, Replit generará una URL pública como:
```
https://[nombre-proyecto].[tu-usuario].repl.co/
```

Esta URL responderá con: **"¡Bots vivos!"**

## ⏰ Configuración de UptimeRobot

Para mantener el proyecto activo 24/7:

1. Ve a [UptimeRobot.com](https://uptimerobot.com) y crea una cuenta gratuita
2. Crea un nuevo monitor con estos datos:
   - **Monitor Type**: HTTP(s)
   - **Friendly Name**: Highrise Bots NOCTURNO
   - **URL**: `https://[tu-proyecto].repl.co/`
   - **Monitoring Interval**: 5 minutos (recomendado)
   - **Alert Contacts**: Tu email (opcional)

3. Guarda el monitor

UptimeRobot hará ping a tu proyecto cada 5 minutos, manteniéndolo activo las 24 horas.

## 🚀 Cómo Usar

### Iniciar el Sistema
El workflow "Bots 24/7" se ejecuta automáticamente. Si necesitas reiniciarlo manualmente:
```bash
python start.py
```

### Verificar Estado
Visita la URL pública en tu navegador. Si ves "¡Bots vivos!", el sistema está funcionando.

### Ver Logs
Los logs de ambos bots aparecen en la consola con prefijos:
- `[MAIN BOT]` - Bot principal
- `[CANTINERO BOT]` - Bot cantinero
- `🌐` - Servidor Flask

## ⚠️ Nota Importante

**Los bots actualmente no pueden conectarse** porque los tokens en los secrets necesitan ser actualizados con tokens válidos de Highrise. El error actual es:
```
ERROR: Error(message='API token not found', do_not_reconnect=False, rid=None)
```

**Solución**: Verifica que los tokens `HIGHRISE_API_TOKEN` y `CANTINERO_API_TOKEN` sean válidos y correspondan a tus bots en Highrise.

## 📊 Arquitectura

```
start.py
├── Thread 1: Bot Principal (main.py)
│   └── Token: HIGHRISE_API_TOKEN
├── Thread 2: Bot Cantinero (cantinero_bot.py)
│   └── Token: CANTINERO_API_TOKEN
└── Thread 3: Flask Server (Puerto 5000)
    └── Endpoint: / → "¡Bots vivos!"
```

## ✨ Ventajas

- ✅ Ambos bots corren simultáneamente sin interferencias
- ✅ Servidor Flask mínimo (no consume recursos)
- ✅ Compatible con plan gratuito de Replit + UptimeRobot
- ✅ Secrets seguros (no hardcodeados)
- ✅ Fácil de monitorear y debuggear

## 🆘 Troubleshooting

### Los bots no conectan
- Verifica que los tokens sean válidos
- Verifica que el Room ID sea correcto
- Revisa los logs para ver errores específicos

### Flask no inicia
- Verifica que el puerto 5000 no esté ocupado
- Revisa que Flask esté instalado correctamente

### UptimeRobot no funciona
- Verifica que la URL pública sea correcta
- Asegúrate de que el proyecto esté corriendo
- Revisa la configuración del monitor en UptimeRobot

---

**¡Listo!** Tu sistema de bots 24/7 está configurado y listo para usar. 🎉
