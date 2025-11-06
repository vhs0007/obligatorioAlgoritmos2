from .Data_prueba import productos
PAGINAS = 5  


def filtro_productos(filtro_carrito: str, order_asc: bool):
    items = productos.copy()

    if filtro_carrito and filtro_carrito != "cat_all":
        items = [p for p in items if p["categoria_id"] == filtro_carrito]

    items.sort(key=lambda p: p["precio"], reverse=not order_asc)
    return items


def paginar_productos(pagina: int, filtro_carrito: str, order_asc: bool):
    items = filtro_productos(filtro_carrito, order_asc)
    total = len(items)

    start = (pagina - 1) * PAGINAS
    end = start + PAGINAS
    pagina_items = items[start:end]

    return pagina_items, total


def lista_productos(numero: str, pagina: int, filtro_carrito: str, order_asc: bool):
    pagina_items, total = paginar_productos(pagina, filtro_carrito, order_asc)

    rows = [
        {"id": "add_" + p["id"], "title": f"{p['nombre']} — ${p['precio']}"}
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

    message = {
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

    return message