# 📊 SugarBI - Documentación Técnica

## 🎯 Descripción General

**SugarBI** es un sistema de Business Intelligence especializado en el análisis de datos de cosecha de caña de azúcar. Combina procesamiento de lenguaje natural, visualizaciones dinámicas y un data mart optimizado para proporcionar insights inteligentes sobre la producción agrícola.

## 🏗️ Arquitectura del Sistema

```
┌─────────────────┐    ┌─────────────────┐    ┌─────────────────┐
│   Frontend      │    │   Backend       │    │   Database      │
│   (Web UI)      │◄──►│   (Flask API)   │◄──►│   (MySQL)       │
│                 │    │                 │    │                 │
│ • Dashboard     │    │ • Chatbot       │    │ • Data Mart     │
│ • Chatbot       │    │ • SQL Generator │    │ • Dimensional   │
│ • Visualizations│    │ • Viz Engine    │    │ • Star Schema   │
└─────────────────┘    └─────────────────┘    └─────────────────┘
```

## 🛠️ Tecnologías Utilizadas

### Backend
- **Python 3.13**: Lenguaje principal
- **Flask 3.1.2**: Framework web
- **Flask-CORS 6.0.1**: Manejo de CORS
- **SQLAlchemy 2.0.43**: ORM para base de datos
- **PyMySQL 1.1.2**: Conector MySQL
- **Pandas 2.3.2**: Manipulación de datos
- **NumPy 2.3.2**: Cálculos numéricos

### Frontend
- **HTML5**: Estructura
- **CSS3**: Estilos y diseño responsivo
- **JavaScript (ES6+)**: Interactividad
- **Bootstrap 5.3.0**: Framework CSS
- **Chart.js**: Visualizaciones
- **Font Awesome 6.0.0**: Iconografía

### Base de Datos
- **MySQL**: Sistema de gestión de base de datos
- **Data Mart Dimensional**: Modelo estrella optimizado

### Herramientas de Desarrollo
- **Git**: Control de versiones
- **Virtual Environment**: Aislamiento de dependencias
- **ConfigParser**: Gestión de configuración

## 📁 Estructura del Proyecto

```
SugarBI/
├── api/                    # API REST endpoints
│   ├── app.py             # Aplicación principal Flask
│   ├── config.py          # Configuración de la aplicación
│   ├── utils.py           # Utilidades generales
│   └── test_api.py        # Pruebas de la API
├── chatbot/               # Motor de chatbot
│   ├── query_parser.py    # Parser de lenguaje natural
│   ├── sql_generator.py   # Generador de consultas SQL
│   └── test_simple.py     # Pruebas del chatbot
├── dashboard/             # Motor de visualizaciones
│   └── visualization_engine.py
├── etls/                  # Scripts ETL
│   ├── cargar_datos.py    # Carga de datos
│   ├── crear_tablas.py    # Creación de tablas
│   └── verificar_*.py     # Scripts de verificación
├── web/                   # Interfaz web
│   ├── app.py             # Aplicación web principal
│   ├── templates/         # Plantillas HTML
│   │   ├── base.html
│   │   ├── index.html
│   │   ├── chatbot.html
│   │   ├── dashboard.html
│   │   └── dashboard_alternativo.html
│   └── static/            # Archivos estáticos
├── config/                # Configuración
│   └── config.ini         # Configuración de BD
├── raw_data/              # Datos fuente
│   ├── *.xlsx             # Archivos Excel
│   └── *.XLS              # Archivos de lluvias
├── requirements.txt       # Dependencias Python
└── venv/                  # Entorno virtual
```

## 🌐 Endpoints de la API

### Endpoints Principales

#### 1. **GET /** - Página Principal
- **Descripción**: Dashboard principal con estadísticas del sistema
- **Respuesta**: HTML con estadísticas generales y ejemplos de consultas

#### 2. **GET /chatbot** - Interfaz del Chatbot
- **Descripción**: Página dedicada al chatbot
- **Respuesta**: HTML con interfaz de chat

#### 3. **GET /dashboard** - Dashboard Tradicional
- **Descripción**: Dashboard con visualizaciones estáticas
- **Respuesta**: HTML con gráficos predefinidos

#### 4. **GET /dashboard-alternativo** - Dashboard Integrado
- **Descripción**: Dashboard con chatbot integrado (25% - 75%)
- **Respuesta**: HTML con interfaz unificada

#### 5. **GET /olap** - Dashboard OLAP
- **Descripción**: Interfaz para análisis multidimensional OLAP
- **Respuesta**: HTML con herramientas de análisis OLAP

