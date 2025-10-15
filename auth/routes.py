"""
Rutas de autenticación y gestión de usuarios
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.urls import url_parse
from auth.models import db, User, Role, SessionToken, AuditLog
from auth.forms import LoginForm, RegisterForm, ChangePasswordForm, UserEditForm, RoleForm
from auth.security import security_manager, require_auth, require_permission, audit_log
from datetime import datetime, timedelta
import logging

# Crear blueprint de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

@auth_bp.route('/login', methods=['GET', 'POST'])
def login():
    """Página de login"""
    if current_user.is_authenticated:
        return redirect(url_for('index'))
    
    form = LoginForm()
    
    if form.validate_on_submit():
        try:
            # Buscar usuario
            user = User.query.filter_by(username=form.username.data).first()
            
            if user is None or not user.check_password(form.password.data):
                # Incrementar intentos de login
                if user:
                    user.increment_login_attempts()
                    security_manager.log_security_event('FAILED_LOGIN', {
                        'username': form.username.data,
                        'reason': 'invalid_password'
                    }, user.id)
                else:
                    security_manager.log_security_event('FAILED_LOGIN', {
                        'username': form.username.data,
                        'reason': 'user_not_found'
                    })
                
                flash('Usuario o contraseña inválidos', 'error')
                return render_template('auth/login.html', form=form)
            
            # Verificar si la cuenta está bloqueada
            if user.is_locked():
                security_manager.log_security_event('BLOCKED_LOGIN_ATTEMPT', {
                    'username': form.username.data,
                    'reason': 'account_locked'
                }, user.id)
                flash('Cuenta bloqueada temporalmente. Intenta más tarde.', 'error')
                return render_template('auth/login.html', form=form)
            
            # Verificar si el usuario está activo
            if not user.is_active:
                security_manager.log_security_event('INACTIVE_LOGIN_ATTEMPT', {
                    'username': form.username.data,
                    'reason': 'account_inactive'
                }, user.id)
                flash('Cuenta desactivada. Contacta al administrador.', 'error')
                return render_template('auth/login.html', form=form)
            
            # Login exitoso
            login_user(user, remember=form.remember_me.data)
            user.reset_login_attempts()
            
            # Crear token de sesión
            token = SessionToken.generate_token()
            session_token = SessionToken(
                token=token,
                user_id=user.id,
                expires_at=datetime.utcnow() + timedelta(days=30),
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(session_token)
            db.session.commit()
            
            # Registrar en log de auditoría
            audit_entry = AuditLog(
                user_id=user.id,
                action='LOGIN',
                resource='auth',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_entry)
            db.session.commit()
            
            # Redirigir a la página solicitada o al dashboard
            next_page = request.args.get('next')
            if not next_page or url_parse(next_page).netloc != '':
                next_page = url_for('index')
            
            flash('Login exitoso', 'success')
            return redirect(next_page)
            
        except Exception as e:
            logging.error(f"Error en login: {str(e)}")
            security_manager.log_security_event('LOGIN_ERROR', {
                'username': form.username.data,
                'error': str(e)
            })
            flash('Error interno del servidor', 'error')
    
    return render_template('auth/login.html', form=form)

@auth_bp.route('/logout')
@login_required
def logout():
    """Cerrar sesión"""
    # Registrar logout en auditoría
    audit_entry = AuditLog(
        user_id=current_user.id,
        action='LOGOUT',
        resource='auth',
        ip_address=request.remote_addr,
        user_agent=request.headers.get('User-Agent')
    )
    db.session.add(audit_entry)
    db.session.commit()
    
    logout_user()
    flash('Sesión cerrada exitosamente', 'info')
    return redirect(url_for('auth.login'))

@auth_bp.route('/register', methods=['GET', 'POST'])
@require_permission('user.create')
def register():
    """Registro de nuevos usuarios"""
    form = RegisterForm()
    
    if form.validate_on_submit():
        try:
            user = User(
                username=form.username.data,
                email=form.email.data,
                first_name=form.first_name.data,
                last_name=form.last_name.data,
                role_id=form.role_id.data
            )
            user.set_password(form.password.data)
            
            db.session.add(user)
            db.session.commit()
            
            # Registrar en auditoría
            audit_entry = AuditLog(
                user_id=current_user.id,
                action='USER_CREATED',
                resource='user',
                details={'new_user_id': user.id, 'username': user.username},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_entry)
            db.session.commit()
            
            flash('Usuario creado exitosamente', 'success')
            return redirect(url_for('auth.users'))
            
        except Exception as e:
            logging.error(f"Error creando usuario: {str(e)}")
            db.session.rollback()
            flash('Error creando usuario', 'error')
    
    return render_template('auth/register.html', form=form)

@auth_bp.route('/users')
@require_permission('user.read')
def users():
    """Lista de usuarios"""
    page = request.args.get('page', 1, type=int)
    users = User.query.paginate(
        page=page, per_page=20, error_out=False
    )
    return render_template('auth/users.html', users=users)

@auth_bp.route('/users/<int:user_id>/edit', methods=['GET', 'POST'])
@require_permission('user.update')
def edit_user(user_id):
    """Editar usuario"""
    user = User.query.get_or_404(user_id)
    form = UserEditForm(user_id=user_id, obj=user)
    
    if form.validate_on_submit():
        try:
            user.username = form.username.data
            user.email = form.email.data
            user.first_name = form.first_name.data
            user.last_name = form.last_name.data
            user.role_id = form.role_id.data
            user.is_active = form.is_active.data
            
            db.session.commit()
            
            # Registrar en auditoría
            audit_entry = AuditLog(
                user_id=current_user.id,
                action='USER_UPDATED',
                resource='user',
                details={'target_user_id': user.id, 'username': user.username},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_entry)
            db.session.commit()
            
            flash('Usuario actualizado exitosamente', 'success')
            return redirect(url_for('auth.users'))
            
        except Exception as e:
            logging.error(f"Error actualizando usuario: {str(e)}")
            db.session.rollback()
            flash('Error actualizando usuario', 'error')
    
    return render_template('auth/edit_user.html', form=form, user=user)

@auth_bp.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Cambiar contraseña"""
    form = ChangePasswordForm()
    
    if form.validate_on_submit():
        try:
            current_user.set_password(form.new_password.data)
            db.session.commit()
            
            # Registrar en auditoría
            audit_entry = AuditLog(
                user_id=current_user.id,
                action='PASSWORD_CHANGED',
                resource='auth',
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_entry)
            db.session.commit()
            
            flash('Contraseña cambiada exitosamente', 'success')
            return redirect(url_for('auth.profile'))
            
        except Exception as e:
            logging.error(f"Error cambiando contraseña: {str(e)}")
            db.session.rollback()
            flash('Error cambiando contraseña', 'error')
    
    return render_template('auth/change_password.html', form=form)

