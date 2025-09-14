#!/usr/bin/env python3
"""
Script para probar el pipeline completo de NLP
"""

import sys
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent
sys.path.append(str(root_dir))

from chatbot.query_parser import QueryParser
from chatbot.sql_generator import SQLGenerator

def test_nlp_pipeline():
    print("🧪 Probando pipeline de NLP...")
    
    # Inicializar componentes
    query_parser = QueryParser()
    sql_generator = SQLGenerator()
    
    # Consultas de prueba
    test_queries = [
        "muestra la tendencia de producción por mes en 2025",
        "top 10 fincas por producción",
        "mejores variedades por TCH",
        "promedio de brix por finca"
    ]
    
    for query in test_queries:
        print(f"\n📝 Consulta: '{query}'")
        
        try:
            # Paso 1: Parsear consulta
            intent = query_parser.parse(query)
            print(f"✅ Intent parseado:")
            print(f"   - Tipo: {intent.query_type.value}")
            print(f"   - Métrica: {intent.metric.value}")
            print(f"   - Dimensión: {intent.dimension.value}")
            print(f"   - Límite: {intent.limit}")
            print(f"   - Filtros: {intent.filters}")
            
            # Paso 2: Generar SQL
            sql_query = sql_generator.generate_sql(intent)
            print(f"✅ SQL generado:")
            print(f"   {sql_query}")
            
        except Exception as e:
            print(f"❌ Error: {str(e)}")
            import traceback
            traceback.print_exc()

if __name__ == "__main__":
    test_nlp_pipeline()