### Endpoints de la API REST

#### 1. **POST /api/chat** - Procesar Consulta del Chatbot
```http
POST /api/chat
Content-Type: application/json

{
    "query": "muestra el top 10 de fincas por producción"
}
```

**Respuesta Exitosa (200)**:
```json
{
    "success": true,
    "data": {
        "query": "muestra el top 10 de fincas por producción",
        "intent": {
            "type": "top_ranking",
            "metric": "toneladas",
            "dimension": "finca",
            "filters": {},
            "limit": 10
        },
        "sql": "SELECT f.nombre_finca, SUM(h.toneladas_cana_molida)...",
        "visualization": {
            "type": "bar",
            "data": {...}
        },
        "raw_data": [...],
        "record_count": 10
    }
}
```

**Respuesta de Error (400/500)**:
```json
{
    "success": false,
    "error": "Descripción del error"
}
```

#### 2. **POST /api/query/parse** - Solo Parsear Consulta
```http
POST /api/query/parse
Content-Type: application/json

{
    "query": "mejores variedades por TCH"
}
```

**Respuesta**:
```json
{
    "success": true,
    "data": {
        "query": "mejores variedades por TCH",
        "intent": {
            "type": "top_ranking",
            "metric": "tch",
            "dimension": "variedad",
            "filters": {},
            "limit": null,
            "time_period": null
        },
        "sql": "SELECT v.nombre_variedad, SUM(h.tch)..."
    }
}
```

#### 3. **POST /api/visualization/create** - Crear Visualización
```http
POST /api/visualization/create
Content-Type: application/json

{
    "chart_type": "bar",
    "title": "Producción por Finca",
    "x_axis": "nombre_finca",
    "y_axis": "total_toneladas",
    "data": [...]
}
```

#### 4. **GET /api/estadisticas** - Estadísticas del Sistema
```http
GET /api/estadisticas
```

**Respuesta**:
```json
{
    "success": true,
    "data": {
        "total_hechos_cosecha": 1250,
        "total_dimfinca": 45,
        "total_dimvariedad": 12,
        "total_dimzona": 8,
        "total_toneladas": 1250000.5,
        "promedio_tch": 85.2,
        "promedio_brix": 18.5,
        "año_inicio": 2014,
        "año_fin": 2025
    }
}
```

#### 5. **GET /api/examples** - Ejemplos de Consultas
```http
GET /api/examples
```

**Respuesta**:
```json
{
    "success": true,
    "data": {
        "examples": [
            "muestra la cantidad en toneladas de caña producida del top 10 de las fincas en el 2025",
            "¿cuáles son las 5 mejores variedades por TCH?",
            "muestra la producción por zona en 2024",
            "¿cuál es el promedio de brix por finca?",
            "muestra la tendencia de producción por mes en 2025"
        ]
    }
}
```

### Endpoints OLAP (Análisis Multidimensional)

#### 6. **POST /api/olap/query** - Ejecutar Consulta OLAP
```http
POST /api/olap/query
Content-Type: application/json

{
    "operation": "drill_down",
    "measures": ["toneladas", "tch"],
    "dimensions": ["tiempo", "geografia"],
    "dimension_levels": {
        "tiempo": "year",
        "geografia": "zone"
    },
    "filters": {"año": 2025},
    "aggregation_functions": ["sum", "avg"],
    "limit": 10
}
```

**Respuesta**:
```json
{
    "success": true,
    "data": {
        "operation": "drill_down",
        "records": [
            {
                "tiempo_year": 2025,
                "geografia_zone": "Zona Norte",
                "toneladas_sum": 15000.5,
                "toneladas_avg": 1250.04,
                "tch_sum": 1200.3,
                "tch_avg": 100.02
            }
        ],
        "metadata": {
            "operation": "drill_down",
            "dimensions": ["tiempo", "geografia"],
            "measures": ["toneladas", "tch"],
            "record_count": 1
        },
        "sql_query": "SELECT t.año as tiempo_year, z.nombre_zona as geografia_zone...",
        "execution_time": 0.045,
        "record_count": 1
    }
}
```

#### 7. **GET /api/olap/dimensions** - Dimensiones Disponibles
```http
GET /api/olap/dimensions
```

**Respuesta**:
```json
{
    "success": true,
    "data": {
        "dimensions": ["tiempo", "geografia", "producto"],
        "dimension_levels": {
            "tiempo": ["year", "quarter", "month", "date"],
            "geografia": ["zone", "farm"],
            "producto": ["variety"]
        }
    }
}
```

