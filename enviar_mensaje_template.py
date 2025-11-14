"""
Script para enviar mensajes usando templates (funciona en sandbox)
"""

import sys
from whatsapp_api import enviar_mensaje_whatsapp

if __name__ == "__main__":
    if len(sys.argv) < 3:
        print("Uso: python enviar_mensaje_template.py <numero_telefono> <mensaje>")
        print("\nEste script envía mensajes usando templates (funciona en sandbox)")
        print("Ejemplos:")
        print('  python enviar_mensaje_template.py "+59897465647" "Hola desde WhatsApp"')
        sys.exit(1)
    
    numero = sys.argv[1]
    mensaje = " ".join(sys.argv[2:])
    
    print(f"Enviando mensaje template a {numero}...")
    print(f"Mensaje: {mensaje}\n")
    print("Nota: Se enviará el template 'hello_world' que funciona en sandbox")
    print("El mensaje personalizado solo aparecerá en producción con templates personalizados\n")
    
    resultado = enviar_mensaje_whatsapp(numero, mensaje, usar_template=True)
    
    if resultado.get('success'):
        print("✅ Mensaje enviado exitosamente!")
        print(f"📨 Message ID: {resultado.get('message_id')}")
    else:
        print("Error al enviar mensaje:")
        print(f"{resultado.get('error', 'Error desconocido')}")
        if 'response' in resultado:
            import json
            print(f"\n📋 Detalles del error:")
            print(json.dumps(resultado['response'], indent=2, ensure_ascii=False))

