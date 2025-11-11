import os
import requests
from Util.get_type import get_type

WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
WHATSAPP_ACCESS_TOKEN = os.getenv("WHATSAPP_ACCESS_TOKEN") or "<TU_TOKEN_DE_ACCESO>"
VERIFY_TOKEN = os.getenv("VERIFY_TOKEN") or "Chacalitas2025"
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "871681339360716")


def normalizar_numero_telefono(numero: str) -> str:
    numero = numero.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not numero.startswith("+"):
        numero = "+" + numero
    return numero


def enviar_mensaje_whatsapp(numero, mensaje):
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json",
    }

    if isinstance(mensaje, str):
        data = {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": mensaje},
        }
    else:
        data = mensaje  

    response = requests.post(url, headers=headers, json=data)
    print(f"➡️ Enviado a {numero}")
    print("📨 Estado:", response.status_code)

    try:
        res_json = response.json()
        return {
            "success": response.status_code == 200,
            "error": res_json.get("error"),
        }
    except Exception as e:
        print("⚠️ Error al interpretar la respuesta:", e)
        return {"success": False, "error": str(e)}


def procesar_mensaje_recibido(data):
    try:
        if data.get("object") != "whatsapp_business_account":
            return None

        entry = data.get("entry", [{}])[0]
        value = entry.get("changes", [{}])[0].get("value", {})

        if "statuses" in value:
            return None

        messages = value.get("messages", [])
        if not messages:
            return None

        message = messages[0]
        numero = message.get("from")

        if numero == WHATSAPP_PHONE_NUMBER_ID:
            print("🛑 Ignorando mensaje del propio bot.")
            return None

        # Extraer nombre del perfil de WhatsApp
        contacts = value.get("contacts", [])
        nombre_whatsapp = None
        if contacts:
            profile = contacts[0].get("profile", {})
            nombre_whatsapp = profile.get("name")
        
        tipo, contenido = get_type(message)
        return numero, contenido, tipo, nombre_whatsapp

    except Exception as e:
        print(f"⚠️ Error al procesar mensaje recibido: {e}")
        return None
