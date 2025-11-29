import os
import json
from google import genai
from google.genai import types
from Util.estado import get_estado
from Util.database import get_db_session, Producto

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

acciones_posibles = [
    "flujo_inicio",
    "flujo_categorias",
    "flujo_productos",
    "flujo_cantidad",
    "flujo_carrito",
    "flujo_confirmacion"
]

palabras_clave = {
    "menu": "flujo_categorias",
    "productos": "flujo_productos",
    "cantidad": "flujo_cantidad",
    "carrito": "flujo_carrito",
    "confirmar": "flujo_confirmacion"
}

estados_posibles = {
    "inicio": "flujo_inicio",
    "categorias": "flujo_categorias",
    "productos": "flujo_productos",
    "cantidad": "flujo_cantidad",
    "carrito": "flujo_carrito",
    "confirmacion": "flujo_confirmacion"
}


def buscar_producto(nombre: str) -> dict:
    db = get_db_session()
    try:
        productos = db.query(Producto).filter(
            Producto.nombre.ilike(f"%{nombre}%")
        ).all()

        if productos:
            producto = productos[0]
            return {
                "producto_id": producto.idproducto,
                "nombre": producto.nombre
            }
        return None
    except:
        return None
    finally:
        db.close()


def procesar_texto_gemini(numero: str, texto: str) -> dict:
    estado = get_estado(numero)
    waiting_for = estado.get("waiting_for")
    estado_actual = estado.get("state", "inicio")

    opciones_disponibles = []
    if estado_actual == "inicio" or not estado_actual:
        opciones_disponibles = ["menu"]
    elif estado_actual == "categorias":
        opciones_disponibles = ["productos"]
    elif estado_actual == "productos":
        opciones_disponibles = ["cantidad"]
    elif estado_actual == "cantidad":
        opciones_disponibles = ["confirmar"]
    elif estado_actual == "carrito":
        opciones_disponibles = ["confirmar"]

    opciones_texto = "\n".join(opciones_disponibles)

    prompt = f"""
Sos un asistente que analiza el mensaje del usuario y respondés con JSON.

Texto del usuario:
"{texto}"

Estado actual:
"{estado_actual}"

Si encontrás un producto existente en la base, devolvé:
- producto_id
- cantidad_detectada si el usuario dijo un número

Devolvé siempre JSON.
Opciones disponibles ahora:
{opciones_texto}

Formato de respuesta:
{{
  "accion": "...",
  "producto_id": (opcional),
  "cantidad_detectada": (opcional),
  "mensaje": "..."
}}
"""

    tool_schema = {
        "name": "buscar_producto",
        "description": "Busca productos por nombre",
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre del producto a buscar"
                }
            },
            "required": ["nombre"]
        }
    }

    try:
        function_declaration = types.FunctionDeclaration(
            name=tool_schema["name"],
            description=tool_schema["description"],
            parameters=tool_schema["parameters"]
        )

        tools = [types.Tool(function_declarations=[function_declaration])]
    except:
        tools = None

    try:
        config_params = {
            "thinking_config": types.ThinkingConfig(thinking_budget=0)
        }
        if tools:
            config_params["tools"] = tools

        response = client.models.generate_content(
            model="gemini-1.5-flash-latest",
            contents=[prompt],
            config=types.GenerateContentConfig(**config_params),
        )

        response_text = response.text if hasattr(response, "text") else ""

        if not response_text:
            return {"accion": "fallback", "mensaje": "No te entendí, ¿me repetís?"}

        try:
            parsed = json.loads(response_text)
            return parsed
        except:
            return {"accion": "fallback", "mensaje": "No te entendí, ¿me repetís?"}

    except:
        return {"accion": "fallback", "mensaje": "Error procesando tu mensaje"}        return producto, cantidad

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
