"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: Demonstriert die Verbesserungen im MineSearch System
"""

import sys
import asyncio
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from minesearch_v2.backend.search_service_multi import MultiProviderSearchService
from minesearch_v2.backend.utils import generate_name_variants, generate_accent_alternatives
from minesearch_v2.backend.specialized_prompts import SpecializedPrompts

# Logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)


async def demonstrate_improvements():
    """Zeigt die implementierten Verbesserungen"""
    
    logger.info("\n" + "="*80)
    logger.info("MINESEARCH v2 - VERBESSERUNGEN DEMONSTRATION")
    logger.info("="*80)
    
    # 1. Erweiterte Akzent-Behandlung
    logger.info("\n1. ERWEITERTE AKZENT-BEHANDLUNG:")
    logger.info("-" * 40)
    
    test_names = ["Quebec", "Eleonore Mine", "Montreal Project"]
    for name in test_names:
        variants = generate_name_variants(name)
        accent_alts = generate_accent_alternatives(name)
        
        logger.info(f"\n'{name}':")
        logger.info(f"  - Gesamt-Varianten: {len(variants)}")
        logger.info(f"  - Akzent-Alternativen: {accent_alts}")
        
        # Prüfe ob Akzent-Version enthalten
        if name == "Quebec" and any("Québec" in v for v in variants):
            logger.info(f"  ✅ Akzent-Version 'Québec' wird generiert")
        elif name == "Eleonore Mine" and any("Éléonore" in v for v in variants):
            logger.info(f"  ✅ Akzent-Version 'Éléonore' wird generiert")
    
    # 2. Spezialisierte Prompts
    logger.info("\n\n2. SPEZIALISIERTE PROMPTS:")
    logger.info("-" * 40)
    
    # Zeige Beispiel für Quellensuche-Prompt
    source_prompt = SpecializedPrompts.get_source_discovery_prompt(
        "Canadian Malartic", "Canada", "Quebec", "Gold"
    )
    logger.info("\nQuellensuche-Prompt (Auszug):")
    logger.info(source_prompt[:500] + "...")
    
    # Zeige Beispiel für Restaurationskosten-Prompt
    resto_prompt = SpecializedPrompts.get_restoration_costs_prompt(
        "Canadian Malartic", "Canada", "Gold"
    )
    logger.info("\n\nRestaurationskosten-Prompt (Auszug):")
    logger.info(resto_prompt[:500] + "...")
    
    # 3. Multi-Modell Strategie
    logger.info("\n\n3. MULTI-MODELL STRATEGIE:")
    logger.info("-" * 40)
    
    service = MultiProviderSearchService()
    all_models = list(service.registry.get_all_models().keys())
    
    logger.info(f"\nVerfügbare Modelle: {len(all_models)}")
    
    # Gruppiere nach Provider
    providers = {}
    for model in all_models:
        provider = model.split(':')[0]
        if provider not in providers:
            providers[provider] = []
        providers[provider].append(model)
    
    logger.info("\nModelle nach Provider:")
    for provider, models in sorted(providers.items()):
        logger.info(f"  - {provider}: {len(models)} Modelle")
        for model in models[:2]:  # Zeige erste 2
            logger.info(f"    • {model}")
        if len(models) > 2:
            logger.info(f"    • ... und {len(models)-2} weitere")
    
    # 4. Zweistufiger Prozess
    logger.info("\n\n4. ZWEISTUFIGER SUCH-PROZESS:")
    logger.info("-" * 40)
    
    logger.info("\nPhase 1: Quellensammlung")
    logger.info("  - ALLE 34 Modelle sammeln parallel Quellen")
    logger.info("  - Deduplizierung und Ranking nach Qualität")
    logger.info("  - Tier 1: Offizielle Quellen (SEDAR, SEC, Unternehmensseiten)")
    logger.info("  - Tier 2: Fachmedien (Mining.com, Reuters)")
    logger.info("  - Tier 3: Allgemeine Medien")
    
    logger.info("\nPhase 2: Datenextraktion")
    logger.info("  - Jedes Modell analysiert ALLE gesammelten Quellen")
    logger.info("  - 5 spezialisierte Prompts pro Modell:")
    logger.info("    • Finanzdaten (Fokus: Restaurationskosten)")
    logger.info("    • Technische Daten (Fokus: Koordinaten)")
    logger.info("    • Betriebsdaten (Fokus: Eigentümer)")
    logger.info("    • Produktionsdaten")
    logger.info("    • Umfassende Extraktion")
    
    # 5. Konfidenz-Scoring
    logger.info("\n\n5. CROSS-MODEL VALIDATION:")
    logger.info("-" * 40)
    
    logger.info("\nKonfidenz-Berechnung:")
    logger.info("  - Mehrfachfunde erhöhen Glaubwürdigkeit")
    logger.info("  - Beispiel: 5 Modelle finden '$146.7M' → 100% Konfidenz")
    logger.info("  - Beispiel: 2 Modelle finden '$146.7M', 1 findet '$150M' → 66% Konfidenz")
    logger.info("  - Widersprüche werden transparent gemacht")
    
    # 6. Erwartete Verbesserungen
    logger.info("\n\n6. ERWARTETE VERBESSERUNGEN:")
    logger.info("-" * 40)
    
    logger.info("\n📊 Datenabdeckung:")
    logger.info("  - Vorher: ~65% der Felder")
    logger.info("  - Nachher: 90-100% der Felder")
    
    logger.info("\n📚 Quellenanzahl:")
    logger.info("  - Vorher: 3-5 Quellen pro Mine")
    logger.info("  - Nachher: 20-30+ Quellen pro Mine")
    
    logger.info("\n💰 Restaurationskosten:")
    logger.info("  - Vorher: 65% Erfolgsrate")
    logger.info("  - Nachher: >90% Erfolgsrate")
    
    logger.info("\n🎯 Glaubwürdigkeit:")
    logger.info("  - Durch Mehrfachvalidierung")
    logger.info("  - Transparente Konfidenz-Scores")
    logger.info("  - Quellenbasierte Validierung")
    
    logger.info("\n" + "="*80)
    logger.info("DEMO ABGESCHLOSSEN")
    logger.info("="*80)


async def test_single_mine_improved():
    """Testet eine einzelne Mine mit verbessertem System"""
    logger.info("\n\nTESTE CANADIAN MALARTIC MIT VERBESSERTEM SYSTEM...")
    logger.info("-" * 60)
    
    service = MultiProviderSearchService()
    
    # Teste mit mehreren Modellen für Cross-Validation
    test_models = [
        'perplexity:sonar-pro',
        'openai:o3-deep-research',
        'grok:grok-3-fast',
        'anthropic:claude-opus-4'
    ]
    
    # Verwende search_with_source_sharing für bessere Ergebnisse
    result = await service.search_with_source_sharing(
        model_ids=test_models,
        mine_name='Canadian Malartic Mine',
        country='Canada',
        region='Quebec',
        commodity='Gold'
    )
    
    # Zeige Ergebnisse
    if result.get('success'):
        data = result.get('best_data', {})
        logger.info(f"\n✅ Erfolgreiche Suche!")
        logger.info(f"Felder gefüllt: {len([v for v in data.values() if v])}/21")
        logger.info(f"Durchschnittliche Konfidenz: {result.get('data_quality', {}).get('average_confidence', 0):.0%}")
        
        # Zeige Restaurationskosten wenn gefunden
        resto = data.get('Restaurationskosten')
        if resto:
            logger.info(f"\n💰 Restaurationskosten gefunden: {resto}")
            
            # Zeige welche Modelle es gefunden haben
            model_results = result.get('model_results', {})
            resto_findings = []
            for model_id, model_result in model_results.items():
                if model_result.get('success'):
                    model_resto = model_result.get('data', {}).get('Restaurationskosten')
                    if model_resto:
                        resto_findings.append(f"{model_id}: {model_resto}")
            
            if resto_findings:
                logger.info("\nGefunden von:")
                for finding in resto_findings:
                    logger.info(f"  - {finding}")
    else:
        logger.info(f"\n❌ Fehler: {result.get('error', 'Unbekannt')}")


async def main():
    """Hauptfunktion"""
    # Zeige Verbesserungen
    await demonstrate_improvements()
    
    # Optional: Teste echte Suche
    user_input = input("\n\nMöchten Sie eine echte Suche testen? (j/n): ")
    if user_input.lower() == 'j':
        await test_single_mine_improved()


if __name__ == "__main__":
    asyncio.run(main())