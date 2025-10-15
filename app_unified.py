"""
SugarBI - Aplicación Unificada
Backend Flask que sirve tanto API REST como Frontend React desde un solo servidor
"""

from flask import Flask, render_template, request, jsonify, redirect, url_for, flash, session, send_from_directory
from flask_cors import CORS
from flask_login import LoginManager, login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
import sys
import os
import secrets
from pathlib import Path
import pandas as pd
import numpy as np
from sqlalchemy import create_engine, text
import configparser
from datetime import datetime, timedelta

# Agregar el directorio raíz al path para importar módulos
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

# Importar módulos del proyecto
from chatbot.query_parser import QueryParser
from chatbot.sql_generator import SQLGenerator
from dashboard.visualization_engine import VisualizationEngine, ChartConfig, ChartType
from auth.models import db, User, Role, SessionToken, AuditLog
from auth.security import security_manager, require_auth, require_permission, audit_log
from auth.forms import LoginForm, RegisterForm

# Configuración de la aplicación
app = Flask(__name__, 
            static_folder='../sugarBI-frontend/dist',
            template_folder='../sugarBI-frontend/dist')

# Configuración de seguridad
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

# Configurar CORS
CORS(app, origins=['http://localhost:3000', 'http://localhost:5173', 'http://localhost:5000'])

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
        ruta_base = Path(__file__).parent
        config = configparser.ConfigParser()
        config.read(ruta_base / 'config' / 'config.ini', encoding='utf-8')
        
        db_config = config['mysql']
        cadena_conexion = (
            f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
            f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
        )
        return create_engine(cadena_conexion)

# ===== RUTAS PRINCIPALES =====

@app.route('/')
def index():
    """Página principal - servir React app"""
    return send_from_directory(app.static_folder, 'index.html')

@app.route('/<path:path>')
def serve_react(path):
    """Servir archivos estáticos de React"""
    if os.path.exists(os.path.join(app.static_folder, path)):
        return send_from_directory(app.static_folder, path)
    else:
        # Para React Router, servir index.html
        return send_from_directory(app.static_folder, 'index.html')

# ===== RUTAS DE AUTENTICACIÓN =====

@app.route('/auth/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect('/')
    
    if request.method == 'POST':
        try:
            username = request.form.get('username')
            password = request.form.get('password')
            remember_me = request.form.get('remember_me') == 'on'
            
            if not username or not password:
                return jsonify({
                    "success": False,
                    "error": "Por favor completa todos los campos"
                }), 400
            
            # Buscar usuario
            user = User.query.filter_by(username=username).first()
            
            if user is None or not user.check_password(password):
                if user:
                    user.increment_login_attempts()
                    security_manager.log_security_event('FAILED_LOGIN', {
                        'username': username,
                        'reason': 'invalid_password'
                    }, user.id)
                
                return jsonify({
                    "success": False,
                    "error": "Usuario o contraseña inválidos"
                }), 401
            
            # Verificar si la cuenta está bloqueada
            if user.is_locked():
                security_manager.log_security_event('BLOCKED_LOGIN_ATTEMPT', {
                    'username': username,
                    'reason': 'account_locked'
                }, user.id)
                return jsonify({
                    "success": False,
                    "error": "Cuenta bloqueada temporalmente. Intenta más tarde."
                }), 403
            
            # Verificar si el usuario está activo
            if not user.is_active:
                security_manager.log_security_event('INACTIVE_LOGIN_ATTEMPT', {
                    'username': username,
                    'reason': 'account_inactive'
                }, user.id)
                return jsonify({
                    "success": False,
                    "error": "Cuenta desactivada. Contacta al administrador."
                }), 403
            
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
            
            return jsonify({
                "success": True,
                "message": f"¡Bienvenido, {user.username}!",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                    "role": user.role.name if user.role else None
                }
            })
            
        except Exception as e:
            security_manager.log_security_event('LOGIN_ERROR', {
                'error': str(e),
                'username': request.form.get('username', '')
            })
            return jsonify({
                "success": False,
                "error": "Error interno del servidor. Intenta más tarde."
            }), 500
    
    return jsonify({"success": False, "error": "Método no permitido"}), 405

@app.route('/auth/logout', methods=['POST'])
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
    return jsonify({
        "success": True,
        "message": "Has cerrado sesión correctamente."
    })

@app.route('/auth/register', methods=['POST'])
def register():
    """Registro de usuarios"""
    if current_user.is_authenticated:
        return jsonify({
            "success": False,
            "error": "Ya hay una sesión activa"
        }), 400
    
    try:
        data = request.get_json()
        username = data.get('username')
        email = data.get('email')
        password = data.get('password')
        first_name = data.get('first_name', '')
        last_name = data.get('last_name', '')
        
        if not all([username, email, password]):
            return jsonify({
                "success": False,
                "error": "Todos los campos son requeridos"
            }), 400
        
        # Verificar si el usuario ya existe
        if User.query.filter_by(username=username).first():
            return jsonify({
                "success": False,
                "error": "El nombre de usuario ya está en uso."
            }), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({
                "success": False,
                "error": "El email ya está registrado."
            }), 400
        
        # Crear nuevo usuario
        user = User(
            username=username,
            email=email,
            first_name=first_name,
            last_name=last_name,
            is_active=True
        )
        user.set_password(password)
        
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
        
        return jsonify({
            "success": True,
            "message": "¡Registro exitoso! Ya puedes iniciar sesión."
        })
        
    except Exception as e:
        db.session.rollback()
        security_manager.log_security_event('REGISTRATION_ERROR', {
            'error': str(e),
            'username': data.get('username', '')
        })
        return jsonify({
            "success": False,
            "error": "Error al crear la cuenta. Intenta más tarde."
        }), 500

@app.route('/auth/me')
@login_required
def get_current_user():
    """Obtener información del usuario actual"""
    return jsonify({
        "success": True,
        "user": {
            "id": current_user.id,
            "username": current_user.username,
            "email": current_user.email,
            "first_name": current_user.first_name,
            "last_name": current_user.last_name,
            "role": current_user.role.name if current_user.role else None,
            "is_active": current_user.is_active
        }
    })

# ===== API ENDPOINTS =====

@app.route('/api/chat', methods=['POST'])
def process_chat_query():
    """Procesa consultas del chatbot y retorna visualizaciones"""
    try:
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
        return jsonify(response_data)
        
    except Exception as e:
        import traceback
        print(f"Error en /api/chat: {str(e)}")
        print(f"Traceback: {traceback.format_exc()}")
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

@app.route('/api/estadisticas')
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

# ===== MANEJO DE ERRORES =====

@app.errorhandler(404)
def not_found(error):
    return jsonify({"success": False, "error": "Endpoint no encontrado"}), 404

@app.errorhandler(500)
def internal_error(error):
    return jsonify({"success": False, "error": "Error interno del servidor"}), 500

# ===== INICIALIZACIÓN =====

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
    print("🚀 Iniciando SugarBI Unificado...")
    print("🔐 Sistema de autenticación integrado")
    print("🤖 Chatbot API: http://localhost:5000/api/chat")
    print("📊 Estadísticas: http://localhost:5000/api/estadisticas")
    print("🌐 Frontend React: http://localhost:5000/")
    print("🔑 Auth: http://localhost:5000/auth/login")
    
    # Crear tablas de autenticación
    create_tables()
    
    app.run(debug=True, host='0.0.0.0', port=5000)
