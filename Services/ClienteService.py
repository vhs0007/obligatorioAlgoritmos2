from Util.database import get_db_session, Cliente

class ClienteService:
    def __init__(self, db_session=None):
        self.db = db_session or get_db_session()

    def obtener_o_crear_cliente(self, telefono: str, nombre: str = None) -> Cliente:

        cliente = self.db.query(Cliente).filter(Cliente.telefono == telefono).first()
        
        if cliente:
            print(f"Cliente: {cliente.nombre} ({cliente.telefono})")
            return cliente
        
        nombre_cliente = nombre or "Cliente WhatsApp"
        nuevo_cliente = Cliente(
            nombre=nombre_cliente,
            telefono=telefono
        )
        
        self.db.add(nuevo_cliente)
        self.db.commit()
        self.db.refresh(nuevo_cliente)
        
        print(f"Cliente creado: {nuevo_cliente.nombre} ({nuevo_cliente.telefono})")
        return nuevo_cliente
    
    def obtener_cliente_por_telefono(self, telefono: str) -> Cliente:
        """Obtiene un cliente por su número de teléfono."""
        return self.db.query(Cliente).filter(Cliente.telefono == telefono).first()
    
    def actualizar_nombre(self, telefono: str, nombre: str) -> bool:
        """Actualiza el nombre de un cliente."""
        cliente = self.obtener_cliente_por_telefono(telefono)
        if cliente:
            cliente.nombre = nombre
            self.db.commit()
            return True
        return False
