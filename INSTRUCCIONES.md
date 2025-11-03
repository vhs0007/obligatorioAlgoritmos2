# 📱 Instrucciones para WhatsApp Business API

## 🚀 Inicio Rápido

### 1. Instalar dependencias

```bash
uv sync
```

O si usas pip:

```bash
pip install fastapi requests uvicorn
```

### 2. Configurar el servidor webhook (para recibir mensajes)

#### Opción A: Usando ngrok (recomendado para desarrollo local)

1. **Instala ngrok:**
   - Descarga desde: https://ngrok.com/download
   - O usa chocolatey en Windows: `choco install ngrok`

2. **Inicia el servidor webhook:**
   ```bash
   python main.py webhook
   ```

3. **En otra terminal, inicia ngrok:**
   ```bash
   ngrok http 8000
   ```

4. **Copia la URL HTTPS** que ngrok te da (algo como: `https://abc123.ngrok.io`)

5. **Configura el webhook en Meta Developer Console:**
   - Ve a: https://developers.facebook.com/apps/
   - Selecciona tu app → WhatsApp → Configuration
   - En "Webhook", pega la URL: `https://abc123.ngrok.io/webhook`
   - Token de verificación: `mi_token_verificacion_secreto`
   - Haz clic en "Verify and Save"

#### Opción B: Usando un servidor en producción

Simplemente despliega el servidor en un host público y configura la URL del webhook en Meta Developer Console.

### 3. Enviar un mensaje

Para enviar un mensaje de prueba:

```bash
python enviar_mensaje.py "+15551648009" "Hola, este es un mensaje de prueba"
```

O usando main.py:

```bash
python main.py enviar "+15551648009" "Hola desde el bot"
```

**Nota:** El número debe incluir el código de país sin espacios (ej: +15551648009).

## 📋 Archivos del proyecto

- `whatsapp_api.py` - Módulo principal con funciones de WhatsApp
- `webhook_server.py` - Servidor FastAPI para recibir mensajes
- `main.py` - Aplicación principal (servidor webhook por defecto)
- `enviar_mensaje.py` - Script simple para enviar mensajes

## 🔧 Configuración

Las credenciales están configuradas directamente en `whatsapp_api.py`:

- **Access Token:** Ya configurado
- **Phone Number ID:** Se obtiene automáticamente de la API
- **Verify Token:** `mi_token_verificacion_secreto`

Si necesitas cambiar estas configuraciones, edita el archivo `whatsapp_api.py`.

## 📨 Recibir mensajes

Cuando el servidor webhook esté ejecutándose:

1. El servidor mostrará los mensajes recibidos en la consola
2. Los mensajes se mostrarán con el formato:
   ```
   📨 NUEVO MENSAJE RECIBIDO:
      De: +1234567890
      Tipo: text
      Mensaje: Hola, este es mi mensaje
   ```

## 🛠️ Comandos útiles

```bash
# Ejecutar servidor webhook
python main.py webhook

# Enviar un mensaje
python enviar_mensaje.py "+15551648009" "Tu mensaje aquí"

# Verificar que el servidor está funcionando
curl http://localhost:8000/
```

## ⚠️ Solución de problemas

### Error: "Phone Number ID no está configurado"

1. Ve a https://developers.facebook.com/apps/
2. Selecciona tu app → WhatsApp → API Setup
3. Copia el "Phone number ID"
4. Configúralo como variable de entorno:
   ```bash
   set WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id
   ```

### Error al verificar el webhook

- Asegúrate de que el token de verificación en Meta Developer Console sea exactamente: `mi_token_verificacion_secreto`
- Verifica que ngrok esté corriendo y que la URL sea HTTPS

### No se reciben mensajes

- Verifica que el webhook esté configurado correctamente en Meta Developer Console
- Asegúrate de que ngrok esté corriendo (para desarrollo local)
- Verifica que el servidor esté ejecutándose en el puerto 8000

## 📚 Más información

- Documentación de WhatsApp Business API: https://developers.facebook.com/docs/whatsapp
- Documentación de FastAPI: https://fastapi.tiangolo.com/
