# SugarBI Backend

Sistema de Business Intelligence para análisis de datos de cosecha de caña de azúcar.

## 🚀 Características

- **API REST**: Endpoints para dashboard, filtros y análisis
- **Filtros Inteligentes**: Sistema de intersecciones con validación
- **Chatbot con LangChain**: Procesamiento de lenguaje natural
- **Motor OLAP**: Análisis multidimensional avanzado
- **Autenticación JWT**: Sistema de roles (Admin, Analista, Consultor)
- **Rate Limiting**: Protección contra abuso de API

## 🛠️ Tecnologías

- **Flask 3.1** con Python 3.11+
- **MySQL** para base de datos
- **SQLAlchemy** para ORM
- **LangChain** para IA
- **Pandas** para procesamiento de datos
- **PyJWT** para autenticación

## 📦 Instalación

### Requisitos Previos
- Python 3.11+
- MySQL 8.0+
- Git

### Instalación
```bash
# Clonar repositorio
git clone <repo-url>
cd SugarBI-backend

# Crear entorno virtual
python -m venv venv

# Activar entorno virtual
# Windows:
venv\Scripts\activate
# Linux/Mac:
source venv/bin/activate

# Instalar dependencias
pip install -r requirements.txt
```

## 🔧 Configuración

### Variables de Entorno
Crear archivo `.env`:

```env
# Base de datos
DB_HOST=localhost
DB_PORT=3306
DB_NAME=sugarbi
DB_USER=root
DB_PASSWORD=toor

# JWT
JWT_SECRET_KEY=your-secret-key-here
JWT_ACCESS_TOKEN_EXPIRES=3600

# OpenAI (para chatbot)
OPENAI_API_KEY=your-openai-api-key

# Rate Limiting
RATELIMIT_STORAGE_URL=memory://
```

### Base de Datos
```bash
# Importar base de datos
mysql -u root -p sugarbi < sugarbi_database_export.sql
```

## 🚀 Ejecución

### Desarrollo
```bash
# Activar entorno virtual
venv\Scripts\activate  # Windows
# source venv/bin/activate  # Linux/Mac

# Ejecutar servidor
python web/app.py
```

### Producción
```bash
# Con Gunicorn
gunicorn -w 4 -b 0.0.0.0:5001 web.app:app

# Con uWSGI
uwsgi --http :5001 --module web.app:app --processes 4 --threads 2
```

## 📊 Estructura del Proyecto

```
SugarBI-backend/
├── web/
│   ├── app.py              # Aplicación principal Flask
│   └── templates/          # Templates HTML
├── auth/
│   ├── models.py          # Modelos de usuario
│   ├── routes.py          # Rutas de autenticación
│   └── security.py        # Configuración de seguridad
├── dashboard/
│   └── powerbi_integration.py  # Integración PowerBI
├── filter_intersections.py     # Lógica de filtros inteligentes
├── filter_parser.py           # Parser de filtros
├── requirements.txt           # Dependencias Python
├── sugarbi_database_export.sql # Export de base de datos
└── config.ini                # Configuración de base de datos
```

## 🔗 Endpoints API

### Autenticación
- `POST /api/auth/login` - Iniciar sesión
- `POST /api/auth/logout` - Cerrar sesión
- `GET /api/auth/me` - Información del usuario

### Dashboard
- `GET /api/estadisticas` - Estadísticas globales
- `GET /api/cosecha/top` - Top cosechas
- `GET /api/cosecha-filtered` - Datos filtrados

### Filtros Inteligentes
- `GET /api/filter-options` - Opciones de filtros
- `POST /api/filter-intersections` - Intersecciones de filtros

### Chatbot
- `POST /api/chat/query` - Consulta de chatbot
- `GET /api/chat/examples` - Ejemplos de consultas

### OLAP
- `GET /api/olap/dimensions` - Dimensiones disponibles
- `GET /api/olap/measures` - Medidas disponibles
- `POST /api/olap/query` - Ejecutar consulta OLAP

## 🔐 Autenticación y Roles

### Roles Disponibles
- **Admin**: Acceso completo a todas las funcionalidades
- **Analista**: Dashboard, Chatbot, OLAP completo
- **Consultor**: Dashboard y Chatbot solo lectura

### Uso de JWT
```python
# Headers requeridos
Authorization: Bearer <jwt_token>
```

## 📊 Base de Datos

### Tablas Principales
- `dimfinca` - Dimensiones de fincas
- `dimvariedad` - Variedades de caña
- `dimzona` - Zonas geográficas
- `dimtiempo` - Dimensiones temporales
- `hechos_cosecha` - Hechos de producción

### Importar Datos
```bash
# Restaurar desde export
mysql -u root -p sugarbi < sugarbi_database_export.sql

# Verificar datos
mysql -u root -p -e "USE sugarbi; SELECT COUNT(*) FROM hechos_cosecha;"
```

## 🐛 Troubleshooting

### Problemas Comunes

1. **Error de conexión a BD**: Verificar credenciales en `config.ini`
2. **Error 500 en OLAP**: Verificar permisos de usuario
3. **Rate limiting**: Ajustar límites en `auth/security.py`
4. **Chatbot no responde**: Verificar `OPENAI_API_KEY`

### Logs
```bash
# Habilitar logs detallados
export FLASK_DEBUG=1
python web/app.py
```

## 🚀 Deployment

### Docker (Recomendado)
```dockerfile
FROM python:3.11-slim

WORKDIR /app
COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .
EXPOSE 5001

CMD ["gunicorn", "-w", "4", "-b", "0.0.0.0:5001", "web.app:app"]
```

### Variables de Entorno de Producción
```env
FLASK_ENV=production
DB_HOST=your-db-host
DB_PASSWORD=your-secure-password
JWT_SECRET_KEY=your-production-secret
OPENAI_API_KEY=your-openai-key
```

## 📝 Scripts Útiles

```bash
# Backup de base de datos
mysqldump -u root -p sugarbi > backup_$(date +%Y%m%d).sql

# Verificar estado de la API
curl http://localhost:5001/api/health

# Test de autenticación
curl -X POST http://localhost:5001/api/auth/login \
  -H "Content-Type: application/json" \
  -d '{"username":"admin","password":"admin123"}'
```