"""
Módulo de seguridad y protección contra ataques OWASP
"""

import re
import bleach
import validators
from flask import request, current_app
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from functools import wraps
import logging
from datetime import datetime, timedelta
import hashlib
import secrets

# Configurar logging de seguridad
security_logger = logging.getLogger('security')

class SecurityManager:
    """Gestor de seguridad para la aplicación"""
    
    def __init__(self, app=None):
        self.app = app
        self.limiter = None
        if app:
            self.init_app(app)
    
    def init_app(self, app):
        """Inicializar la aplicación con medidas de seguridad"""
        self.app = app
        
        # Configurar rate limiting (aumentado para desarrollo)
        self.limiter = Limiter(
            app=app,
            key_func=get_remote_address,
            default_limits=["10000 per hour", "1000 per minute"]
        )
        
        # Configurar headers de seguridad
        self.setup_security_headers()
        
        # Configurar logging de seguridad
        self.setup_security_logging()
    
    def setup_security_headers(self):
        """Configurar headers de seguridad"""
        @self.app.after_request
        def set_security_headers(response):
            # Prevenir clickjacking
            response.headers['X-Frame-Options'] = 'DENY'
            
            # Prevenir MIME type sniffing
            response.headers['X-Content-Type-Options'] = 'nosniff'
            
            # Habilitar XSS protection
            response.headers['X-XSS-Protection'] = '1; mode=block'
            
            # Política de referrer
            response.headers['Referrer-Policy'] = 'strict-origin-when-cross-origin'
            
            # Content Security Policy
            csp = (
                "default-src 'self'; "
                "script-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "style-src 'self' 'unsafe-inline' https://cdn.jsdelivr.net https://cdnjs.cloudflare.com; "
                "img-src 'self' data: https:; "
                "font-src 'self' https://cdnjs.cloudflare.com; "
                "connect-src 'self'; "
                "frame-ancestors 'none';"
            )
            response.headers['Content-Security-Policy'] = csp
            
            # HSTS (solo en producción con HTTPS)
            if self.app.config.get('ENV') == 'production':
                response.headers['Strict-Transport-Security'] = 'max-age=31536000; includeSubDomains'
            
            return response
    
    def setup_security_logging(self):
        """Configurar logging de seguridad"""
        if not self.app.debug:
            import os
            # Crear directorio de logs si no existe
            os.makedirs('logs', exist_ok=True)
            security_handler = logging.FileHandler('logs/security.log')
            security_handler.setLevel(logging.WARNING)
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            security_handler.setFormatter(formatter)
            security_logger.addHandler(security_handler)
    
    def log_security_event(self, event_type, details, user_id=None, ip_address=None):
        """Registrar evento de seguridad"""
        log_data = {
            'event_type': event_type,
            'details': details,
            'user_id': user_id,
            'ip_address': ip_address or get_remote_address(),
            'user_agent': request.headers.get('User-Agent'),
            'timestamp': datetime.utcnow().isoformat()
        }
        
        security_logger.warning(f"Security Event: {log_data}")
    
    def validate_input(self, data, input_type='text'):
        """Validar y sanitizar input del usuario"""
        if not data:
            return None
        
        # Sanitizar HTML
        if input_type == 'html':
            allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br']
            data = bleach.clean(data, tags=allowed_tags, strip=True)
        
        # Validar email
        elif input_type == 'email':
            if not validators.email(data):
                raise ValueError("Email inválido")
        
        # Validar URL
        elif input_type == 'url':
            if not validators.url(data):
                raise ValueError("URL inválida")
        
        # Validar SQL injection patterns
        sql_patterns = [
            r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
            r"(--|#|/\*|\*/)",
            r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
            r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
        ]
        
        for pattern in sql_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                self.log_security_event('SQL_INJECTION_ATTEMPT', {
                    'input': data,
                    'pattern': pattern
                })
                raise ValueError("Input contiene patrones sospechosos")
        
        # Validar XSS patterns
        xss_patterns = [
            r"<script[^>]*>.*?</script>",
            r"javascript:",
            r"on\w+\s*=",
            r"<iframe[^>]*>",
            r"<object[^>]*>",
            r"<embed[^>]*>",
        ]
        
        for pattern in xss_patterns:
            if re.search(pattern, data, re.IGNORECASE):
                self.log_security_event('XSS_ATTEMPT', {
                    'input': data,
                    'pattern': pattern
                })
                raise ValueError("Input contiene patrones XSS")
        
        return data.strip()
    
    def generate_csrf_token(self):
        """Generar token CSRF"""
        return secrets.token_urlsafe(32)
    
    def verify_csrf_token(self, token, session_token):
        """Verificar token CSRF"""
        return token and session_token and token == session_token

