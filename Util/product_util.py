
from Util.database import get_db_session, Producto, Categoria
from Util.estado import get_estado


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
    """
    Muestra productos en lista interactiva de WhatsApp.
    Máximo 5 productos + opciones de navegación (Filtrar, Ordenar, Siguiente, Volver, Volver al Inicio).
    """
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
        
        # Construir filas de la lista interactiva (máximo 5 productos)
        rows = []
        for producto in productos_pagina:
            categoria = db.query(Categoria).filter(Categoria.id_categoria == producto.id_categoria).first()
            cat_nombre = categoria.nombre if categoria else "Sin categoría"
            # Limitar longitud del título para WhatsApp (máximo 24 caracteres)
            titulo = f"{producto.nombre} - ${producto.precio}"
            if len(titulo) > 24:
                titulo = titulo[:21] + "..."
            rows.append({
                "id": f"add_{producto.idproducto}",
                "title": titulo,
                "description": cat_nombre
            })
        
        # Agregar opciones de navegación según la letra
        # i. Filtrar (siempre disponible)
        rows.append({"id": "prod_filter", "title": "🔍 Filtrar"})
        
        # iii. Ordenar por precio
        orden_texto = "⬆️ Ordenar: Barato→Caro" if orden_asc else "⬇️ Ordenar: Caro→Barato"
        rows.append({"id": "prod_order", "title": orden_texto})
        
        # iv. Siguientes productos (solo si hay más páginas)
        if pagina_actual < total_paginas:
            rows.append({"id": "prod_next", "title": "➡️ Siguientes productos"})
        
        # v. Volver (si está en página 2+)
        if pagina_actual > 1:
            rows.append({"id": "prod_prev", "title": "⬅️ Volver"})
        
        # vi. Volver al Inicio (si está en página 3+)
        if pagina_actual > 2:
            rows.append({"id": "prod_home", "title": "🏠 Volver al Inicio"})
        
        # Obtener nombre de categoría para el header
        categoria_nombre = "Todas las categorías"
        if filtro != "cat_all":
            try:
                cat_id = int(filtro.replace("cat_", ""))
                categoria = db.query(Categoria).filter(Categoria.id_categoria == cat_id).first()
                if categoria:
                    categoria_nombre = categoria.nombre
            except:
                pass
        
        secciones = [{
            "title": f"Productos - {categoria_nombre}",
            "rows": rows
        }]
        
        return {
            "messaging_product": "whatsapp",
            "to": numero,
            "type": "interactive",
            "interactive": {
                "type": "list",
                "header": {"type": "text", "text": "🍽️ Nuestros Productos"},
                "body": {"text": f"Seleccioná un producto para agregarlo al carrito\n📄 Página {pagina_actual}/{total_paginas}"},
                "footer": {"text": f"Orden: {'Barato→Caro' if orden_asc else 'Caro→Barato'}"},
                "action": {"button": "Ver productos", "sections": secciones},
            },
        }
    finally:
        db.close()

