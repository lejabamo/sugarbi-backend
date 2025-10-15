"""
Aplicación web principal de SugarBI
Integra chatbot, dashboard, API y sistema de autenticación en una interfaz web completa
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_cors import CORS, cross_origin
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import sys
import os
import secrets
from pathlib import Path

# Agregar el directorio raíz al path para importar módulos
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from chatbot.query_parser import QueryParser
from chatbot.sql_generator import SQLGenerator
from chatbot.sql_agent import SugarBISQLAgent
from dashboard.visualization_engine import VisualizationEngine, ChartConfig, ChartType
from auth.models import db, User, Role, SessionToken, AuditLog
from auth.security import security_manager, require_auth, require_permission, audit_log
from auth.forms import LoginForm, RegisterForm
import pandas as pd
import numpy as np
from sqlalchemy import create_engine
import configparser
from datetime import datetime, timedelta

# Configuración de la aplicación
app = Flask(__name__)

# Configuración de seguridad - usar configuración por defecto
app.config['SECRET_KEY'] = secrets.token_hex(32)
app.config['SESSION_COOKIE_SECURE'] = False
app.config['SESSION_COOKIE_HTTPONLY'] = True
app.config['SESSION_COOKIE_SAMESITE'] = 'Lax'
app.config['PERMANENT_SESSION_LIFETIME'] = 3600
# Configuración de base de datos
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root:toor@localhost:3306/sugarbi'

app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['JSON_AS_ASCII'] = False
app.config['JSONIFY_PRETTYPRINT_REGULAR'] = True

# Inicializar extensiones
db.init_app(app)
login_manager = LoginManager()
login_manager.init_app(app)
login_manager.login_view = 'login'
login_manager.login_message = 'Por favor, inicia sesión para acceder a esta página.'
login_manager.login_message_category = 'info'

# Configurar CORS para permitir frontend
CORS(app, 
     origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5000'],
     supports_credentials=True,
     allow_headers=['Content-Type', 'Authorization', 'X-Requested-With'],
     methods=['GET', 'POST', 'PUT', 'DELETE', 'OPTIONS'],
     expose_headers=['Content-Range', 'X-Content-Range'])

# Inicializar gestor de seguridad
security_manager.init_app(app)

# Callback para cargar usuarios
@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# Inicializar componentes
query_parser = QueryParser()
sql_generator = SQLGenerator()
viz_engine = VisualizationEngine()

# Configuración de la base de datos
def get_db_connection():
    """Crear conexión a la base de datos"""
    # Usar configuración directa del archivo config.ini
    ruta_base = Path(__file__).parent.parent
    config = configparser.ConfigParser()
    config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
    
    db_config = config['mysql']
    cadena_conexion = (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )
    return create_engine(cadena_conexion)

# Inicializar agente SQL con LangChain
def get_sql_agent():
    """Obtener instancia del agente SQL"""
    try:
        # Obtener configuración de base de datos
        ruta_base = Path(__file__).parent.parent
        config = configparser.ConfigParser()
        config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
        
        db_config = config['mysql']
        database_url = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        
        # Obtener API key de OpenAI (opcional)
        openai_api_key = os.getenv('OPENAI_API_KEY')
        
        return SugarBISQLAgent(database_url, openai_api_key)
    except Exception as e:
        print(f"Error inicializando agente SQL: {e}")
        return None

# Rutas principales
@app.route('/')
def index():
    """Página principal del dashboard"""
    return render_template('index_clean.html')

@app.route('/chatbot')
def chatbot_page():
    """Página del chatbot"""
    return render_template('chatbot_clean.html')

@app.route('/dashboard')
def dashboard_page():
    """Página del dashboard"""
    return render_template('dashboard_clean.html')

@app.route('/dashboard-alternativo')
def dashboard_alternativo():
    """Dashboard integrado con chatbot y visualizaciones"""
    return render_template('dashboard_alternativo_clean.html')

@app.route('/olap')
@login_required
def olap_dashboard():
    """Dashboard OLAP para análisis multidimensional"""
    return render_template('olap_dashboard.html')

@app.route('/olap-interactive')
@login_required
def olap_interactive():
    """Dashboard OLAP interactivo"""
    return render_template('olap_interactive.html')

@app.route('/olap-analytics')
@login_required
def olap_analytics():
    """Dashboard OLAP con análisis avanzado"""
    return render_template('olap_analytics.html')

# Rutas de autenticación
@app.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            remember_me = request.form.get('remember_me') == 'on'
            
            if not username or not password:
                flash('Por favor completa todos los campos', 'error')
                return render_template('auth/login_simple.html')
            
            # Buscar usuario
            user = User.query.filter_by(username=username).first()
            
            if user is None or not user.check_password(password):
                # Incrementar intentos de login
                if user:
                    user.increment_login_attempts()
                    security_manager.log_security_event('FAILED_LOGIN', {
                        'username': username,
                        'reason': 'invalid_password'
                    }, user.id)
                else:
                    security_manager.log_security_event('FAILED_LOGIN', {
                        'username': username,
                        'reason': 'user_not_found'
                    })
                
                flash('Usuario o contraseña inválidos', 'error')
                return render_template('auth/login_simple.html')
            
            # Verificar si la cuenta está bloqueada
            if user.is_locked():
                security_manager.log_security_event('BLOCKED_LOGIN_ATTEMPT', {
                    'username': username,
                    'reason': 'account_locked'
                }, user.id)
                flash('Cuenta bloqueada temporalmente. Intenta más tarde.', 'error')
                return render_template('auth/login_simple.html')
            
            # Verificar si el usuario está activo
            if not user.is_active:
                security_manager.log_security_event('INACTIVE_LOGIN_ATTEMPT', {
                    'username': username,
                    'reason': 'account_inactive'
                }, user.id)
                flash('Cuenta desactivada. Contacta al administrador.', 'error')
                return render_template('auth/login_simple.html')
            
            # Login exitoso
            login_user(user, remember=remember_me)
            user.reset_login_attempts()
            
            # Crear token de sesión
            token = SessionToken.generate_token()
            session_token = SessionToken(
                token=token,
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(hours=24),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(session_token)
            db.session.commit()
            
            # Registrar evento de seguridad
            security_manager.log_security_event('SUCCESSFUL_LOGIN', {
                'username': user.username,
                'ip_address': request.remote_addr
            }, user.id)
            
            flash(f'¡Bienvenido, {user.username}!', 'success')
            
            # Redirigir a la página solicitada o al dashboard
            next_page = request.args.get('next')
            if not next_page or not next_page.startswith('/'):
                next_page = url_for('index')
            return redirect(next_page)
            
        except Exception as e:
            flash('Error interno del servidor. Intenta más tarde.', 'error')
            security_manager.log_security_event('LOGIN_ERROR', {
                'error': str(e),
                'username': request.form.get('username', '')
            })
    
    return render_template('auth/login_simple.html')

@app.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    username = current_user.username
    
    # Invalidar tokens de sesión
    SessionToken.query.filter_by(user_id=current_user.id, is_active=True).update({'is_active': False})
    db.session.commit()
    
    # Registrar evento de seguridad
    security_manager.log_security_event('LOGOUT', {
        'username': username
    }, current_user.id)
    
    logout_user()
    flash('Has cerrado sesión correctamente.', 'info')
    return redirect(url_for('login'))

@app.route('/register', methods=['GET', 'POST'])
def register():
    """Página de registro"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = RegisterForm()
    
    if form.validate_on_submit():
        try:
            # Verificar si el usuario ya existe
            if User.query.filter_by(username=form.username.data).first():
                flash('El nombre de usuario ya está en uso.', 'error')
                return render_template('auth/register.html', form=form)
            
            if User.query.filter_by(email=form.email.data).first():
                flash('El email ya está registrado.', 'error')
                return render_template('auth/register.html', form=form)
            
            # Crear nuevo usuario
            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                is_active=True
            )
            user.set_password(form.password.data)
            
            # Asignar rol por defecto (viewer)
            default_role = Role.query.filter_by(name='viewer').first()
            if not default_role:
                # Crear rol por defecto si no existe
                default_role = Role(
                    name='viewer',
                    description='Usuario con permisos de solo lectura',
                    permissions=['data.read', 'analytics.read']
                )
                db.session.add(default_role)
                db.session.flush()
            
            user.role_id = default_role.id
            
            db.session.add(user)
            db.session.commit()
            
            # Registrar evento de seguridad
            security_manager.log_security_event('USER_REGISTERED', {
                'username': user.username,
                'email': user.email
            }, user.id)
            
            flash('¡Registro exitoso! Ya puedes iniciar sesión.', 'success')
            return redirect(url_for('login'))
            
        except Exception as e:
            db.session.rollback()
            flash('Error al crear la cuenta. Intenta más tarde.', 'error')
            security_manager.log_security_event('REGISTRATION_ERROR', {
                'error': str(e),
                'username': form.username.data
            })
    
    return render_template('auth/register.html', form=form)

