from Util.database import Pedido, DetallePedido, Producto
from datetime import datetime, timedelta
from Services.RepartidorService import RepartidorService
import math
import random

class PedidosService:
    def __init__(self, db_session):
        self.db = db_session
        self.cola_no = []
        self.cola_ne = []
        self.cola_so = []
        self.cola_se = []
        self.tandas_creadas = []
        self.contador_tandas = 0
        self.repartidor_service = RepartidorService()
    
    def asignar_zona(pedido_latitud, pedido_longitud):
        ref_latitud = -31.3876594
        ref_longitud = -57.9628518
        
        res_latitud = ref_latitud - float(pedido_latitud)
        res_longitud = ref_longitud - float(pedido_longitud)
        
        if res_latitud >= 0 and res_longitud >= 0:
            return "NO"
        elif res_latitud >= 0 and res_longitud <= 0:
            return "NE"
        elif res_latitud <= 0 and res_longitud >= 0:
            return "SO"
        elif res_latitud <= 0 and res_longitud <= 0:
            return "SE"
        else:
            return "NO"
    
    def obtener_cola_por_zona(self, zona):
        if zona == "NO":
            return self.cola_no
        elif zona == "NE":
            return self.cola_ne
        elif zona == "SO":
            return self.cola_so
        elif zona == "SE":
            return self.cola_se
        else:
            return self.cola_no
    
    def encolar_pedido(self, pedido):
        cola = self.obtener_cola_por_zona(pedido.zona)
        cola.append(pedido)
        print(f" Pedido {pedido.idpedido} encolado en zona {pedido.zona}. Total en cola: {len(cola)}")
    
    def debe_crear_tanda(self, zona):
        cola = self.obtener_cola_por_zona(zona)
        
        if len(cola) >= 3:
            return True, "3_pedidos"
        
        if len(cola) > 0:
            primer_pedido = cola[0]
            if primer_pedido.fecha_confirmacion:
                tiempo_espera = datetime.now() - primer_pedido.fecha_confirmacion
                if tiempo_espera >= timedelta(minutes=45):
                    return True, "45_minutos"
        
        return False, None
    
    def crear_tanda(self, zona):
        cola = self.obtener_cola_por_zona(zona)
        
        if len(cola) == 0:
            return None
        
        cantidad = min(7, len(cola))
        pedidos_tanda = []
        
        for _ in range(cantidad):
            if len(cola) > 0:
                pedido = cola.pop(0)
                pedidos_tanda.append(pedido)
        
        self.contador_tandas += 1
        id_tanda = self.contador_tandas
        
        for pedido in pedidos_tanda:
            pedido.id_tanda = id_tanda
            self.db.commit()
        
        tanda = {
            "id": id_tanda,
            "zona": zona,
            "pedidos": pedidos_tanda,
            "creada_en": datetime.now()
        }
        
        self.tandas_creadas.append(tanda)
        
        print(f" Tanda {id_tanda} creada para zona {zona} con {len(pedidos_tanda)} pedidos")
        
        self.repartidor_service.asignar_tanda(tanda)
        
        return tanda
    
    def revisar_todas_las_zonas(self):
        zonas = ["NO", "NE", "SO", "SE"]
        tandas_creadas = []
        
        for zona in zonas:
            debe_crear, razon = self.debe_crear_tanda(zona)
            if debe_crear:
                tanda = self.crear_tanda(zona)
                if tanda:
                    tandas_creadas.append(tanda)
        
        return tandas_creadas
    
    def obtener_tandas_pendientes(self):
        return self.tandas_creadas
    
    def obtener_tanda_por_id(self, id_tanda):
        for tanda in self.tandas_creadas:
            if tanda["id"] == id_tanda:
                return tanda
        return None

    def crear_pedido(self, id_chat, id_cliente, direccion, latitud=None, longitud=None):
        pedido = Pedido(
            id_chat=id_chat,
            id_cliente=id_cliente,
            direccion=direccion,
            latitud=latitud,
            longitud=longitud,
            estado="pendiente",
            fecha_confirmacion=datetime.now(),
            codigo_verificacion=random.randint(1000, 9999)
        )
        self.db.add(pedido)
        self.db.commit()
        self.db.refresh(pedido)
        
        if pedido.latitud and pedido.longitud:
            zona = self.asignar_zona(pedido.latitud, pedido.longitud)
            pedido.zona = zona
            self.db.commit()
            self.encolar_pedido(pedido)
            
            self.revisar_todas_las_zonas()
        else:
            print(f"Pedido {pedido.idpedido} no tiene coordenadas, no se puede asignar zona")
        
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

    def cancelar_pedido(self, id_pedido):
        pedido = self.db.query(Pedido).filter(Pedido.idpedido == id_pedido).first()
        if pedido:
            self.db.delete(pedido)
            self.db.commit()
            return True
        return False

    def add_to_cart_pedidos(self, numero, product_id, cantidad, observaciones=""):
        from Util.estado import get_cart
        cart = get_cart(numero)
        
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
        from Util.estado import get_cart
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