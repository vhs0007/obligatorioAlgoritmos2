"""
Script para inicializar las tablas en la base de datos.
Ejecutar después de conectar la base de datos en Render.
"""
from Util.database import init_db, get_db_connection
import logging

logging.basicConfig(level=logging.INFO)

def main():
    """Inicializa todas las tablas en la base de datos."""
    try:
        print("🔄 Inicializando base de datos...")
        
        # Verificar conexión primero
        conn = get_db_connection()
        conn.close()
        print("✅ Conexión a la base de datos exitosa")
        
        # Crear tablas
        init_db()
        print("✅ Tablas creadas correctamente")
        print("\n📋 Tablas creadas:")
        print("  - categoria")
        print("  - producto")
        print("  - cliente")
        print("  - repartidor")
        print("  - chat")
        print("  - mensaje")
        print("  - pedido")
        print("  - detalle_pedido")
        
    except Exception as e:
        print(f"❌ Error al inicializar la base de datos: {e}")
        import traceback
        traceback.print_exc()
        raise

if __name__ == "__main__":
    main()

