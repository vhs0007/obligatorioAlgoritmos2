from fastapi import FastAPI, Request
from fastapi.responses import PlainTextResponse
import traceback
from Models.chat import Chat
from Services.PedidoService import PedidosService
from Services.ProductoService import ProductosService
from Services.ChatService import ChatService
from Services.ClienteService import ClienteService
from Util.database import get_db_session
from whatsapp_api import procesar_mensaje_recibido, WHATSAPP_PHONE_NUMBER_ID

app = FastAPI()
VERIFY_TOKEN = "Chacalitas2025"


@app.get("/")
async def root():
    return {
        "message": "WhatsApp Webhook Server funcionando",
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
        print(f"Mensaje recibido ({tipo}) de {numero}: {mensaje}")

        db_session = get_db_session()
        chat_service = ChatService(db_session)
        pedido_service = PedidosService(db_session)
        producto_service = ProductosService()
        
        id_cliente = ClienteService.obtener_o_crear_cliente("", "", numero)
        
        chat_bd = chat_service.obtener_o_crear_chat(id_cliente, numero)
        id_chat = chat_bd.id_chat
        
        if tipo in ("text", "interactive"):
            chat_service.registrar_mensaje(id_chat, mensaje, es_cliente=True)
        elif tipo == "location":
            chat_service.registrar_mensaje(id_chat, f"Ubicación: {mensaje}", es_cliente=True)
        
        chat = Chat(
            id_chat=id_chat,
            id_cliente=id_cliente,
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