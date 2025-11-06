from whatsapp_api import enviar_mensaje_whatsapp
from utils.Data_prueba import categorias
from state import get_session, reset_session
from utils.products import build_product_list_message
from utils.cart import add_to_cart, detalle_carrito


def menu_categorias(numero):
    secciones = [{
        "title": "Categorías de comidas",
        "rows": [{"id": c["id"], "title": c["nombre"]} for c in categorias],
    }]

    return {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🍔 ¡Bienvenido a GordoEats! 😋"},
            "body": {"text": "Seleccioná una categoría para ver nuestras opciones:"},
            "footer": {"text": "Usá el menú para elegir 👇"},
            "action": {"button": "Ver categorías", "sections": secciones},
        },
    }


def mostrar_productos(numero):
    sesion = get_session(numero)
    payload = build_product_list_message(numero, sesion["page"], sesion["filter"], sesion["order_asc"])
    return enviar_mensaje_whatsapp(numero, payload, usar_template=False)

def mostrar_carrito(numero):
    resumen = detalle_carrito(numero)
    if resumen["items_count"] == 0:
        return enviar_mensaje_whatsapp(numero, "🛒 Tu carrito está vacío. Escribí *menu* para ver productos.")
    cuerpo = resumen["body"] + f"\n\n💵 Total: ${resumen['total']}\n\nOpciones:\n1️⃣ Quitar producto\n2️⃣ Seguir pidiendo\n3️⃣ Confirmar pedido"
    return enviar_mensaje_whatsapp(numero, cuerpo)


def confirmar_pedido(numero):
    return enviar_mensaje_whatsapp(numero, "📍 Enviá tu ubicación para calcular el envío.")


def handle_text(numero, mensaje):
    mensaje_lower = mensaje.lower().strip()
    sesion = get_session(numero)

    respuestas = {
        ("hola", "hi", "hello", "buenos dias", "buenas tardes", "buenas noches"):
            "¡Hola! 👋 ¿En qué puedo ayudarte?",
        ("help", "ayuda", "ayudame"):
            "📋 Comandos:\n- Hola: saludo\n- Info: información del bot\n- Menu: ver productos\n- Carrito: ver tu pedido",
        ("info", "informacion", "información"):
            "🤖 Soy el bot de GordoEats, te ayudo a hacer tus pedidos más rápido 🍔",
    }

    for claves, respuesta in respuestas.items():
        if mensaje_lower in claves:
            return enviar_mensaje_whatsapp(numero, respuesta)

    if mensaje_lower == "menu":
        msg = menu_categorias(numero)
        return enviar_mensaje_whatsapp(numero, msg, usar_template=False)

    if mensaje_lower == "carrito":
        return mostrar_carrito(numero)

    if mensaje_lower in ("salir", "cancelar", "cancel"):
        from state import clear_cart
        reset_session(numero)
        clear_cart(numero)
        return enviar_mensaje_whatsapp(numero, "🧹 Se canceló el proceso. Volvés al inicio.")

    if sesion.get("esperando_cantidad"):
        prod_id = sesion.pop("esperando_cantidad")
        try:
            partes = mensaje.split()
            cantidad = int(partes[0])
            if cantidad <= 0:
                raise ValueError
        except:
            return enviar_mensaje_whatsapp(numero, "⚠️ Cantidad inválida. Escribí un número (ej: 2)")

        obs = " ".join(partes[1:]) if len(partes) > 1 else ""
        ok, err = add_to_cart(numero, prod_id, cantidad, obs)
        if not ok:
            return enviar_mensaje_whatsapp(numero, f"❌ Error: {err}")
        return enviar_mensaje_whatsapp(numero, f"✅ Agregados {cantidad} al carrito. Escribí *carrito* para ver tu pedido.")

    return enviar_mensaje_whatsapp(
        numero,
        f"✅ Recibí tu mensaje: \"{mensaje}\". Escribí 'Ayuda' para ver opciones."
    )

def handle_location(numero, contenido):
    try:
        lat, lon = contenido.split(",")
        msg = f"📍 Recibí tu ubicación:\nLatitud: {lat}\nLongitud: {lon}"
        return enviar_mensaje_whatsapp(numero, msg)
    except Exception as e:
        print(f"⚠️ Error al procesar ubicación: {e}")
        return enviar_mensaje_whatsapp(numero, "⚠️ No se pudo procesar la ubicación correctamente.")
