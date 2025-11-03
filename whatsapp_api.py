"""
Módulo para interactuar con la API de WhatsApp Business de Meta.
Permite enviar y recibir mensajes.
"""

import requests
import os
import json
from typing import Dict, Optional, Union, Tuple


# ===================== CONFIGURACIÓN =====================
WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN") or "EAAS2SGNAVIABPyYN1XI8ZAXj4G2IEF9PEPqyLgC51d1ZCXblVGlUuCNIgd8s6ewr1ZBJcaoGPZBZBsesoZARFZAsdBCCAzlTZAS6QQRLFhAwR6QEEkVy6b9QCxtvMWsEtLZAiBRyvPQ5Gzmq1ZBVH25PF1mwFIwaPHMz9oVxvm89eZBKAoeCKlAdQe25ioe8ZCjgikYhguncqqJJOKq3pZATCj317EZCu9hrBOIzfFAYISJw597yXQVJlR4dde7peXcYRkauMb1ZBRaCSQrq54zFZA7ZAdhz6"
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN") or "Chacalitas2025"

# Si el ID no está en el entorno, usar el fijo de sandbox o prueba
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "871681339360716")


# ===================== FUNCIONES AUXILIARES =====================

def normalizar_numero_telefono(numero: str) -> str:
    """Normaliza el número de teléfono (elimina espacios y agrega + si falta)."""
    numero = numero.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not numero.startswith("+"):
        numero = "+" + numero
    return numero


# ===================== FUNCIONES PARA ENVIAR MENSAJES =====================

def enviar_mensaje_whatsapp(
    numero_telefono: str,
    mensaje: Union[str, Dict],
    usar_template: bool = False
) -> Dict:
    """
    Envía un mensaje por WhatsApp.
    Si usar_template=True, usa el template 'hello_world'.
    """
    if not numero_telefono or not mensaje:
        return {'success': False, 'error': 'Número y mensaje son obligatorios'}

    numero = normalizar_numero_telefono(numero_telefono)
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }

    # Detectar si es un dict interactivo
    if isinstance(mensaje, dict):
        payload = mensaje  # Ya es el JSON correcto para mensajes interactivos
    elif usar_template:
        payload = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "template",
            "template": {"name": "hello_world", "language": {"code": "en_US"}}
        }
    else:
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero,
            "type": "text",
            "text": {"body": mensaje},
        }

    try:
        print(f"📤 Enviando mensaje a {numero}...")
        response = requests.post(url, headers=headers, json=payload, timeout=15)
        data = response.json()

        if response.status_code == 200:
            msg_id = data.get("messages", [{}])[0].get("id", "")
            return {"success": True, "message_id": msg_id, "response": data}
        else:
            err = data.get("error", {})
            return {
                "success": False,
                "error": f"{err.get('message', 'Error desconocido')} (Código {err.get('code')})",
                "response": data,
            }

    except Exception as e:
        return {"success": False, "error": str(e)}


# ===================== FUNCIONES PARA RECIBIR MENSAJES =====================

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
