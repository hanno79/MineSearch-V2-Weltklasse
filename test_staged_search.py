"""
Author: rahn
Datum: 17.06.2025
Version: 1.0
Beschreibung: Test-Skript für die Staged Search Implementierung
"""

import asyncio
import sys
import os

from src.core.config import Config
from src.core.orchestrator import MineSearchOrchestrator
from src.agents.base_agent import MineQuery
from src.agents.factory import AgentFactory

async def test_staged_search():
    """Testet die staged search mit mehreren Agenten"""
    print("=== Test Staged Search ===\n")
    
    # Erstelle Config
    config = Config()
    
    # Status Callback für detaillierte Ausgabe
    def status_callback(message: str):
        print(f"[STATUS] {message}")
    
    # Erstelle Orchestrator
    orchestrator = MineSearchOrchestrator(config, status_callback)
    
    # Initialisiere
    print("Initialisiere Orchestrator...")
    await orchestrator.initialize()
    
    # Zeige verfügbare Agenten
    available_agents = list(orchestrator.agents.keys())
    print(f"\nVerfügbare Agenten: {len(available_agents)}")
    print(f"Agenten: {', '.join(available_agents[:10])}...")
    
    # Simuliere viele aktive Agenten (mehr als das alte Limit)
    orchestrator.active_agents = available_agents  # Nutze ALLE verfügbaren Agenten
    print(f"\nAktive Agenten gesetzt: {len(orchestrator.active_agents)}")
    
    # Erstelle Test-Query
    query = MineQuery(
        mine_name="Kidd Creek",
        region="Ontario", 
        country="Canada",
        languages=["en", "fr"],
        required_fields=[
            # Basic fields
            "betreiber", "operator", "koordinaten", "coordinates",
            "rohstofftyp", "commodity", "aktivitaetsstatus", "status",
            # Financial fields  
            "sanierungskosten", "restoration_costs", "remediation_costs",
            "closure_costs", "environmental_bond", "financial_assurance",
            # Production fields
            "produktionsbeginn", "production_start", "jahresproduktion", 
            "annual_production", "mine_type", "minentyp",
            # Environmental fields
            "umweltauswirkungen", "kontamination", "wassermanagement"
        ]
    )
    
    # Teste staged search
    print("\n=== Starte Staged Search ===")
    search_params = {
        'use_staged_search': True,
        'timeout_per_stage': 60,  # Kurzer Timeout für Test
        'active_agents': orchestrator.active_agents
    }
    
    try:
        results = await orchestrator.search_mine(query, search_params)
        print(f"\n=== Ergebnisse ===")
        print(f"Gesamt gefundene Ergebnisse: {len(results)}")
        
        # Zeige Ergebnisse nach Feld
        fields_found = {}
        for result in results:
            field = result.field_name
            if field not in fields_found:
                fields_found[field] = 0
            fields_found[field] += 1
        
        print("\nErgebnisse nach Feld:")
        for field, count in sorted(fields_found.items(), key=lambda x: x[1], reverse=True):
            print(f"  - {field}: {count} Ergebnisse")
            
    except Exception as e:
        print(f"\nFehler bei Suche: {e}")
        import traceback
        traceback.print_exc()
    
    # Cleanup
    print("\nCleanup...")
    await orchestrator.cleanup()
    print("Test abgeschlossen!")

if __name__ == "__main__":
    # Führe Test aus
    asyncio.run(test_staged_search())