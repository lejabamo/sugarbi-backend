# API SugarBI - Data Mart de Cosecha de Caña

API REST desarrollada con Flask para consumir los datos del data mart de cosecha de caña.

## 🚀 Inicio Rápido

### 1. Instalar dependencias
```bash
pip install -r requirements.txt
```

### 2. Ejecutar la API
```bash
python api/app.py
```

### 3. Acceder a la API
- **URL Base**: http://localhost:5000
- **Documentación**: http://localhost:5000

## 📊 Endpoints Disponibles

### 🏠 Endpoint Principal
- **GET** `/` - Información general de la API

### 📋 Dimensiones
- **GET** `/api/fincas` - Lista todas las fincas
- **GET** `/api/variedades` - Lista todas las variedades
- **GET** `/api/zonas` - Lista todas las zonas
- **GET** `/api/tiempo` - Lista períodos de tiempo

### 📈 Hechos y Estadísticas
- **GET** `/api/cosecha` - Datos de cosecha con filtros opcionales
- **GET** `/api/estadisticas` - Estadísticas generales del data mart
- **GET** `/api/cosecha/top` - Top cosechas por criterio

## 🔍 Parámetros de Consulta

### Filtros para `/api/cosecha`
- `finca_id` - ID de la finca
- `variedad_id` - ID de la variedad
- `zona_id` - ID de la zona
- `año` - Año de cosecha
- `mes` - Mes de cosecha
- `limit` - Número máximo de registros (default: 100)
- `offset` - Número de registros a omitir (default: 0)

### Parámetros para `/api/cosecha/top`
- `criterio` - Criterio de ordenamiento: `toneladas`, `tch`, `brix`, `sacarosa`
- `limit` - Número de registros (default: 10)

## 📝 Ejemplos de Uso

### Obtener todas las fincas
```bash
curl http://localhost:5000/api/fincas
```

### Obtener cosechas del año 2023
```bash
curl "http://localhost:5000/api/cosecha?año=2023&limit=10"
```

### Obtener top 5 cosechas por toneladas
```bash
curl "http://localhost:5000/api/cosecha/top?criterio=toneladas&limit=5"
```

### Obtener estadísticas generales
```bash
curl http://localhost:5000/api/estadisticas
```

## 🧪 Pruebas

Ejecutar las pruebas de la API:
```bash
python api/test_api.py
```

## 📊 Estructura de Respuesta

### Respuesta Exitosa
```json
{
  "success": true,
  "data": [...],
  "total": 100,
  "filters": {...},
  "pagination": {...}
}
```

### Respuesta con Error
```json
{
  "success": false,
  "error": "Mensaje de error"
}
```

## 🔧 Configuración

La API utiliza la configuración de base de datos definida en `config/config.ini`.

### Variables de Entorno
- `DEBUG` - Modo debug (default: True)
- `SECRET_KEY` - Clave secreta de Flask
- `LOG_LEVEL` - Nivel de logging (default: INFO)

## 📈 Características

- ✅ **CORS habilitado** - Para integración con frontend
- ✅ **Validación de parámetros** - Filtros y paginación
- ✅ **Manejo de errores** - Respuestas consistentes
- ✅ **Documentación automática** - Endpoint de información
- ✅ **Filtros avanzados** - Múltiples criterios de búsqueda
- ✅ **Paginación** - Control de límites y offset
- ✅ **Estadísticas** - Métricas del data mart

## 🚀 Próximas Mejoras

- [ ] Autenticación y autorización
- [ ] Cache de consultas
- [ ] Documentación Swagger/OpenAPI
- [ ] Endpoints de agregación
- [ ] Exportación de datos
- [ ] Webhooks para notificaciones

## 📞 Soporte

Para soporte técnico o reportar problemas, contactar al equipo de desarrollo.

