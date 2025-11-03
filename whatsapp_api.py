"""
Módulo para interactuar con la API de WhatsApp Business de Meta
Funciones para enviar y recibir mensajes
"""

import requests
import os
from typing import Dict, Optional, Tuple
import json

# ========== CONFIGURACIÓN ==========
# Configura estas variables en tu entorno o directamente aquí
WHATSAPP_API_URL = "https://graph.facebook.com/v22.0"
WHATSAPP_ACCESS_TOKEN = "EAAS2SGNAVIABPZCrebD2Rr6M8tefmZBPYKpkKPOJ3y2scrbE8OHlTj4BW6ZBCcCOZBZBjlZCY41QVKAJATvKydpgj2rEMcbbU5sVlZCEKZBk5zHEvtz1ImOhA9gywIRKD9IOvDBMm6Tmk5Ro0VnRDLQLHPC37XDtNT5ZC4ZCeo8p3wZBsRZAKACSM92beNKyeufoIJnc3qkY1WXQUeMXyl7tu3XQ03umP1D9gZBNr0qJOuZBgcKAbWFg7AKwcZChuIuT8uc95ZAs14ZAjx0pFEviTb2ZBZBEzTMHgZDZD"
VERIFY_TOKEN = "Chacalitas2025"

# Phone Number ID configurado directamente
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", "871681339360716")

# ========== FUNCIONES AUXILIARES ==========

def obtener_phone_number_id() -> Optional[str]:
    """Obtiene el Phone Number ID desde la API de Meta."""
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    # Intentar obtener desde /me/phone_numbers
    try:
        url = f"{WHATSAPP_API_URL}/me/phone_numbers"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            phone_numbers = data.get('data', [])
            if phone_numbers and isinstance(phone_numbers, list) and len(phone_numbers) > 0:
                phone_id = phone_numbers[0].get('id')
                if phone_id:
                    print(f"📱 Phone Number ID obtenido desde API: {phone_id}")
                    return phone_id
    except Exception as e:
        print(f"⚠️ Error al obtener Phone Number ID desde /me/phone_numbers: {str(e)}")
    
    # Intentar obtener desde WhatsApp Business Account
    try:
        url = f"{WHATSAPP_API_URL}/me?fields=whatsapp_business_account"
        response = requests.get(url, headers=headers, timeout=10)
        if response.status_code == 200:
            data = response.json()
            waba = data.get('whatsapp_business_account', {})
            phone_numbers = waba.get('phone_numbers', {}).get('data', [])
            if phone_numbers and isinstance(phone_numbers, list) and len(phone_numbers) > 0:
                phone_id = phone_numbers[0].get('id')
                if phone_id:
                    print(f"📱 Phone Number ID obtenido desde WABA: {phone_id}")
                    return phone_id
    except Exception as e:
        print(f"⚠️ Error al obtener Phone Number ID desde WABA: {str(e)}")
    
    return None

def normalizar_numero_telefono(numero: str) -> str:
    """Normaliza el número de teléfono removiendo espacios y caracteres especiales, excepto el + inicial."""
    # Remover espacios y guiones
    numero = numero.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    # Asegurar que comience con +
    if not numero.startswith("+"):
        # Si no tiene +, agregarlo (asumiendo que es un número internacional)
        if numero.startswith("1"):  # Código de país para USA
            numero = "+" + numero
        else:
            numero = "+" + numero
    return numero

# Intentar obtener Phone Number ID automáticamente desde la API primero
# Si falla, usar el valor configurado
print("🔍 Intentando obtener Phone Number ID desde la API...")
phone_id_obtenido = obtener_phone_number_id()
if phone_id_obtenido:
    WHATSAPP_PHONE_NUMBER_ID = phone_id_obtenido
    print(f"✅ Phone Number ID obtenido desde API: {WHATSAPP_PHONE_NUMBER_ID}")
else:
    # Si no se pudo obtener, usar el valor configurado
    print(f"✅ Usando Phone Number ID configurado: {WHATSAPP_PHONE_NUMBER_ID}")

# ========== FUNCIONES PARA ENVIAR MENSAJES ==========