#### 8. **GET /api/olap/measures** - Medidas Disponibles
```http
GET /api/olap/measures
```

**Respuesta**:
```json
{
    "success": true,
    "data": {
        "measures": ["toneladas", "tch", "brix", "sacarosa", "area", "rendimiento"],
        "aggregation_functions": ["sum", "avg", "count", "min", "max", "std"]
    }
}
```

#### 9. **GET /api/olap/examples** - Ejemplos de Consultas OLAP
```http
GET /api/olap/examples
```

**Respuesta**:
```json
{
    "success": true,
    "data": {
        "examples": [
            {
                "name": "Drill-down por tiempo",
                "description": "Ver producción por año, luego por trimestre, luego por mes",
                "operation": "drill_down",
                "measures": ["toneladas"],
                "dimensions": ["tiempo"],
                "dimension_levels": {"tiempo": "year"},
                "aggregation_functions": ["sum"]
            }
        ]
    }
}
```

## 🗄️ Modelo de Base de Datos

### Esquema Dimensional (Star Schema)

#### Tabla de Hechos: `hechos_cosecha`
```sql
CREATE TABLE hechos_cosecha (
    id INT PRIMARY KEY AUTO_INCREMENT,
    id_finca INT,
    codigo_variedad VARCHAR(10),
    codigo_zona VARCHAR(10),
    codigo_tiempo INT,
    toneladas_cana_molida DECIMAL(10,2),
    tch DECIMAL(8,2),
    brix DECIMAL(5,2),
    sacarosa DECIMAL(5,2),
    area_cosechada DECIMAL(8,2),
    rendimiento_teorico DECIMAL(8,2),
    FOREIGN KEY (id_finca) REFERENCES dimfinca(finca_id),
    FOREIGN KEY (codigo_variedad) REFERENCES dimvariedad(variedad_id),
    FOREIGN KEY (codigo_zona) REFERENCES dimzona(codigo_zona),
    FOREIGN KEY (codigo_tiempo) REFERENCES dimtiempo(tiempo_id)
);
```

#### Dimensiones

**1. Dimensión Finca (`dimfinca`)**
```sql
CREATE TABLE dimfinca (
    finca_id INT PRIMARY KEY,
    nombre_finca VARCHAR(100),
    codigo_finca VARCHAR(20),
    ubicacion VARCHAR(200),
    area_total DECIMAL(10,2)
);
```

**2. Dimensión Variedad (`dimvariedad`)**
```sql
CREATE TABLE dimvariedad (
    variedad_id VARCHAR(10) PRIMARY KEY,
    nombre_variedad VARCHAR(100),
    tipo_caña VARCHAR(50),
    ciclo_cultivo INT,
    resistencia_enfermedades VARCHAR(100)
);
```

**3. Dimensión Zona (`dimzona`)**
```sql
CREATE TABLE dimzona (
    codigo_zona VARCHAR(10) PRIMARY KEY,
    nombre_zona VARCHAR(100),
    region VARCHAR(50),
    altitud DECIMAL(8,2),
    clima VARCHAR(50)
);
```

**4. Dimensión Tiempo (`dimtiempo`)**
```sql
CREATE TABLE dimtiempo (
    tiempo_id INT PRIMARY KEY,
    año INT,
    mes INT,
    nombre_mes VARCHAR(20),
    trimestre INT,
    semestre INT,
    fecha_completa DATE
);
```

## 🤖 Motor de Chatbot

### Componentes Principales

#### 1. **QueryParser** (`chatbot/query_parser.py`)
- **Función**: Convierte lenguaje natural a estructuras de datos
- **Clases**:
  - `QueryType`: Enum para tipos de consulta
  - `MetricType`: Enum para métricas disponibles
  - `DimensionType`: Enum para dimensiones
  - `QueryIntent`: Dataclass para intención parseada
  - `QueryParser`: Parser principal

**Tipos de Consulta Soportados**:
- `TOP_RANKING`: "top 10 fincas"
- `STATISTICS`: "promedio de producción"
- `COMPARISON`: "comparar variedades"
- `TREND`: "tendencia por mes"
- `BASIC`: Consultas simples

**Métricas Disponibles**:
- `TONELADAS`: Producción en toneladas
- `TCH`: Toneladas por hectárea
- `BRIX`: Contenido de azúcar
- `SACAROSA`: Porcentaje de sacarosa
- `AREA`: Área cosechada
- `RENDIMIENTO`: Rendimiento teórico

**Dimensiones Disponibles**:
- `FINCA`: Análisis por finca
- `VARIEDAD`: Análisis por variedad
- `ZONA`: Análisis por zona
- `TIEMPO`: Análisis temporal

