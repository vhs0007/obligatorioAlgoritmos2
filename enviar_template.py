"""
Script para enviar mensajes tipo template (funciona en sandbox sin 24h window)
"""

import sys
from whatsapp_api import WHATSAPP_API_URL, WHATSAPP_PHONE_NUMBER_ID, WHATSAPP_ACCESS_TOKEN
import requests

def enviar_template(numero_telefono: str, template_name: str = "hello_world", language_code: str = "en_US"):
    """Envía un mensaje template por WhatsApp."""
    if not numero_telefono:
        return {'success': False, 'error': 'Número de teléfono es obligatorio'}
    
    # Normalizar número
    numero = numero_telefono.replace(" ", "").replace("-", "").replace("(", "").replace(")", "")
    if not numero.startswith("+"):
        numero = "+" + numero
    
    url = f"{WHATSAPP_API_URL}/{WHATSAPP_PHONE_NUMBER_ID}/messages"
    headers = {
        "Authorization": f"Bearer {WHATSAPP_ACCESS_TOKEN}",
        "Content-Type": "application/json"
    }
    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "template",
        "template": {
            "name": template_name,
            "language": {
                "code": language_code
            }
        }
    }
    
    try:
        print(f"📤 Enviando template '{template_name}' a {numero}...")
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
            return {
                'success': False,
                'error': error_info.get('message', 'Error desconocido'),
                'response': response_data
            }
    except Exception as e:
        return {'success': False, 'error': f'Error: {str(e)}'}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print("Uso: python enviar_template.py <numero_telefono> [template_name] [language_code]")
        print("\nEjemplos:")
        print('  # Template por defecto (hello_world):')
        print('  python enviar_template.py "+59897465647"')
        print('  # Template personalizado:')
        print('  python enviar_template.py "+59897465647" "hello_world" "es"')
        print("\nTemplates disponibles en sandbox:")
        print('  - hello_world (en_US, es, etc.)')
        sys.exit(1)
    
    numero = sys.argv[1]
    template = sys.argv[2] if len(sys.argv) > 2 else "hello_world"
    language = sys.argv[3] if len(sys.argv) > 3 else "en_US"
    
    resultado = enviar_template(numero, template, language)
    
    if resultado.get('success'):
        print("✅ Template enviado exitosamente!")
        print(f"📨 Message ID: {resultado.get('message_id')}")
    else:
        print("❌ Error al enviar template:")
        print(f"   {resultado.get('error', 'Error desconocido')}")
        if 'response' in resultado:
            import json
            print(f"\n📋 Detalles del error:")
            print(json.dumps(resultado['response'], indent=2, ensure_ascii=False))

