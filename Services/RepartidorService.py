from Util.database import get_db_connection
import random

class RepartidorService:

    def asignar_repartidor(id_pedido):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute("SELECT idrepartidor FROM repartidor ORDER BY RANDOM() LIMIT 1")
        repartidor = cur.fetchone()
        if not repartidor:
            return None

        cur.execute("UPDATE pedido SET id_repartidor = %s WHERE idpedido = %s", (repartidor[0], id_pedido))
        conn.commit()
        cur.close()
        conn.close()
        return repartidor[0]

    def registrar_recorrido(id_repartidor, km):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute("UPDATE repartidor SET cantidadkmrecorridos = cantidadkmrecorridos + %s WHERE idrepartidor = %s",
                    (km, id_repartidor))
        conn.commit()
        cur.close()
        conn.close()
