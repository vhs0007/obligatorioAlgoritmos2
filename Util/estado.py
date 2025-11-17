"""
Variables locales para estado de sesión y carrito.
No se persisten en BD, son temporales por sesión.
"""

# ESTADO: reemplaza SESSION - estado temporal de navegación (no se persiste en BD)
ESTADO = {}

def get_estado(numero):
    """Obtiene el estado de navegación del usuario (página, filtro, orden)."""
    return ESTADO.setdefault(numero, {
        "page": 1,
        "filter": "cat_all",
        "order_asc": True,
        "state": "inicio"  
    })

def reset_estado(numero):
    """Resetea el estado de navegación del usuario."""
    if numero in ESTADO:
        ESTADO[numero] = {
            "page": 1,
            "filter": "cat_all",
            "order_asc": True,
            "state": "inicio"  
        }

# CARRITO: variable local para el carrito temporal (no se persiste en BD)
CARRITO = {}

def get_cart(numero):
    """Obtiene el carrito del usuario."""
    return CARRITO.setdefault(numero, {})

def clear_cart(numero):
    """Limpia el carrito del usuario."""
    if numero in CARRITO:
        del CARRITO[numero]

