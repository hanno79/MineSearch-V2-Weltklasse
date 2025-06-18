#!/usr/bin/env python
"""
Test mit echter Mine: Canadian Malartic
"""
import asyncio
import sys
import os
sys.path.insert(0, os.path.dirname(os.path.abspath(__file__)))

from src.core.config import Config
from src.core.orchestrator import MineSearchOrchestrator
from src.agents.base_agent import MineQuery
from src.data.exporter import DataExporter
from datetime import datetime


async def test_malartic():
    """Test mit Canadian Malartic Mine"""
    print("=== Test: Canadian Malartic Mine ===\n")
    
    config = Config()
    orchestrator = MineSearchOrchestrator(config)
    
    # Initialize
    await orchestrator.initialize()
    print(f"Aktive Agenten: {orchestrator.active_agents}\n")
    
    # Create query for real mine
    query = MineQuery(
        mine_name="Canadian Malartic",
        region="Quebec",
        country="Canada",
        languages=["en", "fr"],
        required_fields=[
            "betreiber",        # Operator
            "koordinaten",      # Coordinates
            "rohstofftyp",      # Commodity type
            "jahresproduktion", # Annual production
            "mitarbeiter",      # Employees
            "flaeche",          # Area
            "aktivitaetsstatus",# Activity status
            "sanierungskosten"  # Restoration costs
        ]
    )
    
    print(f"Suche nach: {query.mine_name}")
    print(f"Region: {query.region}, {query.country}\n")
    
    # Run search
    print("Starte Suche...")
    results = await orchestrator.search_mine(query)
    
    print(f"\n✓ Suche abgeschlossen! {len(results)} Ergebnisse gefunden\n")
    
    # Group and display results
    if results:
        field_groups = {}
        for result in results:
            if result.field_name not in field_groups:
                field_groups[result.field_name] = []
            field_groups[result.field_name].append(result)
        
        print("=== Gefundene Informationen ===\n")
        
        for field, field_results in field_groups.items():
            print(f"{field.upper()}:")
            # Sort by confidence
            sorted_results = sorted(field_results, key=lambda r: r.confidence_score, reverse=True)
            
            for i, result in enumerate(sorted_results[:2]):  # Top 2 per field
                print(f"  {i+1}. {result.value}")
                print(f"     Quelle: {result.source}")
                print(f"     Konfidenz: {result.confidence_score:.2f}")
                if result.source_url:
                    print(f"     URL: {result.source_url[:60]}...")
                print()
        
        # Export results
        print("\nExportiere Ergebnisse...")
        exporter = DataExporter()
        
        # Convert to dict for export
        results_dict = [r.to_dict() for r in results]
        
        # Export to JSON
        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        json_file = f"data/output/canadian_malartic_{timestamp}.json"
        exporter.export_to_json(results_dict, json_file)
        print(f"✓ JSON exportiert: {json_file}")
        
        # Export to CSV
        csv_file = f"data/output/canadian_malartic_{timestamp}.csv"
        exporter.export_to_csv(results_dict, csv_file)
        print(f"✓ CSV exportiert: {csv_file}")
        
    else:
        print("Keine Ergebnisse gefunden.")
        print("\nMögliche Gründe:")
        print("- Keine API Keys konfiguriert")
        print("- Mine Name nicht korrekt")
        print("- Netzwerkprobleme")
    
    # Show statistics
    stats = orchestrator.get_agent_statistics()
    print("\n=== Agent Statistiken ===")
    for agent, stat in stats.items():
        if stat['is_active']:
            print(f"\n{agent}:")
            print(f"  Status: {stat['status']}")
            print(f"  Anfragen: {stat['stats'].get('total_requests', 0)}")
            print(f"  Erfolge: {stat['stats'].get('successful_requests', 0)}")
            print(f"  Gefundene Felder: {stat['stats'].get('total_fields_found', 0)}")
    
    # Cleanup
    await orchestrator.cleanup()
    print("\n✓ Test abgeschlossen!")


if __name__ == "__main__":
    print("Starte Test mit Canadian Malartic Mine...\n")
    asyncio.run(test_malartic())