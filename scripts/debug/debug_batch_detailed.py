#!/usr/bin/env python3
"""
Detailierte Debug-Analyse der Batch-API
Tracke die exakten Werte zwischen Provider-Suche und HTML-Ausgabe
"""

import requests
import json
import sys
import os

# Add backend to path (relative to script location)
script_dir = os.path.dirname(os.path.abspath(__file__))
backend_path = os.path.join(script_dir, '..', '..', 'backend')
sys.path.append(backend_path)

def detailed_batch_debug():
    print("🔍 DETAILLIERTE BATCH-API VERFOLGUNG")
    
    # 1. PRÜFE DIREKT NACH PROVIDER-SUCHE (vor Konsolidierung)
    print("\n1️⃣ TESTE DIREKTE PROVIDER-SUCHE")
    
    from minesearch.providers.registry import provider_registry
    from minesearch.config import config
    import asyncio
    
    async def test_provider():
        # Initialize Provider Registry
        if not provider_registry._providers:
            provider_registry.initialize(config.PROVIDERS)
        
        provider = provider_registry.get_provider_for_model('openrouter:deepseek-free')
        if not provider:
            print("❌ Provider nicht gefunden")
            return None
            
        # Direkte Provider-Suche (wie in Batch-API)
        query = "Éléonore mine Canada Gold"
        model_name = 'deepseek-free'
        options = {
            'mine_name': 'Éléonore',
            'country': 'Canada',
            'commodity': 'Gold',
            'region': 'Quebec'
        }
        
        print(f"🔍 Provider-Aufruf: {query}")
        search_result = await provider.search(query, model_name, options)
        
        if search_result and search_result.success:
            structured_data = search_result.structured_data or {}
            
            print(f"✅ Provider-Success: {len(structured_data)} Felder")
            
            # Zähle gefüllte Felder (wie in Batch-API)
            filled_fields = [
                (k, v) for k, v in structured_data.items() 
                if v and str(v).strip() and str(v).strip() not in ['', 'None', 'null', 'nichts gefunden']
            ]
            
            print(f"📊 Gefüllte Felder: {len(filled_fields)}/{len(structured_data)}")
            
            # Zeige kritische Felder
            critical_fields = ['Eigentümer', 'Betreiber', 'x-Koordinate', 'y-Koordinate', 'Aktivitätsstatus']
            print("\n🔍 KRITISCHE FELDER NACH PROVIDER:")
            for field in critical_fields:
                value = structured_data.get(field, '(nicht vorhanden)')
                print(f"  {field}: {repr(value)}")
            
            return structured_data
        else:
            print("❌ Provider-Suche fehlgeschlagen")
            return None
    
    provider_data = asyncio.run(test_provider())
    
    if not provider_data:
        print("❌ Kann nicht weiter debuggen - Provider-Suche fehlgeschlagen")
        return
    
    # 2. SIMULIERE BATCH-API KONSOLIDIERUNG
    print("\n2️⃣ TESTE BATCH-API KONSOLIDIERUNG")
    
    # Simuliere individual_results Struktur (wie in Batch-API)
    individual_results = [{
        'model_id': 'openrouter:deepseek-free',
        'success': True,
        'data': {
            'structured_data': provider_data,
            'raw_content': 'mock_content',
            'field_count': len(provider_data),
            'filled_field_count': len([v for v in provider_data.values() if v and str(v).strip() and str(v).strip() not in ['', 'None', 'null', 'nichts gefunden']])
        }
    }]
    
    # Simuliere Batch-API Konsolidierungslogik (Zeilen 615-630)
    successful_models = [r for r in individual_results if r['success']]
    best_structured_data = {}
    
    if successful_models:
        max_filled_fields = 0
        for model_result in successful_models:
            model_data = model_result.get('data', {})
            structured_data = model_data.get('structured_data', {})
            
            if structured_data:
                filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() not in ['-', '', 'None', 'null', 'nichts gefunden']])
                
                if filled_fields > max_filled_fields:
                    max_filled_fields = filled_fields
                    best_structured_data = structured_data
    
    print(f"📊 Nach Konsolidierung: {len(best_structured_data)} Felder")
    
    # Vergleiche kritische Felder vor/nach Konsolidierung
    critical_fields = ['Eigentümer', 'Betreiber', 'x-Koordinate', 'y-Koordinate', 'Aktivitätsstatus']
    print("\n🔍 KRITISCHE FELDER NACH KONSOLIDIERUNG:")
    for field in critical_fields:
        orig_value = provider_data.get(field, '(nicht vorhanden)')
        cons_value = best_structured_data.get(field, '(nicht vorhanden)')
        
        if orig_value != cons_value:
            print(f"  ⚠️ {field}: {repr(orig_value)} → {repr(cons_value)} (GEÄNDERT)")
        else:
            print(f"  ✅ {field}: {repr(cons_value)}")
    
    # 3. TESTE HTML-GENERIERUNG
    print("\n3️⃣ TESTE HTML-GENERIERUNG")
    
    # Simuliere result_data Struktur (wie in Batch-API)
    result_data = {
        "mine_name": "Éléonore",
        "country": "Canada",
        "commodity": "Gold",
        "region": "Quebec",
        "success": True,
        "data": {
            "structured_data": best_structured_data,
            "individual_results": individual_results,
            "successful_models": len(successful_models),
            "failed_models": 0,
            "total_models": 1
        }
    }
    
    results = [result_data]
    
    # Teste HTML-Generierung
    from minesearch.html_utils import create_batch_results_table
    html_output = create_batch_results_table(results)
    
    # Analysiere HTML
    nichts_gefunden_count = html_output.count('nichts gefunden')
    
    # Suche nach kritischen Werten im HTML
    critical_values = ['Newmont', '52.883', 'aktiv', 'Untertage']
    found_values = []
    for value in critical_values:
        if value.lower() in html_output.lower():
            found_values.append(value)
    
    print(f"📊 HTML-Analyse:")
    print(f"  ❌ 'nichts gefunden': {nichts_gefunden_count}")
    print(f"  ✅ Kritische Werte gefunden: {found_values}")
    
    # 4. FINALE DIAGNOSE
    print("\n4️⃣ DIAGNOSE")
    
    provider_filled = len([v for v in provider_data.values() if v and str(v).strip() and str(v).strip() not in ['', 'None', 'null']])
    consolidated_filled = len([v for v in best_structured_data.values() if v and str(v).strip() and str(v).strip() not in ['', 'None', 'null']])
    
    print(f"📊 DATEN-VERLAUF:")
    print(f"  Provider: {provider_filled}/{len(provider_data)} Felder")
    print(f"  Konsolidierung: {consolidated_filled}/{len(best_structured_data)} Felder") 
    print(f"  HTML: {len(found_values)} kritische Werte sichtbar")
    
    if provider_filled > 5 and consolidated_filled < 5:
        print("🔥 PROBLEM IN KONSOLIDIERUNG!")
    elif consolidated_filled > 5 and len(found_values) < 2:
        print("🔥 PROBLEM IN HTML-GENERIERUNG!")
    elif provider_filled < 5:
        print("🔥 PROBLEM IN PROVIDER-SUCHE!")
    else:
        print("✅ Alle Stufen funktionieren - Problem woanders")
    
    # Speichere Debugging-Daten
    debug_data = {
        'provider_data': provider_data,
        'consolidated_data': best_structured_data,
        'html_contains_nichts_gefunden': nichts_gefunden_count,
        'html_critical_values': found_values
    }
    
    with open('/tmp/batch_debug_detailed.json', 'w') as f:
        json.dump(debug_data, f, indent=2, default=str)
    
    print("\n📁 Debug-Daten gespeichert: /tmp/batch_debug_detailed.json")

if __name__ == "__main__":
    detailed_batch_debug()