def enviar_mensaje_whatsapp(numero_telefono: str, mensaje: str, usar_template: bool = False) -> Dict:
    """
    Envía un mensaje por WhatsApp.
    
    Args:
        numero_telefono: Número de teléfono del destinatario
        mensaje: Contenido del mensaje
        usar_template: Si True, envía como template (funciona en sandbox sin 24h window)
                      Si False, envía como texto normal (solo funciona si el usuario escribió en las últimas 24h)
    """
    if not numero_telefono or not mensaje:
        return {'success': False, 'error': 'Número y mensaje son obligatorios'}
    
    if not WHATSAPP_PHONE_NUMBER_ID:
        return {'success': False, 'error': 'Phone Number ID no está configurado'}
    
    # Normalizar el número de teléfono
    numero_normalizado = normalizar_numero_telefono(numero_telefono)
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    
    # Si usar_template es True, usar template hello_world
    if usar_template:
        payload = {
            "messaging_product": "whatsapp",
            "to": numero_normalizado,
            "type": "template",
            "template": {
                "name": "hello_world",
                "language": {
                    "code": "en_US"
                }
            }
        }
    else:
        # Mensaje de texto normal
        payload = {
            "messaging_product": "whatsapp",
            "recipient_type": "individual",
            "to": numero_normalizado,
            "type": "text",
            "text": {"body": mensaje}
        }
    
    try:
        print(f"📤 Enviando request a: {url}")
        print(f"📱 Número normalizado: {numero_normalizado}")
        print(f"🔑 Usando Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")
        
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'message_id': response_data.get('messages', [{}])[0].get('id', ''),
                'response': response_data
            }
        else:
            error_info = response_data.get('error', {})
            error_message = error_info.get('message', 'Error desconocido')
            error_code = error_info.get('code', 'N/A')
            error_type = error_info.get('type', 'N/A')
            
            # Mensaje de ayuda específico según el error
            ayuda = ""
            if error_code == 100:
                ayuda = "\n💡 Esto puede indicar que:\n   - El Phone Number ID no es correcto\n   - El token no tiene permisos para este Phone Number ID\n   - El token no tiene los scopes necesarios (whatsapp_business_messaging)"
            elif error_code == 10:
                ayuda = "\n💡 Error de permisos (OAuthException):\n   - En modo SANDBOX, los mensajes de texto solo funcionan si el usuario te escribió en las últimas 24h\n   - Para enviar sin restricciones, usa un TEMPLATE:\n     * Ejecuta: python enviar_template.py \"+59897465647\"\n     * O usa: enviar_mensaje_whatsapp(numero, mensaje, usar_template=True)\n   - Los templates funcionan siempre sin ventana de 24 horas\n   - Si el error persiste, verifica que el token tenga los permisos:\n     * whatsapp_business_messaging\n     * whatsapp_business_management"
            
            return {
                'success': False,
                'error': f"{error_message} (Código: {error_code}, Tipo: {error_type}){ayuda}",
                'response': response_data
            }
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}'}

# ========== FUNCIONES PARA RECIBIR MENSAJES ==========

def procesar_mensaje_recibido(webhook_data: Dict) -> Optional[Tuple[str, str, str]]:
    """Procesa los datos del webhook de WhatsApp."""
    try:
        if webhook_data.get('object') != 'whatsapp_business_account':
            return None
            
        entry = webhook_data.get('entry', [{}])[0]
        changes = entry.get('changes', [{}])[0]
        value = changes.get('value', {})
        messages = value.get('messages', [])
        
        if not messages:
            return None
            
        message = messages[0]
        numero_telefono = message.get('from', '')
        message_type = message.get('type', '')
        
        # Extraer el mensaje según el tipo
        if message_type == 'text':
            contenido = message.get('text', {}).get('body', '')
        elif message_type == 'button':
            contenido = message.get('button', {}).get('text', '')
        elif message_type == 'interactive':
            interactive = message.get('interactive', {})
            if interactive.get('type') == 'button_reply':
                contenido = interactive.get('button_reply', {}).get('title', '')
            elif interactive.get('type') == 'list_reply':
                contenido = interactive.get('list_reply', {}).get('title', '')
        elif message_type == 'location':
            loc = message.get('location', {})
            contenido = f"Ubicación: {loc.get('latitude')}, {loc.get('longitude')}"
        else:
            contenido = f"Mensaje tipo {message_type}"
        
        return (numero_telefono, contenido, message_type)
    except Exception as e:
        print(f"Error al procesar mensaje: {str(e)}")
        return None

def verificar_webhook(mode: str, token: str, challenge: str) -> Optional[str]:
    """Verifica el webhook de WhatsApp."""
    if mode == 'subscribe' and token == VERIFY_TOKEN:
        return challenge
    return None

# ========== EJEMPLO DE USO ==========

if __name__ == "__main__":
    # Ejemplo de envío de mensaje
    print("=== EJEMPLO DE ENVÍO DE MENSAJE ===")
    resultado = enviar_mensaje_whatsapp("59899123456", "¡Hola desde el bot!")
    print(f"Resultado: {json.dumps(resultado, indent=2)}\n")
    
    # Ejemplo de procesamiento de mensaje recibido
    print("=== EJEMPLO DE RECEPCIÓN DE MENSAJE ===")
    mensaje_ejemplo = {
        "object": "whatsapp_business_account",
        "entry": [{
            "changes": [{
                "value": {
                    "messages": [{
                        "from": "59899123456",
                        "type": "text",
                        "text": {"body": "Hola, quiero hacer un pedido"}
                    }]
                }
            }]
        }]
    }
    resultado = procesar_mensaje_recibido(mensaje_ejemplo)
    if resultado:
        numero, mensaje, tipo = resultado
        print(f"De: {numero}")
        print(f"Mensaje: {mensaje}")
        print(f"Tipo: {tipo}")
    else:
        print("No se pudo procesar el mensaje")
