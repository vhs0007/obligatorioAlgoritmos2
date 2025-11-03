"""
Servidor webhook con FastAPI para recibir mensajes de WhatsApp
"""

from fastapi import FastAPI, Request, Query
from fastapi.responses import JSONResponse, PlainTextResponse
import json
from whatsapp_api import (
    procesar_mensaje_recibido,
    verificar_webhook,
    enviar_mensaje_whatsapp,
    WHATSAPP_PHONE_NUMBER_ID
)

app = FastAPI(title="WhatsApp Webhook Server")


@app.get("/")
async def root():
    """Página de inicio."""
    return {
        "message": "WhatsApp Webhook Server está funcionando",
        "phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
        "endpoints": {
            "webhook": "/webhook",
            "health": "/health"
        }
    }


@app.get("/health")
async def health():
    """Endpoint de salud."""
    return {"status": "ok"}


@app.get("/webhook")
async def verificar_webhook_endpoint(
    mode: str = Query(..., alias="hub.mode"),
    token: str = Query(..., alias="hub.verify_token"),
    challenge: str = Query(..., alias="hub.challenge")
):
    """
    Endpoint para verificar el webhook de WhatsApp.
    WhatsApp enviará una petición GET con estos parámetros para verificar el servidor.
    """
    print(f"\n[WEBHOOK VERIFICATION] Mode: {mode}, Token recibido: {token}")
    
    resultado = verificar_webhook(mode, token, challenge)
    
    if resultado:
        print("[WEBHOOK VERIFICATION] ✅ Webhook verificado correctamente")
        return PlainTextResponse(resultado)
    else:
        print("[WEBHOOK VERIFICATION] ❌ Verificación fallida")
        return JSONResponse(
            {"error": "Verificación fallida"},
            status_code=403
        )


@app.post("/webhook")
async def recibir_webhook(request: Request):
    """
    Endpoint para recibir mensajes de WhatsApp.
    WhatsApp enviará una petición POST cuando se reciba un mensaje.
    """
    try:
        body = await request.json()
        
        # Log del webhook completo (útil para debugging)
        print("\n" + "="*60)
        print("[WEBHOOK RECIBIDO]")
        print(json.dumps(body, indent=2, ensure_ascii=False))
        print("="*60)
        
        # Procesar el mensaje
        resultado = procesar_mensaje_recibido(body)
        
        if resultado:
            numero, mensaje, tipo = resultado
            
            print(f"\n📨 NUEVO MENSAJE RECIBIDO:")
            print(f"   De: {numero}")
            print(f"   Tipo: {tipo}")
            print(f"   Mensaje: {mensaje}")
            print("-" * 60)
            
            # Opcional: Enviar respuesta automática
            # respuesta_automatica = enviar_mensaje_whatsapp(
            #     numero,
            #     f"Recibí tu mensaje: {mensaje}"
            # )
            # print(f"Respuesta enviada: {respuesta_automatica}")
            
        else:
            # Puede ser una notificación de estado (enviado, entregado, leído, etc.)
            entry = body.get('entry', [{}])[0]
            changes = entry.get('changes', [{}])[0]
            value = changes.get('value', {})
            
            # Verificar si hay statuses (actualizaciones de estado de mensaje)
            statuses = value.get('statuses', [])
            if statuses:
                status = statuses[0]
                print(f"\n📊 ACTUALIZACIÓN DE ESTADO:")
                print(f"   ID Mensaje: {status.get('id', 'N/A')}")
                print(f"   Estado: {status.get('status', 'N/A')}")
                print(f"   Para: {status.get('recipient_id', 'N/A')}")
                print("-" * 60)
            
        # WhatsApp espera una respuesta 200 para confirmar que recibimos el webhook
        return JSONResponse({"status": "ok"})
        
    except Exception as e:
        print(f"\n❌ ERROR al procesar webhook: {str(e)}")
        import traceback
        traceback.print_exc()
        return JSONResponse(
            {"error": str(e)},
            status_code=500
        )


if __name__ == "__main__":
    import uvicorn
    
    print("\n" + "="*60)
    print("🚀 Iniciando servidor webhook de WhatsApp...")
    print(f"📱 Phone Number ID: {WHATSAPP_PHONE_NUMBER_ID}")
    print("="*60)
    print("\n📌 Para probar localmente, usa ngrok:")
    print("   1. Instala ngrok: https://ngrok.com/download")
    print("   2. Ejecuta: ngrok http 8000")
    print("   3. Copia la URL HTTPS y configúrala en Meta Developer Console")
    print("\n🌐 Servidor ejecutándose en: http://localhost:8000")
    print("📥 Webhook URL: http://localhost:8000/webhook")
    print("="*60 + "\n")
    
    uvicorn.run(app, host="0.0.0.0", port=8000)
