#!/usr/bin/env python3
"""
Quick System Status Check
"""

import requests
import subprocess
import sys

def check_system_status():
    print("🔍 MINESEARCH V2 SYSTEM STATUS CHECK")
    print("="*50)
    
    # Backend Check
    try:
        response = requests.get("http://localhost:8000/health", timeout=5)
        if response.status_code == 200:
            print("✅ Backend (Port 8000): LÄUFT")
            print(f"   Response: {response.json()}")
        else:
            print(f"❌ Backend (Port 8000): HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Backend (Port 8000): FEHLER - {e}")
    
    # Frontend Check
    try:
        response = requests.get("http://localhost:8080", timeout=5)
        if response.status_code == 200:
            print("✅ Frontend (Port 8080): LÄUFT")
            print(f"   Content-Length: {len(response.text)} bytes")
        else:
            print(f"❌ Frontend (Port 8080): HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ Frontend (Port 8080): FEHLER - {e}")
    
    # API Test
    try:
        response = requests.get("http://localhost:8000/api/models", timeout=5)
        if response.status_code == 200:
            models = response.json()
            print(f"✅ API Models: {len(models)} verfügbar")
        else:
            print(f"⚠️ API Models: HTTP {response.status_code}")
    except Exception as e:
        print(f"❌ API Models: FEHLER - {e}")
    
    # Process Check
    try:
        result = subprocess.run(['ps', 'aux'], capture_output=True, text=True)
        uvicorn_count = result.stdout.count('uvicorn')
        http_server_count = result.stdout.count('http.server')
        print(f"📊 Prozesse: {uvicorn_count} uvicorn, {http_server_count} http.server")
    except Exception as e:
        print(f"❌ Process Check: {e}")
    
    # Port Check
    try:
        result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True)
        port_8000 = ':8000' in result.stdout
        port_8080 = ':8080' in result.stdout
        print(f"🔌 Ports: 8000={port_8000}, 8080={port_8080}")
    except Exception as e:
        print(f"❌ Port Check: {e}")
    
    print("="*50)
    print("🌐 URLs zum Testen:")
    print("   Backend: http://localhost:8000")
    print("   Frontend: http://localhost:8080")
    print("   Health: http://localhost:8000/health")

if __name__ == "__main__":
    check_system_status()