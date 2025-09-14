#!/usr/bin/env python3
"""
Script para probar el endpoint de cosecha
"""

import requests
import json

def test_cosecha():
    url = "http://localhost:5001/api/cosecha/top"
    params = {
        "criterio": "toneladas",
        "limit": 5
    }
    
    try:
        print("🧪 Probando endpoint de cosecha...")
        print(f"URL: {url}")
        print(f"Parámetros: {params}")
        
        response = requests.get(url, params=params)
        
        print(f"\n📊 Respuesta:")
        print(f"Status Code: {response.status_code}")
        print(f"Headers: {dict(response.headers)}")
        
        try:
            response_data = response.json()
            print(f"JSON Response: {json.dumps(response_data, indent=2)}")
        except:
            print(f"Text Response: {response.text}")
            
    except Exception as e:
        print(f"❌ Error: {str(e)}")

if __name__ == "__main__":
    test_cosecha()
