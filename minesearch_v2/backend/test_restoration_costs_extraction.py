"""
Author: rahn
Datum: 26.07.2025
Version: 1.0
Beschreibung: Test der Restaurationskosten-Extraktion mit echten Minen-Daten
"""

import sys
import os
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

import logging
from extraction_restoration_costs import RestorationCostExtractor
from data_extraction import DataExtractor

# Setup Logging
logging.basicConfig(level=logging.DEBUG)
logger = logging.getLogger(__name__)

def test_restoration_cost_extractor():
    """Teste die RestorationCostExtractor direkt"""
    
    extractor = RestorationCostExtractor()
    
    # Test Daten mit verschiedenen Formaten
    test_texts = [
        # Test 1: Standard ARO
        """Eleonore Gold Mine in Quebec, Canada operates under strict environmental regulations. 
        Asset Retirement Obligation (ARO): CAD$45.3 million as of December 2023. The mine produces 
        approximately 300,000 ounces of gold annually.""",
        
        # Test 2: Closure Costs
        """The Lac des Iles Mine closure costs are estimated at $12.5 million CAD for site restoration 
        and environmental remediation work scheduled for 2025.""",
        
        # Test 3: Environmental Liability
        """Environmental liabilities for the Abacus Mine total CAD$8.7 million, including progressive 
        rehabilitation and final closure activities.""",
        
        # Test 4: Kleine Beträge
        """Exploration closure plan requires $25,000 CAD initial restoration guarantee as per 
        Quebec mining regulations.""",
        
        # Test 5: Französisch (Quebec)
        """Les coûts de restauration pour la mine d'Eleonore sont estimés à 45,3 millions CAD$, 
        incluant la garantie financière et les travaux de fermeture."""
    ]
    
    print("=" * 80)
    print("TEST: RestorationCostExtractor - Direkte Extraktion")
    print("=" * 80)
    
    for i, text in enumerate(test_texts, 1):
        print(f"\n--- Test {i} ---")
        print(f"Text: {text[:100]}...")
        
        result = extractor.extract_restoration_costs(text)
        
        if result:
            print(f"✅ GEFUNDEN:")
            for key, value in result.items():
                print(f"   {key}: {value}")
        else:
            print("❌ NICHTS GEFUNDEN")

def test_data_extractor_integration():
    """Teste die Integration in DataExtractor"""
    
    extractor = DataExtractor()
    
    # Test mit kompletter Perplexity-ähnlicher Response
    test_response = """# Eleonore Gold Mine - Comprehensive Information

## Basic Information
- **Name**: Eleonore Gold Mine
- **Location**: James Bay region, Quebec, Canada
- **Owner**: Newmont Corporation (100%)
- **Operator**: Newmont Corporation
- **Status**: Active (production since 2015)

## Financial Information
The Eleonore mine has significant environmental obligations:
- **Asset Retirement Obligation (ARO)**: CAD$45.3 million (as of December 2023)
- **Annual closure costs provision**: CAD$2.1 million
- **Environmental liability**: CAD$8.2 million for progressive rehabilitation

## Coordinates
- **Latitude**: 52.7000°N
- **Longitude**: 76.0833°W

## Production Details
- **Commodity**: Gold
- **Mine Type**: Underground
- **Annual Production**: 300,000 oz gold (2023)
- **Production Start**: 2015

## Sources
[1] Newmont Annual Report 2023
[2] Quebec GESTIM Database
[3] NI 43-101 Technical Report 2023"""
    
    print("\n" + "=" * 80)
    print("TEST: DataExtractor Integration - Vollständige Extraktion")
    print("=" * 80)
    
    result = extractor.extract_structured_data(test_response, "Eleonore", "Canada")
    
    print(f"\n📊 EXTRAHIERTE DATEN:")
    print("-" * 40)
    
    for field, value in result.items():
        if value and str(value).strip() and field != '_source_mapping':
            print(f"{field}: {value}")
    
    # Fokus auf Restaurationskosten
    resto_costs = result.get('Restaurationskosten', '')
    print(f"\n🔍 RESTAURATIONSKOSTEN DETAIL:")
    print(f"   Wert: '{resto_costs}'")
    print(f"   Typ: {type(resto_costs)}")
    print(f"   Leer: {not resto_costs or str(resto_costs).strip() == ''}")

def test_with_database_samples():
    """Teste mit echten Daten aus der Datenbank"""
    
    try:
        from database.manager import DatabaseManager
        db = DatabaseManager()
        
        # Hole die letzten 5 Suchergebnisse
        recent_searches = db.get_recent_searches(limit=5)
        
        if not recent_searches:
            print("\n⚠️  Keine Suchergebnisse in der Datenbank gefunden")
            return
        
        print("\n" + "=" * 80)
        print("TEST: Echte Datenbank-Samples")
        print("=" * 80)
        
        extractor = RestorationCostExtractor()
        
        for search in recent_searches:
            print(f"\n--- Mine: {search.mine_name} ---")
            print(f"Modell: {search.model_used}")
            print(f"Land: {search.country}")
            
            # Teste mit den gespeicherten strukturierten Daten
            if hasattr(search, 'structured_data') and search.structured_data:
                resto_value = search.structured_data.get('Restaurationskosten', '')
                print(f"Gespeicherte Restaurationskosten: '{resto_value}'")
                
                # Teste ob diese korrekt extrahiert wurden
                if resto_value and resto_value not in ['X', '']:
                    print(f"✅ Restaurationskosten gefunden: {resto_value}")
                else:
                    print(f"❌ Keine Restaurationskosten gespeichert")
            else:
                print("⚠️  Keine strukturierten Daten verfügbar")
                
    except ImportError:
        print("\n⚠️  DatabaseManager nicht verfügbar - überspringe Datenbank-Tests")
    except Exception as e:
        print(f"\n❌ Fehler beim Datenbanktest: {e}")

def main():
    """Haupttest-Funktion"""
    
    print("🔬 RESTAURATIONSKOSTEN-EXTRAKTION VALIDIERUNG")
    print("🤖 ExtractionValidator Agent - Umfassende Tests")
    
    try:
        # Test 1: Direkte RestorationCostExtractor
        test_restoration_cost_extractor()
        
        # Test 2: DataExtractor Integration
        test_data_extractor_integration()
        
        # Test 3: Echte Datenbank-Samples
        test_with_database_samples()
        
        print("\n" + "=" * 80)
        print("✅ ALLE TESTS ABGESCHLOSSEN")
        print("=" * 80)
        
    except Exception as e:
        print(f"\n❌ FEHLER: {e}")
        import traceback
        traceback.print_exc()

if __name__ == "__main__":
    main()