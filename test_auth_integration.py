#!/usr/bin/env python3
"""
Script de prueba para verificar la integración del sistema de autenticación
"""

import sys
import requests
import json
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

def test_auth_integration():
    """Probar la integración del sistema de autenticación"""
    
    base_url = "http://localhost:5001"
    
    print("🧪 Probando integración del sistema de autenticación...")
    print(f"🌐 URL base: {base_url}")
    
    # Test 1: Verificar que la página de login es accesible
    print("\n1️⃣ Probando acceso a página de login...")
    try:
        response = requests.get(f"{base_url}/login", timeout=5)
        if response.status_code == 200:
            print("  ✅ Página de login accesible")
        else:
            print(f"  ❌ Error en página de login: {response.status_code}")
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error de conexión: {e}")
        return False
    
    # Test 2: Verificar que las rutas protegidas redirigen al login
    print("\n2️⃣ Probando protección de rutas...")
    protected_routes = [
        "/dashboard",
        "/dashboard-alternativo", 
        "/olap",
        "/api/estadisticas"
    ]
    
    for route in protected_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5, allow_redirects=False)
            if response.status_code in [302, 401]:  # Redirección o no autorizado
                print(f"  ✅ Ruta {route} protegida correctamente")
            else:
                print(f"  ⚠️  Ruta {route} no protegida (status: {response.status_code})")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error probando {route}: {e}")
    
    # Test 3: Probar login con credenciales por defecto
    print("\n3️⃣ Probando login con credenciales por defecto...")
    login_data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        # Primero obtener la página de login para obtener el CSRF token si es necesario
        session = requests.Session()
        login_page = session.get(f"{base_url}/login")
        
        # Intentar hacer login
        response = session.post(f"{base_url}/login", data=login_data, timeout=5)
        
        if response.status_code == 200 and "dashboard" in response.url:
            print("  ✅ Login exitoso con credenciales por defecto")
        elif response.status_code == 200:
            print("  ⚠️  Login procesado, pero redirección inesperada")
        else:
            print(f"  ❌ Error en login: {response.status_code}")
            print(f"  📄 Respuesta: {response.text[:200]}...")
            
    except requests.exceptions.RequestException as e:
        print(f"  ❌ Error en login: {e}")
    
    # Test 4: Verificar que la API requiere autenticación
    print("\n4️⃣ Probando protección de API...")
    api_endpoints = [
        "/api/chat",
        "/api/estadisticas",
        "/api/examples"
    ]
    
    for endpoint in api_endpoints:
        try:
            if endpoint == "/api/chat":
                response = requests.post(f"{base_url}{endpoint}", 
                                       json={"query": "test"}, 
                                       timeout=5)
            else:
                response = requests.get(f"{base_url}{endpoint}", timeout=5)
            
            if response.status_code == 401:
                print(f"  ✅ API {endpoint} protegida correctamente")
            else:
                print(f"  ⚠️  API {endpoint} no protegida (status: {response.status_code})")
                
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error probando API {endpoint}: {e}")
    
    # Test 5: Verificar páginas públicas
    print("\n5️⃣ Probando acceso a páginas públicas...")
    public_routes = [
        "/",
        "/login",
        "/register"
    ]
    
    for route in public_routes:
        try:
            response = requests.get(f"{base_url}{route}", timeout=5)
            if response.status_code == 200:
                print(f"  ✅ Página pública {route} accesible")
            else:
                print(f"  ❌ Error en página pública {route}: {response.status_code}")
        except requests.exceptions.RequestException as e:
            print(f"  ❌ Error probando {route}: {e}")
    
    print("\n🎉 Pruebas de integración completadas!")
    print("\n📋 Resumen:")
    print("  • Verifica que todas las rutas protegidas requieren autenticación")
    print("  • Verifica que las páginas públicas son accesibles")
    print("  • Verifica que el login funciona con las credenciales por defecto")
    print("  • Verifica que la API está protegida")
    
    return True

def test_database_connection():
    """Probar la conexión a la base de datos"""
    
    print("\n🗄️ Probando conexión a la base de datos...")
    
    try:
        from web.app import app, db, User, Role
        
        with app.app_context():
            # Probar conexión
            user_count = User.query.count()
            role_count = Role.query.count()
            
            print(f"  ✅ Conexión exitosa")
            print(f"  📊 Usuarios en BD: {user_count}")
            print(f"  🎭 Roles en BD: {role_count}")
            
            # Verificar usuarios por defecto
            admin_user = User.query.filter_by(username='admin').first()
            if admin_user:
                print(f"  ✅ Usuario admin encontrado")
            else:
                print(f"  ⚠️  Usuario admin no encontrado")
                
            return True
            
    except Exception as e:
        print(f"  ❌ Error de conexión a BD: {e}")
        return False

if __name__ == '__main__':
    import argparse
    
    parser = argparse.ArgumentParser(description='Probar integración del sistema de autenticación')
    parser.add_argument('--db-only', action='store_true', 
                       help='Solo probar conexión a base de datos')
    parser.add_argument('--web-only', action='store_true',
                       help='Solo probar integración web')
    
    args = parser.parse_args()
    
    if args.db_only:
        test_database_connection()
    elif args.web_only:
        test_auth_integration()
    else:
        # Probar ambos
        db_ok = test_database_connection()
        if db_ok:
            test_auth_integration()
        else:
            print("❌ No se puede probar la integración web sin conexión a BD")
            sys.exit(1)



