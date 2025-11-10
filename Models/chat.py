from functools import wraps
from typing import Any, Optional, Dict, Callable
import inspect
from datetime import datetime
from Services.PedidoService import PedidosService
from Services.ProductoService import ProductosService
from Util.database import get_db_session
from whatsapp_api import enviar_mensaje_whatsapp
from Util.menus import menu_categorias, mostrar_productos
from Util.state import clear_cart

class Chat:
    def __init__(self, id_chat=None, id_cliente=None, id_repartidor=None, pedido_service=None, producto_service=None):
        self.id_chat = id_chat
        self.id_cliente = id_cliente
        self.id_repartidor = id_repartidor
        self.pedido_service = pedido_service
        self.producto_service = producto_service
        self.function_graph: Dict[str, Dict] = {}
        self.usuarios: Dict[str, Dict[str, Any]] = {}  
        self.sesiones: Dict[str, Dict[str, Any]] = {}  
        self.waiting_for: Optional[Callable] = None
        self.conversation_data: Dict[str, Any] = {}
        
        self._register_commands()
    
    def _register_commands(self):
        self.function_graph = {
            "menu": {
                'function': self.cmd_menu,
                'name': 'cmd_menu',
                'doc': self.cmd_menu.__doc__,
                'command': 'menu'
            },
            "ayuda": {
                'function': self.funcion_ayuda,
                'name': 'funcion_ayuda',
                'doc': self.funcion_ayuda.__doc__,
                'command': 'ayuda'
            },
            "carrito": {
                'function': self.cmd_carrito,
                'name': 'cmd_carrito',
                'doc': self.cmd_carrito.__doc__,
                'command': 'carrito'
            },
        }
    
    def get_session(self, numero):
        if numero not in self.sesiones:
            self.sesiones[numero] = {
                "page": 1,
                "filter": "cat_all",
                "order_asc": True,
                "state": "inicio"  
            }
        return self.sesiones[numero]
    
    def reset_session(self, numero):
        if numero in self.sesiones:
            self.sesiones[numero] = {
                "page": 1,
                "filter": "cat_all",
                "order_asc": True,
                "state": "inicio"  
            }
    
    def clear_state(self, numero):
        self.reset_session(numero)
        self.reset_conversation()
    
    def obtener_o_crear_usuario(self, numero):
        if numero not in self.usuarios:
            self.usuarios[numero] = {}
        return self.usuarios[numero]
    
    def set_waiting_for(self, numero, func: Callable, **context_data):
        """Establecer función esperada para próximo mensaje del usuario."""
        usuario = self.obtener_o_crear_usuario(numero)
        usuario['waiting_for'] = func
        usuario['context_data'] = context_data
        
        print(f"⏳ {numero}: Esperando respuesta para: {func.__name__}")
    
    def set_conversation_data(self, key: str, value: Any):
        self.conversation_data[key] = value
    
    def get_conversation_data(self, key: str, default: Any = None) -> Any:
        return self.conversation_data.get(key, default)
    
    def clear_conversation_data(self):
        self.conversation_data = {}
    
    def reset_conversation(self):
        self.waiting_for = None
        self.conversation_data = {}
        print("✅ Conversación reseteada.")
    
    def is_waiting_response(self, numero) -> bool:
        usuario = self.usuarios.get(numero, {})
        return usuario.get('waiting_for') is not None
    
    def get_waiting_function(self, numero) -> Optional[Callable]:
        usuario = self.usuarios.get(numero, {})
        return usuario.get('waiting_for')
    
    def print_state(self):
        print(f"\n{'='*60}")
        print("ESTADO DE LA CONVERSACIÓN")
        print(f"{'='*60}")
        waiting = self.waiting_for
        print(f"Esperando respuesta: {waiting.__name__ if waiting else 'No'}")
        print(f"Datos de conversación: {self.conversation_data}")
        print(f"{'='*60}\n")

    # ==================== FUNCIONES DEL BOT PARA MANEJAR LA CONVERSACIÓN ====================
    
    def cmd_menu(self, numero, texto):
        sesion = self.get_session(numero)
        sesion["state"] = "viendo_categorias"
        return enviar_mensaje_whatsapp(numero, menu_categorias(numero))

    def funcion_ayuda(self, numero, texto):
        ayuda_texto = (
            "🤖 *Comandos disponibles:*\n"
            "/menu - Ver el menú de productos\n"
            "/carrito - Ver tu carrito actual\n"
            "/ayuda - Mostrar esta ayuda\n"
            "/cancelar - Cancelar pedido actual"
        )
        return enviar_mensaje_whatsapp(numero, ayuda_texto)

    def cmd_carrito(self, numero, texto):
        res = self.pedido_service.mostrar_carrito_pedidos(numero)
        if res["empty"]:
            return enviar_mensaje_whatsapp(numero, res["body"])
        return enviar_mensaje_whatsapp(numero, res["body"])

    def handle_text(self, numero, texto):
        """Punto de entrada para mensajes de texto desde el webhook."""
        texto = texto.lower().strip()
        if not self.id_cliente:
            self.id_cliente = numero 
            self.id_chat = f"chat_{numero}"
        flujo_actual = self.get_waiting_function(numero)
        if flujo_actual:
            return flujo_actual(numero, texto)
        return self.flujo_inicio(numero, texto)

    # --- FLUJO ---

    def flujo_inicio(self, numero, mensaje):
        if mensaje in ("menu", "hola", "hi", "buenas", "buenos dias"):
            self.set_waiting_for(numero, self.flujo_categorias)
            return enviar_mensaje_whatsapp(numero, menu_categorias(numero))

        if mensaje == "carrito":
            self.set_waiting_for(numero, self.flujo_carrito)
            res = self.pedido_service.mostrar_carrito_pedidos(numero)
            return enviar_mensaje_whatsapp(numero, res["body"])

        return enviar_mensaje_whatsapp(
            numero,
            "👋 Escribí *menu* para ver productos o *carrito* para ver tu pedido."
        )

    def flujo_categorias(self, numero, mensaje):
        if mensaje.startswith("cat_"):
            self.set_waiting_for(numero, self.flujo_productos)
            return mostrar_productos(numero, mensaje)

        if mensaje == "salir":
            self.clear_state(numero)
            return enviar_mensaje_whatsapp(numero, "❌ Cancelado. Escribí *menu* para empezar de nuevo.")

        return enviar_mensaje_whatsapp(numero, "📋 Elegí una categoría del menú.")

    def flujo_productos(self, numero, mensaje):
        if mensaje == "carrito":
            self.set_waiting_for(numero, self.flujo_carrito)
            res = self.pedido_service.mostrar_carrito_pedidos(numero)
            return enviar_mensaje_whatsapp(numero, res["body"])

        if mensaje == "menu":
            self.set_waiting_for(numero, self.flujo_categorias)
            return enviar_mensaje_whatsapp(numero, menu_categorias(numero))

        if mensaje.startswith("add_"):
            prod_id = mensaje.replace("add_", "")
            self.set_waiting_for(numero, lambda n, t: self.flujo_cantidad(n, t, prod_id))
            return enviar_mensaje_whatsapp(numero, "📝 Escribí la cantidad con observación (ej: 2 sin cebolla)")

        return enviar_mensaje_whatsapp(numero, "📋 Escribí *carrito* para ver tu pedido o *menu* para volver al inicio.")

    def flujo_cantidad(self, numero, mensaje, prod_id):
        partes = mensaje.split()
        try:
            cantidad = int(partes[0])
            if cantidad <= 0:
                raise ValueError
        except ValueError:
            return enviar_mensaje_whatsapp(numero, "⚠️ Cantidad inválida. Escribí un número válido (ej: 2).")

        aclaracion = " ".join(partes[1:]) if len(partes) > 1 else ""
        ok, err = self.pedido_service.add_to_cart_pedidos(numero, prod_id, cantidad, aclaracion)
        if not ok:
            return enviar_mensaje_whatsapp(numero, f"❌ Error al agregar: {err}")

        self.set_waiting_for(numero, self.flujo_productos)
        return enviar_mensaje_whatsapp(
            numero,
            f"✅ {cantidad} agregado(s) al carrito.\nEscribí *carrito* para ver tu pedido o *menu* para volver."
        )

    def flujo_carrito(self, numero, mensaje):
        if mensaje in ("2", "seguir", "seguir pidiendo"):
            self.set_waiting_for(numero, self.flujo_categorias)
            return enviar_mensaje_whatsapp(numero, menu_categorias(numero))

        if mensaje in ("3", "confirmar"):
            self.set_waiting_for(numero, self.flujo_confirmacion)
            return enviar_mensaje_whatsapp(numero, "📍 Enviá tu ubicación para calcular el envío.")

        if mensaje in ("1", "quitar", "eliminar"):
            return enviar_mensaje_whatsapp(numero, "🗑️ Escribí el nombre del producto a quitar (a implementar).")

        if mensaje in ("salir", "cancelar"):
            self.clear_state(numero)
            clear_cart(numero)
            return enviar_mensaje_whatsapp(numero, "❌ Pedido cancelado. Escribí *menu* para comenzar de nuevo.")

        res = self.pedido_service.mostrar_carrito_pedidos(numero)
        if res["empty"]:
            return enviar_mensaje_whatsapp(numero, res["body"])
        return enviar_mensaje_whatsapp(numero, "📋 Escribí 1 para quitar, 2 para seguir pidiendo o 3 para confirmar.")

    def es_ubicacion(self, contenido: str) -> bool:
        """Validar si el contenido es una ubicación (lat, lon)."""
        try:
            partes = contenido.split(',')
            return len(partes) == 2 and float(partes[0]) and float(partes[1])
        except (ValueError, IndexError):
            return False

    def flujo_confirmacion(self, numero, mensaje):
        if mensaje in ("cancelar", "salir"):
            self.clear_state(numero)
            return enviar_mensaje_whatsapp(numero, "❌ Pedido cancelado.")

        if self.es_ubicacion(mensaje):
            return self.handle_location(numero, mensaje)

        return enviar_mensaje_whatsapp(numero, "📍 Enviá tu ubicación para calcular el envío.")

    def handle_location(self, numero, contenido):
        """Maneja la recepción de ubicación del usuario."""
        try:
            lat, lon = contenido.split(',')
            id_cliente = self.id_cliente or self.conversation_data.get('id_cliente')
            id_chat = self.id_chat or self.conversation_data.get('id_chat')
            direccion = self.conversation_data.get('direccion') or ''
            pedido_service = self.pedido_service
            if not (pedido_service and id_cliente and id_chat):
                return enviar_mensaje_whatsapp(numero, "⚠️ Faltan datos para crear el pedido. Intentalo de nuevo.")

            pedido = pedido_service.crear_pedido(id_chat=id_chat, id_cliente=id_cliente, direccion=direccion, latitud=lat, longitud=lon)
            self.conversation_data['id_pedido'] = getattr(pedido, 'idpedido', None)
            msg = f"📍 Recibí tu ubicación:\nLatitud: {lat}\nLongitud: {lon}\nTu pedido fue registrado con ID: {getattr(pedido, 'idpedido', 'N/A')}"
            return enviar_mensaje_whatsapp(numero, msg)
        except Exception:
            return enviar_mensaje_whatsapp(numero, "⚠️ No se pudo procesar la ubicación correctamente.")
