from Util.database import get_db_session, Producto
PAGINAS = 5

def filtrar_productos(filtro_carrito: str, order_asc: bool):
    """Obtiene productos desde la base de datos y los filtra/ordena."""
    db = get_db_session()
    try:
        query = db.query(Producto)
        
        # Filtrar por categoría si no es "cat_all"
        if filtro_carrito and filtro_carrito != "cat_all":
            # Extraer el ID de categoría del formato "cat_X"
            try:
                cat_id = int(filtro_carrito.replace("cat_", ""))
                query = query.filter(Producto.id_categoria == cat_id)
            except (ValueError, AttributeError):
                pass  # Si no se puede parsear, mostrar todos
        
        # Obtener todos los productos
        productos = query.all()
        
        # Convertir a lista de diccionarios
        items = [
            {
                "id": str(p.idproducto),
                "nombre": p.nombre,
                "precio": p.precio,
                "id_categoria": p.id_categoria
            }
            for p in productos
        ]
        
        # Ordenar por precio
        items.sort(key=lambda p: p["precio"], reverse=not order_asc)
        return items
    finally:
        db.close()


def paginar_productos(pagina: int, filtro_carrito: str, order_asc: bool):
    items = filtrar_productos(filtro_carrito, order_asc)
    total = len(items)

    start = (pagina - 1) * PAGINAS
    end = start + PAGINAS
    pagina_items = items[start:end]

    return pagina_items, total


def lista_productos(numero: str, pagina: int, filtro_carrito: str, order_asc: bool):
    pagina_items, total = paginar_productos(pagina, filtro_carrito, order_asc)

    rows = [
        {"id": f"add_{p['id']}", "title": f"{p['nombre']} — ${p['precio']}"}
        for p in pagina_items
    ]

    rows.append({"id": "action_filter", "title": "🔎 Filtrar"})
    order_label = "🔽 Ordenar precio (desc)" if order_asc else "🔼 Ordenar precio (asc)"
    rows.append({"id": "action_order", "title": order_label})

    has_next = (pagina * PAGINAS) < total
    has_prev = pagina > 1

    if has_next:
        rows.append({"id": "action_next", "title": "➡️ Siguientes productos"})
    if has_prev:
        rows.append({"id": "action_prev", "title": "⬅️ Volver"})
    if pagina >= 3:
        rows.append({"id": "action_home", "title": "⤴️ Volver al Inicio"})

    return {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "🛒 Menú de productos"},
            "body": {"text": f"Mostrando productos (página {pagina}). Total: {total} disponibles."},
            "footer": {"text": f"Filtro: {filtro_carrito} • Orden: {'asc' if order_asc else 'desc'}"},
            "action": {
                "button": "Ver opciones",
                "sections": [{"title": "Productos", "rows": rows}],
            },
        },
    }
