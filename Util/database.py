import logging
import psycopg2
from typing import Optional
from datetime import datetime
from sqlmodel import SQLModel, create_engine, Session, Field

DATABASE_URL = "postgresql+psycopg2://valentinsilva:22012005@localhost:5432/obligatorioalgoritmos"

engine = create_engine(DATABASE_URL, echo=True)

logger = logging.getLogger("database")


class Categoria(SQLModel, table=True):
    __tablename__ = "categoria"
    idcategoria: int = Field(autoincrement=True, primary_key=True)
    nombre: str


class Producto(SQLModel, table=True):
    __tablename__ = "producto"
    idproducto: int = Field(autoincrement=True, primary_key=True)
    nombre: str
    precio: float
    tiempodeelaboracion: int
    id_categoria: int = Field(foreign_key="categoria.idcategoria")


class Pedido(SQLModel, table=True):
    __tablename__ = "pedido"
    idpedido: int = Field(autoincrement=True, primary_key=True)
    id_chat: int = Field(foreign_key="chat.idchat")
    id_cliente: int = Field(foreign_key="cliente.idcliente")
    id_repartidor: int = Field(foreign_key="repartidor.idrepartidor")
    direccion: str
    latitud: Optional[str] = None
    longitud: Optional[str] = None
    estado: str


class DetallePedido(SQLModel, table=True):
    __tablename__ = "detalle_pedido"
    id_pedido: int = Field(foreign_key="pedido.idpedido")
    id_producto: int = Field(foreign_key="producto.idproducto")
    cantidad: int

class Repartidor(SQLModel, table=True):
    __tablename__ = "repartidor"
    idrepartidor: int = Field(autoincrement=True, primary_key=True)
    nombre: str
    telefono: str
    cantidadkmrecorridos: float
    zonaasignada: str

class Ingrediente(SQLModel, table=True):
    __tablename__ = "ingrediente"
    idingrediente: int = Field(autoincrement=True, primary_key=True)
    nombre: str
    costo: float

class IngredienteProducto(SQLModel, table=True):
    __tablename__ = "ingrediente_producto"
    id_ingrediente: int = Field(foreign_key="ingrediente.idingrediente")
    id_producto: int = Field(foreign_key="producto.idproducto")
    cantidad: int

class Cliente(SQLModel, table=True):
    __tablename__ = "cliente"
    idcliente: int = Field(autoincrement=True, primary_key=True)
    nombre: str
    telefono: str

class Chat(SQLModel, table=True):
    __tablename__ = "chat"
    idchat: int = Field(autoincrement=True, primary_key=True)
    id_cliente: int = Field(foreign_key="cliente.idcliente")
    id_repartidor: int = Field(foreign_key="repartidor.idrepartidor")

class Mensaje(SQLModel, table=True):
    __tablename__ = "mensaje"
    idmensaje: int = Field(autoincrement=True, primary_key=True)
    id_chat: int = Field(foreign_key="chat.idchat")
    contenido: str

def get_db_session():
    try:
        return Session(engine)
    except Exception as e:
        logger.error("No se pudo obtener la sesión de base de datos", exc_info=True)
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
        logger.error("Error obteniendo conexión a la base de datos", exc_info=True)
        raise

