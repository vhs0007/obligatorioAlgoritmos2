"""
Script simple para enviar un mensaje de prueba por WhatsApp
"""

import sys
from whatsapp_api import enviar_mensaje_whatsapp

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python enviar_mensaje.py <numero_telefono> <mensaje>")
        print("\nEjemplos:")
        print('  # Número de prueba (sandbox):')
        print('  python enviar_mensaje.py "+15551648009" "Hola, este es un mensaje de prueba"')
        print('  # Número real (debe estar verificado):')
        print('  python enviar_mensaje.py "+59897465647" "Hola desde WhatsApp Business"')
        sys.exit(1)
    
    numero = sys.argv[1]
    mensaje = " ".join(sys.argv[2:])
    
    print(f"📤 Enviando mensaje a {numero}...")
    print(f"💬 Mensaje: {mensaje}\n")
    
    resultado = enviar_mensaje_whatsapp(numero, mensaje)
    
    if resultado.get('success'):
        print("✅ Mensaje enviado exitosamente!")
        print(f"📨 Message ID: {resultado.get('message_id')}")
    else:
        print("❌ Error al enviar mensaje:")
        print(f"   {resultado.get('error', 'Error desconocido')}")
        if 'response' in resultado:
            print(f"\n📋 Detalles del error:")
            import json
            print(json.dumps(resultado['response'], indent=2, ensure_ascii=False))
