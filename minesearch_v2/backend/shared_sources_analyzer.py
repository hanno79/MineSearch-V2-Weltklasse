"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Analyzer für geteilte Quellen zwischen Providern
"""

import logging
from typing import Dict, List, Any

logger = logging.getLogger(__name__)


class SharedSourcesAnalyzer:
    """Analysiert Minen mit geteilten Quellen von mehreren Providern"""
    
    def __init__(self, registry):
        self.registry = registry
    
    async def analyze_with_shared_sources(self, model_id: str, mine_name: str,
                                        country: str, commodity: str, region: str,
                                        enhanced_query: str, shared_sources: List[Dict],
                                        convert_to_standard_format) -> Dict[str, Any]:
        """Analysiere Mine mit geteilten Quellen"""
        
        provider = self.registry.get_provider_for_model(model_id)
        if not provider:
            return {"success": False, "error": f"Provider für {model_id} nicht gefunden"}
        
        # Erweiterte Optionen mit shared sources
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity,
            'region': region,
            'shared_sources': shared_sources,  # Alle gesammelten Quellen
            'phase': 'source_analysis',        # Kennzeichnung für Provider
            'temperature': 0.1                 # Niedrigere Temperature für konsistente Extraktion
        }
        
        try:
            provider_name, model_key = model_id.split(':')
            
            # Prüfe ob Provider extract_from_sources unterstützt
            if hasattr(provider, 'extract_from_sources'):
                # Nutze spezialisierte Methode wenn verfügbar
                result = await provider.extract_from_sources(shared_sources, model_key, options)
            else:
                # Fallback auf normale search mit enhanced query
                result = await provider.search(enhanced_query, model_key, options)
            
            return convert_to_standard_format(result, model_id, mine_name, country)
            
        except Exception as e:
            logger.error(f"[SOURCE-SHARING] Fehler in Phase 2 mit {model_id}: {str(e)}")
            return {"success": False, "error": str(e)}