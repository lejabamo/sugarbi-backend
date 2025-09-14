#!/usr/bin/env python3
"""
Script de prueba para el motor OLAP de SugarBI
Prueba las operaciones multidimensionales básicas
"""

import sys
from pathlib import Path
import json

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from dashboard.olap_engine import OLAEEngine, OLAPQuery, OLAPOperation, AggregationFunction, DimensionLevel
import configparser

def get_database_url():
    """Obtener URL de conexión a la base de datos"""
    config = configparser.ConfigParser()
    config.read('config/config.ini', encoding='utf-8')
    
    db_config = config['mysql']
    return (
        f"mysql+pymysql://{db_config['user']}:{db_config['password']}"
        f"@{db_config['host']}:{db_config['port']}/{db_config['database']}"
    )

def test_olap_engine():
    """Probar el motor OLAP con diferentes operaciones"""
    print("🧪 Iniciando pruebas del motor OLAP...")
    
    try:
        # Crear motor OLAP
        database_url = get_database_url()
        olap_engine = OLAEEngine(database_url)
        
        print("✅ Motor OLAP creado exitosamente")
        
        # Probar 1: Operación de agregación básica
        print("\n📊 Prueba 1: Agregación básica por año")
        query1 = OLAPQuery(
            operation=OLAPOperation.AGGREGATE,
            measures=["toneladas", "tch"],
            dimensions=["tiempo"],
            dimension_levels={"tiempo": DimensionLevel.YEAR},
            filters={},
            aggregation_functions=[AggregationFunction.SUM, AggregationFunction.AVG],
            limit=5
        )
        
        result1 = olap_engine.execute_olap_query(query1)
        if result1.success:
            print(f"✅ Consulta exitosa: {result1.record_count} registros")
            print(f"⏱️ Tiempo de ejecución: {result1.execution_time:.3f}s")
            if result1.data:
                print("📋 Primeros resultados:")
                for i, record in enumerate(result1.data[:3]):
                    print(f"  {i+1}. {record}")
        else:
            print(f"❌ Error: {result1.metadata.get('error')}")
        
        # Probar 2: Drill-down por tiempo
        print("\n🔍 Prueba 2: Drill-down por tiempo (año -> semestre)")
        query2 = OLAPQuery(
            operation=OLAPOperation.DRILL_DOWN,
            measures=["toneladas"],
            dimensions=["tiempo"],
            dimension_levels={"tiempo": DimensionLevel.YEAR},
            filters={"año": 2025},
            aggregation_functions=[AggregationFunction.SUM],
            limit=10
        )
        
        result2 = olap_engine.execute_olap_query(query2)
        if result2.success:
            print(f"✅ Drill-down exitoso: {result2.record_count} registros")
            print(f"⏱️ Tiempo de ejecución: {result2.execution_time:.3f}s")
        else:
            print(f"❌ Error: {result2.metadata.get('error')}")
        
        # Probar 3: Slice por zona específica
        print("\n✂️ Prueba 3: Slice por zona específica")
        query3 = OLAPQuery(
            operation=OLAPOperation.SLICE,
            measures=["toneladas", "brix"],
            dimensions=["tiempo", "geografia"],
            dimension_levels={"tiempo": DimensionLevel.MONTH, "geografia": DimensionLevel.ZONE},
            filters={"año": 2025, "zona": "Zona Norte"},
            aggregation_functions=[AggregationFunction.SUM, AggregationFunction.AVG],
            limit=10
        )
        
        result3 = olap_engine.execute_olap_query(query3)
        if result3.success:
            print(f"✅ Slice exitoso: {result3.record_count} registros")
            print(f"⏱️ Tiempo de ejecución: {result3.execution_time:.3f}s")
        else:
            print(f"❌ Error: {result3.metadata.get('error')}")
        
        # Probar 4: Roll-up geográfico
        print("\n📈 Prueba 4: Roll-up geográfico (finca -> zona)")
        query4 = OLAPQuery(
            operation=OLAPOperation.ROLL_UP,
            measures=["toneladas"],
            dimensions=["geografia"],
            dimension_levels={"geografia": DimensionLevel.FARM},
            filters={"año": 2025},
            aggregation_functions=[AggregationFunction.SUM],
            limit=10
        )
        
        result4 = olap_engine.execute_olap_query(query4)
        if result4.success:
            print(f"✅ Roll-up exitoso: {result4.record_count} registros")
            print(f"⏱️ Tiempo de ejecución: {result4.execution_time:.3f}s")
        else:
            print(f"❌ Error: {result4.metadata.get('error')}")
        
        # Probar 5: Dice múltiple
        print("\n🎲 Prueba 5: Dice múltiple (filtros en varias dimensiones)")
        query5 = OLAPQuery(
            operation=OLAPOperation.DICE,
            measures=["toneladas", "tch", "brix"],
            dimensions=["tiempo", "geografia", "producto"],
            dimension_levels={"tiempo": DimensionLevel.MONTH, "geografia": DimensionLevel.FARM, "producto": DimensionLevel.VARIETY},
            filters={"año": 2025, "mes": 8},
            aggregation_functions=[AggregationFunction.SUM, AggregationFunction.AVG],
            limit=5
        )
        
        result5 = olap_engine.execute_olap_query(query5)
        if result5.success:
            print(f"✅ Dice exitoso: {result5.record_count} registros")
            print(f"⏱️ Tiempo de ejecución: {result5.execution_time:.3f}s")
        else:
            print(f"❌ Error: {result5.metadata.get('error')}")
        
        # Probar dimensiones y medidas disponibles
        print("\n📋 Prueba 6: Dimensiones y medidas disponibles")
        dimensions = olap_engine.get_available_dimensions()
        measures = olap_engine.get_available_measures()
        aggregations = olap_engine.get_available_aggregations()
        
        print(f"✅ Dimensiones: {dimensions['dimensions']}")
        print(f"✅ Medidas: {measures}")
        print(f"✅ Agregaciones: {aggregations}")
        
        print("\n🎉 Todas las pruebas completadas!")
        
    except Exception as e:
        print(f"❌ Error general: {str(e)}")
        import traceback
        traceback.print_exc()

