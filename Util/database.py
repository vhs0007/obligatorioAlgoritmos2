import logging
import psycopg2
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, create_engine, Session, Field

DATABASE_URL = "postgresql+psycopg2://postgres:Raboloko18!@localhost:5432/obligatorio_algoritmos"

engine = create_engine(DATABASE_URL, echo=True)

logger = logging.getLogger("database")


# =========================
# Modelos (SQLModel)
# =========================

class Categoria(SQLModel, table=True):
    id_categoria: Optional[int] = Field(default=None, primary_key=True)
    nombre: str


class Producto(SQLModel, table=True):
    idproducto: Optional[int] = Field(default=None, primary_key=True)
    nombre: str
    precio: float
    id_categoria: Optional[int] = Field(default=None, foreign_key="categoria.id_categoria")


class Pedido(SQLModel, table=True):
    idpedido: Optional[int] = Field(default=None, primary_key=True)
    id_chat: str
    id_cliente: str
    id_repartidor: Optional[int] = None
    direccion: str
    latitud: Optional[str] = None
    longitud: Optional[str] = None
    fecha_confirmacion: Optional[datetime] = None


class DetallePedido(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    id_pedido: int = Field(foreign_key="pedido.idpedido")
    id_producto: int = Field(foreign_key="producto.idproducto")
    cantidad: int


# =========================
# Sesiones y conexiones
# =========================

def get_db_session():
    try:
        return Session(engine)
    except Exception as e:
        logger.error("No se pudo obtener la sesión de base de datos", exc_info=True)
        raise

def init_db():
    try:
        SQLModel.metadata.create_all(engine)
        logger.info("Base de datos inicializada correctamente")
    except Exception as e:
        logger.error("Error inicializando la base de datos", exc_info=True)
        raise


def get_db_connection():
    """
    Conexión cruda (psycopg2) para servicios que ejecutan SQL directo.
    """
    try:
        dsn = DATABASE_URL.replace("+psycopg2", "")
        conn = psycopg2.connect(dsn)
        return conn
    except Exception as e:
        logger.error("Error obteniendo conexión cruda a la base de datos", exc_info=True)
        raise

if __name__ == "__main__":
    init_db()
