#!/usr/bin/env python3
"""
Script para probar el chatbot con LangChain
"""

import requests
import json

def test_langchain_chat():
    url = "http://localhost:5001/api/chat/langchain"
    data = {
        "query": "muestra la tendencia de producción por mes en 2025"
    }
    
    try:
        print("🧪 Probando chatbot con LangChain...")
        print(f"URL: {url}")
        print(f"Consulta: {data['query']}")
        
        response = requests.post(url, json=data)
        
        print(f"\n📊 Respuesta:")
        print(f"Status Code: {response.status_code}")
        
        try:
            response_data = response.json()
            print(f"Success: {response_data.get('success', False)}")
            
            if response_data.get('success'):
                data_result = response_data.get('data', {})
                print(f"Registros encontrados: {data_result.get('record_count', 0)}")
                print(f"Respuesta natural: {data_result.get('natural_response', 'N/A')}")
                print(f"Tipo de consulta: {data_result.get('intent', {}).get('type', 'N/A')}")
                print(f"Métrica: {data_result.get('intent', {}).get('metric', 'N/A')}")
                print(f"Dimensión: {data_result.get('intent', {}).get('dimension', 'N/A')}")
                
                if data_result.get('visualization'):
                    print(f"Visualización: {data_result['visualization']['type']}")
            else:
                print(f"Error: {response_data.get('error', 'Error desconocido')}")
                
        except Exception as e:
            print(f"Error parseando JSON: {e}")
            print(f"Respuesta raw: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_langchain_chat()
