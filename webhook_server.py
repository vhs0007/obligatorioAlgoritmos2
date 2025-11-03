from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import json
import traceback
from whatsapp_api import procesar_mensaje_recibido, enviar_mensaje_whatsapp, WHATSAPP_PHONE_NUMBER_ID

app = FastAPI()
VERIFY_TOKEN = "Chacalitas2025"

@app.get("/")
async def root():
    return {
        "message": "✅ WhatsApp Webhook Server funcionando correctamente",
        "phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
        "endpoints": {"webhook": "/webhook", "health": "/health"},
    }

@app.get("/health")
async def health():
    return {"status": "ok"}

@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    print(f"\n[WEBHOOK VERIFY] Mode: {mode}, Token recibido: {token}")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        print("[WEBHOOK VERIFY] ✅ Verificación exitosa.")
        return PlainTextResponse(challenge)

    print("[WEBHOOK VERIFY] ❌ Verificación fallida.")
    return PlainTextResponse("Token inválido", status_code=403)

@app.post("/webhook")
async def receive(request: Request):
    try:
        data = await request.json()
        print("📩 Evento recibido:")
        print(json.dumps(data, indent=2, ensure_ascii=False))

        if not data.get("entry"):
            print("⚠️ Evento vacío (sin entry), ignorando.")
            return PlainTextResponse("NO_ENTRY", status_code=200)

        resultado = procesar_mensaje_recibido(data)

        if resultado:
            numero, mensaje, tipo = resultado
            print(f"\n📨 NUEVO MENSAJE RECIBIDO de {numero} ({tipo}): {mensaje}")
            mensaje_lower = mensaje.lower().strip()

            # Lógica de respuesta
            if mensaje_lower in ['hola', 'hi', 'hello', 'buenos dias', 'buenas tardes', 'buenas noches']:
                respuesta = "¡Hola! 👋 Gracias por contactarnos. ¿En qué puedo ayudarte?"
            elif mensaje_lower in ['help', 'ayuda', 'ayudame']:
                respuesta = "📋 Comandos:\n- Hola: saludo\n- Info: información del bot\n- Ayuda: ver opciones"
            elif mensaje_lower in ['info', 'informacion', 'información']:
                respuesta = "🤖 Soy un bot de WhatsApp desarrollado con FastAPI y Render."
            else:
                respuesta = f"✅ Recibí tu mensaje: \"{mensaje}\". Escribí 'Ayuda' para ver opciones."

            print("💬 Enviando respuesta automática...")
            envio = enviar_mensaje_whatsapp(numero, respuesta)

            if envio.get("success"):
                print(f"✅ Respuesta enviada. Message ID: {envio.get('message_id')}")
            else:
                print(f"⚠️ Error al enviar respuesta: {envio.get('error')}")

        else:
            print("📊 Evento sin mensaje (probablemente actualización de estado).")

        return PlainTextResponse("EVENT_RECEIVED", status_code=200)

    except Exception as e:
        print(f"\n❌ ERROR al procesar webhook: {e}")
        traceback.print_exc()
        return PlainTextResponse("ERROR", status_code=500)
