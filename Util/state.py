USUARIOS = {}
SESSION = {}
CARRITO = {}

def ensure_user(numero, usu=None):
    if numero not in USUARIOS:
        USUARIOS[numero] = {"numero": numero, "usu": usu or {}, "fecha": None}
    return USUARIOS[numero]

def get_session(numero):
    return SESSION.setdefault(numero, {
        "page": 1,
        "filter": "cat_all",
        "order_asc": True,
        "state": "inicio"  
    })

def reset_session(numero):
    if numero in SESSION:
        SESSION[numero] = {
            "page": 1,
            "filter": "cat_all",
            "order_asc": True,
            "state": "inicio"  
        }

def get_cart(numero):
    return CARRITO.setdefault(numero, {})

def clear_cart(numero):
    if numero in CARRITO:
        del CARRITO[numero]
