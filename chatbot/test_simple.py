"""
Test simple para verificar el funcionamiento del parser y generador
"""

import sys
import os
from pathlib import Path

# Agregar el directorio raíz al path
root_dir = Path(__file__).parent.parent
sys.path.append(str(root_dir))

from chatbot.query_parser import QueryParser
from chatbot.sql_generator import SQLGenerator

def test_query(query_text):
    print(f"\n=== Probando consulta: '{query_text}' ===")
    
    try:
        # Paso 1: Parsear
        parser = QueryParser()
        intent = parser.parse(query_text)
        
        print(f"Tipo: {intent.query_type.value}")
        print(f"Métrica: {intent.metric.value}")
        print(f"Dimensión: {intent.dimension.value}")
        print(f"Filtros: {intent.filters}")
        print(f"Límite: {intent.limit}")
        
        # Paso 2: Generar SQL
        generator = SQLGenerator()
        sql = generator.generate_sql(intent)
        
        print(f"\nSQL generado:")
        print(sql)
        
        return True
        
    except Exception as e:
        print(f"ERROR: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    # Consultas de prueba
    test_queries = [
        "muestra el top 5 de fincas por producción",
        "top 10 fincas",
        "mejores variedades por TCH",
        "producción por zona"
    ]
    
    for query in test_queries:
        test_query(query)



