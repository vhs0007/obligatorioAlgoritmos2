from Util.database import get_db_session
from Services.PedidoService import PedidosService
from Services.ProductoService import ProductosService
from Models.Chat import Chat


def crear_bot_instancia():
    db_session = get_db_session()
    
    pedido_service = PedidosService(db_session)
    producto_service = ProductosService(db_session)
    cliente_service = ClienteService(db_session)
    bot = Chat(
        pedido_service=pedido_service,
        producto_service=producto_service
    )
    
    return bot  


bot = crear_bot_instancia()


if __name__ == "__main__":
    print("Bot iniciado correctamente")
    print(f"Estado del bot {bot}")
