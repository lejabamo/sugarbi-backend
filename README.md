# 🍃 SugarBI - Sistema de Business Intelligence para Cosecha de Caña

[![Python](https://img.shields.io/badge/Python-3.13-blue.svg)](https://python.org)
[![Flask](https://img.shields.io/badge/Flask-3.1.2-green.svg)](https://flask.palletsprojects.com/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0-orange.svg)](https://mysql.com)
[![License](https://img.shields.io/badge/License-MIT-yellow.svg)](LICENSE)

## 🎯 Descripción

**SugarBI** es un sistema de Business Intelligence especializado en el análisis de datos de cosecha de caña de azúcar. Combina procesamiento de lenguaje natural, visualizaciones dinámicas y un data mart optimizado para proporcionar insights inteligentes sobre la producción agrícola.

## ✨ Características Principales

- 🤖 **Chatbot Inteligente**: Consultas en lenguaje natural
- 📊 **Visualizaciones Dinámicas**: Gráficos interactivos automáticos
- 🗄️ **Data Mart Dimensional**: Modelo estrella optimizado
- 🌐 **Dashboard Integrado**: Interfaz unificada (25% chatbot - 75% visualizaciones)
- 📱 **Responsive Design**: Compatible con dispositivos móviles
- 🔄 **API REST**: Endpoints para integración externa

## 🚀 Demo en Vivo

### Dashboard Integrado
Accede al dashboard principal con chatbot integrado:
**http://localhost:5001/dashboard-alternativo**

### Análisis OLAP
Accede al dashboard de análisis multidimensional:
**http://localhost:5001/olap**

### Otras Interfaces
- **Chatbot**: http://localhost:5001/chatbot
- **Dashboard**: http://localhost:5001/dashboard
- **API**: http://localhost:5001/api/

## 🛠️ Tecnologías

### Backend
- **Python 3.13** - Lenguaje principal
- **Flask 3.1.2** - Framework web
- **SQLAlchemy 2.0.43** - ORM
- **Pandas 2.3.2** - Manipulación de datos
- **PyMySQL 1.1.2** - Conector MySQL

### Frontend
- **HTML5/CSS3/JavaScript** - Interfaz web
- **Bootstrap 5.3.0** - Framework CSS
- **Chart.js** - Visualizaciones
- **Font Awesome** - Iconografía

### Base de Datos
- **MySQL 8.0** - Sistema de gestión
- **Data Mart Dimensional** - Modelo estrella

## 📦 Instalación Rápida

### 1. Clonar Repositorio
```bash
git clone <repository-url>
cd SugarBI
```

### 2. Crear Entorno Virtual
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

### 3. Instalar Dependencias
```bash
pip install -r requirements.txt
```

### 4. Configurar Base de Datos
Editar `config/config.ini`:
```ini
[mysql]
host = localhost
port = 3306
user = tu_usuario
password = tu_password
database = sugarbi_db
```

### 5. Inicializar Base de Datos
```bash
python etls/crear_tablas.py
python etls/cargar_datos.py
```

### 6. Ejecutar Aplicación
```bash
python web/app.py
```

## 🎮 Ejemplos de Uso

### Consultas del Chatbot

#### Rankings
```
"muestra el top 10 de fincas por producción"
"mejores 5 variedades por TCH"
"primeros 8 zonas por rendimiento"
```

#### Estadísticas
```
"¿cuál es el promedio de brix por finca?"
"muestra la suma total de toneladas en 2025"
"¿cuántas fincas hay en total?"
```

#### Tendencias
```
"muestra la tendencia de producción por mes en 2025"
"evolución del TCH por año"
"progresión de brix por trimestre"
```

### API REST

#### Consulta del Chatbot
```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "top 5 fincas por producción"}'
```

#### Estadísticas del Sistema
```bash
curl http://localhost:5001/api/estadisticas
```

### Análisis OLAP

#### Consulta OLAP
```bash
curl -X POST http://localhost:5001/api/olap/query \
  -H "Content-Type: application/json" \
  -d '{
    "operation": "drill_down",
    "measures": ["toneladas"],
    "dimensions": ["tiempo"],
    "dimension_levels": {"tiempo": "year"},
    "aggregation_functions": ["sum"]
  }'
```

#### Dimensiones y Medidas Disponibles
```bash
curl http://localhost:5001/api/olap/dimensions
curl http://localhost:5001/api/olap/measures
```

## 📊 Estructura del Proyecto

```
SugarBI/
├── api/                    # API REST endpoints
├── chatbot/               # Motor de chatbot
│   ├── query_parser.py    # Parser de lenguaje natural
│   └── sql_generator.py   # Generador de consultas SQL
├── dashboard/             # Motor de visualizaciones
├── etls/                  # Scripts ETL
├── web/                   # Interfaz web
│   ├── app.py             # Aplicación principal
│   └── templates/         # Plantillas HTML
├── config/                # Configuración
├── raw_data/              # Datos fuente
└── requirements.txt       # Dependencias
```

## 🗄️ Modelo de Datos

### Esquema Dimensional (Star Schema)

- **Tabla de Hechos**: `hechos_cosecha` (métricas de producción)
- **Dimensiones**:
  - `dimfinca` - Información de fincas
  - `dimvariedad` - Tipos de caña
  - `dimzona` - Zonas geográficas
  - `dimtiempo` - Dimensiones temporales

## 🌐 Endpoints de la API

| Método | Endpoint | Descripción |
|--------|----------|-------------|
| `POST` | `/api/chat` | Procesar consulta del chatbot |
| `POST` | `/api/query/parse` | Solo parsear consulta |
| `POST` | `/api/visualization/create` | Crear visualización |
| `GET` | `/api/estadisticas` | Estadísticas del sistema |
| `GET` | `/api/examples` | Ejemplos de consultas |
| `POST` | `/api/olap/query` | Ejecutar consulta OLAP |
| `GET` | `/api/olap/dimensions` | Dimensiones disponibles |
| `GET` | `/api/olap/measures` | Medidas disponibles |
| `GET` | `/api/olap/examples` | Ejemplos de consultas OLAP |

## 🎨 Interfaces Disponibles

### 1. Dashboard Integrado (Recomendado)
- **URL**: `/dashboard-alternativo`
- **Layout**: 25% chatbot - 75% visualizaciones
- **Características**: Interfaz unificada, análisis en tiempo real

### 2. Análisis OLAP
- **URL**: `/olap`
- **Características**: Análisis multidimensional, operaciones drill-down/roll-up

### 3. Chatbot Independiente
- **URL**: `/chatbot`
- **Características**: Chat dedicado, análisis de consultas

### 4. Dashboard Tradicional
- **URL**: `/dashboard`
- **Características**: Visualizaciones estáticas, estadísticas generales

## 🧪 Pruebas

### Ejecutar Pruebas del Chatbot
```bash
python chatbot/test_simple.py
```

### Pruebas Manuales
1. Acceder a http://localhost:5001/dashboard-alternativo
2. Probar consultas en el chatbot
3. Verificar visualizaciones
4. Comprobar exportación de datos

## 📈 Características Avanzadas

- **Procesamiento de Lenguaje Natural**: Entiende consultas en español
- **Generación Automática de SQL**: Convierte consultas a SQL optimizado
- **Visualizaciones Inteligentes**: Selecciona el tipo de gráfico apropiado
- **Exportación de Datos**: Descarga resultados en CSV
- **Diseño Responsivo**: Funciona en desktop y móvil

## 🔧 Configuración

### Variables de Entorno
```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
```

### Configuración de Producción
- Configurar servidor web (Nginx, Apache)
- Usar WSGI server (Gunicorn, uWSGI)
- Configurar HTTPS
- Implementar autenticación

## 📚 Documentación

- **[Documentación Técnica Completa](DOCUMENTACION_TECNICA.md)**
- **[Guía de API](docs/API.md)**
- **[Guía de Despliegue](docs/DEPLOYMENT.md)**

## 🤝 Contribución

1. Fork del repositorio
2. Crear rama de feature (`git checkout -b feature/nueva-funcionalidad`)
3. Commit cambios (`git commit -am 'Agregar nueva funcionalidad'`)
4. Push a la rama (`git push origin feature/nueva-funcionalidad`)
5. Crear Pull Request

## 📞 Soporte

- **Issues**: [GitHub Issues](https://github.com/tu-usuario/SugarBI/issues)
- **Documentación**: [Wiki del Proyecto](https://github.com/tu-usuario/SugarBI/wiki)
- **Email**: soporte@sugarbi.com

## 📄 Licencia

Este proyecto está bajo la Licencia MIT. Ver el archivo [LICENSE](LICENSE) para más detalles.

## 🙏 Agradecimientos

- Universidad del Valle
- Equipo de desarrollo SugarBI
- Comunidad de código abierto
ud
---

**Desarrollado con ❤️ para el análisis inteligente de datos agrícolas**

[![Made with Python](https://img.shields.io/badge/Made%20with-Python-blue.svg)](https://python.org)
[![Powered by Flask](https://img.shields.io/badge/Powered%20by-Flask-green.svg)](https://flask.palletsprojects.com/)
