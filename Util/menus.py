from whatsapp_api import enviar_mensaje_whatsapp
from Util.estado import get_estado
from Util.product_util import lista_productos
from Util.database import get_db_session, Categoria

def obtener_categorias():
    db = get_db_session()
    try:
        categorias_db = db.query(Categoria).all()
        
        categorias = [
            {"id": f"cat_{cat.id_categoria}", "nombre": cat.nombre}
            for cat in categorias_db
        ]
        
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
    estado = get_estado(numero)
    if categoria_id:
        estado["filter"] = categoria_id
    payload = lista_productos(numero, estado.get("page", 1), estado.get("filter", "cat_all"), estado.get("order_asc", True))
    return enviar_mensaje_whatsapp(numero, payload)

