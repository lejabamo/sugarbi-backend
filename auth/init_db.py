#!/usr/bin/env python3
"""
Script de inicialización de la base de datos de autenticación
Crea las tablas necesarias y un usuario administrador por defecto
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from web.app import app, db, User, Role, SessionToken, AuditLog
from datetime import datetime

def init_database():
    """Inicializar la base de datos con tablas y datos por defecto"""
    
    with app.app_context():
        try:
            print("🔧 Inicializando base de datos de autenticación...")
            
            # Crear todas las tablas
            print("📋 Creando tablas...")
            db.create_all()
            
            # Crear roles por defecto
            print("👥 Creando roles por defecto...")
            
            # Rol Administrador
            admin_role = Role.query.filter_by(name='admin').first()
            if not admin_role:
                admin_role = Role(
                    name='admin',
                    description='Administrador del sistema con acceso completo',
                    permissions=[
                        'user.create', 'user.read', 'user.update', 'user.delete',
                        'role.create', 'role.read', 'role.update', 'role.delete',
                        'data.read', 'data.write', 'data.delete',
                        'analytics.read', 'analytics.write',
                        'system.admin'
                    ]
                )
                db.session.add(admin_role)
                print("  ✅ Rol 'admin' creado")
            else:
                print("  ℹ️  Rol 'admin' ya existe")
            
            # Rol Analista
            analyst_role = Role.query.filter_by(name='analyst').first()
            if not analyst_role:
                analyst_role = Role(
                    name='analyst',
                    description='Analista de datos con permisos de lectura y escritura',
                    permissions=[
                        'data.read', 'analytics.read', 'analytics.write'
                    ]
                )
                db.session.add(analyst_role)
                print("  ✅ Rol 'analyst' creado")
            else:
                print("  ℹ️  Rol 'analyst' ya existe")
            
            # Rol Visualizador
            viewer_role = Role.query.filter_by(name='viewer').first()
            if not viewer_role:
                viewer_role = Role(
                    name='viewer',
                    description='Usuario con permisos de solo lectura',
                    permissions=[
                        'data.read', 'analytics.read'
                    ]
                )
                db.session.add(viewer_role)
                print("  ✅ Rol 'viewer' creado")
            else:
                print("  ℹ️  Rol 'viewer' ya existe")
            
            # Commit de roles
            db.session.commit()
            
            # Crear usuario administrador por defecto
            print("👤 Creando usuario administrador...")
            admin_user = User.query.filter_by(username='admin').first()
            if not admin_user:
                admin_user = User(
                    username='admin',
                    email='admin@sugarbi.com',
                    first_name='Administrador',
                    last_name='Sistema',
                    is_active=True,
                    is_admin=True,
                    role_id=admin_role.id
                )
                admin_user.set_password('admin123')  # Cambiar en producción
                db.session.add(admin_user)
                print("  ✅ Usuario 'admin' creado")
                print("  🔑 Usuario: admin")
                print("  🔑 Contraseña: admin123")
                print("  ⚠️  IMPORTANTE: Cambiar la contraseña en producción")
            else:
                print("  ℹ️  Usuario 'admin' ya existe")
            
            # Crear usuario demo
            demo_user = User.query.filter_by(username='demo').first()
            if not demo_user:
                demo_user = User(
                    username='demo',
                    email='demo@sugarbi.com',
                    first_name='Usuario',
                    last_name='Demo',
                    is_active=True,
                    is_admin=False,
                    role_id=analyst_role.id
                )
                demo_user.set_password('demo123')
                db.session.add(demo_user)
                print("  ✅ Usuario 'demo' creado")
                print("  🔑 Usuario: demo")
                print("  🔑 Contraseña: demo123")
            else:
                print("  ℹ️  Usuario 'demo' ya existe")
            
            # Commit final
            db.session.commit()
            
            print("\n🎉 ¡Base de datos inicializada correctamente!")
            print("\n📊 Resumen:")
            print(f"  • Roles creados: {Role.query.count()}")
            print(f"  • Usuarios creados: {User.query.count()}")
            print("\n🔐 Credenciales por defecto:")
            print("  • Admin: admin / admin123")
            print("  • Demo: demo / demo123")
            print("\n⚠️  RECORDATORIO: Cambiar las contraseñas en producción")
            
        except Exception as e:
            print(f"❌ Error al inicializar la base de datos: {str(e)}")
            db.session.rollback()
            return False
    
    return True

def reset_database():
    """Resetear completamente la base de datos (CUIDADO: Elimina todos los datos)"""
    
    response = input("⚠️  ¿Estás seguro de que quieres eliminar TODOS los datos? (escribe 'SI' para confirmar): ")
    if response != 'SI':
        print("❌ Operación cancelada")
        return False
    
    with app.app_context():
        try:
            print("🗑️  Eliminando todas las tablas...")
            db.drop_all()
            print("✅ Tablas eliminadas")
            
            print("🔧 Recreando base de datos...")
            return init_database()
            
        except Exception as e:
            print(f"❌ Error al resetear la base de datos: {str(e)}")
            return False

def show_status():
    """Mostrar el estado actual de la base de datos"""
    
    with app.app_context():
        try:
            print("📊 Estado de la base de datos:")
            print(f"  • Roles: {Role.query.count()}")
            print(f"  • Usuarios: {User.query.count()}")
            print(f"  • Tokens de sesión: {SessionToken.query.count()}")
            print(f"  • Logs de auditoría: {AuditLog.query.count()}")
            
            print("\n👥 Usuarios:")
            for user in User.query.all():
                status = "🟢 Activo" if user.is_active else "🔴 Inactivo"
                admin = "👑 Admin" if user.is_admin else ""
                print(f"  • {user.username} ({user.email}) - {status} {admin}")
            
            print("\n🎭 Roles:")
            for role in Role.query.all():
                print(f"  • {role.name}: {role.description}")
                
        except Exception as e:
            print(f"❌ Error al obtener el estado: {str(e)}")

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Gestión de la base de datos de autenticación')
    parser.add_argument('action', choices=['init', 'reset', 'status'], 
                       help='Acción a realizar: init (inicializar), reset (resetear), status (estado)')
    
    args = parser.parse_args()
    
    if args.action == 'init':
        success = init_database()
        sys.exit(0 if success else 1)
    elif args.action == 'reset':
        success = reset_database()
        sys.exit(0 if success else 1)
    elif args.action == 'status':
        show_status()
        sys.exit(0)