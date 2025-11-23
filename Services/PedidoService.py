from Util.database import Pedido, DetallePedido, Producto
from datetime import datetime, timedelta
from Services.RepartidorService import RepartidorService
import math
import random
import threading
from functools import partial
import time

class PedidosService:
    cola_no = []
    cola_ne = []
    cola_so = []
    cola_se = []
    tandas_creadas = []
    contador_tandas = 0
    timeouts_activos = {}  # {zona: threading.Thread}
    
    def __init__(self, db_session):
        self.db = db_session
        self.repartidor_service = RepartidorService()
        total_en_colas = (len(PedidosService.cola_no) + len(PedidosService.cola_ne) + 
                          len(PedidosService.cola_so) + len(PedidosService.cola_se))
        print(f"📦 PedidosService inicializado - Pedidos en colas: {total_en_colas} (NO:{len(PedidosService.cola_no)}, NE:{len(PedidosService.cola_ne)}, SO:{len(PedidosService.cola_so)}, SE:{len(PedidosService.cola_se)})")
    
    def asignar_zona(self, pedido_latitud, pedido_longitud):
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
            return PedidosService.cola_no
        elif zona == "NE":
            return PedidosService.cola_ne
        elif zona == "SO":
            return PedidosService.cola_so
        elif zona == "SE":
            return PedidosService.cola_se
        else:
            return PedidosService.cola_no
    
    def encolar_pedido(self, pedido):
        cola = self.obtener_cola_por_zona(pedido.zona)
        cola.append(pedido.idpedido)
        print(f"📦 pedido {pedido.idpedido} encolado en zona {pedido.zona}. Total en cola: {len(cola)}")
    
    def debe_crear_tanda(self, zona):
        cola = self.obtener_cola_por_zona(zona)
        print(f"🔍 debe_crear_tanda({zona}): cola tiene {len(cola)} pedidos")
        
        if len(cola) >= 3:
            print(f"✅ debe_crear_tanda({zona}): True (3 o más pedidos)")
            return True, "3_pedidos"
        
        if len(cola) > 0:
            primer_pedido_id = cola[0]
            primer_pedido = self.db.query(Pedido).filter(Pedido.idpedido == primer_pedido_id).first()
            if primer_pedido and primer_pedido.fecha_confirmacion:
                tiempo_espera = datetime.now() - primer_pedido.fecha_confirmacion
                print(f"🔍 debe_crear_tanda({zona}): tiempo_espera = {tiempo_espera}, minutos = {tiempo_espera.total_seconds() / 60}")
                if tiempo_espera >= timedelta(minutes=2):
                    print(f"✅ debe_crear_tanda({zona}): True (2 minutos de espera)")
                    return True, "2_minutos"
            else:
                print(f"ℹ️ debe_crear_tanda({zona}): pedido sin fecha_confirmacion o no encontrado")
        
        print(f"❌ debe_crear_tanda({zona}): False")
        return False, None
    
    def crear_tanda(self, zona):
        cola = self.obtener_cola_por_zona(zona)
        
        if len(cola) == 0:
            return None
        
        cantidad = min(3, len(cola))
        pedidos_ids = []
        pedidos_tanda = []
        
        for _ in range(cantidad):
            if len(cola) > 0:
                pedido_id = cola.pop(0)
                pedidos_ids.append(pedido_id)
        
        PedidosService.contador_tandas += 1
        id_tanda = PedidosService.contador_tandas
        
        for pedido_id in pedidos_ids:
            pedido = self.db.query(Pedido).filter(Pedido.idpedido == pedido_id).first()
            if pedido:
                pedido.id_tanda = id_tanda
                pedidos_tanda.append(pedido)
        
        self.db.commit()
        
        tanda = {
            "id": id_tanda,
            "zona": zona,
            "pedidos": pedidos_tanda,
            "creada_en": datetime.now()
        }
        
        PedidosService.tandas_creadas.append(tanda)
        
        print(f" Tanda {id_tanda} creada para zona {zona} con {len(pedidos_tanda)} pedidos")
        
        self.repartidor_service.asignar_tanda(tanda)
        
        return tanda
    
    def revisar_todas_las_zonas(self):
        print(f"🔍 revisar_todas_las_zonas() llamado")
        zonas = ["NO", "NE", "SO", "SE"]
        tandas_creadas = []
        
        for zona in zonas:
            print(f"🔍 Revisando zona {zona}...")
            debe_crear, razon = self.debe_crear_tanda(zona)
            print(f"🔍 debe_crear_tanda({zona}) = {debe_crear}, razón: {razon}")
            if debe_crear:
                print(f"🔔 debe_crear_tanda retornó True para zona {zona} - razón: {razon}")
                print(f"📞 Llamando programar timeout_zona({zona})...")
                self.programar_timeout_zona(zona)
                print(f"✅ programar timeout_zona({zona}) completado")
                
                tanda = self.crear_tanda(zona)
                if tanda:
                    tandas_creadas.append(tanda)
                    self.cancelar_timeout_zona(zona)
                    print(f"✅ Tanda creada inmediatamente para zona {zona}, timeout cancelado")
                else:
                    print(f"⚠️ No se pudo crear tanda para zona {zona}, timeout seguirá activo")
            else:
                print(f"ℹ️ No se debe crear tanda para zona {zona}")
        
        return tandas_creadas
    
    def programar_timeout_zona(self, zona):
        self.cancelar_timeout_zona(zona)
        
        print(f"🔧 Iniciando thread para timeout de zona {zona}...")
        t = threading.Thread(target=PedidosService._timeout_zona_static, args=(zona,))
        t.daemon = True
        t.start()
        PedidosService.timeouts_activos[zona] = t
        print(f"⏰ Timeout de 3 minutos programado para zona {zona} (thread ID: {t.ident})")
    
    @staticmethod
    def _timeout_zona_static(zona):
        """Timeout de 3 minutos: si no se creó tanda, la crea automáticamente."""
        print(f"⏳ Thread de timeout iniciado para zona {zona}, esperando 180 segundos...")
        time.sleep(180)  
        print(f"⏰ Timeout de 3 minutos alcanzado para zona {zona}")
        
        cola = None
        if zona == "NO":
            cola = PedidosService.cola_no
        elif zona == "NE":
            cola = PedidosService.cola_ne
        elif zona == "SO":
            cola = PedidosService.cola_so
        elif zona == "SE":
            cola = PedidosService.cola_se
        
        print(f"📊 Verificando cola de zona {zona}: {len(cola) if cola else 0} pedidos")
        
        if cola and len(cola) > 0:
            print(f"⏰ Timeout de 3 minutos alcanzado para zona {zona}. Creando tanda...")
            
            from Util.database import get_db_session
            db_session = get_db_session()
            try:
                pedido_service = PedidosService(db_session)
                
                debe_crear, razon = pedido_service.debe_crear_tanda(zona)
                print(f"🔍 Verificación: debe_crear={debe_crear}, razón={razon}")
                if debe_crear:
                    tanda = pedido_service.crear_tanda(zona)
                    if tanda:
                        print(f"✅ Tanda creada por timeout en zona {zona}")
                    else:
                        print(f"❌ No se pudo crear tanda por timeout en zona {zona}")
                else:
                    print(f"ℹ️ Ya no se debe crear tanda para zona {zona}")
            except Exception as e:
                print(f"⚠️ Error en timeout de zona {zona}: {e}")
                import traceback
                traceback.print_exc()
            finally:
                db_session.close()
        else:
            print(f"ℹ️ No hay pedidos en cola para zona {zona}, no se crea tanda")
        
        # Limpiar timeout
        if zona in PedidosService.timeouts_activos:
            del PedidosService.timeouts_activos[zona]
            print(f"🧹 Timeout limpiado para zona {zona}")
    
    def cancelar_timeout_zona(self, zona):
        if zona in PedidosService.timeouts_activos:
           
            if zona in PedidosService.timeouts_activos:
                del PedidosService.timeouts_activos[zona]
                print(f"⏹️ Timeout cancelado para zona {zona}")
    
    def obtener_tandas_pendientes(self):
        return PedidosService.tandas_creadas
    
    def obtener_tanda_por_id(self, id_tanda):
        for tanda in PedidosService.tandas_creadas:
            if tanda["id"] == id_tanda:
                return tanda
        return None

    def crear_pedido(self, id_chat, id_cliente, direccion, latitud=None, longitud=None):
        print(f"Creando pedido - Latitud: {latitud}, Longitud: {longitud}, Dirección: {direccion}")
        
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
        
        print(f"Pedido {pedido.idpedido} creado en BD - Latitud: {pedido.latitud}, Longitud: {pedido.longitud}")
        
        if pedido.latitud and pedido.longitud:
            zona = self.asignar_zona(pedido.latitud, pedido.longitud)
            pedido.zona = zona
            print(f"Zona asignada para pedido {pedido.idpedido}: {zona}")
            self.db.commit()
            self.encolar_pedido(pedido)
            
            self.revisar_todas_las_zonas()
        else:
            print(f"Pedido {pedido.idpedido} NO tiene coordenadas válidas - Latitud: {pedido.latitud}, Longitud: {pedido.longitud}")
        
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