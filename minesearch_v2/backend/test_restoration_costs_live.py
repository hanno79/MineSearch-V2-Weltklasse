"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Live-Test der Restaurationskosten-Extraktion mit echter Suche
"""

import asyncio
import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from search_service import MineSearchService

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_live_restoration_costs():
    """Teste Restaurationskosten-Extraktion mit echter Mine-Suche"""
    
    print("🔴 LIVE TEST: Restaurationskosten-Extraktion")
    print("=" * 60)
    
    search_service = MineSearchService()
    
    # Test-Minen mit bekannten Restaurationskosten
    test_mines = [
        {
            'name': 'Eleonore',
            'country': 'Canada',
            'commodity': 'Gold',
            'expected': 'ARO/closure costs in CAD'
        },
        {
            'name': 'Abacus',
            'country': 'Canada', 
            'commodity': 'Gold',
            'expected': 'Initial restoration costs'
        }
    ]
    
    # Verwende kostenloses Modell
    model = "openrouter:meta-llama/llama-3.1-8b-instruct:free"
    
    for i, mine in enumerate(test_mines, 1):
        print(f"\n--- Test {i}: {mine['name']} ---")
        print(f"Land: {mine['country']}")
        print(f"Rohstoff: {mine['commodity']}")
        print(f"Erwartet: {mine['expected']}")
        
        try:
            result = await search_service.search_mine(
                mine_name=mine['name'],
                country=mine['country'],
                commodity=mine['commodity'],
                model=model
            )
            
            if result.get('success'):
                data = result.get('data', {})
                resto_costs = data.get('Restaurationskosten', '')
                
                print(f"✅ Suche erfolgreich")
                print(f"🔍 Restaurationskosten: '{resto_costs}'")
                
                if resto_costs and resto_costs not in ['X', '']:
                    print(f"✅ RESTAURATIONSKOSTEN EXTRAHIERT: {resto_costs}")
                else:
                    print(f"❌ Keine Restaurationskosten gefunden")
                
                # Zeige weitere relevante Felder
                relevant_fields = ['Eigentümer', 'Betreiber', 'Aktivitätsstatus', 'Country', 'Region']
                for field in relevant_fields:
                    value = data.get(field, '')
                    if value and value != 'X':
                        print(f"   {field}: {value}")
                        
            else:
                print(f"❌ Suche fehlgeschlagen: {result.get('error', 'Unbekannter Fehler')}")
                
        except Exception as e:
            print(f"❌ FEHLER: {e}")
    
    print("\n" + "=" * 60)
    print("✅ LIVE TEST ABGESCHLOSSEN")

async def main():
    """Hauptfunktion"""
    await test_live_restoration_costs()

if __name__ == "__main__":
    asyncio.run(main())