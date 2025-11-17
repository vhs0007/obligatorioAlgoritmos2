from Util.database import get_db_connection
import math

class RepartidorService:

    def asignar_repartidor(id_pedido, zona):
        conn = get_db_connection()
        cur = conn.cursor()

        cur.execute(
            "SELECT idrepartidor FROM repartidor WHERE zonaasignada = %s ORDER BY cantidadkmrecorridos ASC LIMIT 1",
            (zona,)
        )
        repartidor = cur.fetchone()
        
        if not repartidor:
            print(f" Error: No se encontró repartidor para la zona {zona}")
            cur.close()
            conn.close()
            return None

        # Asignar repartidor al pedido
        cur.execute("UPDATE pedido SET id_repartidor = %s WHERE idpedido = %s", (repartidor[0], id_pedido))
        
        if cur.rowcount == 0:
            print(f"⚠️ Error: No se pudo asignar el repartidor {repartidor[0]} al pedido {id_pedido}")
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
            return 0.0
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        centro_lat = -31.3876594
        centro_lon = -57.9628518
        
        total_km = 0.0
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
