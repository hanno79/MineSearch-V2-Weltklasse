#!/usr/bin/env python3
"""
Author: rahn
Datum: 12.07.2025
Version: 1.0
Beschreibung: Begrenzte Provider-Tests für Demo-Zwecke
"""

import asyncio
import logging
import json
from datetime import datetime
from typing import Dict, Any

# Test Framework Import
from provider_test_framework import ProviderTestFramework
from database_validator import DatabaseValidator

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


async def main():
    """
    Führt begrenzte Tests durch (nur erste 3 Provider für Demo)
    """
    logger.info("🚀 [LIMITED-TESTS] Starte begrenzte Provider-Tests für Demo")
    
    try:
        # 1. Initialisiere Test-Framework
        test_framework = ProviderTestFramework()
        
        # 2. Teste nur erste 3 Provider-Familien
        limited_providers = ['perplexity', 'openrouter', 'anthropic']
        
        for provider_family in limited_providers:
            logger.info(f"📊 [LIMITED-TESTS] Teste Provider-Familie: {provider_family}")
            
            test_results = await test_framework.run_comprehensive_tests(
                provider_filter=provider_family,
                runs_per_mine=3  # Reduziert auf 3 Runs
            )
            
            # Kurzschrift-Report für diese Familie
            if test_results.get("success"):
                summary = test_results.get("test_summary", {})
                models_tested = summary.get('total_models_tested', 0)
                success_rate = summary.get('overall_success_rate', 0)
                
                print(f"\n✅ {provider_family.upper()}: {models_tested} Modelle, {success_rate:.1%} Erfolg")
                
                # Top-Performer dieser Familie
                model_performance = test_results.get("model_performance", {})
                if model_performance:
                    best_model = max(
                        model_performance.items(),
                        key=lambda x: x[1]['success_rate']
                    )
                    print(f"   🏆 Bestes Modell: {best_model[0]} ({best_model[1]['success_rate']:.1%})")
            else:
                print(f"\n❌ {provider_family.upper()}: Tests fehlgeschlagen")
        
        # 3. Finale Datenbank-Validierung
        logger.info("🔍 [LIMITED-TESTS] Finale Datenbank-Validierung...")
        validator = DatabaseValidator()
        
        validation_results = await validator.validate_comprehensive(
            models_to_check=None,  # Alle Modelle
            mines_to_check=["Éléonore", "Niobec", "LaRonde"]
        )
        
        # 4. Finale Zusammenfassung
        print("\n" + "="*60)
        print("🎯 LIMITED TEST ZUSAMMENFASSUNG")
        print("="*60)
        print(f"✅ 3 Provider-Familien getestet")
        print(f"🗄️  Datenbank-Status: {validation_results.get('overall_status', 'UNKNOWN')}")
        
        issues = validation_results.get("issues_summary", {})
        if issues.get("critical"):
            print(f"🚨 Kritische Issues: {len(issues['critical'])}")
        if issues.get("warnings"):
            print(f"⚠️  Warnungen: {len(issues['warnings'])}")
            
        # Speichere Validierungs-Report
        report_filename = f"limited_test_validation_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
        with open(report_filename, 'w', encoding='utf-8') as f:
            json.dump(validation_results, f, indent=2, ensure_ascii=False, default=str)
        
        print(f"📄 Validierungs-Report: {report_filename}")
        print("="*60)
        
        return validation_results
        
    except Exception as e:
        logger.error(f"🚨 [LIMITED-TESTS] Kritischer Fehler: {e}")
        print(f"\n❌ FEHLER: {e}")
        return None


if __name__ == "__main__":
    asyncio.run(main())