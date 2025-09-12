"""
Compact Search Service
Kompakte Version des Search Service mit delegierter Funktionalität

Author: MineSearch Development Team
Date: 2025-01-11
"""

import asyncio
import logging
from datetime import datetime
from typing import Dict, Any, List, Optional

from minesearch.config.base import config, Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from minesearch.utils import normalize_accents, get_country_config
from minesearch.providers.registry import provider_registry
from minesearch.cost_monitor import cost_monitor
from minesearch.search_service_utils import SearchServiceUtils

logger = logging.getLogger(__name__)


class MineSearchService:
    """Hauptklasse für Mining-Suchen mit Provider-Unterstützung"""

    def __init__(self):
        """Initialisiere Search Service"""
        # Provider-basierte Architektur
        provider_registry.initialize(config.PROVIDERS)
        self.registry = provider_registry
        self.utils = SearchServiceUtils()

    async def search_mine(self, mine_name: str, model: str, country: Optional[str] = None,
                         commodity: Optional[str] = None, region: Optional[str] = None,
                         _is_auto_enhanced: bool = False) -> Dict[str, Any]:
        """
        Hauptsuchfunktion für Mining-Informationen

        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            model: Zu verwendendes Modell
            region: Region (optional)
            _is_auto_enhanced: Intern - verhindert Rekursion

        Returns:
            Strukturiertes Suchergebnis
        """
        logger.info(f"[SEARCH] Starte Suche für: {mine_name}, Land: {country}, Modell: {model}")

        # Normalisiere Eingaben
        normalized_mine_name = normalize_accents(mine_name)
        country_config = get_country_config(country)

        # Prüfe Modell-Verfügbarkeit
        full_model_id = model if ':' in model else f"openrouter:{model}"
        if not self.registry.is_model_available(full_model_id):
            logger.warning(f"Modell {full_model_id} nicht verfügbar, verwende Default: {config.DEFAULT_MODEL}")
            full_model_id = config.DEFAULT_MODEL

        # Kostenüberwachung
        if not cost_monitor.check_model_costs(full_model_id, "search"):
            logger.error(f"Verwendung von kostenpflichtigem Modell {full_model_id} blockiert")
            alternatives = cost_monitor.suggest_free_alternatives(full_model_id)
            if alternatives:
                full_model_id = alternatives[0]
                logger.info(f"Verwende kostenlose Alternative: {full_model_id}")
            else:
                full_model_id = config.DEFAULT_MODEL

        try:
            # Generiere Suchbegriffe
            search_terms = self.utils.generate_search_terms(normalized_mine_name, country, region)

            # Führe Suche durch
            search_results = await self.utils.execute_search_with_providers(search_terms, full_model_id, country_config)

            # Extrahiere und verarbeite Daten
            extracted_data = await self.utils.extract_and_process_data(search_results, normalized_mine_name, full_model_id)

            # Speichere Ergebnisse
            await self.utils.save_search_results(normalized_mine_name, full_model_id, extracted_data, search_results, country, region)

            # Erstelle Ergebnis
            result = {
                'mine_name': normalized_mine_name,
                'country': country,
                'region': region,
                'commodity': commodity,
                'model_used': full_model_id,
                'data': extracted_data,
                'sources': [{'url': r.url, 'title': r.title, 'content': r.content[:200] + '...' if r.content else ''} for r in search_results],
                'timestamp': datetime.now().isoformat(),
                'search_terms_used': search_terms
            }

            # Cache Ergebnis
            await self.utils.save_to_cache(normalized_mine_name, country or "", full_model_id, result, commodity, region)

            logger.info(f"[SEARCH] ✅ Suche abgeschlossen für {normalized_mine_name}")
            return result

        except Exception as e:
            logger.error(f"[SEARCH] ❌ Fehler bei Suche für {normalized_mine_name}: {e}")
            return {
                'mine_name': normalized_mine_name,
                'error': str(e),
                'timestamp': datetime.now().isoformat()
            }

    async def search_multiple_mines(self, mine_names: List[str], model: str, country: Optional[str] = None) -> List[Dict[str, Any]]:
        """Suche mehrere Minen parallel"""
        tasks = []
        for mine_name in mine_names:
            task = self.search_mine(mine_name, model, country)
            tasks.append(task)
        
        results = await asyncio.gather(*tasks, return_exceptions=True)
        
        # Behandle Exceptions
        processed_results = []
        for i, result in enumerate(results):
            if isinstance(result, Exception):
                processed_results.append({
                    'mine_name': mine_names[i],
                    'error': str(result),
                    'timestamp': datetime.now().isoformat()
                })
            else:
                processed_results.append(result)
        
        return processed_results

    def get_available_models(self) -> List[str]:
        """Hole verfügbare Modelle"""
        return self.registry.get_available_models()

    def get_provider_status(self) -> Dict[str, Any]:
        """Hole Provider-Status"""
        return self.registry.get_status()


# Service-Instanz für Kompatibilität
from minesearch.services_container import services
search_service = services.search_service

__all__ = ["MineSearchService", "search_service"]
