from whatsapp_api import enviar_mensaje_whatsapp
from Util.state import SESSION
from Util.product_util import lista_productos
from Util.database import get_db_session, Categoria

def obtener_categorias():
    """Obtiene las categorías desde la base de datos."""
    db = get_db_session()
    try:
        # Obtener todas las categorías de la tabla Categoria
        categorias_db = db.query(Categoria).all()
        
        # Convertir a lista con formato esperado
        categorias = [
            {"id": f"cat_{cat.id_categoria}", "nombre": cat.nombre}
            for cat in categorias_db
        ]
        
        # Agregar opción "Todas" al inicio
        categorias.insert(0, {"id": "cat_all", "nombre": "Todas las categorías"})
        
        return categorias
    finally:
        db.close()

def menu_categorias(numero):
    categorias = obtener_categorias()
    secciones = [{
        "title": "Categorías de comidas",
        "rows": [{"id": c["id"], "title": c["nombre"]} for c in categorias],
    }]
    return {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🍔 ¡Bienvenido a GordoEats! 😋"},
            "body": {"text": "Seleccioná una categoría para ver nuestras opciones:"},
            "footer": {"text": "Usá el menú para elegir 👇"},
            "action": {"button": "Ver categorías", "sections": secciones},
        },
    }


def mostrar_productos(numero, categoria_id=None):
    sesion = SESSION.get(numero, {})
    if categoria_id:
        sesion["filter"] = categoria_id
    payload = lista_productos(numero, sesion.get("page", 1), sesion.get("filter", "cat_all"), sesion.get("order_asc", True))
    return enviar_mensaje_whatsapp(numero, payload)


# Nota: mostrar_carrito se maneja a través de PedidoService.mostrar_carrito_pedidos()
# Esta función se mantiene por compatibilidad pero no se usa directamente