#!/usr/bin/env python3
"""
Author: rahn
Datum: 04.08.2025
Version: 1.0
Beschreibung: Test-Script für Progress-Tracking System
"""

import asyncio
import sys
import os
from pathlib import Path

# Backend-Pfad hinzufügen
backend_path = Path(__file__).parent / "minesearch_v2" / "backend"
sys.path.insert(0, str(backend_path))

try:
    from progress_tracker import progress_tracker, ProgressEventType
    print("✅ Progress-Tracker erfolgreich importiert")
except ImportError as e:
    print(f"❌ Fehler beim Importieren des Progress-Trackers: {e}")
    sys.exit(1)

async def test_progress_tracker():
    """Test der Progress-Tracker Funktionalität"""
    print("\n=== Progress-Tracker System Test ===\n")
    
    # Test 1: Session erstellen
    print("🔧 Test 1: Session-Erstellung")
    session_id = progress_tracker.create_session("Test Mine", total_steps=5)
    print(f"   Session erstellt: {session_id}")
    
    # Test 2: Session-Status abrufen
    print("\n🔧 Test 2: Session-Status")
    status = progress_tracker.get_session_status(session_id)
    print(f"   Status: {status}")
    
    # Test 3: Search starten
    print("\n🔧 Test 3: Search Start")
    progress_tracker.start_search(session_id, "Test Mine", "test-model")
    
    # Test 4: Progress-Updates (mathematisch korrekt)
    print("\n🔧 Test 4: Progress-Updates")
    for step in range(1, 6):
        progress_tracker.update_progress(
            session_id, 
            step, 
            f"Schritt {step} von 5",
            "Test Mine",
            "test-model"
        )
        
        # Prüfe mathematische Korrektheit: (step / 5) * 100
        expected_percentage = (step / 5) * 100
        status = progress_tracker.get_session_status(session_id)
        actual_percentage = status['progress_percentage']
        
        print(f"   Schritt {step}: {actual_percentage}% (erwartet: {expected_percentage}%)")
        
        if abs(actual_percentage - expected_percentage) > 0.01:
            print(f"   ❌ FEHLER: Falsche Berechnung!")
            return False
        else:
            print(f"   ✅ Korrekte Berechnung: ({step}/5)*100 = {actual_percentage}%")
        
        await asyncio.sleep(0.1)  # Kurze Pause
    
    # Test 5: Search abschließen
    print("\n🔧 Test 5: Search Completion")
    progress_tracker.complete_search(session_id, "Test Mine", 42)
    
    # Test 6: Event-History
    print("\n🔧 Test 6: Event-History")
    history = progress_tracker.get_session_history(session_id)
    print(f"   History-Events: {len(history)}")
    for event in history:
        print(f"   - {event['event_type']}: {event['current_operation']} ({event['progress_percentage']}%)")
    
    # Test 7: Session beenden
    print("\n🔧 Test 7: Session Ende")
    progress_tracker.end_session(session_id)
    
    print("\n✅ Alle Tests erfolgreich!")
    return True

async def test_error_handling():
    """Test der Error-Handling Funktionalität"""
    print("\n=== Error-Handling Test ===\n")
    
    # Test 1: Session mit Fehler
    print("🔧 Test 1: Error-Handling")
    session_id = progress_tracker.create_session("Error Test Mine", total_steps=3)
    
    progress_tracker.start_search(session_id, "Error Test Mine", "error-model")
    progress_tracker.update_progress(session_id, 1, "Schritt 1 ok", "Error Test Mine", "error-model")
    progress_tracker.error_search(session_id, "Simulierter Netzwerk-Fehler", "Error Test Mine")
    
    # Prüfe History
    history = progress_tracker.get_session_history(session_id)
    error_events = [e for e in history if e['event_type'] == 'search_error']
    
    if error_events:
        print(f"   ✅ Error-Event korrekt registriert: {error_events[0]['error_message']}")
    else:
        print("   ❌ Kein Error-Event gefunden")
        return False
    
    progress_tracker.end_session(session_id)
    print("   ✅ Error-Handling Test erfolgreich!")
    return True

async def test_mathematical_precision():
    """Test der mathematischen Präzision der Progress-Berechnung"""
    print("\n=== Mathematische Präzision Test ===\n")
    
    test_cases = [
        (1, 3),    # 33.333...%
        (2, 7),    # 28.571...%
        (5, 13),   # 38.461...%
        (10, 17),  # 58.823...%
    ]
    
    for step, total in test_cases:
        session_id = progress_tracker.create_session(f"Math Test {step}/{total}", total_steps=total)
        progress_tracker.update_progress(session_id, step, f"Test {step}/{total}", "Math Mine", "math-model")
        
        # Mathematisch korrekte Berechnung
        expected = (step / total) * 100
        
        status = progress_tracker.get_session_status(session_id)
        actual = status['progress_percentage']
        
        print(f"   Schritt {step}/{total}: {actual:.3f}% (erwartet: {expected:.3f}%)")
        
        if abs(actual - expected) > 0.001:
            print(f"   ❌ FEHLER: Mathematische Ungenauigkeit!")
            return False
        else:
            print(f"   ✅ Mathematisch korrekt: ({step}/{total})*100 = {actual:.3f}%")
        
        progress_tracker.end_session(session_id)
    
    print("   ✅ Alle mathematischen Tests bestanden!")
    return True

async def main():
    """Haupttest-Funktion"""
    print("🚀 Starte Progress-Tracking System Tests...")
    
    try:
        # Grundfunktionalität testen
        if not await test_progress_tracker():
            print("❌ Grundfunktionalitäts-Test fehlgeschlagen")
            return False
        
        # Error-Handling testen
        if not await test_error_handling():
            print("❌ Error-Handling-Test fehlgeschlagen")
            return False
        
        # Mathematische Präzision testen
        if not await test_mathematical_precision():
            print("❌ Mathematik-Test fehlgeschlagen")
            return False
        
        print("\n🎉 ALLE TESTS ERFOLGREICH! 🎉")
        print("\nProgress-Tracking System ist bereit für den Einsatz:")
        print("- ✅ Korrekte Mathematik: (completed / total) * 100")
        print("- ✅ Session-Management funktioniert")
        print("- ✅ WebSocket-Broadcasting vorbereitet")
        print("- ✅ Error-Handling implementiert")
        print("- ✅ Event-History verfügbar")
        
        return True
        
    except Exception as e:
        print(f"❌ Unerwarteter Fehler: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    success = asyncio.run(main())
    sys.exit(0 if success else 1)