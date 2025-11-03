# 📥 Configurar Webhook para Recibir Mensajes

## 🚀 Pasos para Configurar el Webhook

### 1. Ejecutar el servidor webhook localmente

```bash
python main.py webhook
```

O directamente:

```bash
python webhook_server.py
```

El servidor estará corriendo en: `http://localhost:8000`

### 2. Exponer el servidor con ngrok

En otra terminal, ejecuta:

```bash
ngrok http 8000
```

Esto te dará una URL HTTPS como: `https://abc123.ngrok.io`

### 3. Configurar el webhook en Meta Developer Console

1. Ve a: https://developers.facebook.com/apps/
2. Selecciona tu app (Bruno Rossi)
3. Ve a **WhatsApp** → **Configuration**
4. En la sección **Webhook**, haz clic en **Edit**
5. Configura:
   - **Callback URL**: `https://tu-url-de-ngrok.webhook` (ejemplo: `https://abc123.ngrok.io/webhook`)
   - **Verify Token**: `Chacalitas2025`
   - Haz clic en **Verify and Save**

### 4. Suscribirse a eventos

Después de verificar el webhook:
1. Haz clic en **Manage**
2. Selecciona los eventos que quieres recibir:
   - ✅ **messages** (para recibir mensajes)
   - ✅ **message_status** (para recibir actualizaciones de estado)
3. Haz clic en **Save**

## 📨 Cómo Funciona

Una vez configurado:

1. **Cuando recibes un mensaje:**
   - WhatsApp envía un POST a `/webhook`
   - El servidor muestra el mensaje en consola
   - El bot responde automáticamente según el contenido

2. **Los mensajes se muestran así:**
   ```
   📨 NUEVO MENSAJE RECIBIDO:
      De: +59897465647
      Tipo: text
      Mensaje: Hola
   ```

3. **El bot responde automáticamente** con respuestas inteligentes según el contenido.

## ⚠️ Importante en Sandbox

En modo **SANDBOX**, el bot solo puede responder a:
- Números que hayas agregado como números de prueba en Meta Developer Console
- Números que te hayan escrito en las últimas 24 horas

Para agregar números de prueba:
1. Ve a tu app → WhatsApp → API Setup
2. En "To", agrega el número (ej: `+59897465647`)
3. Haz clic en "Send Message" para verificarlo

## 🧪 Probar el Webhook

### Opción 1: Desde WhatsApp
Envía un mensaje desde un número verificado al número de prueba: `+1 555 164 8009`

### Opción 2: Usar el número real
Envía un mensaje al número `+598 97 465 647` (si está verificado)

## 📋 Respuestas Automáticas

El bot responde automáticamente a:

- **Hola/Hi/Hello** → Saludo amigable
- **Ayuda/Help** → Lista de comandos disponibles
- **Info** → Información del bot
- **Otros mensajes** → Confirma recepción y ofrece ayuda

## 🔧 Personalizar Respuestas

Edita `webhook_server.py` en la sección de respuestas automáticas (líneas ~89-105) para personalizar las respuestas del bot.

