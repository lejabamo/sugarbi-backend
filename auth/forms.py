"""
Formularios de autenticación con validación de seguridad
"""

from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SelectField, TextAreaField
from wtforms.validators import DataRequired, Email, Length, EqualTo, ValidationError
from auth.security import validate_password_strength, validate_username, validate_input
from auth.models import User, Role

class LoginForm(FlaskForm):
    """Formulario de login"""
    username = StringField('Usuario', validators=[
        DataRequired(message='El nombre de usuario es requerido'),
        Length(min=3, max=20, message='El nombre de usuario debe tener entre 3 y 20 caracteres')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida')
    ])
    remember_me = BooleanField('Recordarme')
    
    def validate_username(self, field):
        """Validar nombre de usuario"""
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
    
    def validate_password(self, field):
        """Validar contraseña"""
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))

class RegisterForm(FlaskForm):
    """Formulario de registro"""
    username = StringField('Usuario', validators=[
        DataRequired(message='El nombre de usuario es requerido'),
        Length(min=3, max=20, message='El nombre de usuario debe tener entre 3 y 20 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='El email es requerido'),
        Email(message='Email inválido')
    ])
    first_name = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])
    last_name = StringField('Apellido', validators=[
        DataRequired(message='El apellido es requerido'),
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])
    password = PasswordField('Contraseña', validators=[
        DataRequired(message='La contraseña es requerida'),
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    password2 = PasswordField('Confirmar Contraseña', validators=[
        DataRequired(message='La confirmación de contraseña es requerida'),
        EqualTo('password', message='Las contraseñas no coinciden')
    ])
    role_id = SelectField('Rol', coerce=int, validators=[
        DataRequired(message='El rol es requerido')
    ])
    
    def __init__(self, *args, **kwargs):
        super(RegisterForm, self).__init__(*args, **kwargs)
        # Cargar roles disponibles
        self.role_id.choices = [(role.id, role.name) for role in Role.query.all()]
    
    def validate_username(self, field):
        """Validar nombre de usuario"""
        # Validar formato
        is_valid, message = validate_username(field.data)
        if not is_valid:
            raise ValidationError(message)
        
        # Validar seguridad
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Verificar si ya existe
        if User.query.filter_by(username=field.data).first():
            raise ValidationError('El nombre de usuario ya está en uso')
    
    def validate_email(self, field):
        """Validar email"""
        # Validar formato
        try:
            validate_input(field.data, 'email')
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Verificar si ya existe
        if User.query.filter_by(email=field.data).first():
            raise ValidationError('El email ya está registrado')
    
    def validate_password(self, field):
        """Validar contraseña"""
        # Validar seguridad
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Validar fortaleza
        is_valid, message = validate_password_strength(field.data)
        if not is_valid:
            raise ValidationError(message)
    
    def validate_first_name(self, field):
        """Validar nombre"""
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
    
    def validate_last_name(self, field):
        """Validar apellido"""
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))

class ChangePasswordForm(FlaskForm):
    """Formulario para cambiar contraseña"""
    current_password = PasswordField('Contraseña Actual', validators=[
        DataRequired(message='La contraseña actual es requerida')
    ])
    new_password = PasswordField('Nueva Contraseña', validators=[
        DataRequired(message='La nueva contraseña es requerida'),
        Length(min=8, message='La contraseña debe tener al menos 8 caracteres')
    ])
    new_password2 = PasswordField('Confirmar Nueva Contraseña', validators=[
        DataRequired(message='La confirmación de contraseña es requerida'),
        EqualTo('new_password', message='Las contraseñas no coinciden')
    ])
    
    def validate_current_password(self, field):
        """Validar contraseña actual"""
        from flask_login import current_user
        if not current_user.check_password(field.data):
            raise ValidationError('La contraseña actual es incorrecta')
    
    def validate_new_password(self, field):
        """Validar nueva contraseña"""
        # Validar seguridad
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Validar fortaleza
        is_valid, message = validate_password_strength(field.data)
        if not is_valid:
            raise ValidationError(message)
        
        # Verificar que no sea igual a la actual
        from flask_login import current_user
        if current_user.check_password(field.data):
            raise ValidationError('La nueva contraseña debe ser diferente a la actual')

