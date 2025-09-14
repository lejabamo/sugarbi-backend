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
from chatbot.sql_generator import SQLGenerator
from chatbot.langchain_chatbot import langchain_chatbot
from dashboard.visualization_engine import VisualizationEngine, ChartConfig, ChartType
from dashboard.olap_engine import OLAEEngine, OLAPQuery, OLAPOperation, AggregationFunction, DimensionLevel
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
        
        # Consulta simplificada sin JOINs problemáticos
        query = f"""
        SELECT 
            h.toneladas_cana_molida,
            h.tch,
            h.brix,
            h.sacarosa,
            h.id_finca,
            h.codigo_variedad,
            h.codigo_zona,
            h.codigo_tiempo
        FROM hechos_cosecha h
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
        
        intent = QueryIntent(
            query_type=query_type_map.get(langchain_result.get("query_type", "basic"), QueryType.BASIC),
            metric=metric_type_map.get(langchain_result.get("metric", "toneladas"), MetricType.TONELADAS),
            dimension=dimension_type_map.get(langchain_result.get("dimension", "finca"), DimensionType.FINCA),
            filters=langchain_result.get("filters", {}),
            limit=langchain_result.get("limit", 10),
            time_period=None
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
        
        # Encontrar columnas para visualización
        x_column = None
        y_column = None
        
        for col in available_columns:
            if any(keyword in col.lower() for keyword in ['finca', 'variedad', 'zona', 'tiempo', 'año', 'mes']):
                x_column = col
            elif any(keyword in col.lower() for keyword in ['toneladas', 'tch', 'brix', 'sacarosa', 'total', 'promedio']):
                y_column = col
        
        if not x_column:
            x_column = available_columns[0] if available_columns else "item"
        if not y_column:
            y_column = available_columns[1] if len(available_columns) > 1 else available_columns[0]
        
        visualization = {
            "type": chart_type,
            "data": {
                "labels": [str(record.get(x_column, f"Item {i}")) for i, record in enumerate(data_for_viz[:10])],
                "datasets": [{
                    "label": y_column or "Valor",
                    "data": [record.get(y_column, 0) for record in data_for_viz[:10]],
                    "backgroundColor": "rgba(59, 130, 246, 0.5)",
                    "borderColor": "rgba(59, 130, 246, 1)",
                    "borderWidth": 1
                }]
            },
            "options": {
                "responsive": True,
                "scales": {
                    "y": {
                        "beginAtZero": True
                    }
                }
            }
        }
        
        # Paso 7: Generar respuesta natural
        natural_response = langchain_chatbot.generate_response(query, data_for_viz, sql_query)
        
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
        olap_engine = get_olap_engine()
        dimensions = olap_engine.get_available_dimensions()
        
        return jsonify({
            "success": True,
            "data": dimensions
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/api/olap/measures')
def get_olap_measures():
    """Obtener medidas disponibles para OLAP"""
    try:
        olap_engine = get_olap_engine()
        measures = olap_engine.get_available_measures()
        
        return jsonify({
            "success": True,
            "data": {
                "measures": measures
            }
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

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
@require_auth
@require_permission('analytics.read')
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

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Error interno del servidor"}), 500

if __name__ == '__main__':
    print("🚀 Iniciando SugarBI Web Application...")
    print("🤖 Chatbot: http://localhost:5001/chatbot")
    print("📊 Dashboard: http://localhost:5001/dashboard")
    print("🌐 API: http://localhost:5001/api/")
    print("📖 Documentación: http://localhost:5001/")
    
    app.run(debug=True, host='0.0.0.0', port=5001)
