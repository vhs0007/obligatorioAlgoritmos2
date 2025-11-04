"""
Módulo para interactuar con la API de WhatsApp Business de Meta.
Permite enviar y recibir mensajes.
"""

import requests
import os
import json
from typing import Dict, Optional, Tuple

WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN") or "<TU_TOKEN_DE_ACCESO>"
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN") or "Chacalitas2025"
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "871681339360716")


def normalizar_numero_telefono(numero: str) -> str:
    """Normaliza el número de teléfono (elimina espacios y agrega + si falta)."""
    numero = numero.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not numero.startswith("+"):
        numero = "+" + numero
    return numero


def enviar_mensaje_whatsapp(numero, mensaje, usar_template=True):
    """Envía un mensaje de texto o interactivo a través de la API de WhatsApp."""
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Si es texto
    if isinstance(mensaje, str):
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": mensaje}
        }
    # Si es un dict (mensaje interactivo)
    else:
        data = mensaje

    response = requests.post(url, headers=headers, json=data)
    print("➡️ Enviado:", json.dumps(data, indent=2))
    print("⬅️ Respuesta:", response.status_code, response.text)

    try:
        res_json = response.json()
        return {
            "success": response.status_code == 200,
            "message_id": res_json.get("messages", [{}])[0].get("id") if "messages" in res_json else None,
            "error": res_json.get("error")
        }
    except Exception as e:
        print("⚠️ Error al interpretar respuesta:", e)
        return {"success": False, "error": str(e)}


def procesar_mensaje_recibido(webhook_data: Dict) -> Optional[Tuple[str, str, str]]:
    """Procesa un JSON recibido desde el webhook de WhatsApp."""
    try:
        if webhook_data.get("object") != "whatsapp_business_account":
            return None

        entry = webhook_data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})

        # ⚠️ Evitar procesar mensajes enviados por el propio negocio
        if "statuses" in value:
            # Estos son ACKs o confirmaciones de envío
            return None

        messages = value.get("messages", [])
        if not messages:
            return None

        message = messages[0]
        numero = message.get("from")

        # 🚫 Evitar responderse a sí mismo
        if numero == WHATSAPP_PHONE_NUMBER_ID:
            print("🛑 Ignorando mensaje enviado por el propio bot.")
            return None

        tipo = message.get("type", "unknown")

        if tipo == "text":
            contenido = message.get("text", {}).get("body", "")
        elif tipo == "button":
            contenido = message.get("button", {}).get("text", "")
        elif tipo == "interactive":
            interactive = message.get("interactive", {})
            if interactive.get("type") == "button_reply":
                contenido = interactive["button_reply"].get("title", "")
            elif interactive.get("type") == "list_reply":
                contenido = interactive["list_reply"].get("title", "")
            else:
                contenido = "Interacción no reconocida"
        elif tipo == "location":
            loc = message.get("location", {})
            contenido = f"Ubicación: {loc.get('latitude')}, {loc.get('longitude')}"
        else:
            contenido = f"Mensaje tipo {tipo}"

        return (numero, contenido, tipo)

    except Exception as e:
        print(f"⚠️ Error al procesar mensaje recibido: {e}")
        return None
