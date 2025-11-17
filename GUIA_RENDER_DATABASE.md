# 🗄️ Guía: Crear Base de Datos PostgreSQL en Render

## 📋 Paso a Paso

### 1. Acceder al Dashboard de Render

1. Ve a [render.com](https://render.com) e inicia sesión
2. Una vez dentro, verás tu dashboard principal

### 2. Crear Nueva Base de Datos PostgreSQL

1. **Haz clic en el botón "New +"** (arriba a la derecha del dashboard)
2. **Selecciona "PostgreSQL"** de la lista de opciones

### 3. Configurar la Base de Datos

Completa el formulario con:

- **Name**: Un nombre descriptivo (ej: `gordoeats-db`, `obligatorio-algo2-db`)
- **Database**: El nombre de la base de datos (ej: `obligatorio_algoritmos`)
- **User**: El usuario de la base de datos (puedes dejarlo por defecto o personalizarlo)
- **Region**: Selecciona la región más cercana a tus usuarios (ej: `Oregon (US West)` para América)
- **PostgreSQL Version**: Deja la versión más reciente (recomendado)
- **Plan**: 
  - **Free**: Para desarrollo/pruebas (tiene limitaciones)
  - **Starter** ($7/mes): Para producción pequeña
  - **Standard** ($20/mes): Para producción

### 4. Crear la Base de Datos

1. Haz clic en **"Create Database"**
2. Render comenzará a crear tu base de datos (esto toma 1-2 minutos)

### 5. Obtener la URL de Conexión

Una vez creada la base de datos:

1. **Haz clic en el nombre de tu base de datos** en el dashboard
2. En la página de detalles, busca la sección **"Connections"** o **"Internal Database URL"**
3. Verás algo como:
   ```
   postgresql://usuario:password@hostname:5432/database_name
   ```
4. **Copia esta URL completa** - la necesitarás para configurar tu servicio web

### 6. Conectar la Base de Datos a tu Servicio Web

#### Opción A: Conexión Automática (Recomendada)

1. Ve a tu **servicio web** (el que ejecuta `webhook_server.py`)
2. En la configuración del servicio, ve a **"Environment"**
3. Render debería detectar automáticamente tu base de datos PostgreSQL
4. Si aparece en la lista, **haz clic en "Link"** o **"Connect"**
5. Render automáticamente creará la variable de entorno `DATABASE_URL` con la URL correcta

#### Opción B: Conexión Manual

Si la conexión automática no funciona:

1. Ve a tu **servicio web**
2. En la configuración, ve a **"Environment"** → **"Environment Variables"**
3. Haz clic en **"Add Environment Variable"**
4. Agrega:
   - **Key**: `DATABASE_URL`
   - **Value**: Pega la URL que copiaste en el paso 5
5. Haz clic en **"Save Changes"**

### 7. Verificar la Conexión

1. **Reinicia tu servicio web** (Render lo hace automáticamente al guardar variables de entorno)
2. Revisa los logs del servicio para verificar que se conecta correctamente
3. Si ves errores de conexión, verifica que:
   - La URL esté correcta
   - La base de datos esté en estado "Available" (no "Paused")
   - El servicio web tenga acceso a la base de datos

## 🔍 Ubicación de la URL en Render

La URL de conexión puede estar en diferentes lugares según la versión de Render:

### En la página de la base de datos:
- **Pestaña "Info"**: Busca "Internal Database URL" o "Connection String"
- **Pestaña "Connections"**: Muestra las conexiones activas
- **Pestaña "Settings"**: Puede tener información de conexión

### Formato típico de la URL:
```
postgresql://usuario:password@dpg-xxxxx-a.oregon-postgres.render.com:5432/database_name
```

## ⚠️ Notas Importantes

1. **Internal Database URL vs External Database URL**:
   - **Internal**: Usa esta si tu servicio web está en Render (más rápido y seguro)
   - **External**: Solo si necesitas conectarte desde fuera de Render

2. **Seguridad**:
   - La URL contiene credenciales sensibles
   - No la compartas públicamente
   - Render la maneja automáticamente como variable de entorno

3. **Plan Free**:
   - La base de datos se pausa después de 90 días de inactividad
   - Se reactiva automáticamente cuando hay tráfico
   - Puede tardar unos segundos en reactivarse

4. **Inicialización de Tablas**:
   - Después de conectar la base de datos, necesitas crear las tablas
   - Puedes hacerlo ejecutando: `python -c "from Util.database import init_db; init_db()"`
   - O crear un script de inicialización que Render ejecute al iniciar

## 🚀 Script de Inicialización (Opcional)

Puedes crear un script que Render ejecute al iniciar para crear las tablas:

**Archivo: `init_database.py`**
```python
from Util.database import init_db

if __name__ == "__main__":
    print("Inicializando base de datos...")
    init_db()
    print("✅ Base de datos inicializada correctamente")
```

Luego en Render, en la configuración del servicio:
- **Build Command**: `pip install -r requirements.txt && python init_database.py`
- O ejecuta el script manualmente después del primer deploy

## ✅ Checklist

- [ ] Base de datos PostgreSQL creada en Render
- [ ] URL de conexión copiada
- [ ] Base de datos conectada al servicio web (automática o manual)
- [ ] Variable de entorno `DATABASE_URL` configurada
- [ ] Servicio web reiniciado
- [ ] Tablas creadas en la base de datos
- [ ] Conexión verificada en los logs

## 🆘 Solución de Problemas

### Error: "Connection refused"
- Verifica que la base de datos esté en estado "Available"
- Si está pausada, espera unos segundos a que se reactive
- Verifica que la URL sea correcta

### Error: "Database does not exist"
- Verifica que el nombre de la base de datos en la URL coincida
- Crea la base de datos si no existe

### Error: "Authentication failed"
- Verifica que las credenciales en la URL sean correctas
- Si cambiaste la contraseña, actualiza la URL

### La variable DATABASE_URL no aparece
- Agrega manualmente la variable de entorno
- Verifica que el servicio web tenga acceso a la base de datos
- Reinicia el servicio después de agregar la variable

