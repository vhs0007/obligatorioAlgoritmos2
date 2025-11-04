from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import traceback
import json

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


# --- Verificación del webhook con Meta ---
@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Token inválido", status_code=403)


# --- Menú interactivo de categorías ---
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
                            {"id": "cat_1", "title": "🍔 Hamburguesas"},
                            {"id": "cat_2", "title": "🍕 Pizzas"},
                            {"id": "cat_3", "title": "🍽 Minutas"},
                            {"id": "cat_4", "title": "🥤 Bebidas sin alcohol"},
                            {"id": "cat_5", "title": "🍺 Bebidas alcohólicas"},
                            {"id": "cat_6", "title": "🍰 Postres"},
                            {"id": "cat_7", "title": "🥗 Ensaladas"},
                            {"id": "cat_8", "title": "🍝 Pastas"},
                            {"id": "cat_9", "title": "🥪 Sándwiches"},
                            {"id": "cat_10", "title": "⚡ Comidas rápidas"},
                            {"id": "cat_all", "title": "📋 Ver todas las comidas"},
                        ],
                    }
                ],
            },
        },
    }


# --- Endpoint principal (recibe mensajes) ---
@app.post("/webhook")
async def receive(request: Request):
    try:
        data = await request.json()
        print(json.dumps(data, indent=2, ensure_ascii=False))  # útil para debug

        # Ver si es una interacción de lista (click en menú)
        if "messages" in data["entry"][0]["changes"][0]["value"]:
            message = data["entry"][0]["changes"][0]["value"]["messages"][0]
            numero = message["from"]

            if message["type"] == "interactive":
                tipo = message["interactive"]["type"]

                # El usuario tocó una opción del menú
                if tipo == "list_reply":
                    seleccion = message["interactive"]["list_reply"]
                    cat_id = seleccion["id"]
                    cat_titulo = seleccion["title"]

                    print(f"📲 Usuario {numero} seleccionó: {cat_titulo} ({cat_id})")

                    # Ejemplo: responder con productos de esa categoría
                    respuesta = f"Mostrando productos de la categoría: {cat_titulo}"
                    envio = enviar_mensaje_whatsapp(numero, respuesta)
                    return PlainTextResponse("EVENT_RECEIVED", status_code=200)

            # Si no es interactivo → mensaje normal
            resultado = procesar_mensaje_recibido(data)
            if resultado:
                numero, mensaje, tipo = resultado
                mensaje_lower = mensaje.lower().strip()

                if mensaje_lower in ['hola', 'hi', 'hello', 'buenos dias', 'buenas tardes', 'buenas noches']:
                    envio = enviar_mensaje_whatsapp(numero, "¡Hola! 👋 Gracias por contactarnos. ¿En qué puedo ayudarte?")

                elif mensaje_lower in ['help', 'ayuda', 'ayudame']:
                    envio = enviar_mensaje_whatsapp(
                        numero,
                        "📋 Comandos:\n- Hola: saludo\n- Info: información del bot\n- Menu: ver productos"
                    )

                elif mensaje_lower in ['info', 'informacion', 'información']:
                    envio = enviar_mensaje_whatsapp(
                        numero,
                        "🤖 Soy un bot de WhatsApp desarrollado con FastAPI y Render."
                    )

                elif mensaje_lower == 'menu':
                    interactive_msg = menu_categorias(numero)
                    envio = enviar_mensaje_whatsapp(numero, interactive_msg, usar_template=False)

                else:
                    envio = enviar_mensaje_whatsapp(
                        numero,
                        f"✅ Recibí tu mensaje: \"{mensaje}\". Escribí 'Ayuda' para ver opciones."
                    )

                if envio.get("success"):
                    print(f"✅ Respuesta enviada. Message ID: {envio.get('message_id')}")
                else:
                    print(f"⚠️ Error al enviar respuesta: {envio.get('error')}")

        return PlainTextResponse("EVENT_RECEIVED", status_code=200)

    except Exception:
        traceback.print_exc()
        return PlainTextResponse("ERROR", status_code=500)