# API Endpoints
@app.route('/api/chat', methods=['POST', 'OPTIONS'])
@cross_origin(origins=['http://localhost:5173'], supports_credentials=True)
# @require_auth  # Temporalmente deshabilitado para debug
# @audit_log('CHAT_QUERY', 'chatbot')  # Temporalmente deshabilitado para debug
def process_chat_query():
    """
    Procesa consultas del chatbot usando LangChain SQL Agent
    Convierte lenguaje natural a SQL y ejecuta consultas inteligentes
    
    Ejemplo de request:
    {
        "query": "¿cuáles son las 5 mejores variedades por TCH?"
    }
    """
    # Manejar peticiones OPTIONS para CORS
    if request.method == 'OPTIONS':
        return '', 200
    
    try:
        # Obtener datos JSON
        data = request.get_json(force=True)
        query = data.get('query', '').strip()
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Consulta vacía"
            }), 400
        
        print(f"🤖 Procesando consulta: {query}")
        
        # Obtener agente SQL
        sql_agent = get_sql_agent()
        if not sql_agent:
            return jsonify({
                "success": False,
                "error": "Error inicializando agente SQL"
            }), 500
        
        # Procesar consulta con LangChain
        result = sql_agent.process_question(query)
        
        if not result["success"]:
            return jsonify({
                "success": False,
                "error": result.get("error", "Error desconocido"),
                "natural_response": result.get("natural_response", "Lo siento, hubo un error al procesar tu consulta.")
            }), 500
        
        # Retornar respuesta completa
        return jsonify({
            "success": True,
            "query": result["query"],
            "intent": result["intent"],
            "sql": result["sql"],
            "visualization": result["visualization"],
            "raw_data": result["data"],
            "record_count": result["row_count"],
            "natural_response": result["natural_response"]
        })
        
    except Exception as e:
        print(f"❌ Error en process_chat_query: {e}")
        return jsonify({
            "success": False,
            "error": f"Error interno: {str(e)}",
            "natural_response": "Lo siento, hubo un error inesperado. Por favor, inténtalo de nuevo."
        }), 500

