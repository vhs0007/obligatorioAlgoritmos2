import os
import json
from google import genai
from google.genai import types
from Util.estado import get_estado, update_estado
from Util.database import get_db_session, Producto
from Util.mensajeria import enviar_mensaje_whatsapp

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

acciones_posibles = [
    "flujo_inicio",
    "flujo_categorias",
    "flujo_productos",
    "flujo_cantidad",
    "mostrar_carrito",
    "sacar_producto",
    "confirmar_pedido",
    "buscar_producto_directo"
]


def buscar_producto_directo(texto, db):
    palabras = texto.lower().split()
    cantidad = 1

    for i, p in enumerate(palabras):
        if p.isdigit():
            cantidad = int(p)
            palabras.pop(i)
            break

    query = " ".join(palabras)
    producto = db.query(Producto).filter(Producto.nombre.ilike(f"%{query}%")).first()

    if producto:
        return producto, cantidad

    return None, None


def procesar_mensaje_gemini(numero, mensaje):
    estado = get_estado(numero)

    prompt = f"""
    Usuario mensaje: "{mensaje}"
    Estado actual: "{estado}"

    Elegí una acción del listado: {acciones_posibles}

    Si el usuario escribe un mensaje que contiene producto + cantidad
    detectarlo aunque no esté en el flujo correspondiente.

    Si el usuario pide ver el carrito, usar: mostrar_carrito
    Si pide borrar algo del carrito: sacar_producto
    Si dice confirmar pedido: confirmar_pedido
    """

    response = client.models.generate_content(
        model="gemini-1.5-flash",
        contents=prompt,
        config=types.GenerateContentConfig(
            temperature=0.2,
            response_mime_type="application/json"
        )
    )

    data = json.loads(response.text)
    accion = data.get("accion")

    db = get_db_session()

    producto, cantidad = buscar_producto_directo(mensaje, db)
    if producto:
        from Util.carrito import agregar_producto_carrito
        agregar_producto_carrito(numero, producto.id, cantidad)
        update_estado(numero, "flujo_cantidad")
        return enviar_mensaje_whatsapp(numero, f"Agregué {cantidad} x {producto.nombre} al carrito.")

    if accion == "flujo_inicio":
        update_estado(numero, "inicio")
        return enviar_mensaje_whatsapp(numero, "¡Bienvenido! ¿Qué estás buscando?")

    if accion == "flujo_categorias":
        update_estado(numero, "categorias")
        return enviar_mensaje_whatsapp(numero, "Mostrando categorías...")

    if accion == "flujo_productos":
        update_estado(numero, "productos")
        return enviar_mensaje_whatsapp(numero, "Mostrando productos...")

    if accion == "mostrar_carrito":
        from Util.carrito import obtener_carrito_formateado
        carrito = obtener_carrito_formateado(numero)
        return enviar_mensaje_whatsapp(numero, carrito)

    if accion == "sacar_producto":
        from Util.carrito import quitar_producto_carrito
        quitar_producto_carrito(numero)
        return enviar_mensaje_whatsapp(numero, "Producto eliminado del carrito.")

    if accion == "confirmar_pedido":
        update_estado(numero, "confirmado")
        return enviar_mensaje_whatsapp(numero, "Perfecto. Pedido confirmado.")

    return enviar_mensaje_whatsapp(numero, "No te entendí, ¿me repetís?")
