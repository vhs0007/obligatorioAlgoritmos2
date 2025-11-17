
from Util.database import get_db_session, Producto, Categoria
from whatsapp_api import enviar_mensaje_whatsapp


def filtrar_productos(productos, filtro_id):
    if filtro_id == "cat_all":
        return productos
    
    try:
        categoria_id = int(filtro_id.replace("cat_", ""))
        return [p for p in productos if p.id_categoria == categoria_id]
    except (ValueError, AttributeError):
        return productos


def paginar_productos(productos, pagina, items_por_pagina=5):
    total_items = len(productos)
    total_paginas = (total_items + items_por_pagina - 1) // items_por_pagina if total_items > 0 else 1
    
    inicio = (pagina - 1) * items_por_pagina
    fin = inicio + items_por_pagina
    
    productos_pagina = productos[inicio:fin]
    
    return productos_pagina, total_paginas, pagina


def lista_productos(numero, pagina=1, filtro="cat_all", orden_asc=True):
    db = get_db_session()
    try:
        productos = db.query(Producto).all()
        
        if filtro != "cat_all":
            productos = filtrar_productos(productos, filtro)
        
        productos = sorted(productos, key=lambda p: p.precio, reverse=not orden_asc)
        
        productos_pagina, total_paginas, pagina_actual = paginar_productos(productos, pagina)
        
        if not productos_pagina:
            return {
                "messaging_product": "whatsapp",
                "to": numero,
                "type": "text",
                "text": {"body": "📦 No hay productos disponibles en esta categoría."}
            }
        
        lineas = []
        for producto in productos_pagina:
            categoria = db.query(Categoria).filter(Categoria.id_categoria == producto.id_categoria).first()
            cat_nombre = categoria.nombre if categoria else "Sin categoría"
            lineas.append(f"🍽️ *{producto.nombre}*\n💰 ${producto.precio}\n📂 {cat_nombre}\n🆔 add_{producto.idproducto}\n")
        
        footer = f"\n📄 Página {pagina_actual} de {total_paginas}"
        if pagina_actual < total_paginas:
            footer += " | Escribí 'siguiente' para más"
        if pagina_actual > 1:
            footer += " | Escribí 'anterior' para volver"
        
        mensaje = "\n".join(lineas) + footer
        
        return {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "text",
            "text": {"body": mensaje}
        }
    finally:
        db.close()

