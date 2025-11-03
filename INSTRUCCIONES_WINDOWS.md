# 🪟 Instrucciones para ejecutar los bots en Windows

## ⚠️ IMPORTANTE: El problema que estás teniendo

El error `'BotPrincipal' object has no attribute 'highrise'` ocurre porque el bot **NO se está ejecutando con el SDK de Highrise**.

## ✅ Solución: Pasos para ejecutar correctamente

### 1. Instalar el SDK de Highrise

Abre una terminal (CMD o PowerShell) en la carpeta del proyecto y ejecuta:

```bash
pip install highrise-bot-sdk --upgrade
```

### 2. Verificar la instalación

Ejecuta este comando para verificar que el SDK está instalado:

```bash
python -m highrise --version
```

Si ves un error, repite el paso 1.

### 3. Verificar tus archivos de configuración

Asegúrate de tener estos archivos con tus tokens:

**config.json** (para el bot principal):
```json
{
    "api_token": "TU_TOKEN_DEL_BOT_PRINCIPAL",
    "room_id": "TU_ROOM_ID"
}
```

**cantinero_config.json** (para el bot cantinero):
```json
{
    "api_token": "TU_TOKEN_DEL_BOT_CANTINERO",
    "room_id": "TU_ROOM_ID"
}
```

### 4. Ejecutar los bots

Ahora sí, ejecuta:

```bash
python run.py
```

## 🔧 Si el problema persiste

Si aún tienes el error, puede que estés usando una versión antigua del archivo `run.py`. 

### Ejecutar los bots manualmente (método alternativo)

Abre **DOS ventanas de terminal** (una para cada bot):

**Terminal 1 - Bot Principal:**
```bash
python -m highrise main:Bot TU_ROOM_ID TU_TOKEN_BOT_PRINCIPAL
```

**Terminal 2 - Bot Cantinero:**
```bash
python -m highrise cantinero_bot:BartenderBot TU_ROOM_ID TU_TOKEN_BOT_CANTINERO
```

Reemplaza:
- `TU_ROOM_ID` con el ID de tu sala (ejemplo: `686c527e9668a3cb40e1f58d`)
- `TU_TOKEN_BOT_PRINCIPAL` con el token del bot principal
- `TU_TOKEN_BOT_CANTINERO` con el token del bot cantinero

## 📝 Notas importantes

- Los tokens son diferentes para cada bot
- Ambos bots pueden usar el mismo `room_id`
- El SDK de Highrise **debe estar instalado** para que funcione
- En Windows, asegúrate de ejecutar desde la carpeta correcta donde están los archivos `.py`

## 🆘 ¿Necesitas ayuda?

Si sigues teniendo problemas:
1. Verifica que `requirements.txt` tenga: `highrise-bot-sdk>=24.1.0`
2. Ejecuta: `pip install -r requirements.txt`
3. Verifica que Python esté actualizado (3.10 o superior recomendado)
