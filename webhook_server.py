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

def paginar(items, pagina=1, por_pagina=5):
    total = len(items)
    total_paginas = (total + por_pagina - 1) // por_pagina

    pagina = max(1, min(pagina, total_paginas))

    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina
    items_pagina = items[inicio:fin]

    if pagina < total_paginas:
        items_pagina.append({
            "id": f"next_{pagina + 1}",
            "title": "➡️ Siguiente página"
        })
    if pagina > 1:
        items_pagina.insert(0, {
            "id": f"prev_{pagina - 1}",
            "title": "⬅️ Página anterior"
        })

    return {
        "pagina_actual": pagina,
        "total_paginas": total_paginas,
        "items": items_pagina
    }


def menu_categorias(numero, pagina=1):
    categorias = [
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

    paginacion = paginar(categorias, pagina)

    return {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🍔 ¡Bienvenido a GordoEats! 😋"},
            "body": {
                "text": f"Seleccioná una categoría para ver nuestras opciones:\n(Página {paginacion['pagina_actual']}/{paginacion['total_paginas']})"
            },
            "footer": {"text": "Usá el menú para elegir 👇"},
            "action": {
                "button": "Ver categorías",
                "sections": [
                    {
                        "title": "Categorías de comidas",
                        "rows": paginacion["items"]
                    }
                ]
            }
        }
    }

#Cuando se haga el menu de productos se puede reutilizar paginacion
#Hay que ver como resolver el tomar el producto, se puede hacer un metodo grande usando el webhook o ver otra forma


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
                envio = enviar_mensaje_whatsapp(numero, "🤖 Soy un bot de WhatsApp desarrollado con FastAPI y Render. Y soy la version ultimtum de tu chael")
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
