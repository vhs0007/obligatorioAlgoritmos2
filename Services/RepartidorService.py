from Util.database import get_db_connection, Pedido
from Util.coordenadas_gifs import calcular_y_generar_ruta_tanda, calcular_ruta_simple, generar_imagen_ruta_delivery
from whatsapp_api import enviar_imagen_whatsapp, enviar_mensaje_whatsapp
from Util.repartidor_util import enviar_actualizacion_repartidor
import math
import random


def simplificar_pedido(tupla):
    return Pedido(
        idpedido=tupla[0],
        id_chat=tupla[1],
        id_cliente=tupla[2],
        id_repartidor=tupla[3],
        direccion=tupla[4],
        latitud=tupla[5],
        longitud=tupla[6],
        estado=tupla[7],
        codigo_verificacion=tupla[8],
        id_tanda=tupla[9]
    )


class RepartidorService:
    cola_tandas_pendientes = []
    repartidores_ocupados = {}
    
    def __init__(self):
        pass
    
    def obtener_repartidores_disponibles(self):
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT idrepartidor, nombre, apellido FROM repartidor")
        todos_repartidores = cur.fetchall()
        
        cur.close()
        conn.close()
        
        disponibles = []
        for rep in todos_repartidores:
            id_repartidor = rep[0]
            if id_repartidor not in RepartidorService.repartidores_ocupados:
                disponibles.append(rep)
        
        return disponibles
    
    def obtener_repartidor_por_telefono(self, telefono):
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT idrepartidor FROM repartidor WHERE telefono = %s", (telefono,))
        resultado = cur.fetchone()
        
        cur.close()
        conn.close()
        
        if resultado:
            return {
                "id": resultado[0],
            }
        return None
    
    def asignar_tanda_a_repartidor(self, tanda, id_repartidor):
        conn = get_db_connection()
        cur = conn.cursor()
        
        for pedido in tanda["pedidos"]:
            cur.execute(
                "UPDATE pedido SET id_repartidor = %s WHERE idpedido = %s",
                (id_repartidor, pedido.idpedido)
            )
        
        conn.commit()
        
        cur.execute("SELECT telefono, nombre, apellido FROM repartidor WHERE idrepartidor = %s", (id_repartidor,))
        repartidor_info = cur.fetchone()
        
        cur.close()
        conn.close()
        
        RepartidorService.repartidores_ocupados[id_repartidor] = tanda["id"]
        
        nombre_repartidor_completo = f"{repartidor_info[1]} {repartidor_info[2]}" if repartidor_info else "N/A"
        print(f"Repartidor {id_repartidor} ({nombre_repartidor_completo}) asignado a Tanda {tanda['id']} (Zona: {tanda['zona']})")
        
        try:
            if repartidor_info:
                telefono_repartidor = repartidor_info[0]
                nombre_repartidor = f"{repartidor_info[1]} {repartidor_info[2]}"
                
                print(f"\n Generando ruta para {nombre_repartidor}...")
                
                pedidos_data = []
                for pedido in tanda["pedidos"]:
                    pedidos_data.append({
                        'latitud': pedido.latitud,
                        'longitud': pedido.longitud,
                        'direccion': pedido.direccion,
                        'idpedido': pedido.idpedido
                    })
                
                ruta_imagen, info_ruta = calcular_y_generar_ruta_tanda(pedidos_data, tanda["id"])
                
                mensaje = f"Nueva Tanda Asignada #{tanda['id']}\n\n"
                mensaje += f" Pedidos: {info_ruta['num_entregas']}\n"
                mensaje += f" Distancia total: {info_ruta['distancia_km']} km\n"
                mensaje += f" Tiempo estimado: {info_ruta['tiempo_min']} min\n"
                mensaje += f" Zona: {tanda['zona']}\n\n"
                mensaje += f"Kick buttowski"
                mensaje += "\nLa imagen muestra tu ruta óptima de entrega."
                
                pedidos_para_menu = [{
                    'idpedido': p.idpedido,
                    'direccion': p.direccion
                } for p in tanda["pedidos"]]

                enviar_actualizacion_repartidor(
                    telefono_repartidor,
                    pedidos_para_menu,
                    ruta_imagen,
                    mensaje
                )
                
                self.registrar_recorrido(id_repartidor, info_ruta['distancia_km'])
                
        except Exception as e:
            print(f" Error calculando/enviando ruta: {e}")
            print("Continuando sin ruta...")
        
        return True
    
    def asignar_tanda(self, tanda):
        repartidores_disponibles = self.obtener_repartidores_disponibles()
        
        if len(repartidores_disponibles) > 0:
            repartidor_elegido = random.choice(repartidores_disponibles)
            id_repartidor = repartidor_elegido[0]
            print(f"📋 Asignando Tanda {tanda['id']} a repartidor {id_repartidor} (disponibles: {len(repartidores_disponibles)})")
            self.asignar_tanda_a_repartidor(tanda, id_repartidor)
            return True
        else:
            RepartidorService.cola_tandas_pendientes.append(tanda)
            print(f"⚠️ Tanda {tanda['id']} encolada (sin repartidores disponibles)")
            
            return self.asignar_tanda_aleatoria(tanda)
    
    def asignar_tanda_aleatoria(self, tanda):
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT idrepartidor FROM repartidor")
        todos_repartidores = cur.fetchall()
        
        cur.close()
        conn.close()
        
        if len(todos_repartidores) == 0:
            return False
        
        repartidor_elegido = random.choice(todos_repartidores)
        id_repartidor = repartidor_elegido[0]
        
        self.asignar_tanda_a_repartidor(tanda, id_repartidor)
        print(f" Tanda {tanda['id']} asignada aleatoriamente a repartidor {id_repartidor}")
        return True
    
    def finalizar_tanda(self, id_repartidor):
        if id_repartidor in RepartidorService.repartidores_ocupados:
            tanda_id = RepartidorService.repartidores_ocupados[id_repartidor]
            del RepartidorService.repartidores_ocupados[id_repartidor]
            print(f" Tanda {tanda_id} finalizada para repartidor {id_repartidor}")
            
            if len(RepartidorService.cola_tandas_pendientes) > 0:
                siguiente_tanda = RepartidorService.cola_tandas_pendientes.pop(0)
                self.asignar_tanda(siguiente_tanda)
    
    def obtener_tandas_pendientes(self):
        return len(RepartidorService.cola_tandas_pendientes)
    
    def obtener_proximo_pedido(self, tanda_id):
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT idpedido, id_chat, id_cliente, id_repartidor, direccion, 
                   latitud, longitud, estado, codigo_verificacion, id_tanda
            FROM pedido 
            WHERE id_tanda = %s AND estado != 'entregado'
            ORDER BY idpedido
            LIMIT 1
        """, (tanda_id,))
        
        resultado = cur.fetchone()
        cur.close()
        conn.close()
        
        if resultado:
            return simplificar_pedido(resultado)
        return None
    
    def confirmar_entrega(self, id_repartidor, id_pedido, codigo_ingresado):
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("""
            SELECT codigo_verificacion, id_tanda, id_chat, latitud, longitud 
            FROM pedido 
            WHERE idpedido = %s
        """, (id_pedido,))
        pedido_info = cur.fetchone()
        
        if not pedido_info:
            cur.close()
            conn.close()
            return {"success": False, "mensaje": "Pedido no encontrado"}
        
        codigo_correcto, tanda_id, id_chat, lat_actual, lon_actual = pedido_info
        
        if int(codigo_ingresado) != int(codigo_correcto):
            cur.close()
            conn.close()
            return {"success": False, "mensaje": "Código incorrecto"}
        
        cur.execute("UPDATE pedido SET estado = 'entregado' WHERE idpedido = %s", (id_pedido,))
        conn.commit()
        print(f"Pedido {id_pedido} entregado")
        
        proximo_pedido = self.obtener_proximo_pedido(tanda_id)
        
        if not proximo_pedido:
            print(f"Tanda {tanda_id} completada")
            self.finalizar_tanda(id_repartidor)
            cur.close()
            conn.close()
            return {"success": True, "mensaje": "Tanda completada", "tanda_finalizada": True}
        
        _, distancia_km, tiempo_min = calcular_ruta_simple(
            float(lat_actual), float(lon_actual),
            float(proximo_pedido.latitud), float(proximo_pedido.longitud)
        )
        
        mensaje_cliente = (
            f"Tu pedido está en camino!\n\n"
            f"Pedido #{proximo_pedido.idpedido}\n"
            f"{proximo_pedido.direccion}\n"
            f"Llega en: {int(tiempo_min)} minutos\n\n"
            f"Código de verificación: {proximo_pedido.codigo_verificacion}"
        )
        
        enviar_mensaje_whatsapp(proximo_pedido.id_chat, mensaje_cliente)
        print(f"Cliente notificado: {proximo_pedido.id_chat}")
        
        cur.execute("""
            SELECT idpedido, id_chat, id_cliente, id_repartidor, direccion, 
                latitud, longitud, estado, codigo_verificacion, id_tanda
            FROM pedido 
            WHERE id_tanda = %s AND estado != 'entregado'
            ORDER BY idpedido
        """, (tanda_id,))
        pedidos_pendientes_base = cur.fetchall()

        cur.execute("SELECT telefono, nombre, apellido FROM repartidor WHERE idrepartidor = %s", (id_repartidor,))
        repartidor_info = cur.fetchone()
        
        cur.close()
        conn.close()
    
    if pedidos_pendientes_base and repartidor_info:
        pedidos_pendientes = [simplificar_pedido(t) for t in pedidos_pendientes_base]

        pedidos_data = [{
            'latitud': p.latitud,
            'longitud': p.longitud,
            'direccion': p.direccion,
            'idpedido': p.idpedido
        } for p in pedidos_pendientes]

        ruta_imagen, info_ruta = calcular_y_generar_ruta_tanda(pedidos_data, tanda_id)
        
        telefono_repartidor = repartidor_info[0]

        mensaje_rep = (
            f"Ruta Actualizada - Tanda #{tanda_id}\n\n"
            f"Entregado: Pedido #{id_pedido}\n"
            f"Pendientes: {len(pedidos_pendientes)}\n\n"
            f"Próximas entregas:\n"
        )
        
        for i, p in enumerate(pedidos_pendientes, 1):
            mensaje_rep += (
                f"\n{i}. Pedido #{p.idpedido}\n"
                f"   {p.direccion}\n"
                f"   Código: {p.codigo_verificacion}"
            )

        print("SE MANDO EL MAPA AL REPARTIDOR ////////////////////")
        
        pedidos_para_menu = [{
            'idpedido': p.idpedido,
            'direccion': p.direccion
        } for p in pedidos_pendientes]

        enviar_actualizacion_repartidor(
            telefono_repartidor,
            pedidos_para_menu,
            ruta_imagen,
            mensaje_rep
        )
    
        return {
            "success": True,
            "mensaje": "Entrega confirmada",
            "proximo_pedido": proximo_pedido.idpedido,
            "eta_minutos": int(tiempo_min)
        }


    def asignar_repartidor(id_pedido, zona):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT idrepartidor FROM repartidor WHERE zonaasignada = %s ORDER BY cantidadkmrecorridos ASC LIMIT 1",
            (zona,)
        )
        repartidor = cur.fetchone()
        
        if not repartidor:
            print(f"No se encontró repartidor para la zona {zona}")
            cur.close()
            conn.close()
            return None

        cur.execute("UPDATE pedido SET id_repartidor = %s WHERE idpedido = %s", (repartidor[0], id_pedido))
        
        if cur.rowcount == 0:
            print(f"No se pudo asignar el repartidor {repartidor[0]} al pedido {id_pedido}")
            cur.close()
            conn.close()
            return None
        
        conn.commit()
        cur.close()
        conn.close()
        return repartidor[0]

    def registrar_recorrido(self, id_repartidor, km):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE repartidor SET cantidadkmrecorridos = cantidadkmrecorridos + %s WHERE idrepartidor = %s",
            (km, id_repartidor)
        )
        conn.commit()
        cur.close()
        conn.close()
    
    def distancia_haversine(self, lat1, lon1, lat2, lon2):
        R = 6371.0
        
        lat1_rad = math.radians(float(lat1))
        lon1_rad = math.radians(float(lon1))
        lat2_rad = math.radians(float(lat2))
        lon2_rad = math.radians(float(lon2))
        
        dlat = lat2_rad - lat1_rad
        dlon = lon2_rad - lon1_rad
        
        a = math.sin(dlat / 2)**2 + math.cos(lat1_rad) * math.cos(lat2_rad) * math.sin(dlon / 2)**2
        c = 2 * math.atan2(math.sqrt(a), math.sqrt(1 - a))
        
        distancia = R * c
        return distancia
    
    def distancia_manhattan(lat1, lon1, lat2, lon2):
        lat_km = abs(float(lat1) - float(lat2)) * 111.0
        lon_km = abs(float(lon1) - float(lon2)) * 111.0 * math.cos(math.radians((float(lat1) + float(lat2)) / 2))
        
        return lat_km + lon_km
    
    def distancia_euclidiana(lat1, lon1, lat2, lon2):
        lat_km = (float(lat1) - float(lat2)) * 111.0
        lon_km = (float(lon1) - float(lon2)) * 111.0 * math.cos(math.radians((float(lat1) + float(lat2)) / 2))
        
        return math.sqrt(lat_km**2 + lon_km**2)
    
    def calcular_km_ruta(self, id_repartidor, lista_pedidos):
        from Util.database import get_db_connection
        
        if not lista_pedidos:
            return 0
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        centro_lat = -31.3876594
        centro_lon = -57.9628518
        
        total_km = 0
        lat_anterior = centro_lat
        lon_anterior = centro_lon
        
        for id_pedido, lat, lon in lista_pedidos:
            km = RepartidorService.distancia_haversine(lat_anterior, lon_anterior, lat, lon)
            total_km += km
            lat_anterior = lat
            lon_anterior = lon
        
        cur.close()
        conn.close()
        return total_km
