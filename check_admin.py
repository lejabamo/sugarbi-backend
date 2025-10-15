#!/usr/bin/env python3
"""
Script para verificar el usuario admin en la base de datos
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from auth.models import db, User, Role
from web.app import app

def check_admin_user():
    """Verificar si el usuario admin existe y su contraseña"""
    with app.app_context():
        try:
            # Buscar usuario admin
            admin_user = User.query.filter_by(username='admin').first()
            
            if admin_user:
                print("✅ Usuario admin encontrado:")
                print(f"   - ID: {admin_user.id}")
                print(f"   - Username: {admin_user.username}")
                print(f"   - Email: {admin_user.email}")
                print(f"   - Activo: {admin_user.is_active}")
                print(f"   - Admin: {admin_user.is_admin}")
                print(f"   - Rol: {admin_user.role.name if admin_user.role else 'Sin rol'}")
                
                # Verificar contraseña
                password_test = admin_user.check_password('admin123')
                print(f"   - Contraseña 'admin123': {'✅ Correcta' if password_test else '❌ Incorrecta'}")
                
                # Probar otras contraseñas comunes
                common_passwords = ['admin', 'password', '123456', 'toor']
                for pwd in common_passwords:
                    if admin_user.check_password(pwd):
                        print(f"   - Contraseña '{pwd}': ✅ Correcta")
                        break
                else:
                    print("   - Ninguna contraseña común funciona")
                    
            else:
                print("❌ Usuario admin NO encontrado")
                
                # Listar todos los usuarios
                all_users = User.query.all()
                print(f"\nUsuarios existentes ({len(all_users)}):")
                for user in all_users:
                    print(f"   - {user.username} ({user.email})")
                    
        except Exception as e:
            print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    print("🔍 Verificando usuario admin...")
    check_admin_user()