# Endpoint para obtener estadísticas generales
@app.route('/api/query/parse', methods=['POST'])
@require_auth
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
@require_auth
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
# @require_auth  # Temporalmente deshabilitado para pruebas
def get_estadisticas():
    """Obtener estadísticas generales del data mart"""
    try:
        from sqlalchemy import text
        
        # Estadísticas generales
        stats = {}
        
        # Total de registros por tabla
        tables = ['dimfinca', 'dimvariedad', 'dimzona', 'dimtiempo', 'hechos_cosecha']
        for table in tables:
            query = f"SELECT COUNT(*) as total FROM {table}"
            result = db.session.execute(text(query))
            stats[f"total_{table}"] = int(result.fetchone()[0])
        
        # Estadísticas de cosecha
        query = """
        SELECT 
            COUNT(*) as total_cosechas,
            SUM(toneladas_cana_molida) as total_toneladas,
            AVG(tch) as promedio_tch,
            AVG(brix) as promedio_brix,
            AVG(sacarosa) as promedio_sacarosa,
            MIN(t.anio) as año_inicio,
            MAX(t.anio) as año_fin
        FROM hechos_cosecha h
        JOIN dimtiempo t ON CAST(h.codigo_tiempo AS SIGNED) = t.tiempo_id
        """
        result = db.session.execute(text(query))
        row = result.fetchone()
        
        # Convertir valores a tipos nativos de Python para serialización JSON
        cosecha_stats = {
            'total_cosechas': int(row[0]) if row[0] else 0,
            'total_toneladas': float(row[1]) if row[1] else 0,
            'promedio_tch': float(row[2]) if row[2] else 0,
            'promedio_brix': float(row[3]) if row[3] else 0,
            'promedio_sacarosa': float(row[4]) if row[4] else 0,
            'año_inicio': int(row[5]) if row[5] else None,
            'año_fin': int(row[6]) if row[6] else None
        }
        stats.update(cosecha_stats)
        
        return jsonify({
            "success": True,
            "data": stats
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

# ===== ENDPOINTS DE AUTENTICACIÓN API =====
@app.route('/auth/api/login', methods=['POST'])
def api_login():
    """Endpoint de login para API"""
    try:
        data = request.get_json()
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                "success": False,
                "error": "Username y password son requeridos"
            }), 400
        
        # Buscar usuario en la base de datos
        user = User.query.filter_by(username=username).first()
        
        if user and user.check_password(password):
            # Iniciar sesión
            login_user(user, remember=True)
            
            return jsonify({
                "success": True,
                "message": "Login exitoso",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.name if user.role else None
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "Credenciales inválidas"
            }), 401
            
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/auth/api/logout', methods=['POST'])
@login_required
def api_logout():
    """Endpoint de logout para API"""
    try:
        logout_user()
        return jsonify({
            "success": True,
            "message": "Logout exitoso"
        })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

