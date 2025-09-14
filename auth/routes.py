"""
Rutas de autenticación y gestión de usuarios
"""

from flask import Blueprint, render_template, request, jsonify, redirect, url_for, flash, session, current_app
from flask_login import login_user, logout_user, login_required, current_user
# from flask_wtf.csrf import CSRFProtect
from urllib.parse import urlparse
from auth.models import db, User, Role, SessionToken, AuditLog
from auth.forms import LoginForm, RegisterForm, ChangePasswordForm, UserEditForm, RoleForm
from auth.security import security_manager, require_auth, require_permission, audit_log
from datetime import datetime, timedelta
import logging

# Crear blueprint de autenticación
auth_bp = Blueprint('auth', __name__, url_prefix='/auth')

# Crear instancia de CSRF
# csrf = CSRFProtect()

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
            if not next_page or urlparse(next_page).netloc != '':
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
# @csrf.exempt
def api_login():
    """API endpoint para login"""
    try:
        data = request.get_json()
        
        if not data:
            return jsonify({
                'success': False,
                'error': 'Datos JSON requeridos'
            }), 400
        
        username = data.get('username')
        password = data.get('password')
        
        if not username or not password:
            return jsonify({
                'success': False,
                'error': 'Username y password son requeridos'
            }), 400
        
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
            
            return jsonify({
                'success': False,
                'error': 'Usuario o contraseña inválidos'
            }), 401
        
        # Verificar si la cuenta está bloqueada
        if user.is_locked():
            security_manager.log_security_event('BLOCKED_LOGIN_ATTEMPT', {
                'username': username,
                'reason': 'account_locked'
            }, user.id)
            return jsonify({
                'success': False,
                'error': 'Cuenta bloqueada temporalmente'
            }), 401
        
        # Verificar si el usuario está activo
        if not user.is_active:
            security_manager.log_security_event('INACTIVE_LOGIN_ATTEMPT', {
                'username': username,
                'reason': 'account_inactive'
            }, user.id)
            return jsonify({
                'success': False,
                'error': 'Cuenta desactivada'
            }), 401
        
        # Login exitoso
        login_user(user, remember=False)
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
            action='API_LOGIN',
            resource='auth',
            ip_address=request.remote_addr,
            user_agent=request.headers.get('User-Agent')
        )
        db.session.add(audit_entry)
        db.session.commit()
        
        return jsonify({
            'success': True,
            'data': {
                'user': {
                    'id': user.id,
                    'username': user.username,
                    'email': user.email,
                    'first_name': user.first_name,
                    'last_name': user.last_name,
                    'role': user.role.name if user.role else None,
                    'is_admin': user.is_admin,
                    'is_active': user.is_active
                },
                'token': token
            }
        })
        
    except Exception as e:
        logging.error(f"Error en API login: {str(e)}")
        return jsonify({
            'success': False,
            'error': 'Error interno del servidor'
        }), 500

@auth_bp.route('/api/logout', methods=['POST'])
# @csrf.exempt
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


@auth_bp.route('/api/user/me', methods=['GET'])
# @csrf.exempt
@require_auth
def api_user_me():
    """API endpoint para obtener información del usuario actual"""
    if current_user.is_authenticated:
        return jsonify({
            'success': True,
            'data': {
                'id': current_user.id,
                'username': current_user.username,
                'email': current_user.email,
                'first_name': current_user.first_name,
                'last_name': current_user.last_name,
                'role': current_user.role.name if current_user.role else None,
                'is_admin': current_user.is_admin,
                'is_active': current_user.is_active
            }
        })
    else:
        return jsonify({
            'success': False,
            'message': 'No hay sesión activa'
        }), 401

