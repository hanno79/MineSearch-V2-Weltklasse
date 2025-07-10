"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Prüfe welche Provider noch getestet werden müssen
"""

import logging
from database import db_manager, ModelSummary
from config.providers import PROVIDERS_CONFIG

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def check_missing_providers():
    """Prüfe welche Provider noch getestet werden müssen"""
    
    # Hole alle Modelle aus der Konfiguration
    all_configured_models = []
    for provider_name, provider_config in PROVIDERS_CONFIG.items():
        if provider_config.get('enabled', False):
            models = provider_config.get('models', {})
            for model_key, model_info in models.items():
                model_id = f"{provider_name}:{model_key}"
                all_configured_models.append((provider_name, model_key, model_id))
    
    # Hole getestete Modelle aus DB
    with db_manager.get_session() as session:
        tested_models = session.query(ModelSummary.model_id).all()
        tested_model_ids = {m[0] for m in tested_models}
        
        # Hole Modelle mit 0 Tests oder sehr wenigen Tests
        weak_models = session.query(ModelSummary).filter(
            (ModelSummary.total_tests < 5) | (ModelSummary.success_rate == 0)
        ).all()
    
    # Finde fehlende Modelle
    missing_models = []
    needs_retest = []
    
    for provider, model, model_id in all_configured_models:
        if model_id not in tested_model_ids:
            missing_models.append((provider, model, model_id))
    
    # Ausgabe
    logger.info("=== PROVIDER TEST STATUS ===")
    
    logger.info(f"\nKONFIGURIERTE MODELLE: {len(all_configured_models)}")
    logger.info(f"GETESTETE MODELLE: {len(tested_model_ids)}")
    
    if missing_models:
        logger.info(f"\n❌ FEHLENDE MODELLE ({len(missing_models)}):")
        providers = {}
        for provider, model, model_id in missing_models:
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model)
        
        for provider, models in providers.items():
            logger.info(f"\n{provider.upper()}:")
            for model in models:
                logger.info(f"  - {model}")
    
    if weak_models:
        logger.info(f"\n⚠️  SCHWACHE TESTS (< 5 Tests oder 0% Erfolg):")
        for model in weak_models:
            logger.info(f"  - {model.model_id}: {model.total_tests} Tests, {model.success_rate:.0%} Erfolg")
    
    # Erstelle Liste für neue Tests
    providers_to_test = {}
    for provider, model, model_id in missing_models:
        if provider not in providers_to_test:
            providers_to_test[provider] = []
        providers_to_test[provider].append(model)
    
    return providers_to_test, weak_models


if __name__ == "__main__":
    missing, weak = check_missing_providers()
    
    if missing:
        logger.info("\n📋 ZU TESTENDE PROVIDER:")
        for provider, models in missing.items():
            logger.info(f"{provider}: {', '.join(models)}")
    else:
        logger.info("\n✅ Alle konfigurierten Provider wurden getestet!")