from Util.database import get_db_connection
from Util.coordenadas_gifs import calcular_y_generar_ruta_tanda
from whatsapp_api import enviar_imagen_whatsapp
import math
import random

class RepartidorService:
    
    def __init__(self):
        self.cola_tandas_pendientes = []
        self.repartidores_ocupados = {}
    
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
            if id_repartidor not in self.repartidores_ocupados:
                disponibles.append(rep)
        
        return disponibles
    
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
        
        self.repartidores_ocupados[id_repartidor] = tanda["id"]
        
        nombre_repartidor_completo = f"{repartidor_info[1]} {repartidor_info[2]}" if repartidor_info else "N/A"
        print(f"✅ Repartidor {id_repartidor} ({nombre_repartidor_completo}) asignado a Tanda {tanda['id']} (Zona: {tanda['zona']})")
        
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
                
                mensaje = f"🚚 *Nueva Tanda Asignada #{tanda['id']}*\n\n"
                mensaje += f"👤 Repartidor: {nombre_repartidor}\n"
                mensaje += f"📦 Pedidos: {info_ruta['num_entregas']}\n"
                mensaje += f"📏 Distancia total: {info_ruta['distancia_km']} km\n"
                mensaje += f"⏱️ Tiempo estimado: {info_ruta['tiempo_min']} min\n"
                mensaje += f"🗺️ Zona: {tanda['zona']}\n\n"
                mensaje += "📋 *Detalle de entregas:*\n"
                for idx, pedido in enumerate(tanda["pedidos"], 1):
                    mensaje += f"\n{idx}. Pedido #{pedido.idpedido}\n"
                    mensaje += f"   📍 {pedido.direccion}\n"
                    mensaje += f"   🔑 Código: *{pedido.codigo_verificacion}*\n"
                mensaje += "\n📍 La imagen muestra tu ruta óptima de entrega."
                
                resultado = enviar_imagen_whatsapp("+59891453663", ruta_imagen, mensaje)
                
                if resultado.get('success'):
                    print(f"✅ Ruta enviada exitosamente a +59891453663 (testing - asignado a: {nombre_repartidor})")
                else:
                    print(f"⚠️ Error enviando ruta: {resultado.get('error')}")
                
                self.registrar_recorrido(id_repartidor, info_ruta['distancia_km'])
                
        except Exception as e:
            print(f"⚠️ Error calculando/enviando ruta: {e}")
            print("   Continuando sin ruta...")
        
        return True
    
    def asignar_tanda(self, tanda):
        repartidores_disponibles = self.obtener_repartidores_disponibles()
        
        if len(repartidores_disponibles) > 0:
            id_repartidor = repartidores_disponibles[0][0]
            self.asignar_tanda_a_repartidor(tanda, id_repartidor)
            return True
        else:
            self.cola_tandas_pendientes.append(tanda)
            print(f" Tanda {tanda['id']} encolada (sin repartidores disponibles)")
            
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
        if id_repartidor in self.repartidores_ocupados:
            tanda_id = self.repartidores_ocupados[id_repartidor]
            del self.repartidores_ocupados[id_repartidor]
            print(f"✅ Tanda {tanda_id} finalizada para repartidor {id_repartidor}")
            
            if len(self.cola_tandas_pendientes) > 0:
                siguiente_tanda = self.cola_tandas_pendientes.pop(0)
                self.asignar_tanda(siguiente_tanda)
    
    def obtener_tandas_pendientes(self):
        return len(self.cola_tandas_pendientes)

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

    def registrar_recorrido(id_repartidor, km):
        conn = get_db_connection()
        cur = conn.cursor()
        cur.execute(
            "UPDATE repartidor SET cantidadkmrecorridos = cantidadkmrecorridos + %s WHERE idrepartidor = %s",
            (km, id_repartidor)
        )
        conn.commit()
        cur.close()
        conn.close()
    
    def distancia_haversine(lat1, lon1, lat2, lon2):
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
    
    def calcular_km_ruta(id_repartidor, lista_pedidos):
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
