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

def menu_categorias(numero, pagina=1):
    """
    Muestra las categorías paginadas (máximo 9 por página para cumplir límite de WhatsApp).
    """
    estado = get_estado(numero)
    categorias = obtener_categorias()
    
    # Máximo 9 categorías por página (límite de WhatsApp)
    items_por_pagina = 9
    total_categorias = len(categorias)
    total_paginas = (total_categorias + items_por_pagina - 1) // items_por_pagina if total_categorias > 0 else 1
    
    inicio = (pagina - 1) * items_por_pagina
    fin = inicio + items_por_pagina
    categorias_pagina = categorias[inicio:fin]
    
    # Construir filas de la lista
    rows = [{"id": c["id"], "title": c["nombre"]} for c in categorias_pagina]
    
    # Agregar opciones de navegación si es necesario
    if pagina < total_paginas:
        rows.append({"id": "cat_next", "title": "➡️ Siguiente"})
    
    if pagina > 1:
        rows.append({"id": "cat_prev", "title": "⬅️ Volver"})
    
    if pagina > 2:
        rows.append({"id": "cat_home", "title": "🏠 Volver al Inicio"})
    
    # Actualizar estado
    estado["cat_page"] = pagina
    
    secciones = [{
        "title": f"Categorías (Página {pagina}/{total_paginas})",
        "rows": rows
    }]
    
    return {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🍔 ¡Bienvenido a GordoEats! 😋"},
            "body": {"text": "Seleccioná una categoría para ver nuestras opciones:"},
            "footer": {"text": f"Página {pagina} de {total_paginas}"},
            "action": {"button": "Ver categorías", "sections": secciones},
        },
    }


def mostrar_productos(numero, categoria_id=None):
    estado = get_estado(numero)
    if categoria_id:
        estado["filter"] = categoria_id
    payload = lista_productos(numero, estado.get("page", 1), estado.get("filter", "cat_all"), estado.get("order_asc", True))
    return enviar_mensaje_whatsapp(numero, payload)

