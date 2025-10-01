"""
Aplicación web principal de SugarBI
Integra chatbot, dashboard y API en una interfaz web completa
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash
from flask_cors import CORS
from flask_login import LoginManager, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_wtf.csrf import CSRFProtect
import sys
import os
from pathlib import Path
import secrets

# Agregar el directorio raíz al path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from chatbot.query_parser import QueryParser
from filter_parser import FilterParser
from filter_intersections import FilterIntersections
from chatbot.sql_generator import SQLGenerator
from chatbot.langchain_chatbot import langchain_chatbot
from dashboard.visualization_engine import VisualizationEngine, ChartConfig, ChartType
from dashboard.olap_engine import OLAEEngine, OLAPQuery, OLAPOperation, AggregationFunction, DimensionLevel
from dashboard.powerbi_integration import get_powerbi_integration
from dashboard.powerbi_connector import get_powerbi_connector
from auth.models import db, User, Role, SessionToken, AuditLog
from auth.security import security_manager, require_auth, require_permission, audit_log
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import configparser

# Configuración de la aplicación
app = Flask(__name__)

# Configuración de seguridad
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Configuración de base de datos
ruta_base = Path(__file__).parent.parent
config = configparser.ConfigParser()
config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
db_config = config['mysql']

app.config['SQLALCHEMY_DATABASE_URI'] = (
    f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
    f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
)
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

# Inicializar extensiones
db.init_app(app)
CORS(app, 
     origins=["http://localhost:5173", "http://localhost:5174"], 
     supports_credentials=True,
     allow_headers=["Content-Type", "Authorization"],
     methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"])
# Deshabilitar CSRF completamente para desarrollo
# csrf = CSRFProtect(app)

# Configurar Flask-Login
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Por favor inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Inicializar gestor de seguridad
security_manager.init_app(app)

# Registrar blueprints
from auth.routes import auth_bp
app.register_blueprint(auth_bp)

# Crear blueprint API sin CSRF
from flask import Blueprint
api_bp = Blueprint('api', __name__, url_prefix='/auth/api')

# Importar y registrar rutas API
from auth.routes import api_login, api_logout, api_user_me
api_bp.add_url_rule('/login', 'login', api_login, methods=['POST'])
api_bp.add_url_rule('/logout', 'logout', api_logout, methods=['POST'])
api_bp.add_url_rule('/user/me', 'user_me', api_user_me, methods=['GET'])

# Registrar blueprint API sin CSRF
app.register_blueprint(api_bp)

# CSRF deshabilitado para desarrollo
# csrf.exempt(api_bp)

# Inicializar componentes
query_parser = QueryParser()
sql_generator = SQLGenerator()
viz_engine = VisualizationEngine()

# Inicializar sistema de intersecciones de filtros
filter_intersections = None

def get_filter_intersections():
    global filter_intersections
    if filter_intersections is None:
        engine = get_db_connection()
        filter_intersections = FilterIntersections(engine)
        filter_intersections.load_base_data()
    return filter_intersections

# Inicializar motor OLAP
def get_olap_engine():
    """Crear motor OLAP con conexión a la base de datos"""
    ruta_base = Path(__file__).parent.parent
    config = configparser.ConfigParser()
    config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
    
    db_config = config['mysql']
    database_url = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    return OLAEEngine(database_url)

# Configuración de la base de datos
def get_db_connection():
    """Crear conexión a la base de datos"""
    ruta_base = Path(__file__).parent.parent
    config = configparser.ConfigParser()
    config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
    
    db_config = config['mysql']
    cadena_conexion = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    return create_engine(cadena_conexion)

# Rutas principales
@app.route('/')
def index():
    """Página principal del dashboard"""
    if current_user.is_authenticated:
        return redirect(url_for('dashboard'))
    return render_template('index.html')

@app.route('/chatbot')
@login_required
def chatbot_page():
    """Página del chatbot"""
    return render_template('chatbot.html')

@app.route('/dashboard')
@login_required
def dashboard():
    """Página del dashboard"""
    return render_template('dashboard.html')

@app.route('/olap')
@login_required
@require_permission('analytics.read')
def olap_page():
    """Página del análisis OLAP"""
    return render_template('olap_dashboard.html')

@app.route('/olap-interactive')
@login_required
@require_permission('analytics.read')
def olap_interactive_page():
    """Página del análisis OLAP interactivo"""
    return render_template('olap_interactive.html')

@app.route('/analytics')
@login_required
@require_permission('analytics.read')
def analytics_page():
    """Página de análisis de datos con interfaz mejorada"""
    return render_template('olap_analytics.html')

@app.route('/powerbi')
@login_required
@require_permission('analytics.read')
def powerbi_page():
    """Página de integración con Power BI"""
    return render_template('powerbi_integration.html')

# API Endpoints
@app.route('/api/user/me')
@login_required
def get_current_user():
    """Obtener información del usuario actual"""
    return jsonify({
        "success": True,
        "data": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "role": current_user.role.name if current_user.role else "user",
            "is_authenticated": True
        }
    })

@app.route('/api/chat', methods=['POST'])
def process_chat_query():
    """
    Procesa consultas del chatbot y retorna visualizaciones
    
    Ejemplo de request:
    {
        "query": "muestra la cantidad en toneladas de caña producida del top 10 de las fincas en el 2025"
    }
    """
    try:
        # Asegurar que la codificación sea UTF-8
        if request.content_type and 'charset' not in request.content_type:
            request.content_type = request.content_type + '; charset=utf-8'
        
        data = request.get_json(force=True)
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Consulta vacía"
            }), 400
        
        # Paso 1: Parsear la consulta
        intent = query_parser.parse(query)
        
        # Paso 2: Generar SQL
        sql_query = sql_generator.generate_sql(intent)
        
        # Paso 3: Ejecutar consulta
        engine = get_db_connection()
        df = pd.read_sql(sql_query, engine)
        
        if df.empty:
            return jsonify({
                "success": False,
                "error": "No se encontraron datos para la consulta"
            }), 404
        
        # Paso 4: Convertir datos para visualización
        data_for_viz = df.to_dict('records')
        
        # Convertir tipos numpy a nativos de Python
        for record in data_for_viz:
            for key, value in record.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (np.integer, np.int64)):
                    record[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    record[key] = float(value)
        
        # Paso 5: Determinar columnas para visualización
        available_columns = list(data_for_viz[0].keys()) if data_for_viz else []
        
        # Encontrar columna X (dimensión)
        x_column = None
        for col in available_columns:
            if intent.dimension.value.lower() in col.lower() or any(keyword in col.lower() for keyword in ['nombre', 'finca', 'variedad', 'zona']):
                x_column = col
                break
        
        # Encontrar columna Y (métrica)
        y_column = None
        for col in available_columns:
            if intent.metric.value.lower() in col.lower() or any(keyword in col.lower() for keyword in ['total', 'promedio', 'sum', 'avg']):
                y_column = col
                break
        
        # Si no se encuentran, usar las primeras columnas apropiadas
        if not x_column:
            x_column = available_columns[0] if available_columns else "columna_x"
        if not y_column:
            y_column = available_columns[1] if len(available_columns) > 1 else available_columns[0] if available_columns else "columna_y"
        
        # Paso 6: Determinar tipo de gráfico
        chart_type = viz_engine.suggest_chart_type(
            data_for_viz, 
            x_column, 
            y_column
        )
        
        # Paso 7: Crear configuración de visualización
        chart_config = ChartConfig(
            chart_type=chart_type,
            title=f"Consulta: {query}",
            x_axis=x_column,
            y_axis=y_column,
            data=data_for_viz
        )
        
        # Paso 8: Generar visualización
        visualization = viz_engine.create_visualization(chart_config)
        
        return jsonify({
            "success": True,
            "data": {
                "query": query,
                "intent": {
                    "type": intent.query_type.value,
                    "metric": intent.metric.value,
                    "dimension": intent.dimension.value,
                    "filters": intent.filters,
                    "limit": intent.limit
                },
                "sql": sql_query,
                "visualization": visualization,
                "raw_data": data_for_viz,
                "record_count": len(data_for_viz)
            }
        })
        
    except UnicodeDecodeError as e:
        return jsonify({
            "success": False,
            "error": f"Error de codificación: {str(e)}"
        }), 400
    except Exception as e:
        import traceback
        print(f"Error en /api/chat: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/query/parse', methods=['POST'])
def parse_query_only():
    """Solo parsea la consulta sin ejecutar SQL"""
    try:
        data = request.get_json()
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Consulta vacía"
            }), 400
        
        # Parsear consulta
        intent = query_parser.parse(query)
        
        # Generar SQL
        sql_query = sql_generator.generate_sql(intent)
        
        return jsonify({
            "success": True,
            "data": {
                "query": query,
                "intent": {
                    "type": intent.query_type.value,
                    "metric": intent.metric.value,
                    "dimension": intent.dimension.value,
                    "filters": intent.filters,
                    "limit": intent.limit,
                    "time_period": intent.time_period
                },
                "sql": sql_query
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/visualization/create', methods=['POST'])
def create_visualization():
    """Crea una visualización a partir de datos"""
    try:
        data = request.get_json()
        
        chart_config = ChartConfig(
            chart_type=ChartType(data.get('chart_type', 'bar')),
            title=data.get('title', 'Gráfico'),
            x_axis=data.get('x_axis', ''),
            y_axis=data.get('y_axis', ''),
            data=data.get('data', []),
            colors=data.get('colors')
        )
        
        visualization = viz_engine.create_visualization(chart_config)
        
        return jsonify({
            "success": True,
            "data": {
                "visualization": visualization
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/estadisticas')
def get_estadisticas():
    """Obtener estadísticas generales del data mart"""
    try:
        engine = get_db_connection()
        
        # Estadísticas generales
        stats = {}
        
        # Total de registros por tabla
        tables = ['dimfinca', 'dimvariedad', 'dimzona', 'dimtiempo', 'hechos_cosecha']
        for table in tables:
            query = f"SELECT COUNT(*) as total FROM {table}"
            result = pd.read_sql(query, engine)
            stats[f"total_{table}"] = int(result['total'].iloc[0])
        
        # Estadísticas de cosecha
        query = """
        SELECT 
            COUNT(*) as total_cosechas,
            SUM(toneladas_cana_molida) as total_toneladas,
            AVG(tch) as promedio_tch,
            AVG(brix) as promedio_brix,
            AVG(sacarosa) as promedio_sacarosa,
            MIN(t.año) as año_inicio,
            MAX(t.año) as año_fin
        FROM hechos_cosecha h
        JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
        """
        result = pd.read_sql(query, engine)
        
        # Convertir valores numpy a tipos nativos de Python para serialización JSON
        cosecha_stats = {}
        for key, value in result.iloc[0].to_dict().items():
            if pd.isna(value):
                cosecha_stats[key] = None
            elif isinstance(value, (np.integer, np.int64)):
                cosecha_stats[key] = int(value)
            elif isinstance(value, (np.floating, np.float64)):
                cosecha_stats[key] = float(value)
            else:
                cosecha_stats[key] = value
        stats.update(cosecha_stats)
        
        return jsonify({
            "success": True,
            "data": stats
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# APIs para filtros
@app.route('/api/fincas')
def get_fincas():
    """Obtener lista de fincas para filtros"""
    try:
        engine = get_db_connection()
        query = "SELECT finca_id, codigo_finca, nombre_finca FROM dimfinca ORDER BY nombre_finca"
        result = pd.read_sql(query, engine)
        
        fincas = []
        for _, row in result.iterrows():
            fincas.append({
                'finca_id': int(row['finca_id']),
                'codigo_finca': str(row['codigo_finca']),
                'nombre_finca': str(row['nombre_finca'])
            })
        
        return jsonify({
            "success": True,
            "data": fincas
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/variedades')
def get_variedades():
    """Obtener lista de variedades para filtros"""
    try:
        engine = get_db_connection()
        query = "SELECT variedad_id, nombre_variedad FROM dimvariedad ORDER BY nombre_variedad"
        result = pd.read_sql(query, engine)
        
        variedades = []
        for _, row in result.iterrows():
            variedades.append({
                'variedad_id': int(row['variedad_id']),
                'nombre_variedad': str(row['nombre_variedad'])
            })
        
        return jsonify({
            "success": True,
            "data": variedades
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/zonas')
def get_zonas():
    """Obtener lista de zonas para filtros"""
    try:
        engine = get_db_connection()
        query = "SELECT codigo_zona, nombre_zona FROM dimzona ORDER BY codigo_zona"
        result = pd.read_sql(query, engine)
        
        zonas = []
        for _, row in result.iterrows():
            zonas.append({
                'codigo_zona': str(row['codigo_zona']),
                'nombre_zona': str(row['nombre_zona'])
            })
        
        return jsonify({
            "success": True,
            "data": zonas
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/tiempo')
def get_tiempo():
    """Obtener lista de períodos de tiempo para filtros"""
    try:
        engine = get_db_connection()
        query = """
        SELECT DISTINCT 
            tiempo_id, 
            fecha, 
            año, 
            mes, 
            nombre_mes, 
            trimestre 
        FROM dimtiempo 
        ORDER BY año DESC, mes ASC
        """
        result = pd.read_sql(query, engine)
        
        tiempo = []
        for _, row in result.iterrows():
            tiempo.append({
                'tiempo_id': int(row['tiempo_id']),
                'fecha': str(row['fecha']),
                'año': int(row['año']),
                'mes': int(row['mes']),
                'nombre_mes': str(row['nombre_mes']),
                'trimestre': int(row['trimestre'])
            })
        
        return jsonify({
            "success": True,
            "data": tiempo
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# APIs del Parser de Filtros Inteligente
@app.route('/api/filter-options')
def get_filter_options():
    """Obtener opciones de filtros disponibles de forma reactiva usando intersecciones"""
    try:
        # Obtener filtros actuales de la query string
        current_filters = {}
        if request.args.get('finca_id'):
            current_filters['finca_id'] = int(request.args.get('finca_id'))
        if request.args.get('variedad_id'):
            current_filters['variedad_id'] = int(request.args.get('variedad_id'))
        if request.args.get('zona_id'):
            current_filters['zona_id'] = int(request.args.get('zona_id'))
        if request.args.get('año'):
            current_filters['año'] = int(request.args.get('año'))
        if request.args.get('mes'):
            current_filters['mes'] = int(request.args.get('mes'))
        if request.args.get('top_fincas'):
            current_filters['top_fincas'] = int(request.args.get('top_fincas'))
        
        # Usar sistema de intersecciones
        intersections = get_filter_intersections()
        filter_options = intersections.get_available_options(current_filters)
        
        return jsonify({
            "success": True,
            "data": filter_options
        })
        
    except Exception as e:
        print(f"❌ ERROR en /api/filter-options: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/cosecha-filtered')
def get_cosecha_filtered():
    """Obtener datos de cosecha filtrados usando sistema de intersecciones"""
    try:
        # Obtener filtros de la query string
        filters = {}
        if request.args.get('finca_id'):
            filters['finca_id'] = int(request.args.get('finca_id'))
        if request.args.get('variedad_id'):
            filters['variedad_id'] = int(request.args.get('variedad_id'))
        if request.args.get('zona_id'):
            filters['zona_id'] = int(request.args.get('zona_id'))
        if request.args.get('año'):
            filters['año'] = int(request.args.get('año'))
        if request.args.get('mes'):
            filters['mes'] = int(request.args.get('mes'))
        if request.args.get('top_fincas'):
            filters['top_fincas'] = int(request.args.get('top_fincas'))
        
        # Obtener límite
        limit = int(request.args.get('limit', 1000))
        
        # Obtener datos filtrados usando sistema de intersecciones
        intersections = get_filter_intersections()
        group_by_finca = request.args.get('group_by_finca', 'true').lower() == 'true'
        data = intersections.get_filtered_data(filters, limit, group_by_finca)
        
        return jsonify({
            "success": True,
            "data": data,
            "count": len(data),
            "filters_applied": filters,
            "grouped_by_finca": group_by_finca
        })
        
    except Exception as e:
        print(f"❌ ERROR en /api/cosecha-filtered: {e}")
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/examples')
def get_example_queries():
    """Retorna ejemplos de consultas que se pueden hacer"""
    examples = [
        "muestra la cantidad en toneladas de caña producida del top 10 de las fincas en el 2025",
        "¿cuáles son las 5 mejores variedades por TCH?",
        "muestra la producción por zona en 2024",
        "¿cuál es el promedio de brix por finca?",
        "muestra la tendencia de producción por mes en 2025",
        "¿cuáles son las fincas con mayor rendimiento?",
        "muestra la distribución de producción por variedad",
        "¿cuál es la producción total por año?"
    ]
    
    return jsonify({
        "success": True,
        "data": {
            "examples": examples
        }
    })

@app.route('/api/cosecha/top')
def get_top_cosechas():
    """Obtener top cosechas por diferentes criterios"""
    try:
        engine = get_db_connection()
        
        criterio = request.args.get('criterio', 'toneladas')  # toneladas, tch, brix
        limit = request.args.get('limit', 10, type=int)
        
        # Mapear criterios a columnas
        criterios_map = {
            'toneladas': 'h.toneladas_cana_molida',
            'tch': 'h.tch',
            'brix': 'h.brix',
            'sacarosa': 'h.sacarosa'
        }
        
        if criterio not in criterios_map:
            return jsonify({"success": False, "error": "Criterio no válido"}), 400
        
        # Consulta con JOINs para obtener nombres reales
        query = f"""
        SELECT 
            h.toneladas_cana_molida,
            h.tch,
            h.brix,
            h.sacarosa,
            h.id_finca,
            f.nombre_finca,
            f.codigo_finca,
            v.nombre_variedad,
            v.variedad_id,
            z.nombre_zona,
            z.codigo_zona,
            t.año,
            t.mes,
            t.nombre_mes,
            t.fecha
        FROM hechos_cosecha h
        LEFT JOIN dimfinca f ON h.id_finca = f.finca_id
        LEFT JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
        LEFT JOIN dimzona z ON h.codigo_zona = z.codigo_zona
        LEFT JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
        ORDER BY {criterios_map[criterio]} DESC
        LIMIT {limit}
        """
        
        df = pd.read_sql(query, engine)
        
        # Convertir DataFrame a lista de diccionarios
        data = []
        for _, row in df.iterrows():
            record = {}
            for key, value in row.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (np.integer, np.int64)):
                    record[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    record[key] = float(value)
                else:
                    record[key] = value
            data.append(record)
        
        return jsonify({
            "success": True,
            "data": data
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/chat/langchain', methods=['POST'])
def process_chat_query_langchain():
    """
    Procesa consultas del chatbot usando LangChain
    """
    try:
        data = request.get_json(force=True)
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Consulta vacía"
            }), 400
        
        # Paso 1: Procesar consulta con LangChain
        langchain_result = langchain_chatbot.process_query(query)
        
        # Paso 2: Crear intent desde el resultado de LangChain
        from chatbot.query_parser import QueryIntent, QueryType, MetricType, DimensionType
        
        # Mapear strings a enums
        query_type_map = {
            "top_ranking": QueryType.TOP_RANKING,
            "statistics": QueryType.STATISTICS,
            "comparison": QueryType.COMPARISON,
            "trend": QueryType.TREND,
            "basic": QueryType.BASIC
        }
        
        metric_type_map = {
            "toneladas": MetricType.TONELADAS,
            "tch": MetricType.TCH,
            "brix": MetricType.BRIX,
            "sacarosa": MetricType.SACAROSA,
            "area": MetricType.AREA,
            "rendimiento": MetricType.RENDIMIENTO
        }
        
        dimension_type_map = {
            "finca": DimensionType.FINCA,
            "variedad": DimensionType.VARIEDAD,
            "zona": DimensionType.ZONA,
            "tiempo": DimensionType.TIEMPO
        }
        
        # Detectar granularidad temporal si LangChain no la provee
        detected_time_period = langchain_result.get("time_period")
        if not detected_time_period:
            ql = query.lower()
            if "por mes" in ql or "cada mes" in ql or "por cada mes" in ql:
                detected_time_period = "monthly"
            elif "por año" in ql or "por cada año" in ql or "por an" in ql:
                detected_time_period = "yearly"

        # Forzar tipo TREND si hay time_period y ajustar dimensión
        query_type = query_type_map.get(langchain_result.get("query_type", "basic"), QueryType.BASIC)
        dimension = dimension_type_map.get(langchain_result.get("dimension", "finca"), DimensionType.FINCA)
        
        if detected_time_period:
            query_type = QueryType.TREND
            dimension = DimensionType.TIEMPO
        
        intent = QueryIntent(
            query_type=query_type,
            metric=metric_type_map.get(langchain_result.get("metric", "toneladas"), MetricType.TONELADAS),
            dimension=dimension,
            filters=langchain_result.get("filters", {}),
            limit=langchain_result.get("limit", 10),
            time_period=detected_time_period
        )
        
        # Paso 3: Generar SQL
        sql_query = sql_generator.generate_sql(intent)
        
        # Paso 4: Ejecutar consulta
        engine = get_db_connection()
        df = pd.read_sql(sql_query, engine)
        
        if df.empty:
            return jsonify({
                "success": False,
                "error": "No se encontraron datos para la consulta"
            }), 404
        
        # Paso 5: Convertir datos
        data_for_viz = []
        for _, row in df.iterrows():
            record = {}
            for key, value in row.items():
                if pd.isna(value):
                    record[key] = None
                elif isinstance(value, (np.integer, np.int64)):
                    record[key] = int(value)
                elif isinstance(value, (np.floating, np.float64)):
                    record[key] = float(value)
                else:
                    record[key] = value
            data_for_viz.append(record)
        
        # Paso 6: Crear visualización
        available_columns = list(data_for_viz[0].keys()) if data_for_viz else []
        
        # Determinar tipo de gráfica
        chart_type = "line" if intent.query_type == QueryType.TREND else "bar"
        
        # Encontrar columnas para visualización con prioridad para series temporales
        x_column = None
        y_column = None
        
        # Prioridad para series temporales: nombre_mes, mes, año
        if intent.query_type == QueryType.TREND:
            for col in available_columns:
                if 'nombre_mes' in col.lower():
                    x_column = col
                    break
                elif 'mes' in col.lower() and 'nombre' not in col.lower():
                    x_column = col
                    break
                elif 'año' in col.lower():
                    x_column = col
                    break
        
        # Para series temporales, crear etiquetas más descriptivas
        if intent.query_type == QueryType.TREND and data_for_viz:
            # Normalizar nombres de columnas que vienen con prefijos (p. ej. "t.mes")
            lower_cols = [c.lower() for c in available_columns]
            nombre_mes_key = next((c for c in available_columns if 'nombre_mes' in c.lower()), None)
            mes_key = next((c for c in available_columns if ('mes' in c.lower() and 'nombre' not in c.lower())), None)
            anio_key = next((c for c in available_columns if ('año' in c.lower() or 'anio' in c.lower())), None)

            # Si tenemos nombre_mes, usarlo como X
            if nombre_mes_key:
                x_column = nombre_mes_key
            # Si tenemos mes y año, combinar para crear etiquetas descriptivas
            elif mes_key and anio_key:
                for record in data_for_viz:
                    mes_num = record.get(mes_key, '')
                    anio_val = record.get(anio_key, '')
                    if mes_num and anio_val:
                        meses = ['', 'Ene', 'Feb', 'Mar', 'Abr', 'May', 'Jun',
                                 'Jul', 'Ago', 'Sep', 'Oct', 'Nov', 'Dic']
                        try:
                            mes_int = int(mes_num)
                        except Exception:
                            # Si viene como texto tipo "01", intentar limpiar
                            try:
                                mes_int = int(str(mes_num).lstrip('0') or '0')
                            except Exception:
                                mes_int = 0
                        if 1 <= mes_int <= 12:
                            record['etiqueta_temporal'] = f"{meses[mes_int]} {anio_val}"
                        else:
                            record['etiqueta_temporal'] = f"Mes {mes_num} {anio_val}"
                x_column = 'etiqueta_temporal'
        
        # Si no es tendencia o no se encontró columna temporal, buscar por dimensión
        if not x_column:
            for col in available_columns:
                if intent.dimension.value.lower() in col.lower() or any(keyword in col.lower() for keyword in ['nombre', 'finca', 'variedad', 'zona']):
                    x_column = col
                    break
        
        # Buscar columna Y con prioridad para totales
        for col in available_columns:
            if 'total_' in col.lower() and intent.metric.value.lower() in col.lower():
                y_column = col
                break
            elif any(keyword in col.lower() for keyword in ['toneladas', 'tch', 'brix', 'sacarosa']) and 'total' in col.lower():
                y_column = col
                break
        
        # Fallback para Y
        if not y_column:
            for col in available_columns:
                if any(keyword in col.lower() for keyword in ['toneladas', 'tch', 'brix', 'sacarosa', 'total', 'promedio']):
                    y_column = col
                    break
        
        if not x_column:
            x_column = available_columns[0] if available_columns else "item"
        if not y_column:
            y_column = available_columns[1] if len(available_columns) > 1 else available_columns[0]
        
        # Resaltar barra del elemento máximo, mínimo y promedio
        max_index = None
        min_index = None
        avg_index = None
        try:
            if x_column and data_for_viz:
                # Encontrar el índice del elemento con mayor y menor métrica
                metric_values = [rec.get(y_column) or 0 for rec in data_for_viz[:10]]
                if metric_values:
                    max_val = max(metric_values)
                    min_val = min(metric_values)
                    avg_val = sum(metric_values) / len(metric_values)
                    max_index = metric_values.index(max_val)
                    min_index = metric_values.index(min_val)
                    
                    # Encontrar el valor más cercano al promedio
                    if len(metric_values) > 2:  # Solo si hay más de 2 valores
                        closest_to_avg = min(metric_values, key=lambda x: abs(x - avg_val))
                        avg_index = metric_values.index(closest_to_avg)
                        # Si el promedio coincide con max o min, no resaltarlo
                        if avg_index == max_index or avg_index == min_index:
                            avg_index = None
        except Exception:
            max_index = None
            min_index = None
            avg_index = None

        # Títulos y labels consistentes
        metric_label_title = intent.metric.value.capitalize()
        dimension_label_title = intent.dimension.value.capitalize()
        title_prefix = "Tendencia" if intent.query_type == QueryType.TREND else "Distribución"
        chart_title = f"{title_prefix} de {metric_label_title} por {dimension_label_title}"

        visualization = {
            "type": chart_type,
            "data": {
                "labels": [str(record.get(x_column, f"Item {i}")) for i, record in enumerate(data_for_viz[:10])],
                "datasets": [{
                    "label": y_column or metric_label_title,
                    "data": [record.get(y_column, 0) for record in data_for_viz[:10]],
                    "backgroundColor": [
                        # Verde para máximo, rojo para mínimo, naranja para promedio, azul para intermedios
                        ("rgba(34, 197, 94, 0.6)" if max_index is not None and idx == max_index else
                         "rgba(239, 68, 68, 0.6)" if min_index is not None and idx == min_index else
                         "rgba(249, 115, 22, 0.6)" if avg_index is not None and idx == avg_index else
                         "rgba(59, 130, 246, 0.5)")
                        for idx, _ in enumerate(data_for_viz[:10])
                    ],
                    "borderColor": [
                        # Verde para máximo, rojo para mínimo, naranja para promedio, azul para intermedios
                        ("rgba(34, 197, 94, 1)" if max_index is not None and idx == max_index else
                         "rgba(239, 68, 68, 1)" if min_index is not None and idx == min_index else
                         "rgba(249, 115, 22, 1)" if avg_index is not None and idx == avg_index else
                         "rgba(59, 130, 246, 1)")
                        for idx, _ in enumerate(data_for_viz[:10])
                    ],
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "plugins": {
                    "title": {"display": True, "text": chart_title},
                    "legend": {"display": True}
                },
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        }
        
        # Paso 7: Generar respuesta natural
        natural_response = langchain_chatbot.generate_response(query, data_for_viz, sql_query)

        # Generador determinístico adicional para asegurar una respuesta clara
        try:
            metric_candidates = [
                'toneladas_cana_molida', 'tch', 'brix', 'sacarosa', 'area_cosechada', 'rendimiento_teorico',
                'total', 'promedio'
            ]
            # Elegir columna de métrica basada en intención o nombres conocidos
            metric_col = None
            metric_hint = intent.metric.value.lower()
            for col in available_columns:
                if metric_hint in col.lower():
                    metric_col = col
                    break
            if not metric_col:
                for name in metric_candidates:
                    if name in available_columns:
                        metric_col = name
                        break
            # Elegir columna de dimensión (nombre)
            dim_candidates = ['nombre_finca', 'finca', 'nombre_variedad', 'variedad', 'nombre_zona', 'zona']
            dim_col = None
            for col in available_columns:
                if any(keyword in col.lower() for keyword in ['finca', 'variedad', 'zona']):
                    dim_col = col
                    break
            # Detectar intención de promedio por tipo o por texto libre
            lower_query = (query or '').lower()
            query_mentions_avg = any(k in lower_query for k in ['promedio', 'media', 'average', 'avg'])

            # Si la consulta es de tipo estadística/promedio, componer respuesta directa
            avg_summary = None
            try:
                is_stats = (intent.query_type == QueryType.STATISTICS) or query_mentions_avg or \
                           (y_column and any(k in y_column.lower() for k in ['promedio', 'avg', 'media']))
                if is_stats and (metric_col or y_column):
                    col_for_avg = metric_col or y_column
                    values = [rec.get(col_for_avg) for rec in data_for_viz if isinstance(rec.get(col_for_avg), (int, float))]
                    if not values and data_for_viz and isinstance(data_for_viz[0].get(col_for_avg), (int, float)):
                        values = [data_for_viz[0].get(col_for_avg)]
                    if values:
                        avg_val = sum(values) / len(values)
                        metric_label_avg = intent.metric.value.lower()
                        metric_label_avg = 'toneladas' if 'toneladas' in metric_label_avg else metric_label_avg
                        avg_summary = f"El promedio de {metric_label_avg} es de {avg_val:,.0f} {metric_label_avg}."
            except Exception:
                avg_summary = None

            # Si es una consulta de tendencia temporal, generar resumen de serie
            trend_summary = None
            try:
                if intent.query_type == QueryType.TREND and len(data_for_viz) > 1:
                    # Calcular total general
                    total_val = sum(rec.get(y_column, 0) for rec in data_for_viz if isinstance(rec.get(y_column), (int, float)))
                    metric_label_trend = intent.metric.value.lower()
                    metric_label_trend = 'toneladas' if 'toneladas' in metric_label_trend else metric_label_trend
                    
                    # Determinar período
                    if intent.time_period == 'monthly':
                        period_text = f"por mes en {filters.get('año', 'el período seleccionado')}"
                    elif intent.time_period == 'yearly':
                        period_text = "por año"
                    else:
                        period_text = "en el período"
                    
                    # Corregir gramática para toneladas
                    if 'toneladas' in metric_label_trend:
                        metric_label_trend = 'toneladas'
                    
                    if intent.time_period == 'monthly':
                        trend_summary = f"La producción total {period_text} fue de {total_val:,.0f} {metric_label_trend}. Se muestran {len(data_for_viz)} meses."
                    elif intent.time_period == 'yearly':
                        trend_summary = f"La producción total {period_text} fue de {total_val:,.0f} {metric_label_trend}. Se muestran {len(data_for_viz)} años."
                    else:
                        trend_summary = f"La producción total {period_text} fue de {total_val:,.0f} {metric_label_trend}. Se muestran {len(data_for_viz)} períodos."
            except Exception:
                trend_summary = None

            # Determinar top registro
            top_item = None
            if metric_col and dim_col:
                top_item = max(data_for_viz, key=lambda r: (r.get(metric_col) or 0))
            # Formatear periodo si hay filtros de tiempo
            period_text = ''
            f = intent.filters or {}
            if f.get('año') and f.get('mes'):
                # Intentar usar nombre_mes si está disponible
                month_name = None
                for rec in data_for_viz:
                    if rec.get('nombre_mes'):
                        month_name = rec['nombre_mes']
                        break
                if not month_name:
                    meses = ['Enero','Febrero','Marzo','Abril','Mayo','Junio','Julio','Agosto','Septiembre','Octubre','Noviembre','Diciembre']
                    idx = int(f['mes']) - 1
                    if 0 <= idx < 12:
                        month_name = meses[idx]
                if month_name:
                    period_text = f" en {month_name} de {f['año']}"
                else:
                    period_text = f" en {f['mes']}/{f['año']}"
            elif f.get('año'):
                period_text = f" en {f['año']}"
            # Construir resumen si se pudo determinar
            if trend_summary:
                deterministic_summary = trend_summary
            elif avg_summary:
                deterministic_summary = avg_summary
            elif top_item and metric_col and dim_col:
                metric_value = top_item.get(metric_col) or 0
                entity_name = str(top_item.get(dim_col))
                metric_label = intent.metric.value.lower()
                # Normalizar etiqueta
                metric_label = 'toneladas' if 'toneladas' in metric_label else metric_label
                deterministic_summary = f"La {intent.dimension.value} más destacada{period_text} es {entity_name} con {metric_value:,.0f} {metric_label}."
            else:
                # Si solo hay un dato numérico sin dimensión, genera un resumen genérico
                single_summary = None
                try:
                    col = metric_col or y_column
                    if col and data_for_viz and isinstance(data_for_viz[0].get(col), (int, float)):
                        val = data_for_viz[0].get(col)
                        metric_label_single = intent.metric.value.lower()
                        metric_label_single = 'toneladas' if 'toneladas' in metric_label_single else metric_label_single or 'valor'
                        single_summary = f"El {('promedio de ' if query_mentions_avg else '')}{metric_label_single}{period_text} fue de {val:,.0f} {metric_label_single}."
                except Exception:
                    single_summary = None
                deterministic_summary = single_summary

            # Aplicar la respuesta determinística si existe o si la respuesta generada es genérica
            if deterministic_summary:
                if not natural_response or 'Se encontraron' in natural_response:
                    natural_response = deterministic_summary
                else:
                    natural_response = f"{deterministic_summary}\n\n{natural_response}"
        except Exception:
            # No bloquear en caso de fallo; mantener la respuesta existente
            pass
        
        return jsonify({
            "success": True,
            "data": {
                "query": query,
                "intent": {
                    "type": intent.query_type.value,
                    "metric": intent.metric.value,
                    "dimension": intent.dimension.value,
                    "filters": intent.filters,
                    "limit": intent.limit,
                    "explanation": langchain_result.get("explanation", "")
                },
                "sql": sql_query,
                "visualization": visualization,
                "raw_data": data_for_viz,
                "record_count": len(data_for_viz),
                "natural_response": natural_response
            }
        })
        
    except Exception as e:
        import traceback
        print(f"Error en /api/chat/langchain: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# API Endpoints OLAP
@app.route('/api/olap/dimensions')
def get_olap_dimensions():
    """Obtener dimensiones disponibles para OLAP"""
    try:
        # Valores por defecto si falla el motor OLAP
        default_dimensions = {
            "dimensions": [
                {"name": "tiempo", "label": "Tiempo", "levels": ["año", "mes", "trimestre"]},
                {"name": "geografia", "label": "Geografía", "levels": ["zona", "finca"]},
                {"name": "producto", "label": "Producto", "levels": ["variedad"]}
            ]
        }
        
        try:
            olap_engine = get_olap_engine()
            dimensions = olap_engine.get_available_dimensions()
        except:
            dimensions = default_dimensions
        
        return jsonify({
            "success": True,
            "data": dimensions
        })
    except Exception as e:
        return jsonify({
            "success": True,
            "data": {
                "dimensions": [
                    {"name": "tiempo", "label": "Tiempo", "levels": ["año", "mes", "trimestre"]},
                    {"name": "geografia", "label": "Geografía", "levels": ["zona", "finca"]},
                    {"name": "producto", "label": "Producto", "levels": ["variedad"]}
                ]
            }
        })

@app.route('/api/olap/measures')
def get_olap_measures():
    """Obtener medidas disponibles para OLAP"""
    try:
        # Valores por defecto si falla el motor OLAP
        default_measures = [
            {"name": "toneladas_cana_molida", "label": "Toneladas", "type": "numeric"},
            {"name": "tch", "label": "TCH", "type": "numeric"},
            {"name": "brix", "label": "Brix", "type": "numeric"},
            {"name": "sacarosa", "label": "Sacarosa", "type": "numeric"}
        ]
        
        try:
            olap_engine = get_olap_engine()
            measures = olap_engine.get_available_measures()
        except:
            measures = default_measures
        
        return jsonify({
            "success": True,
            "data": {
                "measures": measures
            }
        })
    except Exception as e:
        return jsonify({
            "success": True,
            "data": {
                "measures": [
                    {"name": "toneladas_cana_molida", "label": "Toneladas", "type": "numeric"},
                    {"name": "tch", "label": "TCH", "type": "numeric"},
                    {"name": "brix", "label": "Brix", "type": "numeric"},
                    {"name": "sacarosa", "label": "Sacarosa", "type": "numeric"}
                ]
            }
        })

@app.route('/api/olap/aggregations')
def get_olap_aggregations():
    """Obtener funciones de agregación disponibles"""
    try:
        olap_engine = get_olap_engine()
        aggregations = olap_engine.get_available_aggregations()
        
        return jsonify({
            "success": True,
            "data": {
                "aggregations": aggregations
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/olap/examples')
def get_olap_examples():
    """Obtener ejemplos de consultas OLAP"""
    try:
        olap_engine = get_olap_engine()
        examples = olap_engine.get_olap_examples()
        
        return jsonify({
            "success": True,
            "data": {
                "examples": examples
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/olap/query', methods=['POST'])
def execute_olap_query():
    """Ejecutar consulta OLAP"""
    try:
        data = request.get_json()
        
        # Validar datos requeridos
        if not data.get('measures'):
            return jsonify({
                "success": False,
                "error": "Se requiere al menos una medida"
            }), 400
        
        # Construir consulta OLAP
        operation = OLAPOperation(data.get('operation', 'aggregate'))
        measures = data.get('measures', [])
        dimensions = data.get('dimensions', [])
        
        # Convertir dimension_levels
        dimension_levels = {}
        for dim, level in data.get('dimension_levels', {}).items():
            dimension_levels[dim] = DimensionLevel(level)
        
        # Convertir aggregation_functions
        aggregation_functions = []
        for func in data.get('aggregation_functions', ['sum']):
            aggregation_functions.append(AggregationFunction(func))
        
        # Crear consulta
        query = OLAPQuery(
            operation=operation,
            measures=measures,
            dimensions=dimensions,
            dimension_levels=dimension_levels,
            filters=data.get('filters', {}),
            aggregation_functions=aggregation_functions,
            limit=data.get('limit', 100),
            sort_by=data.get('sort_by')
        )
        
        # Ejecutar consulta
        olap_engine = get_olap_engine()
        result = olap_engine.execute_olap_query(query)
        
        if result.success:
            return jsonify({
                "success": True,
                "data": {
                    "records": result.data,
                    "record_count": result.record_count,
                    "execution_time": result.execution_time,
                    "operation": result.operation,
                    "sql_query": result.sql_query,
                    "metadata": result.metadata
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": result.error
            }), 500
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/olap/pivot', methods=['POST'])
def create_pivot_table():
    """Crear tabla dinámica"""
    try:
        data = request.get_json()
        
        records = data.get('data', [])
        row_dimension = data.get('row_dimension')
        col_dimension = data.get('col_dimension')
        measure = data.get('measure')
        
        if not all([row_dimension, col_dimension, measure]):
            return jsonify({
                "success": False,
                "error": "Se requieren row_dimension, col_dimension y measure"
            }), 400
        
        olap_engine = get_olap_engine()
        pivot_result = olap_engine.create_pivot_table(records, row_dimension, col_dimension, measure)
        
        return jsonify({
            "success": True,
            "data": pivot_result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/olap/dimension-values/<dimension>/<level>')
def get_dimension_values(dimension, level):
    """Obtener valores únicos para una dimensión y nivel"""
    try:
        olap_engine = get_olap_engine()
        dimension_level = DimensionLevel(level)
        values = olap_engine.get_dimension_values(dimension, dimension_level)
        
        return jsonify({
            "success": True,
            "data": {
                "dimension": dimension,
                "level": level,
                "values": values
            }
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint no encontrado"}), 404

# =============================================================================
# POWER BI INTEGRATION ENDPOINTS
# =============================================================================

@app.route('/api/powerbi/schema')
def get_powerbi_schema():
    """Obtener esquema del cubo OLAP para Power BI"""
    try:
        powerbi = get_powerbi_integration()
        if not powerbi:
            return jsonify({
                "success": False,
                "error": "Error inicializando integración Power BI"
            }), 500
        
        result = powerbi.get_cube_schema()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error obteniendo esquema: {str(e)}"
        }), 500

@app.route('/api/powerbi/fact-table')
def export_powerbi_fact_table():
    """Exportar tabla de hechos para Power BI"""
    try:
        powerbi = get_powerbi_integration()
        if not powerbi:
            return jsonify({
                "success": False,
                "error": "Error inicializando integración Power BI"
            }), 500
        
        # Obtener filtros de query parameters
        filters = {}
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('zones'):
            filters['zones'] = request.args.get('zones').split(',')
        if request.args.get('varieties'):
            filters['varieties'] = request.args.get('varieties').split(',')
        
        result = powerbi.export_fact_table(filters if filters else None)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error exportando tabla de hechos: {str(e)}"
        }), 500

@app.route('/api/powerbi/dimensions')
def export_powerbi_dimensions():
    """Exportar tablas de dimensiones para Power BI"""
    try:
        powerbi = get_powerbi_integration()
        if not powerbi:
            return jsonify({
                "success": False,
                "error": "Error inicializando integración Power BI"
            }), 500
        
        result = powerbi.export_dimension_tables()
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error exportando dimensiones: {str(e)}"
        }), 500

@app.route('/api/powerbi/dataset')
def create_powerbi_dataset():
    """Crear dataset completo para Power BI"""
    try:
        powerbi = get_powerbi_integration()
        if not powerbi:
            return jsonify({
                "success": False,
                "error": "Error inicializando integración Power BI"
            }), 500
        
        # Obtener filtros de query parameters
        filters = {}
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('zones'):
            filters['zones'] = request.args.get('zones').split(',')
        if request.args.get('varieties'):
            filters['varieties'] = request.args.get('varieties').split(',')
        
        result = powerbi.create_powerbi_dataset(filters if filters else None)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error creando dataset: {str(e)}"
        }), 500

@app.route('/api/powerbi/analysis', methods=['POST'])
def get_powerbi_analysis():
    """Obtener datos para análisis OLAP específico en Power BI"""
    try:
        powerbi = get_powerbi_integration()
        if not powerbi:
            return jsonify({
                "success": False,
                "error": "Error inicializando integración Power BI"
            }), 500
        
        data = request.get_json()
        if not data:
            return jsonify({
                "success": False,
                "error": "Datos JSON requeridos"
            }), 400
        
        result = powerbi.get_olap_analysis_data(data)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error en análisis: {str(e)}"
        }), 500

@app.route('/api/powerbi/export/csv')
def export_powerbi_csv():
    """Exportar datos en formato CSV para Power BI"""
    try:
        powerbi = get_powerbi_integration()
        if not powerbi:
            return jsonify({
                "success": False,
                "error": "Error inicializando integración Power BI"
            }), 500
        
        # Obtener filtros
        filters = {}
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('zones'):
            filters['zones'] = request.args.get('zones').split(',')
        if request.args.get('varieties'):
            filters['varieties'] = request.args.get('varieties').split(',')
        
        # Obtener datos
        result = powerbi.export_fact_table(filters if filters else None)
        
        if not result["success"]:
            return jsonify(result), 500
        
        # Convertir a CSV
        import io
        import csv
        
        output = io.StringIO()
        data = result["data"]["data"]
        
        if data:
            writer = csv.DictWriter(output, fieldnames=data[0].keys())
            writer.writeheader()
            writer.writerows(data)
        
        csv_content = output.getvalue()
        output.close()
        
        # Crear respuesta con CSV
        from flask import Response
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={
                'Content-Disposition': f'attachment; filename=sugarbi_cosecha_{datetime.now().strftime("%Y%m%d_%H%M%S")}.csv'
            }
        )
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error exportando CSV: {str(e)}"
        }), 500

@app.route('/api/powerbi/export/json')
def export_powerbi_json():
    """Exportar datos en formato JSON para Power BI"""
    try:
        powerbi = get_powerbi_integration()
        if not powerbi:
            return jsonify({
                "success": False,
                "error": "Error inicializando integración Power BI"
            }), 500
        
        # Obtener filtros
        filters = {}
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('zones'):
            filters['zones'] = request.args.get('zones').split(',')
        if request.args.get('varieties'):
            filters['varieties'] = request.args.get('varieties').split(',')
        
        # Obtener dataset completo
        result = powerbi.create_powerbi_dataset(filters if filters else None)
        
        if not result["success"]:
            return jsonify(result), 500
        
        # Crear respuesta con JSON
        from flask import Response
        return Response(
            json.dumps(result["data"], indent=2, ensure_ascii=False),
            mimetype='application/json',
            headers={
                'Content-Disposition': f'attachment; filename=sugarbi_dataset_{datetime.now().strftime("%Y%m%d_%H%M%S")}.json'
            }
        )
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error exportando JSON: {str(e)}"
        }), 500

# =============================================================================
# POWER BI DESKTOP CONNECTOR ENDPOINTS
# =============================================================================

@app.route('/api/powerbi-desktop/connection-info')
def get_powerbi_connection_info():
    """Información de conexión para Power BI Desktop"""
    try:
        connector = get_powerbi_connector()
        if not connector:
            return jsonify({
                "success": False,
                "error": "Error inicializando conector Power BI"
            }), 500
        
        result = connector.get_connection_info()
        return jsonify({
            "success": True,
            "data": result
        })
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error obteniendo información de conexión: {str(e)}"
        }), 500

@app.route('/api/powerbi-desktop/table/<table_name>')
def get_powerbi_table(table_name):
    """Obtener tabla específica para Power BI Desktop"""
    try:
        connector = get_powerbi_connector()
        if not connector:
            return jsonify({
                "success": False,
                "error": "Error inicializando conector Power BI"
            }), 500
        
        # Obtener filtros de query parameters
        filters = {}
        if request.args.get('start_date'):
            filters['start_date'] = request.args.get('start_date')
        if request.args.get('end_date'):
            filters['end_date'] = request.args.get('end_date')
        if request.args.get('zones'):
            filters['zones'] = request.args.get('zones').split(',')
        if request.args.get('varieties'):
            filters['varieties'] = request.args.get('varieties').split(',')
        
        result = connector.get_powerbi_ready_data(table_name, filters if filters else None)
        return jsonify(result)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error obteniendo tabla: {str(e)}"
        }), 500

@app.route('/api/powerbi-desktop/export/<format_type>')
def export_powerbi_desktop(format_type):
    """Exportar datos para Power BI Desktop"""
    try:
        connector = get_powerbi_connector()
        if not connector:
            return jsonify({
                "success": False,
                "error": "Error inicializando conector Power BI"
            }), 500
        
        return connector.export_for_powerbi_desktop(format_type)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error exportando datos: {str(e)}"
        }), 500

@app.route('/api/powerbi-desktop/odata')
def powerbi_odata_endpoint():
    """Endpoint OData para Power BI Desktop (simulado)"""
    try:
        connector = get_powerbi_connector()
        if not connector:
            return jsonify({
                "success": False,
                "error": "Error inicializando conector Power BI"
            }), 500
        
        # Obtener datos de la tabla de hechos
        result = connector.get_powerbi_ready_data("hechos_cosecha")
        
        if not result["success"]:
            return jsonify(result), 500
        
        # Formatear como OData
        odata_response = {
            "@odata.context": f"{request.url_root}api/powerbi-desktop/odata/$metadata",
            "value": result["data"]["data"]
        }
        
        return jsonify(odata_response)
        
    except Exception as e:
        return jsonify({
            "success": False,
            "error": f"Error en endpoint OData: {str(e)}"
        }), 500

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    print("🚀 Iniciando SugarBI Web Application...")
    print("🤖 Chatbot: http://localhost:5001/chatbot")
    print("📊 Dashboard: http://localhost:5001/dashboard")
    print("🔍 OLAP: http://localhost:5001/olap")
    print("📈 Power BI: http://localhost:5001/powerbi")
    print("🌐 API: http://localhost:5001/api/")
    print("📖 Documentación: http://localhost:5001/")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
