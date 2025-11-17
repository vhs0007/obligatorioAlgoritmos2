# ⚙️ Configuración de Base de Datos en Render

## 🔧 Paso 1: Configurar Variable de Entorno

1. Ve a tu **servicio web** en Render (el que ejecuta `webhook_server.py`)
2. Haz clic en **"Environment"** en el menú lateral
3. Haz clic en **"Add Environment Variable"**
4. Agrega:
   - **Key**: `DATABASE_URL`
   - **Value**: `postgresql://obligatorio_algoritmos_user:pvwpiXeC6K1fNySL02rz2Np2uC4J2hYJ@dpg-d4d78t75r7bs73aqanlg-a/obligatorio_algoritmos`
5. Haz clic en **"Save Changes"**
6. Render reiniciará automáticamente tu servicio

## 🗄️ Paso 2: Inicializar Tablas

Después de configurar la variable de entorno, necesitas crear las tablas. Tienes 3 opciones:

### Opción A: Usar el Script de Inicialización (Recomendado)

1. En Render, ve a tu servicio web
2. Ve a **"Shell"** (en el menú lateral)
3. Ejecuta:
   ```bash
   python init_database.py
   ```

### Opción B: Ejecutar desde el Código

Agrega esto temporalmente a `webhook_server.py` al inicio (solo la primera vez):

```python
# Al inicio del archivo, después de los imports
from Util.database import init_db
init_db()  # Solo ejecutar una vez
```

Luego elimina estas líneas después de que las tablas se creen.

### Opción C: Ejecutar Manualmente desde Python

En el Shell de Render:
```python
python -c "from Util.database import init_db; init_db()"
```

## ✅ Verificar que Funciona

1. Revisa los **logs** de tu servicio en Render
2. Deberías ver mensajes como:
   - `✅ Conexión a la base de datos exitosa`
   - `✅ Tablas creadas correctamente`
3. Si ves errores, verifica:
   - Que la variable `DATABASE_URL` esté configurada correctamente
   - Que la base de datos esté en estado "Available" (no pausada)

## 📝 Nota sobre la URL

La URL que proporcionaste parece estar incompleta (falta el puerto). Si tienes problemas de conexión, prueba agregar `:5432` antes de `/obligatorio_algoritmos`:

```
postgresql://obligatorio_algoritmos_user:pvwpiXeC6K1fNySL02rz2Np2uC4J2hYJ@dpg-d4d78t75r7bs73aqanlg-a:5432/obligatorio_algoritmos
```

Pero primero prueba con la URL original, ya que Render a veces maneja el puerto automáticamente.

## 🚀 Después de Configurar

Una vez que las tablas estén creadas, tu bot debería funcionar correctamente. Puedes probar enviando un mensaje a través de WhatsApp.

