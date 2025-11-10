# 🏗️ Arquitectura del Bot de GordoEats

## Visión General

El bot implementa una **arquitectura orientada a servicios y flujos conversacionales** con separación clara de responsabilidades:

```
┌─────────────────────────────────────────────────────────────┐
│                    WEBHOOK (WhatsApp)                        │
│               ↓ recibir_mensaje(numero, texto)               │
└──────────────────────┬──────────────────────────────────────┘
                       │
                       ↓
            ┌──────────────────────┐
            │   Chat (Orquestador)  │ ← Estado por usuario
            │  - Flujos conversac.  │ ← Máquina de estados dinámica
            │  - set_waiting_for()  │ ← Control de contexto
            └──────────┬────────────┘
                       │
        ┌──────────────┼──────────────┐
        ↓              ↓              ↓
┌──────────────┐ ┌──────────────┐ ┌──────────────┐
│PedidosService│ │ProductoService│ │ Chat (Utils) │
│ - Carrito    │ │ - Listados    │ │ - Ubicación  │
│ - Pedidos    │ │ - Filtros     │ │ - Validación │
│ - Detalles   │ │ - Paginación  │ │              │
└──────────────┘ └──────────────┘ └──────────────┘
```

---

## 📦 Componentes Principales

### 1. **Chat (Models/Chat.py)** - Orquestador Principal
- **Responsabilidad**: Manejar flujo conversacional y dirigir a servicios.
- **Características Clave**:
  - ✅ Máquina de estados dinámicos (`waiting_for` por usuario)
  - ✅ Gestión de sesiones por número de teléfono
  - ✅ Contexto conversacional persistente dentro de sesión
  - ✅ Métodos de flujo: `flujo_inicio()`, `flujo_categorias()`, `flujo_productos()`, etc.

### 2. **PedidosService (Services/PedidoService.py)** - Lógica de Negocio
- **Responsabilidad**: Gestionar carrito, pedidos y detalles.
- **Métodos Principales**:
  - `crear_pedido()` - Crear pedido en BD con ubicación
  - `add_to_cart_pedidos()` - Agregar producto al carrito
  - `mostrar_carrito_pedidos()` - Obtener resumen del carrito
  - `agregar_producto()` - Agregar detalle a pedido
  - `obtener_detalle()` - Obtener detalles del pedido
  - `confirmar_pedido()` / `cancelar_pedido()` - Gestionar estado

### 3. **ProductoService (Services/ProductoService.py)** - Catálogo
- **Responsabilidad**: Gestionar visualización y filtrado de productos.
- **Métodos Principales**:
  - `obtener_lista()` - Lista de productos actual
  - `aplicar_filtro()` - Filtrar por categoría
  - `cambiar_orden()` - Cambiar ordenamiento
  - `siguiente_pagina()` / `pagina_anterior()` - Navegación

---

## 🔄 Flujo de un Mensaje

```
Usuario envía: "Hola"
       ↓
webhook_server.py → procesar_mensaje_recibido()
       ↓
bot.recibir_mensaje(numero="+123456", texto="hola")
       ↓
¿Hay waiting_for para este usuario? 
  ├─ SÍ → ejecutar flujo pendiente
  └─ NO → flujo_inicio(numero, "hola")
       ↓
flujo_inicio() → reconoce "hola" → set_waiting_for(numero, flujo_categorias)
       ↓
enviar_mensaje_whatsapp(numero, menu_categorias(numero))
       ↓
Esperar próximo mensaje del usuario...
```

---

## 💾 Gestión de Estado

### Por Usuario (self.usuarios[numero])
```python
{
  'waiting_for': <función del flujo>,
  'context_data': {datos contextuales}
}
```

### Por Sesión (self.sesiones[numero])
```python
{
  'page': 1,
  'filter': 'cat_all',
  'order_asc': True,
  'state': 'inicio'
}
```

---

## 🔗 Integración de Funciones Externas

El Chat importa y utiliza funciones de utilidades:

| Función | Origen | Uso |
|---------|--------|-----|
| `enviar_mensaje_whatsapp()` | `whatsapp_api.py` | Enviar respuestas al usuario |
| `menu_categorias()` | `Util/handlers_message.py` | Generar menú interactivo |
| `mostrar_productos()` | `Util/handlers_message.py` | Listar productos |
| `clear_cart()` | `Util/state.py` | Limpiar carrito por usuario |

---

## 🚀 Instanciación del Bot

```python
# main.py
from database import get_db_session
from Services.PedidoService import PedidosService
from Services.ProductoService import ProductosService
from Models.Chat import Chat

db_session = get_db_session()
pedido_service = PedidosService(db_session)
producto_service = ProductosService()

bot = Chat(
    pedido_service=pedido_service,
    producto_service=producto_service
)
```

---

## 🎯 Ventajas de Esta Arquitectura

✅ **Separación de responsabilidades** - Chat ≠ Lógica de BD  
✅ **Reutilizable** - Servicios independientes de la interfaz  
✅ **Escalable** - Agregar nuevos flujos sin afectar existentes  
✅ **Testeable** - Mock services para pruebas unitarias  
✅ **Mantenible** - Cambios localizados y bajo acoplamiento  
✅ **Context-aware** - Cada usuario tiene su propio estado

---

## 🔮 Próximos Pasos Sugeridos

1. **Implementar persistencia de sesión**: Guardar `sesiones` en Redis/BD
2. **Agregar logging**: Debug y seguimiento de flujos
3. **Validaciones robustas**: Más checks en `handle_location()`
4. **Tests unitarios**: Para servicios y flujos
5. **Integración de pagos**: En `flujo_confirmacion()`
6. **Notificaciones de repartidor**: Después de crear pedido

