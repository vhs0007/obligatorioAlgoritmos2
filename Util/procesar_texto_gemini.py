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
    waiting_for = estado.get("waiting_for")
    estado_actual = estado.get("state", "inicio")

    prompt = f"""Eres un orquestador de flujo de conversación para un sistema de entrega de productos.

CONTEXTO ACTUAL:
- Estado del usuario: {estado_actual}
- Función esperada: {waiting_for if waiting_for else "ninguna"}
- Mensaje del usuario: "{texto}"

ACCIONES DISPONIBLES: {acciones_posibles}

PALABRAS CLAVE:
- "menu" o "menú" → flujo_categorias
- "productos" → flujo_productos  
- "carrito" → flujo_carrito
- "confirmar" → flujo_confirmacion

ESTADOS POSIBLES: {list(estados_posibles.keys())}

INSTRUCCIONES:
1. Si el mensaje contiene una palabra clave, devuelve la acción correspondiente.
2. Si el estado actual es "esperando_cantidad" o waiting_for es "flujo_cantidad" y el mensaje es un número, devuelve "flujo_cantidad".
3. Si el estado actual es "en_carrito" y el mensaje es "cancelar" o "salir", el sistema lo manejará automáticamente (no necesitas procesarlo).
4. Si no hay contexto claro, devuelve "flujo_inicio" para mostrar el menú.

IMPORTANTE: 
- Si el usuario escribe solo números y está esperando cantidad, devuelve "flujo_cantidad".
- Si el usuario escribe "cancelar" o "salir", el sistema lo maneja automáticamente.
- Siempre devuelve un JSON válido con "accion" y "estado".

Devuelve SOLO un JSON con este formato:
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
            return {"accion": "flujo_inicio", "estado": resultado.get("estado", "inicio")}
        
        return resultado
        
    except json.JSONDecodeError as e:
        print(f"⚠️ Error al parsear JSON de Gemini: {e}")
        print(f"📝 Respuesta recibida: {response_text if 'response_text' in locals() else 'N/A'}")
        return {"accion": "flujo_inicio", "estado": "inicio"}
    except Exception as e:
        print(f"⚠️ Error al procesar con Gemini: {type(e).__name__} -> {e}")
        return {"accion": "flujo_inicio", "estado": "inicio"}

