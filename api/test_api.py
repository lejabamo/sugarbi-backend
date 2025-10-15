import requests
import json
import time

# URL base de la API
BASE_URL = "http://localhost:5000"

def test_endpoint(endpoint, description):
    """Probar un endpoint de la API"""
    print(f"\n🧪 Probando: {description}")
    print(f"📍 URL: {BASE_URL}{endpoint}")
    
    try:
        response = requests.get(f"{BASE_URL}{endpoint}")
        
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Status: {response.status_code}")
            print(f"📊 Success: {data.get('success', False)}")
            
            if 'data' in data:
                if isinstance(data['data'], list):
                    print(f"📈 Registros: {len(data['data'])}")
                    if data['data']:
                        print(f"🔍 Primer registro: {list(data['data'][0].keys())}")
                else:
                    print(f"📈 Datos: {type(data['data'])}")
            
            if 'total' in data:
                print(f"📊 Total: {data['total']}")
                
        else:
            print(f"❌ Status: {response.status_code}")
            print(f"❌ Error: {response.text}")
            
    except requests.exceptions.ConnectionError:
        print("❌ Error: No se puede conectar al servidor. ¿Está ejecutándose la API?")
    except Exception as e:
        print(f"❌ Error: {str(e)}")

def test_api():
    """Ejecutar todas las pruebas de la API"""
    print("🚀 === PRUEBAS DE LA API SUGARBI ===")
    print(f"🌐 Servidor: {BASE_URL}")
    
    # Lista de endpoints a probar
    endpoints = [
        ("/", "Endpoint de bienvenida"),
        ("/api/fincas", "Lista de fincas"),
        ("/api/variedades", "Lista de variedades"),
        ("/api/zonas", "Lista de zonas"),
        ("/api/tiempo", "Períodos de tiempo"),
        ("/api/estadisticas", "Estadísticas generales"),
        ("/api/cosecha?limit=5", "Datos de cosecha (limitado)"),
        ("/api/cosecha/top?criterio=toneladas&limit=3", "Top cosechas por toneladas"),
        ("/api/cosecha/top?criterio=tch&limit=3", "Top cosechas por TCH"),
        ("/api/cosecha/top?criterio=brix&limit=3", "Top cosechas por Brix"),
    ]
    
    for endpoint, description in endpoints:
        test_endpoint(endpoint, description)
        time.sleep(0.5)  # Pausa entre pruebas
    
    print("\n🎯 === PRUEBAS CON FILTROS ===")
    
    # Pruebas con filtros
    filter_tests = [
        ("/api/cosecha?año=2023&limit=3", "Cosechas del año 2023"),
        ("/api/cosecha?mes=7&limit=3", "Cosechas del mes 7"),
        ("/api/cosecha?finca_id=1&limit=3", "Cosechas de finca ID 1"),
    ]
    
    for endpoint, description in filter_tests:
        test_endpoint(endpoint, description)
        time.sleep(0.5)
    
    print("\n✅ === PRUEBAS COMPLETADAS ===")
    print("💡 Para más pruebas, visita: http://localhost:5000")

if __name__ == "__main__":
    test_api()








