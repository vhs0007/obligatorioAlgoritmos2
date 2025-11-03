# 📱 Información de Configuración WhatsApp Business API

## 🔑 Credenciales Configuradas

- **Phone Number ID:** `871681339360716`
- **WhatsApp Business Account ID:** `2277309066073479`
- **Número de Prueba (Sandbox):** `+1 555 164 8009`
- **Verify Token:** `Chacalitas2025`

## 📞 Números Disponibles

### Número de Prueba (Sandbox)
- **Número:** `+1 555 164 8009`
- **Uso:** Solo funciona en modo sandbox/prueba
- **Limitaciones:** Solo puede recibir mensajes de números verificados en tu cuenta de desarrollador

### Número de Producción
- **Número:** `+598 97 465 647`
- **Uso:** Número real para producción (debe estar verificado)

## 🚀 Comandos Rápidos

### Enviar mensaje al número de prueba:
```bash
python enviar_mensaje.py "+15551648009" "Hola, mensaje de prueba"
```

### Enviar mensaje a número real:
```bash
python enviar_mensaje.py "+59897465647" "Hola desde WhatsApp Business"
```

### Ejecutar servidor webhook:
```bash
python main.py webhook
```

## ⚠️ Notas Importantes

1. **Modo Sandbox:** El número `+1 555 164 8009` solo funciona en modo sandbox. Para recibir mensajes de este número, debes:
   - Agregar el número emisor a tu lista de números verificados en Meta Developer Console
   - O usar el número desde tu cuenta de desarrollador

2. **Números Reales:** Para usar números reales en producción, deben estar verificados por Meta/WhatsApp.

3. **Webhook:** Configura el webhook en Meta Developer Console con:
   - URL: Tu URL de ngrok o servidor (ej: `https://abc123.ngrok.io/webhook`)
   - Verify Token: `Chacalitas2025`

## 🔍 Verificación

Para verificar que todo está configurado correctamente:

```bash
python verificar_configuracion.py
```

Este script verificará:
- ✅ Token de acceso
- ✅ Phone Number ID
- ✅ Permisos necesarios