#### 2. **SQLGenerator** (`chatbot/sql_generator.py`)
- **Función**: Genera consultas SQL optimizadas
- **Métodos**:
  - `generate_sql()`: Método principal
  - `_generate_top_ranking_sql()`: SQL para rankings
  - `_generate_statistics_sql()`: SQL para estadísticas
  - `_generate_trend_sql()`: SQL para tendencias
  - `_generate_basic_sql()`: SQL básico

## 📊 Motor de Visualizaciones

### VisualizationEngine (`dashboard/visualization_engine.py`)

#### Tipos de Gráficos Soportados
- **Bar Chart**: Gráficos de barras
- **Line Chart**: Gráficos de líneas
- **Pie Chart**: Gráficos de pastel
- **Area Chart**: Gráficos de área
- **Table**: Tablas de datos
- **Scatter Plot**: Gráficos de dispersión

#### Configuración de Gráficos
```python
@dataclass
class ChartConfig:
    chart_type: ChartType
    title: str
    x_axis: str
    y_axis: str
    data: List[Dict[str, Any]]
    colors: Optional[List[str]] = None
    width: int = 800
    height: int = 400
    show_legend: bool = True
    show_grid: bool = True
```

## 🧮 Motor OLAP (Análisis Multidimensional)

### OLAEEngine (`dashboard/olap_engine.py`)

#### Operaciones OLAP Soportadas
- **Drill-Down**: Aumenta el nivel de detalle (año → trimestre → mes)
- **Roll-Up**: Disminuye el nivel de detalle (mes → trimestre → año)
- **Slice**: Filtra una dimensión específica
- **Dice**: Filtra múltiples dimensiones simultáneamente
- **Pivot**: Reorganiza las dimensiones para cambiar perspectiva
- **Aggregate**: Operación básica de agregación

#### Dimensiones y Niveles
```python
class DimensionLevel(Enum):
    # Dimensión Tiempo
    YEAR = "year"
    QUARTER = "quarter"
    MONTH = "month"
    DATE = "date"
    
    # Dimensión Geografía
    ZONE = "zone"
    FARM = "farm"
    
    # Dimensión Producto
    VARIETY = "variety"
```

#### Funciones de Agregación
```python
class AggregationFunction(Enum):
    SUM = "sum"
    AVG = "avg"
    COUNT = "count"
    MIN = "min"
    MAX = "max"
    STD = "std"
```

#### Estructura de Consulta OLAP
```python
@dataclass
class OLAPQuery:
    operation: OLAPOperation
    measures: List[str]
    dimensions: List[str]
    dimension_levels: Dict[str, DimensionLevel]
    filters: Dict[str, Any]
    aggregation_functions: List[AggregationFunction]
    pivot_dimension: Optional[str] = None
    sort_by: Optional[str] = None
    sort_order: str = "desc"
    limit: Optional[int] = None
```

## 🚀 Instalación y Configuración

### Prerrequisitos
- Python 3.13+
- MySQL 8.0+
- Git

### Pasos de Instalación

1. **Clonar el repositorio**:
```bash
git clone <repository-url>
cd SugarBI
```

2. **Crear entorno virtual**:
```bash
python -m venv venv
# Windows
venv\Scripts\activate
# Linux/Mac
source venv/bin/activate
```

3. **Instalar dependencias**:
```bash
pip install -r requirements.txt
```

4. **Configurar base de datos**:
```bash
# Editar config/config.ini
[mysql]
host = localhost
port = 3306
user = tu_usuario
password = tu_password
database = sugarbi_db
```

5. **Crear base de datos y tablas**:
```bash
python etls/crear_tablas.py
python etls/cargar_datos.py
```

6. **Ejecutar la aplicación**:
```bash
python web/app.py
```

### URLs de Acceso
- **Aplicación Principal**: http://localhost:5001
- **Dashboard Integrado**: http://localhost:5001/dashboard-alternativo
- **Chatbot**: http://localhost:5001/chatbot
- **Dashboard Tradicional**: http://localhost:5001/dashboard
- **API REST**: http://localhost:5001/api/

## 📝 Ejemplos de Uso

### Consultas del Chatbot

#### 1. Rankings
```
"muestra el top 10 de fincas por producción"
"mejores 5 variedades por TCH"
"primeros 8 zonas por rendimiento"
```

#### 2. Estadísticas
```
"¿cuál es el promedio de brix por finca?"
"muestra la suma total de toneladas en 2025"
"¿cuántas fincas hay en total?"
```

