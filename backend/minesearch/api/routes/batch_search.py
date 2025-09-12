"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Suchlogik für Batch-Processing (Refactoring aus batch.py)
"""

import logging
from typing import Optional, Dict, Any
from .batch_utils import count_filled_fields

logger = logging.getLogger(__name__)

async def fallback_search_if_needed(mine_name, country, commodity, region, current_best_data):
    """
    Führt Fallback-Suche mit deepseek-free durch, wenn aktuelles Ergebnis schwach ist
    
    Returns: Verbessertes result_data oder None wenn kein Fallback nötig/möglich
    """
    try:
        logger.info(f"[FALLBACK] Starte deepseek-free Fallback für {mine_name}")
        
        # Provider Registry Setup
        from minesearch.providers.registry import provider_registry
        from minesearch.config import config
        
        if not provider_registry._providers:
            provider_registry.initialize(config.PROVIDERS)
        
        provider = provider_registry.get_provider_for_model('openrouter:deepseek-free')
        if not provider:
            logger.error(f"[FALLBACK] Kein deepseek-free Provider verfügbar")
            return None
        
        # Fallback-Suche ausführen
        query = f"{mine_name} mine {country} {commodity} restoration costs area production"
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity, 
            'region': region
        }
        
        search_result = await provider.search(query, 'deepseek-free', options)
        
        if search_result and search_result.success and search_result.structured_data:
            # DEBUG: Log Restaurationskosten vor dem Return
            resto_value = search_result.structured_data.get('Restaurationskosten', '')
            logger.info(f"[FALLBACK-DEBUG] Restaurationskosten vor Return: '{resto_value}'")
            
            fallback_filled = count_filled_fields(search_result.structured_data)
            current_filled = count_filled_fields(current_best_data.get('structured_data', {}))
            
            if fallback_filled > current_filled:
                logger.info(f"[FALLBACK-SUCCESS] deepseek-free better: {fallback_filled} vs {current_filled} Felder")
                
                # DEBUG: Log alle kritischen Felder
                critical_fields = ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Fläche der Mine in qkm']
                for field in critical_fields:
                    value = search_result.structured_data.get(field, '(leer)')
                    logger.info(f"[FALLBACK-DEBUG] {field}: '{value}'")
                
                return {
                    'structured_data': search_result.structured_data,
                    'raw_content': search_result.content,
                    'field_count': len(search_result.structured_data),
                    'filled_field_count': fallback_filled,
                    'enhanced_via_fallback': True
                }
            else:
                logger.info(f"[FALLBACK] deepseek-free nicht besser: {fallback_filled} vs {current_filled} Felder")
        else:
            logger.warning(f"[FALLBACK] deepseek-free Suche fehlgeschlagen für {mine_name}")
            
    except Exception as e:
        logger.error(f"[FALLBACK] Fehler bei Fallback-Suche für {mine_name}: {str(e)}")
    
    return None