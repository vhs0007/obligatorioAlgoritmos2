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
    """
    Busca un producto en la base de datos por nombre (búsqueda parcial, case insensitive).
    Retorna el primer producto encontrado o None si no hay coincidencias.
    """
    db = get_db_session()
    try:
        # Buscar productos que contengan el nombre (case insensitive)
        productos = db.query(Producto).filter(
            Producto.nombre.ilike(f"%{nombre}%")
        ).all()
        
        if productos:
            # Retornar el primer producto encontrado
            producto = productos[0]
            return {
                "producto_id": producto.idproducto,
                "nombre": producto.nombre
            }
        else:
            return {
                "producto_id": None,
                "nombre": None
            }
    except Exception as e:
        print(f"⚠️ Error al buscar producto: {e}")
        return {
            "producto_id": None,
            "nombre": None
        }
    finally:
        db.close()

def procesar_texto_gemini(texto: str, chat=None, numero: str = None) -> dict:
    if not numero:
        raise ValueError("El parámetro 'numero' es requerido")
    estado = get_estado(numero)
    waiting_for = estado.get("waiting_for")
    estado_actual = estado.get("state", "inicio")

    # Determinar opciones disponibles según el estado
    opciones_disponibles = []
    if estado_actual == "inicio" or not estado_actual:
        opciones_disponibles = [
            "- 'menu' o 'menú' → Ver categorías de productos",
            "- 'carrito' → Ver carrito actual",
            "- 'ayuda' → Ver ayuda"
        ]
    elif estado_actual == "viendo_categorias" or waiting_for == "flujo_categorias":
        opciones_disponibles = [
            "- 'menu' o 'menú' → Ver categorías (ya está viendo)",
            "- Seleccionar una categoría (se hace con botones interactivos)",
            "- 'carrito' → Ver carrito",
            "- 'ayuda' → Ver ayuda"
        ]
    elif estado_actual == "viendo_productos" or waiting_for == "flujo_productos":
        opciones_disponibles = [
            "- Seleccionar un producto (se hace con botones interactivos)",
            "- 'carrito' → Ver carrito",
            "- 'menu' → Volver a categorías",
            "- 'ayuda' → Ver ayuda"
        ]
    elif estado_actual == "esperando_cantidad" or waiting_for == "flujo_cantidad":
        opciones_disponibles = [
            "- Escribir un número (cantidad) → Ej: '2' o '2 sin cebolla'",
            "- 'cancelar' → Cancelar y volver al inicio"
        ]
    elif estado_actual == "en_carrito" or waiting_for == "flujo_carrito":
        opciones_disponibles = [
            "- '1', 'quitar' o 'eliminar' → Quitar producto del carrito",
            "- '2', 'seguir' o 'seguir pidiendo' → Continuar agregando productos",
            "- '3' o 'confirmar' → Confirmar pedido y enviar ubicación",
            "- 'carrito' → Ver carrito nuevamente",
            "- 'cancelar' o 'salir' → Cancelar pedido"
        ]
    elif estado_actual == "confirmando" or waiting_for == "flujo_confirmacion":
        opciones_disponibles = [
            "- Enviar ubicación (latitud, longitud) → Ej: '-31.38, -57.96'",
            "- 'cancelar' o 'salir' → Cancelar pedido"
        ]
    else:
        opciones_disponibles = [
            "- 'menu' → Ver menú",
            "- 'carrito' → Ver carrito",
            "- 'ayuda' → Ver ayuda"
        ]

    opciones_texto = "\n".join(opciones_disponibles)

    # Construir información sobre waiting_for
    info_waiting_for = ""
    if waiting_for:
        info_waiting_for = f"""
IMPORTANTE - FUNCIÓN ESPERADA ACTIVA:
El sistema está esperando que el usuario responda a: "{waiting_for}"
Esto significa que el usuario está en medio de un flujo específico.

DEBES EVALUAR:
1. ¿El mensaje del usuario responde a lo que se espera en "{waiting_for}"?
   - Si SÍ → establece "respetar_waiting_for": true y devuelve la acción correspondiente
   - Si NO (el usuario quiere cambiar de flujo, ej: escribe "menu", "carrito", "cancelar") → establece "respetar_waiting_for": false y cambia la acción

Ejemplos:
- Si waiting_for es "flujo_cantidad" y el usuario escribe "2" → respetar_waiting_for: true, accion: "flujo_cantidad"
- Si waiting_for es "flujo_cantidad" y el usuario escribe "menu" → respetar_waiting_for: false, accion: "flujo_categorias"
- Si waiting_for es "flujo_carrito" y el usuario escribe "1" → respetar_waiting_for: true, accion: "flujo_carrito"
- Si waiting_for es "flujo_carrito" y el usuario escribe "menu" → respetar_waiting_for: false, accion: "flujo_categorias"
"""

    # Definir tool schema para buscar_producto
    tool_schema = {
        "name": "buscar_producto",
        "description": "Busca un producto en la base de datos por nombre. Úsala cuando el usuario mencione un producto específico que quiere agregar al carrito.",
        "parameters": {
            "type": "object",
            "properties": {
                "nombre": {
                    "type": "string",
                    "description": "Nombre del producto a buscar (puede ser parcial, ej: 'coca cola', 'hamburguesa', 'pizza muzzarella')"
                }
            },
            "required": ["nombre"]
        }
    }

    prompt = f"""Eres un orquestador de flujo de conversación para un sistema de entrega de productos.

CONTEXTO ACTUAL:
- Estado del usuario: {estado_actual}
- Función esperada (waiting_for): {waiting_for if waiting_for else "ninguna"}
- Mensaje del usuario: "{texto}"
{info_waiting_for}

OPCIONES DISPONIBLES EN ESTE ESTADO:
{opciones_texto}

ACCIONES DEL SISTEMA DISPONIBLES: {acciones_posibles}

PALABRAS CLAVE Y SUS ACCIONES:
- "menu" o "menú" → flujo_categorias (mostrar categorías)
- "carrito" → flujo_carrito (ver carrito)
- "ayuda" → Mostrar ayuda (comando especial)
- "productos" → flujo_productos (ver productos)
- "confirmar" → flujo_confirmacion (confirmar pedido)

COMANDOS ESPECIALES DEL CARRITO (cuando estado es "en_carrito"):
- "1", "quitar", "eliminar" → Quitar producto (se maneja en flujo_carrito)
- "2", "seguir", "seguir pidiendo" → Continuar comprando (se maneja en flujo_carrito)
- "3", "confirmar" → Confirmar pedido (se maneja en flujo_carrito)

NOTA: Los comandos técnicos como "cat_*", "prod_*", "add_*" son comandos internos de botones interactivos y NO deben procesarse aquí.

DETECCIÓN DE PRODUCTOS Y CANTIDADES EN LENGUAJE NATURAL:
Si el usuario escribe un mensaje que menciona un producto y una cantidad (ej: "Quiero 3 Coca Cola zero 1.5", "Dame 2 hamburguesas", "Necesito 1 pizza muzzarella"):
1. DEBES usar la función buscar_producto para encontrar el producto en la base de datos
2. Extrae la cantidad mencionada (número)
3. Una vez que tengas el producto_id y la cantidad:
   - Establece "accion": "flujo_carrito"
   - Establece "estado": "en_carrito"
   - Establece "producto_id": [id del producto encontrado]
   - Establece "cantidad_detectada": [cantidad extraída]
   - Establece "respetar_waiting_for": true
   - Establece "actualizar_waiting_for": "flujo_carrito"
   - Establece "mensaje": [mensaje amigable confirmando lo agregado, ej: "Genial 😄 Agregué 3 Coca Cola Zero. ¿Confirmamos?"]

Si el producto no se encuentra:
- Establece "accion": "flujo_inicio"
- Establece "mensaje": [mensaje amigable indicando que no se encontró el producto y sugiriendo usar el menú]
- Establece "respetar_waiting_for": false

Si no se puede detectar la cantidad:
- Establece "accion": "flujo_cantidad"
- Establece "mensaje": [pregunta al usuario la cantidad]
- Establece "respetar_waiting_for": false

MANEJO DE SALUDOS Y MENSAJES FUERA DE CONTEXTO:

CASO A - Saludo sin estado de flujo asignado (estado_actual es "inicio" o no hay waiting_for):
Si el mensaje es un saludo convencional (hola, buenos días, buenas tardes, buenas noches, hi, hello, etc.) o un mensaje que no corresponde al flujo esperado:
- Establece "accion": "flujo_inicio"
- Establece "estado": "inicio"
- Establece "respetar_waiting_for": false
- Establece "mensaje": [GENERA UNA RESPUESTA AMIGABLE AL SALUDO Y PREGUNTA QUÉ NECESITA EL USUARIO]
  Ejemplo de mensaje: "¡Hola! 👋 ¿En qué puedo ayudarte hoy? Podés escribir *menu* para ver nuestras categorías de productos."

CASO B - Saludo mientras se espera respuesta específica (hay waiting_for activo):
Si el mensaje es un saludo o mensaje que NO responde a lo esperado en "{waiting_for if waiting_for else 'ninguna'}":
- Establece "accion": [la acción correspondiente al waiting_for actual]
- Establece "respetar_waiting_for": true (para mantener el flujo)
- Establece "mensaje": [GENERA UNA RESPUESTA AMIGABLE QUE RECUERDE AL USUARIO QUÉ SE ESPERA]
  Ejemplos según waiting_for:
  - Si waiting_for es "flujo_carrito": "¡Hola! 😊 Estoy esperando que elijas una opción del carrito. Podés escribir '1' para quitar un producto, '2' para seguir comprando, o '3' para confirmar tu pedido."
  - Si waiting_for es "flujo_cantidad": "¡Hola! 😊 Necesito que me indiques la cantidad que deseas. Escribí un número, por ejemplo: '2' o '2 sin cebolla'."
  - Si waiting_for es "flujo_confirmacion": "¡Hola! 😊 Para confirmar tu pedido necesito tu ubicación. Enviá las coordenadas en formato: latitud, longitud (ej: -31.38, -57.96)"

INSTRUCCIONES DE ORQUESTACIÓN:
1. PRIMERO: Detecta si el mensaje es un saludo o mensaje fuera de contexto usando los casos A y B arriba
2. Si hay waiting_for activo, EVALÚA primero si el mensaje responde a lo esperado o quiere cambiar de flujo
3. Si el mensaje es "menu", "menú" o similar → devuelve "flujo_categorias" (respetar_waiting_for: false)
4. Si el mensaje es "carrito" → devuelve "flujo_carrito" (respetar_waiting_for: false si hay otro waiting_for)
5. Si el mensaje es "ayuda" → devuelve "flujo_inicio" (respetar_waiting_for: false)
6. Si waiting_for es "flujo_cantidad" y el mensaje empieza con un número → respetar_waiting_for: true, accion: "flujo_cantidad"
7. Si waiting_for es "flujo_carrito" y el mensaje es "1", "2", "3", "quitar", "seguir", "confirmar" → respetar_waiting_for: true, accion: "flujo_carrito"
8. Si waiting_for es "flujo_confirmacion" y el mensaje parece una ubicación (dos números separados por coma) → respetar_waiting_for: true, accion: "flujo_confirmacion"
9. Si no hay contexto claro o el mensaje no coincide con ninguna opción → devuelve "flujo_inicio" (respetar_waiting_for: false)

IMPORTANTE: 
- Siempre devuelve un JSON válido con "accion", "estado" y "respetar_waiting_for"
- El "estado" debe ser uno de: {list(estados_posibles.keys())}
- Si el usuario escribe algo que no entiendes, redirige a "flujo_inicio"
- Si cambias de flujo (respetar_waiting_for: false), puedes opcionalmente incluir "actualizar_waiting_for" con el nuevo flujo esperado
- Si generas un "mensaje" para el usuario, este será enviado directamente y NO se ejecutará la acción del flujo

Devuelve SOLO un JSON con este formato:
{{
    "accion": "flujo_inicio",
    "estado": "inicio",
    "respetar_waiting_for": false,
    "mensaje": "Texto opcional que se enviará al usuario",
    "actualizar_waiting_for": "flujo_categorias",
    "producto_id": 123,
    "cantidad_detectada": 3
}}

NOTA: Los campos "producto_id" y "cantidad_detectada" solo deben incluirse cuando detectes un producto y cantidad en el mensaje del usuario."""
    
    # Configurar tools para Gemini
    tools = [types.Tool(function_declarations=[types.FunctionDeclaration(
        name=tool_schema["name"],
        description=tool_schema["description"],
        parameters=types.Schema(
            type_=types.Type.OBJECT,
            properties={
                "nombre": types.Schema(
                    type_=types.Type.STRING,
                    description=tool_schema["parameters"]["properties"]["nombre"]["description"]
                )
            },
            required=tool_schema["parameters"]["required"]
        )
    )])]
    
    try:
        # Primera llamada a Gemini con tools
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, "Devolveme sólo un JSON en la respuesta, sin explicaciones."],
            config=types.GenerateContentConfig(
                tools=tools,
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        
        # Verificar si Gemini quiere ejecutar una función
        function_results = []
        
        if hasattr(response, 'candidates') and response.candidates:
            candidate = response.candidates[0]
            if hasattr(candidate, 'content') and candidate.content:
                parts = candidate.content.parts if hasattr(candidate.content, 'parts') else []
                
                # Buscar tool calls en la respuesta
                tool_calls = []
                for part in parts:
                    if hasattr(part, 'function_call') and part.function_call:
                        tool_calls.append(part)
                        tool_calls_found = True
                
                # Si hay tool calls, ejecutarlos y reenviar a Gemini
                if tool_calls:
                    for tool_call in tool_calls:
                        func_name = tool_call.function_call.name
                        # Los args pueden venir como string JSON o como dict
                        if hasattr(tool_call.function_call, 'args'):
                            if isinstance(tool_call.function_call.args, str):
                                args = json.loads(tool_call.function_call.args)
                            else:
                                args = tool_call.function_call.args
                        else:
                            args = {}
                        
                        if func_name == "buscar_producto":
                            nombre_producto = args.get("nombre", "")
                            resultado = buscar_producto(nombre_producto)
                            function_results.append(types.Part(
                                function_response=types.FunctionResponse(
                                    name=func_name,
                                    response=resultado
                                )
                            ))
                    
                    # Reenviar resultado a Gemini para que genere la respuesta final
                    contents_with_result = [
                        prompt,
                        "Devolveme sólo un JSON en la respuesta, sin explicaciones.",
                        *[types.Part(function_call=tc.function_call) for tc in tool_calls],
                        *function_results
                    ]
                    
                    response = client.models.generate_content(
                        model="gemini-2.5-flash",
                        contents=contents_with_result,
                        config=types.GenerateContentConfig(
                            tools=tools,
                            thinking_config=types.ThinkingConfig(thinking_budget=0)
                        ),
                    )
        
        # Obtener el texto de la respuesta
        response_text = response.text if hasattr(response, 'text') and response.text else ""
        
        if not response_text:
            print("⚠️ Respuesta vacía de Gemini, usando acción por defecto")
            return {"accion": "flujo_inicio", "estado": "inicio"}
        
        response_text = response_text.strip()
        
        if "```json" in response_text:
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        elif "```" in response_text:
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            response_text = response_text[first_brace:last_brace + 1]
        
        resultado = json.loads(response_text)
        print(f"Resultado: {resultado}")

        if "accion" not in resultado:
            print(f"⚠️ Respuesta de Gemini no tiene 'accion', usando por defecto. Respuesta: {response_text}")
            return {
                "accion": "flujo_inicio",
                "estado": resultado.get("estado", "inicio"),
                "respetar_waiting_for": False
            }

        # Asegurar que los campos adicionales tengan valores por defecto
        resultado.setdefault("respetar_waiting_for", False)
        resultado.setdefault("estado", "inicio")
        
        # Si no hay actualizar_waiting_for pero respetar_waiting_for es true, no necesitamos actualizar
        # Si respetar_waiting_for es false y hay una nueva acción, limpiar waiting_for (se hace en handle_text)

        return resultado
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Error al parsear JSON de Gemini: {e}")
        print(f"📝 Respuesta recibida: {response_text if 'response_text' in locals() else 'N/A'}")
        return {"accion": "flujo_inicio", "estado": "inicio"}
    except Exception as e:
        print(f"⚠️ Error al procesar con Gemini: {type(e).__name__} -> {e}")
        return {"accion": "flujo_inicio", "estado": "inicio"}

