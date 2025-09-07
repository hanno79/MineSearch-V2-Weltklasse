#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Test für Enhanced Batch Search System
"""

import requests
import json
import time

# API URL
BASE_URL = "http://localhost:8000"

def test_csv_upload():
    """Test CSV Upload"""
    print("🧪 1. TESTE CSV UPLOAD")
    
    with open("test_batch_enhanced.csv", "rb") as f:
        response = requests.post(
            f"{BASE_URL}/api/upload-csv",
            files={"file": f}
        )
    
    if response.status_code == 200:
        print("✅ CSV Upload erfolgreich")
        # Extrahiere Session ID aus HTML Response
        html_content = response.text
        session_id = None
        
        # Primitive Session ID Extraktion aus HTML
        import re
        match = re.search(r'Session ID: ([a-f0-9\-]+)', html_content)
        if match:
            session_id = match.group(1)
            print(f"📋 Session ID: {session_id}")
            return session_id
    else:
        print(f"❌ CSV Upload fehlgeschlagen: {response.status_code}")
        print(f"Response: {response.text[:200]}")
        return None

def test_batch_search_modes(session_id):
    """Test verschiedene Batch-Modi"""
    
    # Test 1: First N Mode (klassisch)
    print("\n🧪 2. TESTE FIRST_N MODE")
    response = requests.post(
        f"{BASE_URL}/api/batch-search",
        data={
            "session_id": session_id,
            "selection_mode": "first_n",
            "count": "3",
            "selected_models": "openrouter:deepseek-free",
            "search_type": "standard"
        }
    )
    
    if response.status_code == 200:
        print("✅ First_N Mode Test erfolgreich")
        print(f"📊 Response length: {len(response.text)}")
    else:
        print(f"❌ First_N Mode fehlgeschlagen: {response.status_code}")
        print(f"Error: {response.text[:200]}")
    
    time.sleep(2)
    
    # Test 2: Range Mode
    print("\n🧪 3. TESTE RANGE MODE")
    response = requests.post(
        f"{BASE_URL}/api/batch-search",
        data={
            "session_id": session_id,
            "selection_mode": "range",
            "start_position": "5",
            "range_count": "3",
            "selected_models": "openrouter:deepseek-free",
            "search_type": "standard"
        }
    )
    
    if response.status_code == 200:
        print("✅ Range Mode Test erfolgreich")
        print(f"📊 Response length: {len(response.text)}")
    else:
        print(f"❌ Range Mode fehlgeschlagen: {response.status_code}")
        print(f"Error: {response.text[:200]}")
    
    time.sleep(2)
    
    # Test 3: Random Mode
    print("\n🧪 4. TESTE RANDOM MODE")
    response = requests.post(
        f"{BASE_URL}/api/batch-search",
        data={
            "session_id": session_id,
            "selection_mode": "random",
            "random_count": "2",
            "selected_models": "openrouter:deepseek-free",
            "search_type": "standard"
        }
    )
    
    if response.status_code == 200:
        print("✅ Random Mode Test erfolgreich")
        print(f"📊 Response length: {len(response.text)}")
    else:
        print(f"❌ Random Mode fehlgeschlagen: {response.status_code}")
        print(f"Error: {response.text[:200]}")

def test_edge_cases(session_id):
    """Test Edge Cases und Validierung"""
    print("\n🧪 5. TESTE EDGE CASES")
    
    # Test: Range über CSV-Grenzen
    print("   - Range über CSV-Grenzen")
    response = requests.post(
        f"{BASE_URL}/api/batch-search",
        data={
            "session_id": session_id,
            "selection_mode": "range",
            "start_position": "12",  # CSV hat nur 15 Minen
            "range_count": "10",     # Zu viele
            "selected_models": "openrouter:deepseek-free",
            "search_type": "standard"
        }
    )
    
    if response.status_code == 200:
        print("   ✅ Edge Case handled korrekt")
    else:
        print(f"   ❌ Edge Case fehlgeschlagen: {response.status_code}")
    
    # Test: Zufällige Anzahl über CSV-Größe
    print("   - Zufällige Anzahl über CSV-Größe")
    response = requests.post(
        f"{BASE_URL}/api/batch-search",
        data={
            "session_id": session_id,
            "selection_mode": "random",
            "random_count": "20",  # CSV hat nur 15 Minen
            "selected_models": "openrouter:deepseek-free",
            "search_type": "standard"
        }
    )
    
    if response.status_code == 200:
        print("   ✅ Edge Case handled korrekt")
    else:
        print(f"   ❌ Edge Case fehlgeschlagen: {response.status_code}")

if __name__ == "__main__":
    print("🚀 ENHANCED BATCH SEARCH SYSTEM TEST")
    print("=" * 50)
    
    # Upload CSV
    session_id = test_csv_upload()
    if not session_id:
        print("❌ Test abgebrochen - CSV Upload fehlgeschlagen")
        exit(1)
    
    # Test verschiedene Modi
    test_batch_search_modes(session_id)
    
    # Test Edge Cases
    test_edge_cases(session_id)
    
    print("\n🎉 ENHANCED BATCH TEST ABGESCHLOSSEN!")
    print("Überprüfen Sie die Server-Logs für detaillierte Informationen.")