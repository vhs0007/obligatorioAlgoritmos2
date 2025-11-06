from whatsapp_api import enviar_mensaje_whatsapp
from .Data_prueba import categorias
from .state import get_session, reset_session, clear_cart
from .mensaje_producto import lista_productos
from .carrito import add_to_cart, detalle_carrito


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


def mostrar_productos(numero, categoria_id=None):
    sesion = get_session(numero)
    if categoria_id:
        sesion["filter"] = categoria_id
    payload = lista_productos(numero, sesion.get("page", 1), sesion.get("filter"), sesion.get("order_asc", True))
    return enviar_mensaje_whatsapp(numero, payload)


def mostrar_carrito(numero):
    resumen = detalle_carrito(numero)
    if resumen["items_count"] == 0:
        return enviar_mensaje_whatsapp(numero, "🛒 Tu carrito está vacío. Escribí *menu* para ver productos.")
    cuerpo = (
        resumen["body"]
        + f"\n\n💵 Total: ${resumen['total']}\n\n"
          "Opciones:\n"
          "1 Quitar producto\n"
          "2 Seguir pidiendo\n"
          "3 Confirmar pedido"
    )
    return enviar_mensaje_whatsapp(numero, cuerpo)


def confirmar_pedido(numero):
    return enviar_mensaje_whatsapp(numero, "📍 Enviá tu ubicación para calcular el envío.")


def handle_text(numero, mensaje):
    sesion = get_session(numero)
    estado = sesion.get("state", "inicio")
    mensaje = mensaje.lower().strip()

    if estado == "inicio":
        return flujo_inicio(numero, mensaje, sesion)
    if estado == "viendo_categorias":
        return flujo_categorias(numero, mensaje, sesion)
    if estado == "viendo_productos":
        return flujo_productos(numero, mensaje, sesion)
    if estado == "viendo_carrito":
        return flujo_carrito(numero, mensaje, sesion)
    if estado == "confirmando":
        return flujo_confirmacion(numero, mensaje, sesion)

    reset_session(numero)
    return enviar_mensaje_whatsapp(numero, "⚠️ Estado inválido. Escribí *menu* para empezar de nuevo.")


def flujo_inicio(numero, mensaje, sesion):
    if mensaje in ("menu", "hola", "hi", "buenas", "buenos dias"):
        sesion["state"] = "viendo_categorias"
        return enviar_mensaje_whatsapp(numero, menu_categorias(numero))
    if mensaje == "carrito":
        sesion["state"] = "viendo_carrito"
        return mostrar_carrito(numero)
    return enviar_mensaje_whatsapp(numero, "👋 Escribí *menu* para ver productos o *carrito* para ver tu pedido.")


def flujo_categorias(numero, mensaje, sesion):
    if mensaje.startswith("cat_"):
        sesion["filter"] = mensaje
        sesion["state"] = "viendo_productos"
        return mostrar_productos(numero, mensaje)
    if mensaje == "salir":
        reset_session(numero)
        return enviar_mensaje_whatsapp(numero, "👋 Cancelado. Escribí *menu* para empezar de nuevo.")
    return enviar_mensaje_whatsapp(numero, "⚠️ Elegí una categoría del menú.")


def flujo_productos(numero, mensaje, sesion):
    if mensaje == "carrito":
        sesion["state"] = "viendo_carrito"
        return mostrar_carrito(numero)
    if mensaje == "menu":
        sesion["state"] = "viendo_categorias"
        return enviar_mensaje_whatsapp(numero, menu_categorias(numero))
    if mensaje.startswith("add_"):
        sesion["esperando_cantidad"] = mensaje.replace("add_", "")
        return enviar_mensaje_whatsapp(numero, "Escribi la cantidad con observacion")
    if sesion.get("esperando_cantidad"):
        prod_id = sesion.pop("esperando_cantidad")
        partes = mensaje.split()
        try:
            cantidad = int(partes[0])
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            return enviar_mensaje_whatsapp(numero, "⚠️ Cantidad inválida. Escribí un número válido (ej: 2).")
        aclaracion = " ".join(partes[1:]) if len(partes) > 1 else ""
        ok, err = add_to_cart(numero, prod_id, cantidad, aclaracion)
        if not ok:
            return enviar_mensaje_whatsapp(numero, f"❌ Error al agregar: {err}")
        return enviar_mensaje_whatsapp(numero, f"✅ {cantidad} agregado(s) al carrito.\nEscribí *carrito* para ver tu pedido o *menu* para volver.")
    return enviar_mensaje_whatsapp(numero, "🍔 Escribí *carrito* para ver tu pedido o *menu* para volver al inicio.")


def flujo_carrito(numero, mensaje, sesion):
    if mensaje in ("2", "seguir", "seguir pidiendo"):
        sesion["state"] = "viendo_categorias"
        return enviar_mensaje_whatsapp(numero, menu_categorias(numero))
    if mensaje in ("3", "confirmar"):
        sesion["state"] = "confirmando"
        return confirmar_pedido(numero)
    if mensaje in ("1", "quitar", "eliminar"):
        return enviar_mensaje_whatsapp(numero, "✏️ Escribí el nombre del producto a quitar (a implementar).")
    if mensaje in ("salir", "cancelar"):
        reset_session(numero)
        clear_cart(numero)
        return enviar_mensaje_whatsapp(numero, "🧹 Pedido cancelado. Escribí *menu* para comenzar de nuevo.")
    return enviar_mensaje_whatsapp(numero, "📋 Escribí 1 para quitar, 2 para seguir pidiendo o 3 para confirmar.")


def flujo_confirmacion(numero, mensaje, sesion):
    if mensaje in ("cancelar", "salir"):
        reset_session(numero)
        return enviar_mensaje_whatsapp(numero, "❌ Pedido cancelado.")
    return enviar_mensaje_whatsapp(numero, "📍 Enviá tu ubicación para calcular el envío.")


def handle_location(numero, contenido):
    try:
        lat, lon = contenido.split(",")
        msg = f"📍 Recibí tu ubicación:\nLatitud: {lat}\nLongitud: {lon}"
        return enviar_mensaje_whatsapp(numero, msg)
    except Exception:
        return enviar_mensaje_whatsapp(numero, "⚠️ No se pudo procesar la ubicación correctamente.")