#### 3. Tendencias
```
"muestra la tendencia de producción por mes en 2025"
"evolución del TCH por año"
"progresión de brix por trimestre"
```

#### 4. Comparaciones
```
"compara la producción entre zonas"
"diferencia entre variedades por TCH"
"contraste de rendimiento por finca"
```

### Uso de la API

#### Ejemplo con cURL
```bash
curl -X POST http://localhost:5001/api/chat \
  -H "Content-Type: application/json" \
  -d '{"query": "top 5 fincas por producción"}'
```

#### Ejemplo con JavaScript
```javascript
const response = await fetch('/api/chat', {
    method: 'POST',
    headers: {
        'Content-Type': 'application/json',
    },
    body: JSON.stringify({
        query: 'muestra la producción por zona en 2025'
    })
});

const result = await response.json();
console.log(result.data.visualization);
```

## 🔧 Configuración Avanzada

### Variables de Entorno
```bash
export FLASK_ENV=development
export FLASK_DEBUG=True
export DATABASE_URL=mysql+pymysql://user:pass@localhost/sugarbi_db
```

### Configuración de Producción
```python
# web/app.py
app.config['DEBUG'] = False
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True
```

## 🧪 Pruebas

### Ejecutar Pruebas del Chatbot
```bash
python chatbot/test_simple.py
```

### Ejecutar Pruebas de la API
```bash
python api/test_api.py
```

### Pruebas Manuales
1. Acceder a http://localhost:5001/dashboard-alternativo
2. Probar consultas en el chatbot
3. Verificar visualizaciones
4. Comprobar exportación de datos

## 📈 Métricas y Monitoreo

### Logs de la Aplicación
- **Debug Mode**: Logs detallados en consola
- **Error Tracking**: Trazabilidad de errores
- **Performance**: Tiempo de respuesta de consultas

### Métricas Disponibles
- Total de registros procesados
- Tiempo promedio de consulta
- Tipos de consultas más frecuentes
- Errores por endpoint

## 🔒 Seguridad

### Medidas Implementadas
- **CORS**: Configurado para desarrollo
- **Input Validation**: Validación de consultas
- **SQL Injection**: Prevención con SQLAlchemy
- **Error Handling**: Manejo seguro de errores

### Recomendaciones para Producción
- Implementar autenticación
- Configurar HTTPS
- Validar inputs más estrictamente
- Implementar rate limiting

## 🚀 Despliegue

### Opciones de Despliegue
1. **Desarrollo Local**: `python web/app.py`
2. **Docker**: Crear Dockerfile
3. **Cloud**: AWS, Azure, GCP
4. **VPS**: Servidor virtual privado

### Requisitos del Servidor
- **CPU**: 2+ cores
- **RAM**: 4GB+ 
- **Storage**: 20GB+
- **Network**: Puerto 5001 abierto

## 📚 Referencias y Recursos

### Documentación de Tecnologías
- [Flask Documentation](https://flask.palletsprojects.com/)
- [SQLAlchemy Documentation](https://docs.sqlalchemy.org/)
- [Chart.js Documentation](https://www.chartjs.org/docs/)
- [Bootstrap Documentation](https://getbootstrap.com/docs/)

### Patrones de Diseño Utilizados
- **MVC**: Model-View-Controller
- **Repository Pattern**: Acceso a datos
- **Factory Pattern**: Creación de visualizaciones
- **Strategy Pattern**: Diferentes tipos de consultas

## 🤝 Contribución

### Cómo Contribuir
1. Fork del repositorio
2. Crear rama de feature
3. Implementar cambios
4. Ejecutar pruebas
5. Crear Pull Request

### Estándares de Código
- **PEP 8**: Estilo de código Python
- **Docstrings**: Documentación de funciones
- **Type Hints**: Tipado estático
- **Testing**: Cobertura de pruebas

## 📞 Soporte

### Contacto
- **Email**: soporte@sugarbi.com
- **Documentación**: Este archivo
- **Issues**: GitHub Issues

### FAQ
**P: ¿Cómo agregar nuevas métricas?**
R: Modificar `MetricType` en `query_parser.py` y agregar mapeo en `sql_generator.py`

**P: ¿Cómo personalizar visualizaciones?**
R: Extender `VisualizationEngine` y agregar nuevos tipos en `ChartType`

**P: ¿Cómo optimizar consultas SQL?**
R: Revisar índices en la base de datos y optimizar joins en `sql_generator.py`

---

**Versión**: 1.0.0  
**Última actualización**: Septiembre 2025  
**Autor**: Equipo SugarBI
