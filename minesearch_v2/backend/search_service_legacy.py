"""
Author: rahn
Datum: 12.07.2025  
Version: 1.0
Beschreibung: Legacy-Kompatibilität für MineSearchService
"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional

from config import config, Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from utils import normalize_accents, generate_name_variants, generate_multilingual_search_terms, get_country_config
from data_extraction import DataExtractor
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery
from providers.registry import provider_registry
from providers.base_provider import SearchResult
from cache_service import get_cache_service, cached_search

logger = logging.getLogger(__name__)


class LegacySearchFunctions:
    """Legacy-Funktionen für Rückwärtskompatibilität"""
    
    def __init__(self):
        self.api_key = config.PERPLEXITY_API_KEY
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.data_extractor = DataExtractor()
    
    def _build_search_query(self, mine_name: str, name_variants: List[str], 
                           country: Optional[str], currency: str, restoration_terms: List[str],
                           search_type: str = "comprehensive") -> str:
        """
        Erstellt spezielle Suchanfrage für verschiedene Suchtypen
        
        Args:
            mine_name: Name der Mine
            name_variants: Verschiedene Schreibweisen des Namens
            country: Land
            currency: Währung
            restoration_terms: Begriffe für Restaurationskosten
            search_type: Art der Suche
            
        Returns:
            Formatierte Suchanfrage
        """
        base_variants = ' OR '.join([f'"{variant}"' for variant in name_variants])
        country_suffix = f" {country}" if country else ""
        
        if search_type == "deep_research":
            return self._build_deep_research_query(mine_name, currency, restoration_terms)
        else:
            return self._build_standard_query(mine_name, currency, restoration_terms)
    
    def _build_deep_research_query(self, mine_name: str, currency: str, restoration_terms: List[str]) -> str:
        """Erstellt erweiterte Forschungsanfrage"""
        restoration_query = " OR ".join(restoration_terms)
        
        return f"""
        Finde ALLE verfügbaren Informationen über die Mine "{mine_name}":

        BETREIBER UND EIGENTÜMER:
        - Wer ist der aktuelle Betreiber/Eigentümer der Mine?
        - Welche Unternehmen waren frühere Betreiber?
        - Gibt es Joint Ventures oder Partnerschaften?

        GEOGRAFISCHE DATEN:
        - Genaue GPS-Koordinaten der Mine
        - In welcher Region/Provinz/Staat liegt die Mine?
        - Höhenlage und geografische Beschreibung

        ROHSTOFFE UND PRODUKTION:
        - Welche Rohstoffe werden/wurden gefördert?
        - Aktuelle und historische Produktionszahlen
        - Reserven und Ressourcen

        FINANZIELLE ASPEKTE:
        - Restaurationskosten/Rekultivierungskosten in {currency}
        - Investitionen und Betriebskosten
        - {restoration_query}

        STATUS UND BETRIEB:
        - Ist die Mine aktiv, stillgelegt oder in Entwicklung?
        - Seit wann ist sie in Betrieb?
        - Geplante Schließung oder Erweiterungen?

        Antworte strukturiert mit konkreten Zahlen und Fakten. Nenne IMMER Quellen.
        """
    
    def _build_standard_query(self, mine_name: str, currency: str, restoration_terms: List[str]) -> str:
        """Erstellt Standard-Suchanfrage"""
        restoration_query = " OR ".join(restoration_terms)
        
        return f"""
        Suche Informationen über die Mine "{mine_name}":
        
        1. Betreiber/Eigentümer
        2. GPS-Koordinaten  
        3. Rohstofftyp
        4. Aktivitätsstatus
        5. Restaurationskosten ({restoration_query}) in {currency}
        6. Produktionsdaten
        7. Mitarbeiterzahl
        8. Fläche in Hektar
        
        Antworte strukturiert mit Fakten und Quellen.
        """
    
    def _get_system_prompt(self) -> str:
        """Systemprompt für Perplexity API"""
        return """Du bist ein Experte für Bergbau und Mining-Recherche. 
        
        WICHTIGE REGELN:
        1. Antworte IMMER auf Deutsch
        2. Gib nur verifizierte Informationen an
        3. Nenne KONKRETE Quellen für alle Angaben
        4. Verwende strukturierte Antworten
        5. Bei Unsicherheit: Sage "Keine Informationen verfügbar"
        6. Bevorzuge offizielle Quellen (Regierungswebsites, Unternehmen, Fachpublikationen)
        7. Gib Zahlen im korrekten Format an (z.B. GPS: 45.123456, -73.654321)
        """
    
    async def _call_perplexity_api(self, search_query: str, model_config: Dict) -> Dict:
        """
        Direkter Aufruf der Perplexity API (Legacy-Funktion)
        
        Args:
            search_query: Suchanfrage
            model_config: Modell-Konfiguration
            
        Returns:
            API-Antwort oder Fehler
        """
        if not self.api_key:
            return {
                "success": False,
                "error": "Perplexity API-Key nicht konfiguriert",
                "content": "",
                "sources": []
            }
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json"
        }
        
        payload = {
            "model": model_config.get("model", "sonar-pro"),
            "messages": [
                {"role": "system", "content": self._get_system_prompt()},
                {"role": "user", "content": search_query}
            ],
            "temperature": model_config.get("temperature", 0.2),
            "max_tokens": model_config.get("max_tokens", 4000),
            "top_p": model_config.get("top_p", 0.9),
            "search_domain_filter": model_config.get("search_domain_filter", ["perplexity.ai"]),
            "return_images": False,
            "return_related_questions": False,
            "search_recency_filter": "month",
            "top_k": 0,
            "stream": False,
            "presence_penalty": 0,
            "frequency_penalty": 1
        }
        
        try:
            async with httpx.AsyncClient(timeout=30.0) as client:
                response = await client.post(self.api_url, headers=headers, json=payload)
                
                if response.status_code == 200:
                    data = response.json()
                    content = data["choices"][0]["message"]["content"]
                    
                    # Extrahiere Quellen
                    sources = []
                    if "citations" in data:
                        sources = [{"url": citation.get("url", ""), "title": citation.get("title", "")} 
                                 for citation in data["citations"]]
                    
                    return {
                        "success": True,
                        "content": content,
                        "sources": sources,
                        "model": payload["model"]
                    }
                else:
                    error_msg = f"API-Fehler {response.status_code}: {response.text}"
                    logger.error(f"[LEGACY] Perplexity API Fehler: {error_msg}")
                    return {
                        "success": False,
                        "error": error_msg,
                        "content": "",
                        "sources": []
                    }
                    
        except Exception as e:
            error_msg = f"Verbindungsfehler: {str(e)}"
            logger.error(f"[LEGACY] Perplexity API Exception: {error_msg}")
            return {
                "success": False,
                "error": error_msg,
                "content": "",
                "sources": []
            }
    
    def _validate_result(self, content: str, mine_name: str, name_variants: List[str]) -> tuple:
        """
        Validiert Suchergebnis
        
        Args:
            content: Inhalt der Antwort
            mine_name: Name der Mine
            name_variants: Name-Varianten
            
        Returns:
            (is_valid, confidence_score)
        """
        if not content or len(content.strip()) < 50:
            return False, 0.0
        
        # Prüfe ob Mine-Name erwähnt wird
        content_lower = content.lower()
        mine_mentioned = False
        
        for variant in name_variants:
            if variant.lower() in content_lower:
                mine_mentioned = True
                break
        
        if not mine_mentioned:
            return False, 0.1
        
        # Berechne Konfidenz basierend auf Inhaltslänge und Struktur
        confidence = min(1.0, len(content) / 1000)
        
        # Bonus für strukturierte Antworten
        if any(indicator in content_lower for indicator in ["betreiber", "koordinaten", "rohstoff", "status"]):
            confidence += 0.2
        
        return True, min(1.0, confidence)
    
    def _calculate_data_quality(self, structured_data: Dict) -> Dict:
        """
        Berechnet Datenqualität basierend auf gefüllten Feldern
        
        Args:
            structured_data: Strukturierte Daten
            
        Returns:
            Qualitäts-Metriken
        """
        total_fields = len(CSV_COLUMNS)
        filled_fields = len([v for v in structured_data.values() if v and str(v).strip()])
        
        quality_score = filled_fields / total_fields if total_fields > 0 else 0
        
        # Gewichtung wichtiger Felder
        important_fields = ["betreiber", "koordinaten", "rohstofftyp", "aktivitaetsstatus"]
        important_filled = sum(1 for field in important_fields 
                             if structured_data.get(field) and str(structured_data[field]).strip())
        
        weighted_score = (important_filled / len(important_fields)) * 0.7 + quality_score * 0.3
        
        return {
            "quality_score": round(weighted_score, 2),
            "filled_fields": filled_fields,
            "total_fields": total_fields,
            "completion_rate": round(quality_score * 100, 1),
            "important_fields_filled": important_filled
        }