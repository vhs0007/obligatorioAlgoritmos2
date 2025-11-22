from whatsapp_api import enviar_mensaje_whatsapp
from Util.database import get_db_connection, Calificacion, UsuarioCalificacion
from sqlmodel import Session, select
from Util.database import get_db_session

def enviar_solicitud_calificacion(numero_cliente):
   
    payload = {
        "messaging_product": "whatsapp",
        "to": numero_cliente,
        "type": "interactive",
        "interactive": {
            "type": "button",
            "body": {
                "text": "¿Cómo calificarías nuestro servicio? ⭐"
            },
            "action": {
                "buttons": [
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"calificar_1",
                            "title": "⭐ 1"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"calificar_2",
                            "title": "⭐⭐ 2"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"calificar_3",
                            "title": "⭐⭐⭐ 3"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"calificar_4",
                            "title": "⭐⭐⭐⭐ 4"
                        }
                    },
                    {
                        "type": "reply",
                        "reply": {
                            "id": f"calificar_5",
                            "title": "⭐⭐⭐⭐⭐ 5"
                        }
                    }
                ]
            }
        }
    }
    
    return enviar_mensaje_whatsapp(numero_cliente, payload)


def manejar_calificacion(numero, calificacion_id):
    try:
        partes = calificacion_id.split("_")
        if len(partes) < 3:
            return enviar_mensaje_whatsapp(numero, "Error al procesar la calificación. Por favor, intenta nuevamente.")
        
        estrellas = int(partes[1])  
        
        if estrellas < 1 or estrellas > 5:
            return enviar_mensaje_whatsapp(numero, "Calificación inválida. Por favor, selecciona entre 1 y 5 estrellas.")
        
        conn = get_db_connection()
        cur = conn.cursor()
        
        cur.execute("SELECT id_cliente FROM cliente WHERE telefono = %s", (numero,))
        cliente_info = cur.fetchone()
        
        id_cliente = cliente_info[0]  
        cur.close()
        conn.close()
        
        db = get_db_session()
        try:
            calificacion = Calificacion(
                estrellas=estrellas
            )
            db.add(calificacion)
            db.commit()
            db.refresh(calificacion)
            
            usuario_calificacion = UsuarioCalificacion(
                id_calificacion=calificacion.id_calificacion,
                id_cliente=id_cliente
            )
            db.add(usuario_calificacion)
            db.commit()
            
            print(f"Calificación guardada: {estrellas} estrellas para cliente {id_cliente}")
            
            mensaje_agradecimiento = f"Gracias por tu calificación de {estrellas} {'⭐' * estrellas} gordo comilon! Tu opinión me importa... Te juro!"
            return enviar_mensaje_whatsapp(numero, mensaje_agradecimiento)
            
        except Exception as e:
            db.rollback()
            print(f"Error al guardar calificación: {e}")
            return enviar_mensaje_whatsapp(numero, "Hubo un error al guardar tu calificación. Por favor, intenta nuevamente.")
        finally:
            db.close()
            
    except Exception as e:
        print(f"Error inesperado en manejar_calificacion: {e}")
        return enviar_mensaje_whatsapp(numero, "Hubo un error inesperado. Por favor, intenta nuevamente.")

