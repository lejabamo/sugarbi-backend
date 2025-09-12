"""
Aplicación web principal de SugarBI
Integra chatbot, dashboard, API y sistema de autenticación en una interfaz web completa
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session
from flask_cors import CORS
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

# Configurar CORS de manera segura
try:
    from config.security_config import SecurityConfig
    cors_config = SecurityConfig.get_cors_config()
    CORS(app, **cors_config)
except ImportError:
    CORS(app)

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
    try:
        from config.security_config import SecurityConfig
        return create_engine(SecurityConfig.get_database_uri())
    except ImportError:
        # Fallback a configuración original
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
@app.route('/api/chat', methods=['POST'])
# @require_auth  # Temporalmente deshabilitado para debug
# @audit_log('CHAT_QUERY', 'chatbot')  # Temporalmente deshabilitado para debug
def process_chat_query():
    print("🚀 ENDPOINT EJECUTÁNDOSE")
    """
    Procesa consultas del chatbot y retorna visualizaciones
    
    Ejemplo de request:
    {
        "query": "muestra la cantidad en toneladas de caña producida del top 10 de las fincas en el 2025"
    }
    """
    print("🔍 DEBUG: Iniciando process_chat_query")
    try:
        # Obtener datos JSON (Flask maneja automáticamente la codificación UTF-8)
        print("🔍 DEBUG: Obteniendo datos JSON")
        data = request.get_json(force=True)
        print(f"🔍 DEBUG: Datos recibidos: {data}")
        query = data.get('query', '').strip()
        print(f"🔍 DEBUG: Query extraída: '{query}'")
        
        if not query:
            return jsonify({
                "success": False,
                "error": "Consulta vacía"
            }), 400
        
        # Paso 1: Parsear la consulta
        print("🔍 DEBUG: Parseando consulta")
        intent = query_parser.parse(query)
        print(f"🔍 DEBUG: Intent parseado: {intent}")
        
        # Paso 2: Generar SQL
        print("🔍 DEBUG: Generando SQL")
        sql_query = sql_generator.generate_sql(intent)
        print(f"🔍 DEBUG: SQL generado: {sql_query[:100]}...")
        
        # Paso 3: Ejecutar consulta usando SQLAlchemy directamente
        from sqlalchemy import text
        try:
            result = db.session.execute(text(sql_query))
            df = pd.DataFrame(result.fetchall(), columns=result.keys())
        except Exception as e:
            return jsonify({
                "success": False,
                "error": f"Error ejecutando consulta: {str(e)}"
            }), 500
        
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
        
        print("🔍 DEBUG: Preparando respuesta exitosa")
        response_data = {
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
        }
        print(f"🔍 DEBUG: Respuesta preparada: {response_data}")
        return jsonify(response_data)
        
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
@require_auth
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
            MIN(t.año) as año_inicio,
            MAX(t.año) as año_fin
        FROM hechos_cosecha h
        JOIN dimtiempo t ON h.codigo_tiempo = t.tiempo_id
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