# Decoradores de seguridad
def require_auth(f):
    """Decorador para requerir autenticación"""
    @wraps(f)
    def decorated_function(*args, **kwargs):
        from flask_login import current_user
        from flask import jsonify
        if not current_user.is_authenticated:
            return jsonify({'error': 'Autenticación requerida'}), 401
        return f(*args, **kwargs)
    return decorated_function

def require_permission(permission):
    """Decorador para requerir permiso específico"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            from flask import jsonify
            if not current_user.is_authenticated:
                return jsonify({'error': 'Autenticación requerida'}), 401
            if not current_user.has_permission(permission):
                return jsonify({'error': 'Permiso insuficiente'}), 403
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def rate_limit(limit):
    """Decorador para rate limiting personalizado"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            # Implementar rate limiting personalizado si es necesario
            return f(*args, **kwargs)
        return decorated_function
    return decorator

def audit_log(action, resource=None):
    """Decorador para logging de auditoría"""
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            from flask_login import current_user
            from auth.models import AuditLog, db
            
            result = f(*args, **kwargs)
            
            # Registrar en log de auditoría
            if current_user.is_authenticated:
                audit_entry = AuditLog(
                    user_id=current_user.id,
                    action=action,
                    resource=resource,
                    ip_address=get_remote_address(),
                    user_agent=request.headers.get('User-Agent')
                )
                db.session.add(audit_entry)
                db.session.commit()
            
            return result
        return decorated_function
    return decorator

# Funciones de validación específicas
def validate_input(data, input_type='text'):
    """Validar y sanitizar input del usuario"""
    if not data:
        return None
    
    # Sanitizar HTML
    if input_type == 'html':
        allowed_tags = ['b', 'i', 'em', 'strong', 'p', 'br']
        data = bleach.clean(data, tags=allowed_tags, strip=True)
    
    # Validar email
    elif input_type == 'email':
        if not validators.email(data):
            raise ValueError("Email inválido")
    
    # Validar URL
    elif input_type == 'url':
        if not validators.url(data):
            raise ValueError("URL inválida")
    
    # Validar SQL injection patterns
    sql_patterns = [
        r"(\b(SELECT|INSERT|UPDATE|DELETE|DROP|CREATE|ALTER|EXEC|UNION|SCRIPT)\b)",
        r"(--|#|/\*|\*/)",
        r"(\b(OR|AND)\s+\d+\s*=\s*\d+)",
        r"(\b(OR|AND)\s+'.*'\s*=\s*'.*')",
    ]
    
    for pattern in sql_patterns:
        if re.search(pattern, data, re.IGNORECASE):
            raise ValueError("Input contiene patrones sospechosos")
    
    # Validar XSS patterns
    xss_patterns = [
        r"<script[^>]*>.*?</script>",
        r"javascript:",
        r"on\w+\s*=",
        r"<iframe[^>]*>",
        r"<object[^>]*>",
        r"<embed[^>]*>",
    ]
    
    for pattern in xss_patterns:
        if re.search(pattern, data, re.IGNORECASE):
            raise ValueError("Input contiene patrones XSS")
    
    return data.strip()

def validate_password_strength(password):
    """Validar fortaleza de contraseña"""
    if len(password) < 8:
        return False, "La contraseña debe tener al menos 8 caracteres"
    
    if not re.search(r"[A-Z]", password):
        return False, "La contraseña debe contener al menos una mayúscula"
    
    if not re.search(r"[a-z]", password):
        return False, "La contraseña debe contener al menos una minúscula"
    
    if not re.search(r"\d", password):
        return False, "La contraseña debe contener al menos un número"
    
    if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", password):
        return False, "La contraseña debe contener al menos un carácter especial"
    
    return True, "Contraseña válida"

def validate_username(username):
    """Validar nombre de usuario"""
    if len(username) < 3 or len(username) > 20:
        return False, "El nombre de usuario debe tener entre 3 y 20 caracteres"
    
    if not re.match(r"^[a-zA-Z0-9_]+$", username):
        return False, "El nombre de usuario solo puede contener letras, números y guiones bajos"
    
    return True, "Nombre de usuario válido"

# Configuración de permisos por defecto
DEFAULT_PERMISSIONS = {
    'admin': [
        'user.create', 'user.read', 'user.update', 'user.delete',
        'role.create', 'role.read', 'role.update', 'role.delete',
        'data.read', 'data.write', 'data.delete',
        'analytics.read', 'analytics.write',
        'system.admin'
    ],
    'analyst': [
        'data.read', 'analytics.read', 'analytics.write'
    ],
    'viewer': [
        'data.read', 'analytics.read'
    ]
}

# Inicializar el gestor de seguridad
security_manager = SecurityManager()