def test_api_endpoints():
    """Probar endpoints de la API OLAP"""
    print("\n🌐 Probando endpoints de la API OLAP...")
    
    import requests
    
    base_url = "http://localhost:5001/api/olap"
    
    try:
        # Probar endpoint de dimensiones
        print("📊 Probando /api/olap/dimensions")
        response = requests.get(f"{base_url}/dimensions")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Dimensiones: {data['data']['dimensions']}")
        else:
            print(f"❌ Error: {response.status_code}")
        
        # Probar endpoint de medidas
        print("📏 Probando /api/olap/measures")
        response = requests.get(f"{base_url}/measures")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Medidas: {data['data']['measures']}")
        else:
            print(f"❌ Error: {response.status_code}")
        
        # Probar endpoint de ejemplos
        print("📚 Probando /api/olap/examples")
        response = requests.get(f"{base_url}/examples")
        if response.status_code == 200:
            data = response.json()
            print(f"✅ Ejemplos disponibles: {len(data['data']['examples'])}")
        else:
            print(f"❌ Error: {response.status_code}")
        
        # Probar consulta OLAP
        print("🔍 Probando consulta OLAP")
        query_data = {
            "operation": "aggregate",
            "measures": ["toneladas"],
            "dimensions": ["tiempo"],
            "dimension_levels": {"tiempo": "year"},
            "aggregation_functions": ["sum"],
            "filters": {"año": 2025},
            "limit": 5
        }
        
        response = requests.post(f"{base_url}/query", json=query_data)
        if response.status_code == 200:
            data = response.json()
            if data['success']:
                print(f"✅ Consulta exitosa: {data['data']['record_count']} registros")
                print(f"⏱️ Tiempo: {data['data']['execution_time']:.3f}s")
            else:
                print(f"❌ Error en consulta: {data.get('error')}")
        else:
            print(f"❌ Error HTTP: {response.status_code}")
            print(f"Respuesta: {response.text}")
        
    except requests.exceptions.ConnectionError:
        print("❌ No se puede conectar al servidor. Asegúrate de que la aplicación esté ejecutándose.")
    except Exception as e:
        print(f"❌ Error en pruebas de API: {str(e)}")

if __name__ == "__main__":
    print("🚀 Iniciando pruebas del sistema OLAP de SugarBI")
    print("=" * 60)
    
    # Probar motor OLAP directamente
    test_olap_engine()
    
    # Probar endpoints de la API
    test_api_endpoints()
    
    print("\n" + "=" * 60)
    print("🏁 Pruebas completadas")

