from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
from whatsapp_api import procesar_mensaje_recibido, enviar_mensaje_whatsapp, WHATSAPP_PHONE_NUMBER_ID

app = FastAPI()
VERIFY_TOKEN = "Chacalitas2025"

# --- Verificación del webhook ---
@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")
    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Token inválido", status_code=403)

# --- Menú interactivo ---
def menu_categorias(numero):
    return {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🍔 ¡Bienvenido a GordoEater! 😋"},
            "body": {"text": "Seleccioná una categoría para ver nuestras opciones:"},
            "footer": {"text": "Usá el menú para elegir 👇"},
            "action": {
                "button": "Ver categorías",
                "sections": [{
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
                        {"id": "cat_all", "title": "📋 Ver todas las comidas"}
                    ]
                }]
            }
        }
    }

@app.post("/webhook")
async def receive(request: Request):
    try:
        data = await request.json()
        resultado = procesar_mensaje_recibido(data)

        if not resultado:
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        numero, mensaje, _ = resultado
        texto = mensaje.lower().strip()

        if any(palabra in texto for palabra in ["hola", "buenos dias", "buenas tardes", "buenas noches"]):
            enviar_mensaje_whatsapp(numero, "¡Hola! 👋 Gracias por contactarnos. ¿En qué puedo ayudarte?")

        elif any(palabra in texto for palabra in ["help", "ayuda", "ayudame"]):
            enviar_mensaje_whatsapp(
                numero,
                "📋 Comandos:\n- Hola: saludo\n- Info: información\n- Menu: ver productos"
            )

        elif any(palabra in texto for palabra in ["info", "informacion", "información"]):
            enviar_mensaje_whatsapp(numero, "🤖 Soy el bot de GordoEater Palometa 🍔")

        elif any(palabra in texto for palabra in ["menu", "menú"]):
            enviar_mensaje_whatsapp(numero, menu_categorias(numero))

        else:
            enviar_mensaje_whatsapp(
                numero,
                f"✅ Recibí tu mensaje: \"{mensaje}\". Escribí 'Ayuda' para ver opciones."
            )

        return PlainTextResponse("EVENT_RECEIVED", status_code=200)

    except Exception as e:
        print("❌ Error en webhook:", e)
        return PlainTextResponse("ERROR", status_code=500)

