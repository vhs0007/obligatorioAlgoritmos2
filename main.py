import sys
import os
import uvicorn
from whatsapp_api import enviar_mensaje_whatsapp
from webhook_server import app

def main():
    print("=== WhatsApp Business API ===\n")

    # Verificar que haya token configurado
    if not os.getenv("WHATSAPP_ACCESS_TOKEN"):
        print("⚠️  Advertencia: No se encontró WHATSAPP_ACCESS_TOKEN en las variables de entorno.")
        print("   El envío de mensajes fallará si no se define.\n")

    if len(sys.argv) > 1:
        comando = sys.argv[1]

        if comando in ("webhook", "server"):
            print("🚀 Iniciando servidor webhook...\n")
            uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)
            return

        elif comando == "enviar" and len(sys.argv) >= 4:
            numero = sys.argv[2]
            mensaje = sys.argv[3]
            print(f"📤 Enviando mensaje a {numero}...")
            resultado = enviar_mensaje_whatsapp(numero, mensaje)
            print("\nResultado:")
            print(f"  ✅ Success: {resultado.get('success')}")
            if resultado.get('success'):
                print(f"  Message ID: {resultado.get('message_id')}")
            else:
                print(f"  ❌ Error: {resultado.get('error')}")
            return

    print("Opciones disponibles:")
    print("  python main.py webhook      → Inicia el servidor webhook")
    print("  python main.py enviar +1234567890 'Tu mensaje' → Envía un mensaje manual")
    print("\nEjecutando servidor webhook por defecto...\n")
    uvicorn.run(app, host="0.0.0.0", port=8000, reload=True)


if __name__ == "__main__":
    main()
