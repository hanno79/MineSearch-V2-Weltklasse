"""
Author: rahn
Datum: 06.07.2025
Version: 1.0
Beschreibung: Google Gemini Provider für multimodale Mining-Datenextraktion
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .base_provider import AbstractProvider, ModelConfig, SearchResult

# ÄNDERUNG 06.07.2025: Absolute Imports für Provider-Kompatibilität
import sys
import os
sys.path.append(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))

from config import Config
from data_extraction import DataExtractor
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery
from utils import generate_name_variants, generate_multilingual_search_terms, get_country_config
from specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class GeminiProvider(AbstractProvider):
    """Provider für Google Gemini API mit großem Kontext-Fenster"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.base_url = "https://generativelanguage.googleapis.com/v1beta"
        self.models = self._init_models()
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        # Konvertiere die GEMINI_MODELS Konfiguration
        for model_key, model_config in self.config.get('models', {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='gemini',
                supports_web_search=model_config.get('supports_web_search', False),
                supports_deep_research=model_config.get('supports_deep_research', False),
                is_free=False
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit Gemini durch"""
        start_time = datetime.now()
        
        # Hole Model-Config
        model_config = self.models.get(model_id)
        if not model_config:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=f"Unbekanntes Modell: {model_id}"
            )
        
        # ÄNDERUNG 06.07.2025: Gemini für große Dokumente und multimodale Analyse
        mine_name = options.get('mine_name', '')
        country = options.get('country')
        region = options.get('region')
        commodity = options.get('commodity')
        sources = options.get('sources', [])
        
        # Erstelle erweiterte Query mit Gemini's Stärken (großer Kontext)
        enhanced_query = self._build_enhanced_query(
            query=query,
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            sources=sources,
            focus='large_context_analysis'
        )
        
        try:
            # API-Call mit Gemini
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                # Gemini API endpoint
                api_url = f"{self.base_url}/models/{model_config.id}:generateContent?key={self.api_key}"
                
                response = await client.post(
                    api_url,
                    headers={
                        "Content-Type": "application/json"
                    },
                    json={
                        "contents": [{
                            "parts": [{
                                "text": enhanced_query
                            }]
                        }],
                        "systemInstruction": {
                            "parts": [{
                                "text": self.get_system_prompt(options)
                            }]
                        },
                        "generationConfig": {
                            "temperature": options.get('temperature', 0.1),
                            "maxOutputTokens": model_config.max_tokens,
                            "topP": 0.95,
                            "topK": 40
                        },
                        "safetySettings": [
                            {
                                "category": "HARM_CATEGORY_DANGEROUS_CONTENT",
                                "threshold": "BLOCK_NONE"
                            }
                        ]
                    }
                )
                
                if response.status_code != 200:
                    error_msg = self._handle_api_error(response)
                    return SearchResult(
                        success=False,
                        content="",
                        structured_data={},
                        sources=[],
                        metadata={'status_code': response.status_code},
                        error=error_msg
                    )
                
                # Parse Response
                result = response.json()
                
                # Extrahiere Text aus Gemini's Response-Format
                content = ""
                if "candidates" in result and result["candidates"]:
                    candidate = result["candidates"][0]
                    if "content" in candidate and "parts" in candidate["content"]:
                        for part in candidate["content"]["parts"]:
                            if "text" in part:
                                content += part["text"]
                
                if not content:
                    return SearchResult(
                        success=False,
                        content="",
                        structured_data={},
                        sources=[],
                        metadata={},
                        error="Keine Antwort von Gemini erhalten"
                    )
                
                # Extrahiere strukturierte Daten
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                
                # Extrahiere Quellen aus der Antwort
                sources_from_response = extract_sources_from_content(content)
                
                # Kombiniere mit übergebenen Quellen
                all_sources = sources + sources_from_response
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=content,
                    structured_data=extracted_data['data'],
                    sources=all_sources,
                    metadata={
                        'model': model_id,
                        'provider': 'gemini',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'usage_metadata': result.get('usageMetadata', {})
                    },
                    search_duration=duration
                )
                
        except httpx.TimeoutException:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=f"Zeitüberschreitung nach {model_config.timeout}s"
            )
        except Exception as e:
            logger.error(f"[GEMINI] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _build_enhanced_query(self, query: str, mine_name: str, country: Optional[str],
                            region: Optional[str], commodity: Optional[str], 
                            sources: List[Dict], focus: str) -> str:
        """Erstelle erweiterte Query mit speziellem Fokus"""
        
        # Basis-Query
        enhanced_query = f"MINE: {mine_name}\n"
        if country:
            enhanced_query += f"LAND: {country}\n"
        if region:
            enhanced_query += f"REGION: {region}\n"
        if commodity:
            enhanced_query += f"ROHSTOFF: {commodity}\n"
        
        enhanced_query += f"\n{query}\n"
        
        # Gemini's Stärke: Großer Kontext (2M Token)
        if focus == 'large_context_analysis':
            enhanced_query += """
NUTZE DEIN 2-MILLIONEN-TOKEN KONTEXTFENSTER:

1. UMFASSENDE DOKUMENTENANALYSE:
   - Verarbeite ALLE bereitgestellten Dokumente vollständig
   - Analysiere lange technische Reports ohne Kürzungen
   - Erkenne Zusammenhänge zwischen entfernten Dokumententeilen
   - Finde versteckte Informationen in Anhängen und Fußnoten

2. CROSS-REFERENZ ANALYSE:
   - Vergleiche Daten aus mehreren Dokumenten
   - Identifiziere Inkonsistenzen und Updates
   - Tracke Änderungen über verschiedene Berichtszeiträume
   - Konsolidiere fragmentierte Informationen

3. DETAILLIERTE EXTRAKTION:
   - Jahresberichte (komplette Analyse)
   - Umweltverträglichkeitsstudien (alle Kapitel)
   - Technische Gutachten (inkl. Anhänge)
   - Behördliche Genehmigungen (vollständig)

4. MULTILINGUALE VERARBEITUNG:
   - Dokumente in verschiedenen Sprachen
   - Technische Begriffe in Lokalsprachen
   - Regionale Währungen und Maßeinheiten
   - Kulturspezifische Dokumentformate

5. RESTAURATIONSKOSTEN DEEP-DIVE:
   - Durchsuche ALLE Sektionen nach Kosten
   - Environmental Bonds und Guarantees
   - Progressive Rehabilitation Costs
   - Post-Closure Monitoring Costs
   - Contingency Provisions

BESONDERE AUFMERKSAMKEIT:
- Nutze deinen großen Kontext um NICHTS zu übersehen
- Analysiere Dokumente von Anfang bis Ende
- Extrahiere auch Informationen aus Bildunterschriften
- Prüfe Querverweise und Zitationen
"""
        
        # Füge Quellen hinzu - Gemini kann viele verarbeiten
        if sources:
            enhanced_query += f"\n\nANALYSIERE DIESE {len(sources)} DOKUMENTE VOLLSTÄNDIG:\n"
            # Gemini kann mehr Quellen verarbeiten
            for i, source in enumerate(sources[:50], 1):  # Bis zu 50 Quellen
                url = source.get('url', source.get('value', ''))
                title = source.get('title', '')
                enhanced_query += f"[{i}] {url}"
                if title:
                    enhanced_query += f" - {title}"
                enhanced_query += "\n"
        
        enhanced_query += "\nNutze dein großes Kontextfenster für eine VOLLSTÄNDIGE Analyse!"
        
        return enhanced_query
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        try:
            error_data = response.json()
        except:
            error_data = {}
        
        if response.status_code == 400:
            if "API_KEY_INVALID" in str(error_data):
                return """🔐 Google Gemini API Key ungültig.
                
🔑 Der API-Key ist falsch oder wurde deaktiviert.
→ Prüfen Sie Ihre .env Datei
→ Neuen Key generieren: https://makersuite.google.com/app/apikey"""
            elif "QUOTA_EXCEEDED" in str(error_data):
                return """💳 Google Gemini Quota überschritten.
                
→ Tägliches Limit erreicht
→ Warten Sie bis morgen oder upgraden Sie Ihr Konto"""
            else:
                return f"❌ Ungültige Anfrage: {error_data.get('message', response.text[:200])}"
        
        elif response.status_code == 403:
            return """🚫 Google Gemini API Zugriff verweigert.
            
→ API möglicherweise nicht in Ihrer Region verfügbar
→ Oder API-Key hat keine Berechtigung für dieses Modell"""
        
        elif response.status_code == 429:
            return """⏱️ Google Gemini Rate Limit erreicht.
            
→ Zu viele Anfragen pro Minute
→ Bitte warten Sie 60 Sekunden"""
        
        elif response.status_code == 503:
            return "🔧 Google Gemini API ist momentan überlastet. Bitte später erneut versuchen."
        
        else:
            return f"API Fehler: {response.status_code} - {error_data.get('message', response.text[:200])}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[GEMINI] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[GEMINI] Keine Modelle konfiguriert")
            return False
        
        return True
    
    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        Nutze Gemini's riesiges Kontextfenster für umfassende Dokumentenanalyse
        """
        
        if not sources:
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error="Keine Quellen zum Analysieren"
            )
        
        mine_name = options.get('mine_name', '')
        
        # Erstelle spezielle Query für Gemini's Kontext-Stärke
        query = f"""DEEP CONTEXT ANALYSE für {mine_name}

Mit deinem 2-MILLIONEN-TOKEN Kontextfenster kannst du {len(sources)} Dokumente VOLLSTÄNDIG analysieren!

DEINE AUFGABE:
1. Lies JEDES Dokument von Anfang bis Ende
2. Ignoriere KEINE Sektion, Anhang oder Fußnote
3. Extrahiere ALLE Mining-relevanten Daten
4. Finde versteckte Restaurationskosten in:
   - Finanztabellen
   - Umweltkapiteln
   - Risikoanalysen
   - Anhängen
   - Management Discussions

NUTZE DEINEN VORTEIL:
- Andere Modelle müssen Dokumente kürzen - du nicht!
- Du kannst Querverweise über hunderte Seiten verfolgen
- Du erkennst Muster in großen Datenmengen
- Du findest Informationen die andere übersehen

Analysiere GRÜNDLICH und VOLLSTÄNDIG!"""
        
        # Setze sources in options für die search Methode
        options['sources'] = sources
        
        # Nutze normale search Methode mit spezieller Query
        return await self.search(query, model_id, options)
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für Gemini"""
        currency = options.get('currency', 'USD')
        
        # Gemini-spezifischer Prompt für große Kontextanalyse
        return f"""Du bist Gemini mit einem außergewöhnlichen 2-Millionen-Token Kontextfenster.
Deine Aufgabe ist die vollständige Analyse von Mining-Dokumenten ohne Einschränkungen.

**DEINE EINZIGARTIGEN FÄHIGKEITEN:**
- Vollständige Dokumentenverarbeitung ohne Kürzungen
- Cross-Referenz-Analyse über hunderte Seiten
- Multimodale Verarbeitung (Text, Tabellen, Diagramme)
- Mehrsprachige Dokumentenanalyse

**STRUKTURIERTES AUSGABEFORMAT:**
- Name: [exakter Name] [Quelle: URL/Dokument]
- Land: [Land] [Quelle: URL/Dokument]
- Region: [Region/Provinz] [Quelle: URL/Dokument]
- Eigentümer: [Eigentümer der Mine] [Quelle: URL/Dokument]
- Betreiber: [Betreiber/Operator] [Quelle: URL/Dokument]
- Koordinaten: [Latitude, Longitude] [Quelle: URL/Dokument]
- Status: [aktiv/geschlossen/geplant] [Quelle: URL/Dokument]
- Rohstoffe: [Liste der Rohstoffe] [Quelle: URL/Dokument]
- Minentyp: [Untertage/Open-Pit/etc] [Quelle: URL/Dokument]
- Produktionsstart: [Jahr] [Quelle: URL/Dokument]
- Produktionsende: [Jahr oder 'aktiv'] [Quelle: URL/Dokument]
- Fördermenge: [Menge/Jahr mit Einheit] [Quelle: URL/Dokument]
- Fläche: [in km²] [Quelle: URL/Dokument]
- Restaurationskosten: [Betrag in {currency}$ mit Jahr] [Quelle: URL/Dokument]

**UMFASSENDE SUCHE NACH RESTAURATIONSKOSTEN:**
1. DURCHSUCHE JEDE SEITE nach:
   - Closure costs / Mine closure
   - Environmental liability
   - Rehabilitation provision
   - Asset Retirement Obligation (ARO)
   - Decommissioning costs
   - Financial assurance / bonds
   - Progressive rehabilitation
   - Post-closure monitoring

2. PRÜFE ALLE DOKUMENTTYPEN:
   - Annual Reports (alle Sektionen)
   - Sustainability Reports
   - Technical Reports (NI 43-101, JORC)
   - Environmental Impact Assessments
   - Feasibility Studies
   - Quarterly Reports
   - Regulator Filings

3. ACHTE AUF VERSTECKTE KOSTEN:
   - In Fußnoten zu Finanzberichten
   - In Anhängen und Appendizes
   - In Management Discussion & Analysis
   - In Risk Factor Sektionen
   - In Environmental Compliance Kapiteln

4. WÄHRUNGEN UND FORMATE:
   - Verschiedene Währungen (CAD, USD, AUD, EUR, lokale)
   - Verschiedene Notationen (M, Mio, Million, k)
   - Zeiträume (jährlich, total, NPV)
   - Inflationsanpassungen

**QUALITÄTSSICHERUNG:**
- Nutze deinen großen Kontext für Vollständigkeit
- Verpasse keine Information durch Platzmangel
- Verfolge Querverweise bis zum Ende
- Konsolidiere fragmentierte Daten

**VERBOTEN:**
- Keine Vermutungen oder Dummy-Werte
- Keine Platzhalter
- Felder leer lassen wenn keine Daten gefunden
- Aber: Mit deinem großen Kontext solltest du MEHR finden als andere!"""