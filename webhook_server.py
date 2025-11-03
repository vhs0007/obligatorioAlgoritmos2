"""
Servidor webhook con FastAPI para recibir mensajes de WhatsApp
"""

from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse, JSONResponse
import json
from whatsapp_api import (
    procesar_mensaje_recibido,
    enviar_mensaje_whatsapp,
    WHATSAPP_PHONE_NUMBER_ID
)

app = FastAPI()

VERIFY_TOKEN = "Chacalitas2025"  # o el token que tengas en Meta


@app.get("/")
async def root():
    """Página de inicio."""
    return {
        "message": "WhatsApp Webhook Server está funcionando",
        "phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Endpoint de salud."""
    return {"status": "ok"}


@app.get("/webhook")
async def verify(request: Request):
    """
    Endpoint para verificar el webhook de WhatsApp.
    WhatsApp enviará una petición GET con estos parámetros para verificar el servidor.
    """
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    print(f"\n[WEBHOOK VERIFICATION] Mode: {mode}, Token recibido: {token}")
    
    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[WEBHOOK VERIFICATION] ✅ Webhook verificado correctamente")
        return PlainTextResponse(challenge)
    print("[WEBHOOK VERIFICATION] ❌ Verificación fallida")
    return PlainTextResponse("Token inválido", status_code=403)


@app.post("/webhook")
async def receive(request: Request):
    """
    Endpoint para recibir mensajes de WhatsApp.
    WhatsApp enviará una petición POST cuando se reciba un mensaje.
    """
    try:
        data = await request.json()
        print("📩 Evento recibido:", json.dumps(data, indent=2, ensure_ascii=False))
        
        # Procesar el mensaje
        resultado = procesar_mensaje_recibido(data)
        
        if resultado:
            numero, mensaje, tipo = resultado
            
            print(f"\n📨 NUEVO MENSAJE RECIBIDO:")
            print(f"   De: {numero}")
            print(f"   Tipo: {tipo}")
            print(f"   Mensaje: {mensaje}")
            print("-" * 60)
            
            # Responder automáticamente al mensaje
            try:
                mensaje_lower = mensaje.lower().strip()
                
                # Respuestas automáticas según el contenido
                respuesta = None
                if mensaje_lower in ['hola', 'hi', 'hello', 'buenos dias', 'buenas tardes', 'buenas noches']:
                    respuesta = f"¡Hola! 👋\nGracias por contactarnos. ¿En qué puedo ayudarte?"
                elif mensaje_lower in ['help', 'ayuda', 'ayudame']:
                    respuesta = "📋 Comandos disponibles:\n- Hola: Saludo\n- Ayuda: Ver esta ayuda\n- Info: Información del bot"
                elif mensaje_lower in ['info', 'informacion', 'información']:
                    respuesta = "🤖 Soy un bot de WhatsApp\nEstoy aquí para ayudarte. Escribe 'Ayuda' para ver más opciones."
                else:
                    # Respuesta genérica
                    respuesta = f"✅ Recibí tu mensaje: \"{mensaje}\"\n\n¿Necesitas ayuda? Escribe 'Ayuda' para ver opciones."
                
                # Enviar respuesta
                print(f"\n💬 Enviando respuesta automática...")
                respuesta_resultado = enviar_mensaje_whatsapp(
                    numero,
                    respuesta,
                    usar_template=False  # Cambia a True si quieres usar template siempre
                )
                
                if respuesta_resultado.get('success'):
                    print(f"✅ Respuesta enviada exitosamente")
                    print(f"   Message ID: {respuesta_resultado.get('message_id')}")
                else:
                    print(f"⚠️ No se pudo enviar respuesta automática:")
                    print(f"   {respuesta_resultado.get('error', 'Error desconocido')}")
                    
            except Exception as e:
                print(f"⚠️ Error al enviar respuesta automática: {str(e)}")
        else:
            # Puede ser una notificación de estado (enviado, entregado, leído, etc.)
            entry = data.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Verificar si hay statuses (actualizaciones de estado de mensaje)
            statuses = value.get('statuses', [])
            if statuses:
                status = statuses[0]
                print(f"\n📊 ACTUALIZACIÓN DE ESTADO:")
                print(f"   ID Mensaje: {status.get('id', 'N/A')}")
                print(f"   Estado: {status.get('status', 'N/A')}")
                print(f"   Para: {status.get('recipient_id', 'N/A')}")
                print("-" * 60)
        
        return PlainTextResponse("EVENT_RECEIVED", status_code=200)
        
    except Exception as e:
        print(f"\n❌ ERROR al procesar webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return PlainTextResponse("ERROR", status_code=500)


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 Iniciando servidor webhook de WhatsApp...")
    print(f"📱 Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")
    print(f"🔑 Verify Token: {VERIFY_TOKEN}")
    print("="*60)
    print("\n📌 Para probar localmente, usa ngrok:")
    print("   1. Instala ngrok: https://ngrok.com/download")
    print("   2. Ejecuta: ngrok http 8000")
    print("   3. Copia la URL HTTPS y configúrala en Meta Developer Console")
    print(f"   4. Verify Token en Meta: {VERIFY_TOKEN}")
    print("\n🌐 Servidor ejecutándose en: http://localhost:8000")
    print("📥 Webhook URL: http://localhost:8000/webhook")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
