from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import json
import traceback
from whatsapp_api import procesar_mensaje_recibido, enviar_mensaje_whatsapp, WHATSAPP_PHONE_NUMBER_ID

app = FastAPI()
VERIFY_TOKEN = "Chacalitas2025"

# --- Endpoints básicos ---
@app.get("/")
async def root():
    return {
        "message": "✅ WhatsApp Webhook Server funcionando",
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

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Token inválido", status_code=403)

# --- Función para generar menú interactivo ---
def menu_categorias(numero):
    return {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🍔 ¡Bienvenido a GordoEats! 😋"},
            "body": {"text": "Seleccioná una categoría para ver nuestras opciones:"},
            "footer": {"text": "Usá el menú para elegir 👇"},
            "action": {
                "button": "Ver categorías",
                "sections": [
                    {
                        "title": "Categorías de comidas",
                        "rows": [
                            {"id": f"cat_{i}", "title": t} for i, t in enumerate([
                                "🍔 Hamburguesas", "🍕 Pizzas", "🍽 Minutas", "🥤 Bebidas sin alcohol",
                                "🍺 Bebidas alcohólicas", "🍰 Postres", "🥗 Ensaladas", "🍝 Pastas",
                                "🥪 Sándwiches", "⚡ Comidas rápidas", "📋 Ver todas las comidas"
                            ], start=1)
                        ]
                    }
                ]
            }
        }
    }

# --- Endpoint principal ---
@app.post("/webhook")
async def receive(request: Request):
    try:
        data = await request.json()
        resultado = procesar_mensaje_recibido(data)

        if resultado:
            numero, mensaje, tipo = resultado
            mensaje_lower = mensaje.lower().strip()

            if mensaje_lower in ['hola', 'hi', 'hello', 'buenos dias', 'buenas tardes', 'buenas noches']:
                envio = enviar_mensaje_whatsapp(numero, "¡Hola! 👋 Gracias por contactarnos. ¿En qué puedo ayudarte?")
            elif mensaje_lower in ['help', 'ayuda', 'ayudame']:
                envio = enviar_mensaje_whatsapp(numero, "📋 Comandos:\n- Hola: saludo\n- Info: información del bot\n- Menu: ver productos")
            elif mensaje_lower in ['info', 'informacion', 'información']:
                envio = enviar_mensaje_whatsapp(numero, "🤖 Soy un bot de WhatsApp desarrollado con FastAPI y Render. Y soy la version ultimtum de charlie garcia")
            elif mensaje_lower == 'menu':
                interactive_msg = menu_categorias(numero)
                envio = enviar_mensaje_whatsapp(numero, interactive_msg, usar_template=False)
            else:
                envio = enviar_mensaje_whatsapp(numero, f"✅ Recibí tu mensaje: \"{mensaje}\". Escribí 'Ayuda' para ver opciones.")

            if envio.get("success"):
                print(f"✅ Respuesta enviada. Message ID: {envio.get('message_id')}")
            else:
                print(f"⚠️ Error al enviar respuesta: {envio.get('error')}")

        return PlainTextResponse("EVENT_RECEIVED", status_code=200)

    except Exception as e:
        traceback.print_exc()
        return PlainTextResponse("ERROR", status_code=500)
