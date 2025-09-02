"""
Author: rahn
Datum: 02.09.2025
Version: 1.0
Beschreibung: Einheitlicher AI-Extraktion-Service für ALLE Provider

Dieser Service vereinheitlicht die Datenextraktion für alle Provider.
Statt zwei parallele Workflows (AI-Prompts + DataExtractor) gibt es nur noch einen:
Raw Content → AI-Extraktion → Normalisierung → Quality Gates
"""

import httpx
import json
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime

from minesearch.specialized_prompts_impl import SpecializedPrompts
from minesearch.value_normalizer import value_normalizer
from minesearch.config.models import OPENROUTER_MODELS

logger = logging.getLogger(__name__)


class UnifiedAIExtractionService:
    """
    Einheitlicher Service für AI-gestützte Datenextraktion.
    
    Ersetzt den alten DataExtractor und sorgt für konsistente
    Ergebnisse über alle Provider hinweg.
    """
    
    def __init__(self, openrouter_api_key: str):
        self.openrouter_api_key = openrouter_api_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        
        # Standard-Modell für Extraktion: Schnell und kostengünstig
        self.default_extraction_model = "anthropic/claude-3-haiku-20240307"
    
    async def extract_from_raw_content(
        self,
        raw_content: str,
        mine_name: str,
        country: str,
        commodity: str = None,
        region: str = None,
        extraction_model: str = None
    ) -> Dict[str, Any]:
        """
        Zentrale Extraktion für ALLE Provider.
        
        Args:
            raw_content: Rohdaten aus Web-Suche, Scraping oder API
            mine_name: Name der Mine
            country: Land
            commodity: Rohstoff (optional)
            region: Region (optional)
            extraction_model: AI-Modell für Extraktion (optional)
            
        Returns:
            Strukturierte und normalisierte Mining-Daten
        """
        start_time = datetime.now()
        
        try:
            # 1. Erstelle strukturierten Prompt
            extraction_prompt = self._build_extraction_prompt(
                mine_name=mine_name,
                country=country,
                commodity=commodity,
                region=region
            )
            
            # 2. AI-Extraktion durchführen
            model_to_use = extraction_model or self.default_extraction_model
            structured_data = await self._call_ai_extraction(
                model=model_to_use,
                raw_content=raw_content,
                extraction_prompt=extraction_prompt
            )
            
            # 3. Normalisierung anwenden (Canada → Kanada etc.)
            normalized_data = self._apply_normalization(structured_data)
            
            # 4. Quality Gates anwenden
            validated_data = self._apply_quality_gates(normalized_data, mine_name)
            
            # 5. Metadaten hinzufügen
            validated_data['_extraction_metadata'] = {
                'extraction_model': model_to_use,
                'extraction_time': (datetime.now() - start_time).total_seconds(),
                'content_length': len(raw_content),
                'unified_workflow': True,
                'version': '1.0'
            }
            
            logger.info(f"[UNIFIED-EXTRACT] Erfolgreiche Extraktion für {mine_name} mit {model_to_use}")
            return validated_data
            
        except Exception as e:
            logger.error(f"[UNIFIED-EXTRACT] Fehler bei Extraktion für {mine_name}: {e}")
            # Fallback: Basis-Struktur mit Fehlermeldung
            return self._get_fallback_structure(mine_name, country, str(e))
    
    def _build_extraction_prompt(
        self,
        mine_name: str,
        country: str,
        commodity: str = None,
        region: str = None
    ) -> Dict[str, str]:
        """Erstellt strukturierten Prompt für Mining-Datenextraktion"""
        
        # Nutze bewährte spezialisierte Prompts
        system_prompt = SpecializedPrompts.get_universal_anti_template_instructions()
        
        # Erweitere mit spezifischen Mining-Anweisungen
        system_prompt += f"""

🎯 DATENEXTRAKTION FÜR MINE: {mine_name}
===============================================

Extrahiere aus dem gegebenen Content strukturierte Mining-Daten.

AUSGABEFORMAT (JSON):
{{
    "Name": "{mine_name}",
    "Country": "normalisiert (Canada → Kanada)",
    "Region": "spezifische Region",
    "Eigentümer": "aktueller Eigentümer",
    "Betreiber": "aktueller Betreiber",
    "x-Koordinate": "präzise Dezimalzahl",
    "y-Koordinate": "präzise Dezimalzahl",
    "Aktivitätsstatus": "Aktiv/Geschlossen/Geplant",
    "Restaurationskosten": "Betrag mit Währung, z.B. '75.6 Millionen CAD'",
    "Jahr der Aufnahme der Kosten": "YYYY",
    "Jahr der Erstellung des Dokumentes": "YYYY",
    "Rohstoffabbau": "Gold, Kupfer, etc.",
    "Minentyp": "Untertage/Tagebau",
    "Produktionsstart": "YYYY",
    "Produktionsende": "YYYY",
    "Fördermenge/Jahr": "Menge mit Einheit",
    "Fläche der Mine in qkm": "Fläche mit Einheit",
    "Quellenangaben": "URLs oder Dokumenttitel"
}}

KRITISCHE REGELN:
- NUR echte, verifizierbare Daten extrahieren
- KEINE Template-Werte, Schätzungen oder Platzhalter
- Bei Unsicherheit: Feld leer lassen
- Numerische Werte: Volle Präzision beibehalten
- Länder: Auf Deutsch normalisieren (Canada → Kanada)
"""
        
        user_prompt = f"""
Analysiere den folgenden Content und extrahiere Mining-Daten für die Mine "{mine_name}" in {country}.

{f"Gesuchter Rohstoff: {commodity}" if commodity else ""}
{f"Region: {region}" if region else ""}

Gib NUR das JSON-Objekt zurück, keine weitere Erklärung.

CONTENT:
{{% RAW_CONTENT %}}
"""
        
        return {
            "system": system_prompt,
            "user": user_prompt
        }
    
    async def _call_ai_extraction(
        self,
        model: str,
        raw_content: str,
        extraction_prompt: Dict[str, str]
    ) -> Dict[str, Any]:
        """Ruft AI-Modell für Datenextraktion auf"""
        
        # Content in User-Prompt einsetzen
        user_content = extraction_prompt["user"].replace("{RAW_CONTENT}", raw_content)
        
        request_data = {
            "model": model,
            "messages": [
                {"role": "system", "content": extraction_prompt["system"]},
                {"role": "user", "content": user_content}
            ],
            "max_tokens": 4000,
            "temperature": 0.1,  # Niedrig für konsistente Extraktion
        }
        
        async with httpx.AsyncClient(timeout=120) as client:
            response = await client.post(
                self.base_url,
                headers={
                    "Authorization": f"Bearer {self.openrouter_api_key}",
                    "HTTP-Referer": "https://mining-data-extraction.com",
                    "X-Title": "MineSearch Unified Extraction",
                    "Content-Type": "application/json"
                },
                json=request_data
            )
            
            if response.status_code != 200:
                raise Exception(f"AI-API Fehler: {response.status_code} - {response.text}")
            
            result = response.json()
            ai_response = result["choices"][0]["message"]["content"]
            
            # JSON aus AI-Response extrahieren
            try:
                # Finde JSON-Block in der Antwort
                json_start = ai_response.find('{')
                json_end = ai_response.rfind('}') + 1
                
                if json_start >= 0 and json_end > json_start:
                    json_str = ai_response[json_start:json_end]
                    structured_data = json.loads(json_str)
                    return structured_data
                else:
                    raise ValueError("Kein JSON in AI-Response gefunden")
                    
            except (json.JSONDecodeError, ValueError) as e:
                logger.error(f"[UNIFIED-EXTRACT] JSON-Parsing-Fehler: {e}")
                logger.error(f"[UNIFIED-EXTRACT] AI-Response: {ai_response}")
                raise Exception(f"Ungültige JSON-Antwort vom AI-Modell: {e}")
    
    def _apply_normalization(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Wendet Value-Normalisierung auf alle Felder an"""
        
        normalized_data = {}
        
        for field_name, value in data.items():
            if field_name.startswith('_'):
                # Metadaten nicht normalisieren
                normalized_data[field_name] = value
            elif value and str(value).strip():
                # Normalisiere nicht-leere Werte
                normalized_value = value_normalizer.normalize_value(str(value), field_name)
                normalized_data[field_name] = normalized_value
                
                if normalized_value != str(value):
                    logger.debug(f"[UNIFIED-NORM] {field_name}: '{value}' → '{normalized_value}'")
            else:
                # Leere Werte beibehalten
                normalized_data[field_name] = value
        
        return normalized_data
    
    def _apply_quality_gates(self, data: Dict[str, Any], mine_name: str) -> Dict[str, Any]:
        """Wendet Quality Gates an (vereinfacht, da AI-Prompts bereits quality-gesichert sind)"""
        
        # Basis-Validierung: Name sollte immer gesetzt sein
        if not data.get('Name'):
            data['Name'] = mine_name
        
        # Entferne explizite Null-Werte und leere Strings
        cleaned_data = {}
        for key, value in data.items():
            if value is not None and str(value).strip():
                cleaned_data[key] = value
        
        return cleaned_data
    
    def _get_fallback_structure(self, mine_name: str, country: str, error: str) -> Dict[str, Any]:
        """Fallback-Struktur bei Fehlern"""
        return {
            'Name': mine_name,
            'Country': country,
            '_extraction_error': error,
            '_extraction_metadata': {
                'unified_workflow': True,
                'success': False,
                'version': '1.0'
            }
        }


# Singleton-Instance für einfache Nutzung
unified_extractor: Optional[UnifiedAIExtractionService] = None

def get_unified_extractor(openrouter_api_key: str) -> UnifiedAIExtractionService:
    """Factory-Funktion für Singleton-Instance"""
    global unified_extractor
    
    if unified_extractor is None:
        unified_extractor = UnifiedAIExtractionService(openrouter_api_key)
    
    return unified_extractor