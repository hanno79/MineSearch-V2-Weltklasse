"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Test-Datei für direct_provider
"""

#!/usr/bin/env python3
"""
DIRECT PROVIDER TIMEOUT TEST
Testet alternative Provider direkt ohne komplexe Orchestrierung
"""
import asyncio
import time
import os
import sys
import logging

# Path setup
sys.path.insert(0, '/app/backend')

from minesearch.providers.abacus_provider import AbacusProvider
from minesearch.providers.tavily_provider import TavilyProvider
from minesearch.config.api_keys import APIKeysConfig
from minesearch.config.providers import PROVIDERS_CONFIG

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def test_provider_direct(provider_name: str):
    """Testet einen Provider direkt mit einfachster Konfiguration"""

    config = PROVIDERS_CONFIG.get(provider_name)
    if not config or not config['enabled']:
        logger.error(f"Provider {provider_name} nicht verfügbar oder deaktiviert")
        return None

    api_key = config['api_key']
    if not api_key:
        logger.error(f"Kein API-Key für {provider_name}")
        return None

    start_time = time.time()

    try:
        # Provider erstellen
        if provider_name == 'abacus':
            provider = AbacusProvider(api_key, config)
            model_id = 'deep-agent'
        elif provider_name == 'tavily':
            provider = TavilyProvider(api_key, config)
            model_id = 'search'
        else:
            logger.error(f"Unbekannter Provider: {provider_name}")
            return None

        # Einfachste Query
        query = "Éléonore mine Canada owner operator restoration costs"
        options = {
            'mine_name': 'Éléonore',
            'country': 'Canada'
        }

        logger.info(f"[{provider_name.upper()}] Starte direkten Test mit {model_id}")

        # Direkter Provider-Aufruf
        result = await provider.search(query, model_id, options)

        duration = time.time() - start_time

        if result.success:
            logger.info(f"[{provider_name.upper()}] ✅ SUCCESS nach {duration:.1f}s")
            # Zeige strukturierte Daten
            data_count = len([v for v in result.structured_data.values() if v])
            logger.info(f"[{provider_name.upper()}] Daten gefunden: {data_count}/18 Felder")
            return True
        else:
            logger.error(f"[{provider_name.upper()}] ❌ FAILED nach {duration:.1f}s: {result.error}")
            return False

    except Exception as e:
        duration = time.time() - start_time
        logger.error(f"[{provider_name.upper()}] 💥 EXCEPTION nach {duration:.1f}s: {str(e)}")
        return False

async def main():
    """Teste alle alternativen Provider direkt"""

    logger.info("🔍 DIRECT PROVIDER TIMEOUT TEST")
    logger.info("=" * 50)

    providers_to_test = ['abacus', 'tavily']

    for provider_name in providers_to_test:
        logger.info(f"\n🧪 Teste {provider_name}...")

        try:
            # Test mit Timeout
            result = await asyncio.wait_for(
                test_provider_direct(provider_name),
                timeout=120.0  # 2 Minuten Maximum
            )

            if result is True:
                logger.info(f"✅ {provider_name}: ERFOLGREICH")
            else:
                logger.info(f"❌ {provider_name}: FEHLGESCHLAGEN")

        except asyncio.TimeoutError:
            logger.error(f"⏰ {provider_name}: TIMEOUT nach 120s")
        except Exception as e:
            logger.error(f"💥 {provider_name}: EXCEPTION {str(e)}")

    logger.info("\n" + "=" * 50)
    logger.info("Direct Provider Test abgeschlossen")

if __name__ == "__main__":
    asyncio.run(main())
