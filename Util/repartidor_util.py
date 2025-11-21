from whatsapp_api import enviar_mensaje_whatsapp, enviar_imagen_whatsapp
from Util.database import get_db_connection

def obtener_pedidos_pendientes_repartidor(id_repartidor):
    conn = get_db_connection()
    cur = conn.cursor()
    
    cur.execute("""
        SELECT idpedido, direccion 
        FROM pedido 
        WHERE id_repartidor = %s AND estado != 'entregado'
        ORDER BY idpedido
    """, (id_repartidor,))
    
    resultados = cur.fetchall()
    cur.close()
    conn.close()
    
    pedidos = []
    for row in resultados:
        pedidos.append({
            'idpedido': row[0],
            'direccion': row[1]
        })
    
    return pedidos

def menu_pedidos_repartidor(numero, pedidos):
    rows = []

    for p in pedidos:
        rows.append({
            "id": f"pedido_{p['idpedido']}",
            "title": f"Pedido #{p['idpedido']}",
            "description": p["direccion"]
        })

    secciones = [{
        "title": "Pedidos Pendientes",
        "rows": rows
    }]

    payload = {
        "messaging_product": "whatsapp",
        "to": numero,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "📦 Tus pedidos pendientes"},
            "body": {"text": "Elegí el pedido que acabás de entregar:"},
            "footer": {"text": "Seleccioná un pedido"},
            "action": {"button": "Ver pedidos", "sections": secciones},
        },
    }

    return enviar_mensaje_whatsapp(numero, payload)

def handle_interactive(numero, interactive):
    if interactive["type"] == "list_reply":
        seleccion = interactive["list_reply"]["id"]
        return manejar_seleccion_pedido(numero, seleccion)
    return None

def manejar_seleccion_pedido(numero, seleccion_id):
    from Services.RepartidorService import RepartidorService
    
    id_pedido = int(seleccion_id.replace("pedido_", ""))

    repartidor_service = RepartidorService()
    repartidor = repartidor_service.obtener_repartidor_por_telefono(numero)

    if not repartidor:
        return enviar_mensaje_whatsapp(numero, "No estás registrado como repartidor.")

    conn = get_db_connection()
    cur = conn.cursor()
    cur.execute("SELECT codigo_verificacion FROM pedido WHERE idpedido = %s", (id_pedido,))
    row = cur.fetchone()
    cur.close()
    conn.close()

    if not row:
        return enviar_mensaje_whatsapp(numero, "Pedido no encontrado.")

    codigo = row[0]

    resultado = RepartidorService().confirmar_entrega(
        repartidor["id"], id_pedido, codigo
    )

    if resultado.get("tanda_finalizada"):
        return enviar_mensaje_whatsapp(numero, "🎉 Tanda completada! Sos un crack 🙌")

    pedidos = obtener_pedidos_pendientes_repartidor(repartidor["id"])
    if not pedidos:
        return enviar_mensaje_whatsapp(numero, "No tenés más pedidos pendientes 🙌")
    
    return menu_pedidos_repartidor(numero, pedidos)

def enviar_actualizacion_repartidor(telefono, pedidos, ruta_imagen, mensaje):

    if ruta_imagen:
        enviar_imagen_whatsapp(telefono, ruta_imagen, mensaje)

    if not pedidos:
        enviar_mensaje_whatsapp(telefono, "No tenés más pedidos pendientes 🙌")
        return

    rows = [{
        "id": f"pedido_{p['idpedido']}",
        "title": f"Pedido #{p['idpedido']}",
        "description": p["direccion"]
    } for p in pedidos]

    payload = {
        "messaging_product": "whatsapp",
        "to": telefono,
        "type": "interactive",
        "interactive": {
            "type": "list",
            "header": {"type": "text", "text": "📦 Pedidos pendientes"},
            "body": {"text": "Elegí el pedido que acabás de entregar:"},
            "footer": {"text": "Seleccioná un pedido"},
            "action": {"button": "Ver pedidos", "sections": [{
                "title": "Pendientes",
                "rows": rows
            }]},
        },
    }

    enviar_mensaje_whatsapp(telefono, payload)
