from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import traceback
from Models.chat import Chat
from Services.PedidoService import PedidosService
from Services.ProductoService import ProductosService
from Util.database import get_db_session
from whatsapp_api import procesar_mensaje_recibido, WHATSAPP_PHONE_NUMBER_ID

app = FastAPI()
VERIFY_TOKEN = "Chacalitas2025"


@app.get("/")
async def root():
    return {
        "message": "✅ WhatsApp Webhook Server funcionando",
        "phone_number_id": WHATSAPP_PHONE_NUMBER_ID,
        "endpoints": {"webhook": "/webhook", "health": "/health"},
    }


@app.get("/health")
async def health():
    return {"status": "ok"}


@app.get("/webhook")
async def verify(request: Request):
    mode = request.query_params.get("hub.mode")
    token = request.query_params.get("hub.verify_token")
    challenge = request.query_params.get("hub.challenge")

    if mode == "subscribe" and token == VERIFY_TOKEN:
        return PlainTextResponse(challenge)
    return PlainTextResponse("Token inválido", status_code=403)


@app.post("/webhook")
async def receive(request: Request):
    try:
        data = await request.json()
        resultado = procesar_mensaje_recibido(data)

        if not resultado:
            return PlainTextResponse("EVENT_RECEIVED", status_code=200)

        numero, mensaje, tipo = resultado
        print(f"📩 Mensaje recibido ({tipo}) de {numero}: {mensaje}")

        # Inicializar servicios y crear instancia de Chat
        db_session = get_db_session()
        pedido_service = PedidosService(db_session)
        producto_service = ProductosService()
        chat = Chat(
            id_chat=f"chat_{numero}",
            id_cliente=numero,
            pedido_service=pedido_service,
            producto_service=producto_service
        )

        if tipo in ("text", "interactive"):
            chat.handle_text(numero, mensaje)
        elif tipo == "location":
            chat.handle_location(numero, mensaje)
        else:
            chat.handle_text(numero, "Tipo de mensaje no soportado aún.")

        return PlainTextResponse("EVENT_RECEIVED", status_code=200)

    except Exception:
        traceback.print_exc()
        return PlainTextResponse("ERROR", status_code=500)