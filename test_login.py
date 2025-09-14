#!/usr/bin/env python3
"""
Script para probar el endpoint de login
"""

import requests
import json

def test_login():
    url = "http://localhost:5001/auth/api/login"
    data = {
        "username": "admin",
        "password": "admin123"
    }
    
    try:
        print("🧪 Probando endpoint de login...")
        print(f"URL: {url}")
        print(f"Datos: {data}")
        
        response = requests.post(url, json=data)
        
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
    test_login()
