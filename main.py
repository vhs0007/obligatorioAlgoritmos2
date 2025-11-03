"""
Aplicación principal para WhatsApp Business API
Puede ejecutarse como servidor webhook o para enviar mensajes
"""

import sys
from whatsapp_api import enviar_mensaje_whatsapp
from webhook_server import app
import uvicorn


def main():
    print("=== WhatsApp Business API ===\n")
    
    # Verificar argumentos de línea de comandos
    if len(sys.argv) > 1:
        comando = sys.argv[1]
        
        if comando == "webhook" or comando == "server":
            # Ejecutar servidor webhook
            print("🚀 Iniciando servidor webhook...\n")
            uvicorn.run(app, host="0.0.0.0", port=8000)
            return
        elif comando == "enviar" and len(sys.argv) >= 4:
            # Enviar mensaje: python main.py enviar +1234567890 "Hola"
            numero = sys.argv[2]
            mensaje = sys.argv[3]
            print(f"📤 Enviando mensaje a {numero}...")
            resultado = enviar_mensaje_whatsapp(numero, mensaje)
            print(f"\nResultado:")
            print(f"  Success: {resultado.get('success')}")
            if resultado.get('success'):
                print(f"  Message ID: {resultado.get('message_id')}")
            else:
                print(f"  Error: {resultado.get('error')}")
            return
    
    # Modo interactivo por defecto
    print("Opciones disponibles:")
    print("  1. Ejecutar servidor webhook: python main.py webhook")
    print("  2. Enviar mensaje: python main.py enviar +1234567890 'Tu mensaje'")
    print("\nEjecutando servidor webhook por defecto...\n")
    print("="*60 + "\n")
    uvicorn.run(app, host="0.0.0.0", port=8000)


if __name__ == "__main__":
    main()
