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
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, "Devolveme sólo un JSON en la respuesta, sin explicaciones."],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        ),
    )
    return json.loads(response.text)

