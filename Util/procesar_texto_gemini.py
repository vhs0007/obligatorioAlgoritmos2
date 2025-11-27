import os
import json
from google import genai
from google.genai import types
from Models.chat import flujo_inicio, flujo_categorias, flujo_productos, flujo_cantidad, flujo_carrito, flujo_confirmacion
from Util.estado import get_estado

client = genai.Client(api_key=os.getenv("GEMINI_API_KEY"))

acciones_posibles = {
    "flujo_inicio": flujo_inicio,
    "flujo_categorias": flujo_categorias,
    "flujo_productos": flujo_productos,
    "flujo_cantidad": flujo_cantidad,
    "flujo_carrito": flujo_carrito,
    "flujo_confirmacion": flujo_confirmacion
}
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

def procesar_texto_gemini(texto: str, numero: str) -> str:
    estado = get_estado(numero)

    prompt = f" eres un orquestador de flujo de conversacion para un sistema de entrega de productos.
        el usuario escribio: {texto}, el estado actual es: {estado},
        las palabras clave posibles son: {palabras_clave},
        las acciones posibles son: {acciones_posibles} devuelve la accion a ejecutar y el estado actualizado los posibles estados son: {estados_posibles} segun el mensaje del usuario correspondiente.
        si el mensaje contiene una palabra clave, devuelve la accion correspondiente.
        si no contiene ninguna palabra clave, devuelve el flujo de inicio o una accion similar
        devolve un json con la accion a ejecutar y el estado actualizado.
        {
            "accion": "flujo_inicio",
            "estado": "inicio"
        }
        "
    response = client.models.generate_content(
        model="gemini-2.5-flash",
        contents=[prompt, "Devolveme sólo un JSON en la respuesta, sin explicaciones."],
        config=types.GenerateContentConfig(
            thinking_config=types.ThinkingConfig(thinking_budget=0)
        ),
    )
    return json.loads(response.text)

