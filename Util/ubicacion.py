import math
import random
import string
import requests

# GOOGLE_API_KEY = "TU_API_KEY_AQUI"

# def distancia(lat1, lon1, lat2, lon2):
#     try:
#         url = (
#             "https://maps.googleapis.com/maps/api/distancematrix/json"
#             f"?origins={lat1},{lon1}&destinations={lat2},{lon2}&key={GOOGLE_API_KEY}"
#         )
#         response = requests.get(url)
#         data = response.json()

#         if data["status"] == "OK":
#             element = data["rows"][0]["elements"][0]
#             if element["status"] == "OK":
#                 distancia_km = element["distance"]["value"] / 1000  
#                 duracion_min = element["duration"]["value"] / 60   
#                 return distancia_km, duracion_min
#             else:
#                 print("⚠️ No se pudo calcular la distancia (status del elemento no OK)")
#         else:
#             print("⚠️ Error en respuesta de la API:", data["status"])

#     except Exception as e:
#         print("❌ Error al conectar con Google Maps:", e)

#     return None, None


def tiempo_entrega(velocidad_kmh, distancia_km):
    horas = distancia_km / velocidad_kmh
    return int(horas * 60)


def codigo_random(n=6):
    codigo = ""
    for i in range(n):
        codigo += str(random.randint(0, 9))
    return codigo