@app.route('/auth/api/user/me')
def api_user_me():
    """Obtener información del usuario actual"""
    try:
        if current_user.is_authenticated:
            return jsonify({
                "success": True,
                "user": {
                    "id": current_user.id,
                    "username": current_user.username,
                    "email": current_user.email,
                    "role": current_user.role.name if current_user.role else None
                }
            })
        else:
            return jsonify({
                "success": False,
                "error": "No hay sesión activa"
            })
    except Exception as e:
        return jsonify({
            "success": False,
            "error": str(e)
        }), 500

# ===== ENDPOINTS DE DIMENSIONES =====
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
        
        query = f"""
        SELECT 
            f.nombre_finca,
            v.nombre_variedad,
            z.nombre_zona,
            t.anio,
            t.mes,
            h.toneladas_cana_molida,
            h.tch,
            h.brix,
            h.sacarosa,
            h.rendimiento_teorico
        FROM hechos_cosecha h
        JOIN dimfinca f ON h.id_finca = f.finca_id
        JOIN dimvariedad v ON h.codigo_variedad = v.variedad_id
        JOIN dimzona z ON h.codigo_zona = z.codigo_zona
        JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
        ORDER BY {criterios_map[criterio]} DESC
        LIMIT {limit}
        """
        
        result = pd.read_sql(query, engine)
        
        return jsonify({
            "success": True,
            "data": result.to_dict('records'),
            "criterio": criterio,
            "total": len(result)
        })
        
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@app.route('/api/examples')
@require_auth
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

# Manejo de errores
@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Error interno del servidor"}), 500

# Contexto de aplicación para crear tablas
def create_tables():
    """Crear tablas de autenticación si no existen"""
    with app.app_context():
        try:
            # Crear todas las tablas
            db.create_all()
            
            # Crear roles por defecto si no existen
            if not Role.query.filter_by(name='admin').first():
                admin_role = Role(
                    name='admin',
                    description='Administrador del sistema',
                    permissions=['user.create', 'user.read', 'user.update', 'user.delete',
                               'role.create', 'role.read', 'role.update', 'role.delete',
                               'data.read', 'data.write', 'data.delete',
                               'analytics.read', 'analytics.write', 'system.admin']
                )
                db.session.add(admin_role)
            
            if not Role.query.filter_by(name='analyst').first():
                analyst_role = Role(
                    name='analyst',
                    description='Analista de datos',
                    permissions=['data.read', 'analytics.read', 'analytics.write']
                )
                db.session.add(analyst_role)
            
            if not Role.query.filter_by(name='viewer').first():
                viewer_role = Role(
                    name='viewer',
                    description='Usuario con permisos de solo lectura',
                    permissions=['data.read', 'analytics.read']
                )
                db.session.add(viewer_role)
            
            # Crear usuario administrador por defecto si no existe
            if not User.query.filter_by(username='admin').first():
                admin_user = User(
                    username='admin',
                    email='admin@sugarbi.com',
                    first_name='Administrador',
                    last_name='Sistema',
                    is_active=True,
                    is_admin=True
                )
                admin_user.set_password('admin123')  # Cambiar en producción
                admin_role = Role.query.filter_by(name='admin').first()
                admin_user.role_id = admin_role.id
                db.session.add(admin_user)
            
            db.session.commit()
            print("✅ Tablas de autenticación creadas/actualizadas correctamente")
            
        except Exception as e:
            print(f"❌ Error al crear tablas: {str(e)}")
            db.session.rollback()

if __name__ == '__main__':
    print("🚀 Iniciando SugarBI Web Application...")
    print("🔐 Sistema de autenticación integrado")
    print("🤖 Chatbot: http://localhost:5001/chatbot")
    print("📊 Dashboard: http://localhost:5001/dashboard")
    print("📊 Dashboard Integrado: http://localhost:5001/dashboard-alternativo")
    print("🔍 OLAP: http://localhost:5001/olap")
    print("🌐 API: http://localhost:5001/api/")
    print("📖 Documentación: http://localhost:5001/")
    print("🔑 Login: http://localhost:5001/login")
    
    # Crear tablas de autenticación (ya creadas manualmente)
    # create_tables()
    
    app.run(debug=True, host='0.0.0.0', port=5001)
