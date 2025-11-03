"""
Módulo para interactuar con la API de WhatsApp Business de Meta.
Permite enviar y recibir mensajes.
"""

import requests
import os
import json
from typing import Dict, Optional, Union, Tuple


WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN") or "EAAS2SGNAVIABPyYN1XI8ZAXj4G2IEF9PEPqyLgC51d1ZCXblVGlUuCNIgd8s6ewr1ZBJcaoGPZBZBsesoZARFZAsdBCCAzlTZAS6QQRLFhAwR6QEEkVy6b9QCxtvMWsEtLZAiBRyvPQ5Gzmq1ZBVH25PF1mwFIwaPHMz9oVxvm89eZBKAoeCKlAdQe25ioe8ZCjgikYhguncqqJJOKq3pZATCj317EZCu9hrBOIzfFAYISJw597yXQVJlR4dde7peXcYRkauMb1ZBRaCSQrq54zFZA7ZAdhz6"
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN") or "Chacalitas2025"

WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "871681339360716")



def normalizar_numero_telefono(numero: str) -> str:
    """Normaliza el número de teléfono (elimina espacios y agrega + si falta)."""
    numero = numero.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not numero.startswith("+"):
        numero = "+" + numero
    return numero



def enviar_mensaje_whatsapp(numero, mensaje):
    import requests
    import json

    url = f"https://graph.facebook.com/v17.0/{PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {ACCESS_TOKEN}",
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



def procesar_mensaje_recibido(webhook_data: Dict) -> Optional[Tuple[str, str, str]]:
    """Procesa un JSON recibido desde el webhook de WhatsApp."""
    try:
        if webhook_data.get("object") != "whatsapp_business_account":
            return None

        entry = webhook_data.get("entry", [{}])[0]
        changes = entry.get("changes", [{}])[0]
        value = changes.get("value", {})
        messages = value.get("messages", [])

        if not messages:
            return None

        message = messages[0]
        numero = message.get("from")
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
