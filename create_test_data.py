#!/usr/bin/env python3
"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Erstelle Test-Daten für Frontend-Validierung
"""

import sys
import os
sys.path.append('/app/minesearch_v2/backend')

import json
from datetime import datetime
from database import db_manager
from database.models import SearchResult

def create_test_entries():
    """Erstelle Test-Einträge in der Datenbank"""
    print("🔧 Erstelle Test-Daten für Frontend-Validierung...")
    
    test_entries = [
        {
            "mine_name": "Demo Mine Alpha",
            "country": "Canada", 
            "region": "Quebec",
            "model_used": "test-model-alpha",
            "structured_data": {
                "Name": "Demo Mine Alpha",
                "Country": "Canada",
                "Region": "Quebec",
                "Eigentümer": "Alpha Mining Corp [1]",
                "Betreiber": "Alpha Operations [1,2]",
                "x-Koordinate": "45.123456",
                "y-Koordinate": "-73.987654",
                "Aktivitätsstatus": "Aktiv [1]",
                "Restaurationskosten": "X",
                "Jahr der Aufnahme der Kosten": "X",
                "Jahr der Erstellung des Dokumentes": "X",
                "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "Gold, Silber [1,2]",
                "Minentyp (Untertage/ Open-Pit/ usw.)": "Open-Pit [2]",
                "Produktionsstart": "2008",
                "Produktionsende": "noch aktiv",
                "Fördermenge/Jahr": "75000 oz/Jahr [1]",
                "Fläche der Mine in qkm": "3.2",
                "Quellenangaben": "[1] Alpha Corp Report: https://alpha-mining.com/report\\n[2] Quebec Mining Database: https://mern.gouv.qc.ca/alpha"
            },
            "source_mapping": {
                "sources": {
                    "1": {"url": "https://alpha-mining.com/report", "title": "Alpha Corp Report", "type": "industry", "reliability": 0.8},
                    "2": {"url": "https://mern.gouv.qc.ca/alpha", "title": "Quebec Mining Database", "type": "government", "reliability": 0.9}
                },
                "field_sources": {
                    "Eigentümer": [1], "Betreiber": [1, 2], "Aktivitätsstatus": [1],
                    "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": [1, 2], "Minentyp (Untertage/ Open-Pit/ usw.)": [2], "Fördermenge/Jahr": [1]
                }
            }
        },
        {
            "mine_name": "Beta Mining Site",
            "country": "Canada",
            "region": "Quebec", 
            "model_used": "test-model-beta",
            "structured_data": {
                "Name": "Beta Mining Site",
                "Country": "Canada",
                "Region": "Quebec",
                "Eigentümer": "X",
                "Betreiber": "Beta Operators Ltd [1]",
                "x-Koordinate": "46.789012",
                "y-Koordinate": "-74.123456",
                "Aktivitätsstatus": "Geschlossen [1,2]",
                "Restaurationskosten": "CAD$5.2 Million [2]",
                "Jahr der Aufnahme der Kosten": "2023 [2]",
                "Jahr der Erstellung des Dokumentes": "X",
                "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "Kupfer, Nickel [1]",
                "Minentyp (Untertage/ Open-Pit/ usw.)": "Untertage [1]",
                "Produktionsstart": "1995",
                "Produktionsende": "2022 [2]",
                "Fördermenge/Jahr": "Mine geschlossen",
                "Fläche der Mine in qkm": "1.8",
                "Quellenangaben": "[1] Beta Operations Report: https://beta-mining.ca/final-report\\n[2] Closure Documentation: https://environment.gouv.qc.ca/beta-closure"
            },
            "source_mapping": {
                "sources": {
                    "1": {"url": "https://beta-mining.ca/final-report", "title": "Beta Operations Report", "type": "industry", "reliability": 0.7},
                    "2": {"url": "https://environment.gouv.qc.ca/beta-closure", "title": "Closure Documentation", "type": "government", "reliability": 0.9}
                },
                "field_sources": {
                    "Betreiber": [1], "Aktivitätsstatus": [1, 2], "Restaurationskosten": [2],
                    "Jahr der Aufnahme der Kosten": [2], "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": [1], 
                    "Minentyp (Untertage/ Open-Pit/ usw.)": [1], "Produktionsende": [2]
                }
            }
        },
        {
            "mine_name": "Gamma Exploration",
            "country": "Canada",
            "region": "Quebec",
            "model_used": "test-model-gamma",
            "structured_data": {
                "Name": "Gamma Exploration",
                "Country": "Canada",
                "Region": "Quebec",
                "Eigentümer": "Gamma Resources Inc [1]",
                "Betreiber": "X",
                "x-Koordinate": "X",
                "y-Koordinate": "X",
                "Aktivitätsstatus": "nur Exploration",
                "Restaurationskosten": "X",
                "Jahr der Aufnahme der Kosten": "X",
                "Jahr der Erstellung des Dokumentes": "X",
                "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": "Gold [1]",
                "Minentyp (Untertage/ Open-Pit/ usw.)": "noch geplant",
                "Produktionsstart": "X",
                "Produktionsende": "X",
                "Fördermenge/Jahr": "nur Exploration",
                "Fläche der Mine in qkm": "X",
                "Quellenangaben": "[1] Gamma Resources Exploration Report: https://gamma-resources.com/exploration"
            },
            "source_mapping": {
                "sources": {
                    "1": {"url": "https://gamma-resources.com/exploration", "title": "Gamma Resources Exploration Report", "type": "industry", "reliability": 0.6}
                },
                "field_sources": {
                    "Eigentümer": [1], "Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)": [1]
                }
            }
        }
    ]
    
    session = db_manager.get_session()
    try:
        for i, entry in enumerate(test_entries, 1):
            print(f"  Erstelle Eintrag {i}: {entry['mine_name']}")
            
            search_result = SearchResult(
                mine_name=entry["mine_name"],
                country=entry["country"],
                region=entry["region"],
                model_used=entry["model_used"],
                search_type="test_data",
                search_timestamp=datetime.now(),
                structured_data=entry["structured_data"],
                source_mapping=entry["source_mapping"],
                success=True
            )
            
            session.add(search_result)
        
        session.commit()
        print(f"✅ {len(test_entries)} Test-Einträge erfolgreich erstellt")
        
        # Verifikation
        count = session.query(SearchResult).count()
        print(f"📊 Gesamt-Einträge in Datenbank: {count}")
        
        return True
        
    except Exception as e:
        print(f"❌ Fehler beim Erstellen der Test-Daten: {e}")
        session.rollback()
        return False
        
    finally:
        session.close()

def main():
    print("🧪 Erstelle Test-Daten für stabile Frontend-Anzeige")
    print("=" * 60)
    
    success = create_test_entries()
    
    print("\n" + "=" * 60)
    if success:
        print("✅ Test-Daten erfolgreich erstellt!")
        print("🎯 Frontend sollte jetzt Daten mit allen Datenkonsistenz-Features anzeigen:")
        print("  1. ✅ Normalisierte LEER-Werte als 'X'")
        print("  2. ✅ Saubere Minentypen ohne Präfixe")
        print("  3. ✅ Quellen-Referenzen [1,2,3] in Feldern")
        print("  4. ✅ Strukturierte Quellenangaben")
        print("  5. ✅ Source-Mapping Metadaten")
    else:
        print("❌ Fehler beim Erstellen der Test-Daten")

if __name__ == "__main__":
    main()