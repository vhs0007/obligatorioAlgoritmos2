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
WHATSAPP_API_URL = "https://graph.facebook.com/v18.0"
WHATSAPP_ACCESS_TOKEN = "EAAS2SGNAVIABPZBxIjZAZCphB2wTZBp2IDrHw6eGjePP1FFMSFIaZCnrZA1sugyWqknfGtWjgyHJendcaKdtRMZANTpP43ltsyvlC7GIRZAnfgFxXpXii1l1HJ3u3LXClvVwKBqZCI8msmfiTcdIfbmkZAhtYZCWUFfUP021O0s8gsNNOpCQnh92jwwMly52TQ5IRorVUIx3HJmEuW2R3ngCPGtkTtKuVQu3bt963N0b9psWEcajpJrf1LiDSnXeCsnch1kORGpYvLzm1qS4oe3qB1R"
VERIFY_TOKEN = "mi_token_verificacion_secreto"

# Obtener Phone Number ID desde variables de entorno o calcularlo
WHATSAPP_PHONE_NUMBER_ID = os.getenv("WHATSAPP_PHONE_NUMBER_ID", None)

# ========== FUNCIONES AUXILIARES ==========

def obtener_phone_number_id() -> Optional[str]:
    """Obtiene el Phone Number ID desde la API de Meta."""
    # Intentar varios endpoints para obtener el Phone Number ID
    endpoints = [
        "/me/phone_numbers",  # Para obtener números de teléfono
        "/me?fields=phone_numbers",  # Información de cuenta
    ]
    
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}"
    }
    
    for endpoint in endpoints:
        try:
            url = f"{WHATSAPP_API_URL}{endpoint}"
            response = requests.get(url, headers=headers, timeout=10)
            if response.status_code == 200:
                data = response.json()
                # Buscar phone_numbers en diferentes estructuras
                if 'data' in data:
                    phone_numbers = data.get('data', [])
                    if phone_numbers and isinstance(phone_numbers, list):
                        return phone_numbers[0].get('id')
                elif 'phone_numbers' in data:
                    phone_numbers = data.get('phone_numbers', {}).get('data', [])
                    if phone_numbers and isinstance(phone_numbers, list):
                        return phone_numbers[0].get('id')
        except Exception as e:
            continue
    
    return None

# Inicializar Phone Number ID si no está configurado
if WHATSAPP_PHONE_NUMBER_ID is None:
    print("🔍 Obteniendo Phone Number ID desde la API...")
    WHATSAPP_PHONE_NUMBER_ID = obtener_phone_number_id()
    if WHATSAPP_PHONE_NUMBER_ID:
        print(f"✅ Phone Number ID obtenido: {WHATSAPP_PHONE_NUMBER_ID}")
    else:
        print("⚠️ No se pudo obtener el Phone Number ID automáticamente.")
        print("💡 Puedes configurarlo manualmente:")
        print("   1. Ve a https://developers.facebook.com/apps/")
        print("   2. Selecciona tu app → WhatsApp → API Setup")
        print("   3. Copia el 'Phone number ID' y configúralo como variable de entorno:")
        print("      WHATSAPP_PHONE_NUMBER_ID=tu_phone_number_id")

# ========== FUNCIONES PARA ENVIAR MENSAJES ==========

def enviar_mensaje_whatsapp(numero_telefono: str, mensaje: str) -> Dict:
    """Envía un mensaje de texto por WhatsApp."""
    if not numero_telefono or not mensaje:
        return {'success': False, 'error': 'Número y mensaje son obligatorios'}
    
    if not WHATSAPP_PHONE_NUMBER_ID:
        return {'success': False, 'error': 'Phone Number ID no está configurado'}
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "recipient_type": "individual",
        "to": numero_telefono,
        "type": "text",
        "text": {"body": mensaje}
    }
    
    try:
        response = requests.post(url, headers=headers, json=payload, timeout=10)
        response_data = response.json()
        
        if response.status_code == 200:
            return {
                'success': True,
                'message_id': response_data.get('messages', [{}])[0].get('id', ''),
                'response': response_data
            }
        else:
            return {
                'success': False,
                'error': response_data.get('error', {}).get('message', 'Error desconocido'),
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
