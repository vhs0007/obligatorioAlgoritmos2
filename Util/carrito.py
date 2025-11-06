from state import get_cart
from Data_prueba import productos

def add_to_cart(numero, product_id, cantidad, observaciones=""):
    cart = get_cart(numero)
    producto = next((p for p in productos if p["id"] == product_id), None)
    if not producto:
        return False, "Producto no encontrado"

    item = cart.get(
        product_id,
        {"cantidad": 0, "nombre": producto["nombre"], "precio": producto["precio"], "obs": ""},
    )

    item["cantidad"] += cantidad
    if observaciones:
        item["obs"] = observaciones

    cart[product_id] = item
    return True, None


def quitar_producto(numero, product_id):
    cart = get_cart(numero)
    if product_id in cart:
        del cart[product_id]
        return True
    return False


def detalle_carrito(numero):
    cart = get_cart(numero)
    lineas = []
    total = 0

    for _, item in cart.items():
        subtotal = item["cantidad"] * item["precio"]
        total += subtotal
        obs = f" ({item['obs']})" if item.get("obs") else ""
        lineas.append(f"{item['cantidad']}x {item['nombre']}{obs} — ${subtotal}")

    body = "\n".join(lineas) if lineas else "Tu carrito está vacío."

    return {"body": body, "total": total, "items_count": len(cart)}
