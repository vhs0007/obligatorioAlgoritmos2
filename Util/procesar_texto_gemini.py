import os
import json
from google import genai
from google.genai import types
from Util.estado import get_estado

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

def procesar_texto_gemini(texto: str, chat=None, numero: str = None) -> dict:
    if not numero:
        raise ValueError("El parámetro 'numero' es requerido")
    estado = get_estado(numero)

    prompt = f"""Eres un orquestador de flujo de conversación para un sistema de entrega de productos.
El usuario escribió: {texto}, el estado actual es: {estado},
las palabras clave posibles son: {palabras_clave},
las acciones posibles son: {acciones_posibles} devuelve la acción a ejecutar y el estado actualizado los posibles estados son: {estados_posibles} según el mensaje del usuario correspondiente.
Si el mensaje contiene una palabra clave, devuelve la acción correspondiente.
Si no contiene ninguna palabra clave, devuelve el flujo de inicio o una acción similar.
Devuelve un JSON con la acción a ejecutar y el estado actualizado.
{{
    "accion": "flujo_inicio",
    "estado": "inicio"
}}"""
    try:
        response = client.models.generate_content(
            model="gemini-2.5-flash",
            contents=[prompt, "Devolveme sólo un JSON en la respuesta, sin explicaciones."],
            config=types.GenerateContentConfig(
                thinking_config=types.ThinkingConfig(thinking_budget=0)
            ),
        )
        
        # Obtener el texto de la respuesta
        response_text = response.text if hasattr(response, 'text') and response.text else ""
        
        if not response_text:
            print("⚠️ Respuesta vacía de Gemini, usando acción por defecto")
            return {"accion": "flujo_inicio", "estado": "inicio"}
        
        # Intentar extraer JSON de la respuesta (puede tener texto adicional)
        response_text = response_text.strip()
        
        # Buscar el JSON en la respuesta (puede estar entre ```json o solo ser el JSON)
        if "```json" in response_text:
            # Extraer JSON de un bloque de código
            start = response_text.find("```json") + 7
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        elif "```" in response_text:
            # Extraer JSON de un bloque de código sin especificar json
            start = response_text.find("```") + 3
            end = response_text.find("```", start)
            if end != -1:
                response_text = response_text[start:end].strip()
        
        # Buscar el primer { y último } para extraer solo el JSON
        first_brace = response_text.find("{")
        last_brace = response_text.rfind("}")
        
        if first_brace != -1 and last_brace != -1 and last_brace > first_brace:
            response_text = response_text[first_brace:last_brace + 1]
        
        # Parsear el JSON
        resultado = json.loads(response_text)
        
        # Validar que tenga los campos esperados
        if "accion" not in resultado:
            print(f"⚠️ Respuesta de Gemini no tiene 'accion', usando por defecto. Respuesta: {response_text}")
            return {"accion": "flujo_inicio", "estado": resultado.get("estado", "inicio")}
        
        return resultado
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Error al parsear JSON de Gemini: {e}")
        print(f"📝 Respuesta recibida: {response_text if 'response_text' in locals() else 'N/A'}")
        return {"accion": "flujo_inicio", "estado": "inicio"}
    except Exception as e:
        print(f"⚠️ Error al procesar con Gemini: {type(e).__name__} -> {e}")
        return {"accion": "flujo_inicio", "estado": "inicio"}