class UserEditForm(FlaskForm):
    """Formulario para editar usuario"""
    username = StringField('Usuario', validators=[
        DataRequired(message='El nombre de usuario es requerido'),
        Length(min=3, max=20, message='El nombre de usuario debe tener entre 3 y 20 caracteres')
    ])
    email = StringField('Email', validators=[
        DataRequired(message='El email es requerido'),
        Email(message='Email inválido')
    ])
    first_name = StringField('Nombre', validators=[
        DataRequired(message='El nombre es requerido'),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])
    last_name = StringField('Apellido', validators=[
        DataRequired(message='El apellido es requerido'),
        Length(min=2, max=50, message='El apellido debe tener entre 2 y 50 caracteres')
    ])
    role_id = SelectField('Rol', coerce=int, validators=[
        DataRequired(message='El rol es requerido')
    ])
    is_active = BooleanField('Usuario Activo')
    
    def __init__(self, user_id=None, *args, **kwargs):
        super(UserEditForm, self).__init__(*args, **kwargs)
        self.user_id = user_id
        # Cargar roles disponibles
        self.role_id.choices = [(role.id, role.name) for role in Role.query.all()]
    
    def validate_username(self, field):
        """Validar nombre de usuario"""
        # Validar formato
        is_valid, message = validate_username(field.data)
        if not is_valid:
            raise ValidationError(message)
        
        # Validar seguridad
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Verificar si ya existe (excluyendo el usuario actual)
        existing_user = User.query.filter_by(username=field.data).first()
        if existing_user and existing_user.id != self.user_id:
            raise ValidationError('El nombre de usuario ya está en uso')
    
    def validate_email(self, field):
        """Validar email"""
        # Validar formato
        try:
            validate_input(field.data, 'email')
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Verificar si ya existe (excluyendo el usuario actual)
        existing_user = User.query.filter_by(email=field.data).first()
        if existing_user and existing_user.id != self.user_id:
            raise ValidationError('El email ya está registrado')

class RoleForm(FlaskForm):
    """Formulario para crear/editar roles"""
    name = StringField('Nombre del Rol', validators=[
        DataRequired(message='El nombre del rol es requerido'),
        Length(min=2, max=50, message='El nombre debe tener entre 2 y 50 caracteres')
    ])
    description = TextAreaField('Descripción', validators=[
        Length(max=500, message='La descripción no puede exceder 500 caracteres')
    ])
    permissions = TextAreaField('Permisos (uno por línea)', validators=[
        DataRequired(message='Los permisos son requeridos')
    ])
    
    def validate_name(self, field):
        """Validar nombre del rol"""
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
    
    def validate_description(self, field):
        """Validar descripción"""
        if field.data:
            try:
                validate_input(field.data, 'text')
            except ValueError as e:
                raise ValidationError(str(e))
    
    def validate_permissions(self, field):
        """Validar permisos"""
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Validar que los permisos estén en la lista permitida
        allowed_permissions = [
            'user.create', 'user.read', 'user.update', 'user.delete',
            'role.create', 'role.read', 'role.update', 'role.delete',
            'data.read', 'data.write', 'data.delete',
            'analytics.read', 'analytics.write',
            'system.admin'
        ]
        
        permissions = [p.strip() for p in field.data.split('\n') if p.strip()]
        for permission in permissions:
            if permission not in allowed_permissions:
                raise ValidationError(f'Permiso no válido: {permission}')

class QueryForm(FlaskForm):
    """Formulario para consultas con validación de seguridad"""
    query = TextAreaField('Consulta', validators=[
        DataRequired(message='La consulta es requerida'),
        Length(max=1000, message='La consulta no puede exceder 1000 caracteres')
    ])
    
    def validate_query(self, field):
        """Validar consulta"""
        try:
            validate_input(field.data, 'text')
        except ValueError as e:
            raise ValidationError(str(e))
        
        # Validar patrones peligrosos específicos para consultas
        import re
        dangerous_patterns = [
            r"DROP\s+TABLE",
            r"DELETE\s+FROM",
            r"UPDATE\s+.*\s+SET",
            r"INSERT\s+INTO",
            r"CREATE\s+TABLE",
            r"ALTER\s+TABLE",
            r"EXEC\s*\(",
            r"EXECUTE\s*\(",
        ]
        
        for pattern in dangerous_patterns:
            if re.search(pattern, field.data, re.IGNORECASE):
                raise ValidationError('La consulta contiene operaciones no permitidas')
