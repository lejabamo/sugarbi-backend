"""
Script para inicializar la base de datos con usuarios y roles por defecto
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from web.app import app, db
from auth.models import User, Role, AuditLog
from auth.security import DEFAULT_PERMISSIONS

def init_database():
    """Inicializar la base de datos con datos por defecto"""
    with app.app_context():
        # Crear todas las tablas
        print("🔧 Creando tablas de la base de datos...")
        db.create_all()
        
        # Crear roles por defecto
        print("👥 Creando roles por defecto...")
        create_default_roles()
        
        # Crear usuario administrador por defecto
        print("👤 Creando usuario administrador...")
        create_admin_user()
        
        print("✅ Base de datos inicializada correctamente!")

def create_default_roles():
    """Crear roles por defecto"""
    roles_data = [
        {
            'name': 'admin',
            'description': 'Administrador del sistema con acceso completo',
            'permissions': DEFAULT_PERMISSIONS['admin']
        },
        {
            'name': 'analyst',
            'description': 'Analista de datos con acceso a consultas y análisis',
            'permissions': DEFAULT_PERMISSIONS['analyst']
        },
        {
            'name': 'viewer',
            'description': 'Usuario con acceso de solo lectura',
            'permissions': DEFAULT_PERMISSIONS['viewer']
        }
    ]
    
    for role_data in roles_data:
        existing_role = Role.query.filter_by(name=role_data['name']).first()
        if not existing_role:
            role = Role(**role_data)
            db.session.add(role)
            print(f"  ✓ Rol '{role_data['name']}' creado")
        else:
            print(f"  ⚠ Rol '{role_data['name']}' ya existe")
    
    db.session.commit()

def create_admin_user():
    """Crear usuario administrador por defecto"""
    admin_role = Role.query.filter_by(name='admin').first()
    
    if not admin_role:
        print("  ❌ Error: No se encontró el rol 'admin'")
        return
    
    existing_admin = User.query.filter_by(username='admin').first()
    if not existing_admin:
        admin_user = User(
            username='admin',
            email='admin@sugarbi.com',
            first_name='Administrador',
            last_name='Sistema',
            role_id=admin_role.id,
            is_admin=True,
            is_active=True
        )
        admin_user.set_password('admin123')  # Contraseña por defecto
        db.session.add(admin_user)
        print("  ✓ Usuario administrador creado (usuario: admin, contraseña: admin123)")
    else:
        print("  ⚠ Usuario administrador ya existe")
    
    db.session.commit()

def create_test_users():
    """Crear usuarios de prueba"""
    print("🧪 Creando usuarios de prueba...")
    
    analyst_role = Role.query.filter_by(name='analyst').first()
    viewer_role = Role.query.filter_by(name='viewer').first()
    
    test_users = [
        {
            'username': 'analista1',
            'email': 'analista1@sugarbi.com',
            'first_name': 'Ana',
            'last_name': 'Liz',
            'role_id': analyst_role.id if analyst_role else None,
            'password': 'analista123'
        },
        {
            'username': 'visualizador1',
            'email': 'visualizador1@sugarbi.com',
            'first_name': 'Carlos',
            'last_name': 'Mendez',
            'role_id': viewer_role.id if viewer_role else None,
            'password': 'visualizador123'
        }
    ]
    
    for user_data in test_users:
        existing_user = User.query.filter_by(username=user_data['username']).first()
        if not existing_user and user_data['role_id']:
            user = User(
                username=user_data['username'],
                email=user_data['email'],
                first_name=user_data['first_name'],
                last_name=user_data['last_name'],
                role_id=user_data['role_id'],
                is_active=True
            )
            user.set_password(user_data['password'])
            db.session.add(user)
            print(f"  ✓ Usuario '{user_data['username']}' creado")
        else:
            print(f"  ⚠ Usuario '{user_data['username']}' ya existe o no tiene rol")
    
    db.session.commit()

def show_users():
    """Mostrar usuarios existentes"""
    print("\n📋 Usuarios en el sistema:")
    users = User.query.all()
    for user in users:
        role_name = user.role.name if user.role else 'Sin rol'
        status = 'Activo' if user.is_active else 'Inactivo'
        print(f"  👤 {user.username} ({user.email}) - {role_name} - {status}")

def reset_database():
    """Resetear la base de datos (CUIDADO: Elimina todos los datos)"""
    print("⚠️  ADVERTENCIA: Esto eliminará todos los datos!")
    confirm = input("¿Estás seguro? Escribe 'SI' para confirmar: ")
    
    if confirm == 'SI':
        with app.app_context():
            db.drop_all()
            print("🗑️  Base de datos eliminada")
            init_database()
    else:
        print("❌ Operación cancelada")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestión de base de datos de autenticación')
    parser.add_argument('--init', action='store_true', help='Inicializar base de datos')
    parser.add_argument('--test-users', action='store_true', help='Crear usuarios de prueba')
    parser.add_argument('--show-users', action='store_true', help='Mostrar usuarios existentes')
    parser.add_argument('--reset', action='store_true', help='Resetear base de datos')
    
    args = parser.parse_args()
    
    if args.init:
        init_database()
    elif args.test_users:
        with app.app_context():
            create_test_users()
    elif args.show_users:
        with app.app_context():
            show_users()
    elif args.reset:
        reset_database()
    else:
        print("Uso: python init_db.py --init")
        print("Opciones disponibles:")
        print("  --init        Inicializar base de datos")
        print("  --test-users  Crear usuarios de prueba")
        print("  --show-users  Mostrar usuarios existentes")
        print("  --reset       Resetear base de datos (PELIGROSO)")