@auth_bp.route('/profile')
@login_required
def profile():
    """Perfil del usuario"""
    return render_template('auth/profile.html', user=current_user)

@auth_bp.route('/roles')
@require_permission('role.read')
def roles():
    """Lista de roles"""
    roles = Role.query.all()
    return render_template('auth/roles.html', roles=roles)

@auth_bp.route('/roles/create', methods=['GET', 'POST'])
@require_permission('role.create')
def create_role():
    """Crear nuevo rol"""
    form = RoleForm()
    
    if form.validate_on_submit():
        try:
            permissions = [p.strip() for p in form.permissions.data.split('\n') if p.strip()]
            
            role = Role(
                name=form.name.data,
                description=form.description.data,
                permissions=permissions
            )
            
            db.session.add(role)
            db.session.commit()
            
            # Registrar en auditoría
            audit_entry = AuditLog(
                user_id=current_user.id,
                action='ROLE_CREATED',
                resource='role',
                details={'role_id': role.id, 'name': role.name},
                ip_address=request.remote_addr,
                user_agent=request.headers.get('User-Agent')
            )
            db.session.add(audit_entry)
            db.session.commit()
            
            flash('Rol creado exitosamente', 'success')
            return redirect(url_for('auth.roles'))
            
        except Exception as e:
            logging.error(f"Error creando rol: {str(e)}")
            db.session.rollback()
            flash('Error creando rol', 'error')
    
    return render_template('auth/create_role.html', form=form)

@auth_bp.route('/audit-logs')
@require_permission('system.admin')
def audit_logs():
    """Logs de auditoría"""
    page = request.args.get('page', 1, type=int)
    logs = AuditLog.query.order_by(AuditLog.timestamp.desc()).paginate(
        page=page, per_page=50, error_out=False
    )
    return render_template('auth/audit_logs.html', logs=logs)

# API endpoints para autenticación
@auth_bp.route('/api/login', methods=['POST'])
def api_login():
    """API endpoint para login"""
    data = request.get_json()
    
    if not data or not data.get('username') or not data.get('password'):
        return jsonify({'error': 'Username y password requeridos'}), 400
    
    try:
        user = User.query.filter_by(username=data['username']).first()
        
        if user and user.check_password(data['password']) and user.is_active and not user.is_locked():
            login_user(user)
            user.reset_login_attempts()
            
            # Crear token JWT
            import jwt
            token = jwt.encode({
                'user_id': user.id,
                'exp': datetime.utcnow() + timedelta(hours=24)
            }, current_app.config['SECRET_KEY'], algorithm='HS256')
            
            return jsonify({
                'success': True,
                'token': token,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role.name if user.role else None
                }
            })
        else:
            if user:
                user.increment_login_attempts()
                security_manager.log_security_event('API_FAILED_LOGIN', {
                    'username': data['username'],
                    'reason': 'invalid_credentials'
                }, user.id)
            
            return jsonify({'error': 'Credenciales inválidas'}), 401
            
    except Exception as e:
        logging.error(f"Error en API login: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500

@auth_bp.route('/api/logout', methods=['POST'])
@require_auth
def api_logout():
    """API endpoint para logout"""
    logout_user()
    return jsonify({'success': True, 'message': 'Logout exitoso'})

@auth_bp.route('/api/verify-token', methods=['POST'])
def api_verify_token():
    """Verificar token JWT"""
    data = request.get_json()
    token = data.get('token')
    
    if not token:
        return jsonify({'error': 'Token requerido'}), 400
    
    try:
        import jwt
        payload = jwt.decode(token, current_app.config['SECRET_KEY'], algorithms=['HS256'])
        user = User.query.get(payload['user_id'])
        
        if user and user.is_active:
            return jsonify({
                'valid': True,
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'role': user.role.name if user.role else None
                }
            })
        else:
            return jsonify({'valid': False}), 401
            
    except jwt.ExpiredSignatureError:
        return jsonify({'valid': False, 'error': 'Token expirado'}), 401
    except jwt.InvalidTokenError:
        return jsonify({'valid': False, 'error': 'Token inválido'}), 401
    except Exception as e:
        logging.error(f"Error verificando token: {str(e)}")
        return jsonify({'error': 'Error interno del servidor'}), 500





