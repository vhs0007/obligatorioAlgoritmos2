from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import traceback
from whatsapp_api import procesar_mensaje_recibido, enviar_mensaje_whatsapp

app = FastAPI()
VERIFY_TOKEN = "Chacalitas2025"


# --- Rutas básicas ---
@app.get("/")
async def home():
    return {"message": "Servidor WhatsApp activo"}

@app.get("/health")
async def health():
    return {"status": "ok"}


# --- Verificación del webhook ---
@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Token inválido", status_code=403)


# --- Función de paginación simple ---
def paginar(lista, pagina=1, por_pagina=5):
    total = len(lista)
    total_paginas = (total + por_pagina - 1) // por_pagina
    pagina = max(1, min(pagina, total_paginas))  # Evita pasar de los límites

    inicio = (pagina - 1) * por_pagina
    fin = inicio + por_pagina
    items = lista[inicio:fin]

    # Botones de navegación
    if pagina < total_paginas:
        items.append({"id": f"next_{pagina + 1}", "title": "➡️ Siguiente página"})
    if pagina > 1:
        items.insert(0, {"id": f"prev_{pagina - 1}", "title": "⬅️ Página anterior"})

    return {"items": items, "pagina": pagina, "total": total_paginas}


# --- Menú con paginación ---
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
        {"id": "cat_all", "title": "📋 Ver todas las comidas"},
    ]

    paginacion = paginar(categorias, pagina)

    return {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🍴 Menú GordoEats"},
            "body": {
                "text": f"Elegí una categoría 👇\n"
                        f"(Página {paginacion['pagina']} de {paginacion['total']})"
            },
            "action": {
                "button": "Ver categorías",
                "sections": [
                    {"title": "Categorías", "rows": paginacion["items"]}
                ]
            },
        },
    }


# --- Webhook principal ---
@app.post("/webhook")
async def recibir_mensaje(request: Request):
    try:
        data = await request.json()
        resultado = procesar_mensaje_recibido(data)

        if not resultado:
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        numero, mensaje, tipo = resultado
        texto = mensaje.lower().strip()

        if texto in ["hola", "buenas", "hi"]:
            enviar_mensaje_whatsapp(numero, "¡Hola! 👋 Juan es un panfleto")
        elif texto in ["ayuda", "help"]:
            enviar_mensaje_whatsapp(numero, "📋 Comandos:\n- hola\n- info\n- menu")
        elif texto in ["info", "informacion"]:
            enviar_mensaje_whatsapp(numero, "Soy un Panfleto")
        elif texto.startswith("menu"):
            # Permite escribir "menu 2" para ir a la página 2, por ejemplo
            partes = texto.split()
            pagina = int(partes[1]) if len(partes) > 1 and partes[1].isdigit() else 1
            msg = menu_categorias(numero, pagina)
            enviar_mensaje_whatsapp(numero, msg, usar_template=False)
        else:
            enviar_mensaje_whatsapp(numero, f"Recibí tu mensaje: {mensaje}")

        return PlainTextResponse("EVENT_RECEIVED", status_code=200)

    except Exception:
        traceback.print_exc()
        return PlainTextResponse("ERROR", status_code=500)
