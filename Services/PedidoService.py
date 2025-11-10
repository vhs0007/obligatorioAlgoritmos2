from Util.database import Pedido, DetallePedido, Producto
from datetime import datetime

class PedidosService:
    def __init__(self, db_session):
        self.db = db_session

    def crear_pedido(self, id_chat, id_cliente, direccion, latitud=None, longitud=None):
        pedido = Pedido(
            id_chat=id_chat,
            id_cliente=id_cliente,
            direccion=direccion,
            latitud=latitud,
            longitud=longitud,
        )
        self.db.add(pedido)
        self.db.commit()
        self.db.refresh(pedido)
        return pedido

    def agregar_producto(self, id_pedido, id_producto, cantidad):
        detalle = DetallePedido(
            id_pedido=id_pedido,
            id_producto=id_producto,
            cantidad=cantidad,
        )
        self.db.add(detalle)
        self.db.commit()
        return detalle

    def obtener_detalle(self, id_pedido):
        detalles = (
            self.db.query(DetallePedido, Producto)
            .join(Producto, DetallePedido.id_producto == Producto.idproducto)
            .filter(DetallePedido.id_pedido == id_pedido)
            .all()
        )

        resultado = [
            {
                "producto": prod.nombre,
                "cantidad": det.cantidad,
                "precio": prod.precio,
                "subtotal": prod.precio * det.cantidad,
            }
            for det, prod in detalles
        ]

        total = sum(item["subtotal"] for item in resultado)
        return {"items": resultado, "total": total}

    def confirmar_pedido(self, id_pedido):
        pedido = self.db.query(Pedido).filter(Pedido.idpedido == id_pedido).first()
        if pedido:
            pedido.fecha_confirmacion = datetime.now()
            self.db.commit()
        return pedido

    def cancelar_pedido(self, id_pedido):
        pedido = self.db.query(Pedido).filter(Pedido.idpedido == id_pedido).first()
        if pedido:
            self.db.delete(pedido)
            self.db.commit()
            return True
        return False

    def add_to_cart_pedidos(self, numero, product_id, cantidad, observaciones=""):
        from Util.state import get_cart
        cart = get_cart(numero)
        
        # Buscar producto en la base de datos
        producto = self.db.query(Producto).filter(Producto.idproducto == int(product_id)).first()
        if not producto:
            return False, "Producto no encontrado"
        
        item = cart.get(
            product_id,
            {"cantidad": 0, "nombre": producto.nombre, "precio": float(producto.precio), "obs": ""},
        )
        item["cantidad"] += cantidad
        if observaciones:
            item["obs"] = observaciones
        cart[product_id] = item
        return True, None

    def detalle_carrito(self, numero):
        from Util.state import get_cart
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

    def mostrar_carrito_pedidos(self, numero):
        resumen = self.detalle_carrito(numero)
        if resumen["items_count"] == 0:
            return {"empty": True, "body": "Tu carrito está vacío. Escribí *menu* para ver productos."}
        cuerpo = (
            resumen["body"]
            + f"\n\n💵 Total: ${resumen['total']}\n\n"
              "Opciones:\n"
              "1 Quitar producto\n"
              "2 Seguir pidiendo\n"
              "3 Confirmar pedido"
        )
        return {"empty": False, "body": cuerpo, "summary": resumen}