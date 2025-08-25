"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: OpenRouter Provider für Mining-Suchen
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import json

from .base_provider import AbstractProvider, ModelConfig, SearchResult

from minesearch.data_extraction import DataExtractor
from minesearch.source_discovery import extract_sources_from_content
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.utils import (
    generate_name_variants,
    get_country_config,
    generate_multilingual_search_terms,
)
from minesearch.specialized_prompts import SpecializedPrompts

logger = logging.getLogger(__name__)


class OpenRouterProvider(AbstractProvider):
    """Provider für OpenRouter API"""
    
    def __init__(self, api_key: str, config: Dict[str, Any]):
        super().__init__(api_key, config)
        self.api_url = config.get('base_url', 'https://openrouter.ai/api/v1') + '/chat/completions'
        self.models = self._init_models()
        self.data_extractor = DataExtractor()
    
    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}
        
        # Konvertiere OpenRouter Modelle aus Config
        for model_key, model_config in self.config.get('models', {}).items():
            # ÄNDERUNG 24.08.2025: Provider-Kategorie für UI-Darstellung berücksichtigen
            provider_category = model_config.get('provider_category', 'openrouter')
            
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='openrouter',  # Technischer Provider (für Routing)
                provider_category=provider_category,  # UI-Kategorie
                supports_web_search=model_config.get('supports_web_search', False),
                supports_deep_research=model_config.get('supports_deep_research', False),
                is_free=model_config.get('is_free', True)
            )
        
        return models
    
    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit OpenRouter durch"""
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
        
        try:
            # ÄNDERUNG 04.07.2025: Enhanced Source Discovery nutzen
            mine_name = options.get('mine_name', '')
            country = options.get('country')
            region = options.get('region')
            
            # ÄNDERUNG 06.07.2025: Nutze übergebene Quellen wenn vorhanden
            discovered_sources = options.get('discovered_sources', [])
            skip_discovery = options.get('skip_source_discovery', False)
            
            # Initialisiere source_discovery immer
            source_discovery = EnhancedSourceDiscovery()
            
            if not discovered_sources and not skip_discovery and mine_name:
                # Nur wenn keine Quellen übergeben wurden, führe eigene Discovery durch
                logger.info(f"[OPENROUTER] Starte eigene Source Discovery für {mine_name}")
                discovered_sources = source_discovery.discover_sources_for_mine(
                    mine_name=mine_name,
                    country=country,
                    region=region
                )
                logger.info(f"[OPENROUTER] {len(discovered_sources)} Quellen selbst entdeckt")
            else:
                logger.info(f"[OPENROUTER] Nutze {len(discovered_sources)} übergebene Quellen")
            
            # Generiere Sprachvarianten
            name_variants = generate_name_variants(mine_name) if mine_name else []
            country_config = get_country_config(country) if country else {}
            multilingual_terms = generate_multilingual_search_terms(country_config)
            
            # Angepasster Query für OpenRouter mit Quellen
            enhanced_query = self._enhance_query_for_no_web(
                query, options, 
                discovered_sources=discovered_sources,
                name_variants=name_variants,
                multilingual_terms=multilingual_terms
            )
            
            # API-Call
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json",
                        "HTTP-Referer": "https://minesearch.app",  # Optional für OpenRouter
                        "X-Title": "MineSearch v2"  # Optional für OpenRouter
                    },
                    json={
                        "model": model_config.id,
                        "messages": [
                            {
                                "role": "system",
                                "content": self.get_system_prompt(options)
                            },
                            {
                                "role": "user",
                                "content": enhanced_query
                            }
                        ],
                        # ÄNDERUNG 07.07.2025: Temperature auf 0 für maximale Konsistenz
                        "temperature": options.get('temperature', 0.0),
                        "max_tokens": model_config.max_tokens,
                        "top_p": 0.9
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
                
                # OpenRouter Response Format
                if 'choices' in result and result['choices']:
                    content = result['choices'][0]['message']['content']
                else:
                    content = result.get('message', 'Keine Antwort erhalten')
                
                # Extrahiere strukturierte Daten
                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)
                # BUGFIX 20.07.2025: Verwende discovered sources für Source-Tracking
                # Konvertiere discovered_sources zu standardisierten Source-Format
                sources = []
                for source in discovered_sources[:10]:  # Limitiere auf Top 10 für Performance
                    sources.append({
                        'url': source.get('url', ''),
                        'title': source.get('title', source.get('url', '')),
                        'type': source.get('type', 'unknown'),
                        'reliability': source.get('reliability_score', 0.5)
                    })
                
                # ÄNDERUNG 07.07.2025: Zusätzliche Validierung direkt im Provider
                # Verhindere "Koordinaten" als Betreiber
                if extracted_data['data'].get('Betreiber'):
                    betreiber = str(extracted_data['data']['Betreiber']).strip()
                    if betreiber.lower() in ['koordinaten', 'coordinates', 'coords', 'koordinate'] or 'koordinaten:' in betreiber.lower():
                        logger.warning(f"[OPENROUTER] Ungültiger Betreiber entfernt: {betreiber}")
                        extracted_data['data']['Betreiber'] = ""
                        # Entferne auch aus data_with_sources
                        if 'Betreiber' in extracted_data.get('data_with_sources', {}):
                            extracted_data['data_with_sources']['Betreiber'] = {"value": "", "sources": []}
                
                # DEBUG 23.08.2025: Log alle Restaurationskosten für Debugging
                if extracted_data['data'].get('Restaurationskosten'):
                    resto = extracted_data['data']['Restaurationskosten']
                    logger.info(f"[OPENROUTER-DEBUG] Restaurationskosten extrahiert: '{resto}'")
                    
                    # ÄNDERUNG 07.07.2025: Validiere Restaurationskosten
                    # Prüfe auf verdächtige Werte
                    suspicious_values = ['USD$1.0 million', 'CAD$1.0 million', '$1.0 million', '1.0 million', 
                                       'USD$1 million', 'CAD$1 million', '$1 million', '1 million',
                                       'CAD$10000.0 million', 'USD$10000.0 million']
                    if resto in suspicious_values or (isinstance(resto, str) and any(sv in resto for sv in suspicious_values)):
                        logger.warning(f"[OPENROUTER] Verdächtiger Restaurationswert entfernt: {resto}")
                        extracted_data['data']['Restaurationskosten'] = ""
                        # Entferne auch aus data_with_sources
                        if 'Restaurationskosten' in extracted_data.get('data_with_sources', {}):
                            extracted_data['data_with_sources']['Restaurationskosten'] = {"value": "", "sources": []}
                    else:
                        logger.info(f"[OPENROUTER-DEBUG] Restaurationskosten BEHALTEN: '{resto}'")
                else:
                    logger.info(f"[OPENROUTER-DEBUG] Keine Restaurationskosten extrahiert")
                
                # KORRIGIERT: Keine Source Discovery bei LLM-Providern da keine echten Sources
                
                # Finalisiere Session
                session_summary = source_discovery.finalize_session()
                
                duration = (datetime.now() - start_time).total_seconds()
                
                return SearchResult(
                    success=True,
                    content=content,
                    structured_data=extracted_data['data'],
                    sources=sources,
                    metadata={
                        'model': model_id,
                        'provider': 'openrouter',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
                        'source_mapping': extracted_data.get('source_mapping', {}),  # QUELLENREFERENZEN-FIX 24.08.2025
                        'usage': result.get('usage', {}),
                        'source_discovery_session': session_summary,
                        'discovered_sources_count': len(discovered_sources)
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
            logger.error(f"[OPENROUTER] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )
    
    def _enhance_query_for_no_web(self, query: str, options: Dict[str, Any], 
                                  discovered_sources: List[Dict] = None,
                                  name_variants: List[str] = None,
                                  multilingual_terms: Dict[str, List[str]] = None) -> str:
        """
        Erweitere Query für Modelle ohne Web-Suche
        Füge Kontext, Quellen und Sprachvarianten hinzu
        """
        mine_name = options.get('mine_name', '')
        country = options.get('country', '')
        commodity = options.get('commodity', '')
        region = options.get('region', '')
        
        # ÄNDERUNG 04.07.2025: Nutze spezialisierte Prompts
        # ÄNDERUNG 05.07.2025: Verstärkter Fokus auf Restaurationskosten
        specialized_prompt = SpecializedPrompts.get_enhanced_query(
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            focus_fields=['restoration_costs', 'coordinates', 'ownership', 'production']
        )
        
        # Füge zusätzlichen spezifischen Restaurationskosten-Prompt hinzu
        restoration_prompt = SpecializedPrompts.get_restoration_costs_prompt(mine_name, country, commodity)
        
        # ÄNDERUNG 08.07.2025: ALLE Quellen nutzen, nicht nur Top 20
        sources_text = ""
        if discovered_sources:
            sources_text = f"\n\n📚 WICHTIG: Nutze dein Wissen über ALLE {len(discovered_sources)} folgenden Quellen!\n"
            sources_text += "Auch wenn du nicht direkt darauf zugreifen kannst, kennst du möglicherweise Daten aus diesen Quellen:\n\n"
            
            # Gruppiere nach Quellentyp
            gov_sources = [s for s in discovered_sources if s.get('type') == 'government']
            db_sources = [s for s in discovered_sources if s.get('type') == 'database']
            exchange_sources = [s for s in discovered_sources if s.get('type') == 'exchange']
            other_sources = [s for s in discovered_sources if s.get('type') not in ['government', 'database', 'exchange']]
            
            if gov_sources:
                sources_text += "REGIERUNGSQUELLEN:\n"
                for i, source in enumerate(gov_sources, 1):
                    sources_text += f"[G{i}] {source['url']}\n"
                sources_text += "\n"
            
            if exchange_sources:
                sources_text += "BÖRSENDOKUMENTE:\n"
                for i, source in enumerate(exchange_sources, 1):
                    sources_text += f"[EX{i}] {source['url']}\n"
                sources_text += "\n"
            
            if db_sources:
                sources_text += "MINING-DATENBANKEN:\n"
                for i, source in enumerate(db_sources, 1):
                    sources_text += f"[DB{i}] {source['url']}\n"
                sources_text += "\n"
            
            if other_sources:
                sources_text += "WEITERE QUELLEN:\n"
                for i, source in enumerate(other_sources, 1):
                    sources_text += f"[{i}] {source['url']}\n"
            
            sources_text += "\n⚠️ Berücksichtige ALLE diese Quellen in deiner Antwort!"
        
        # Füge Namensvarianten hinzu
        variants_text = ""
        if name_variants:
            variants_text = f"\n\nMÖGLICHE SCHREIBWEISEN: {', '.join(name_variants[:5])}"
        
        # Füge mehrsprachige Begriffe hinzu
        multilingual_text = ""
        if multilingual_terms:
            key_terms = []
            for term_type, terms in multilingual_terms.items():
                if term_type == 'restoration_costs' and terms:
                    key_terms.extend(terms[:5])  # Top 5 Begriffe
            if key_terms:
                multilingual_text = f"\n\nSUCHBEGRIFFE für Restaurationskosten: {', '.join(key_terms)}"
        
        enhanced = f"""Basierend auf deinem Wissen über Bergbau und Mining, beantworte folgende Anfrage:

{query}

MINE: {mine_name}
LAND: {country if country else 'Unbekannt'}
REGION: {region if region else 'Unbekannt'}
ROHSTOFF: {commodity if commodity else 'Unbekannt'}
{variants_text}
{multilingual_text}
{sources_text}

{specialized_prompt}

{restoration_prompt}

KRITISCHE ANWEISUNGEN - KEINE DUMMY-WERTE:
1. NIEMALS Standard-Werte wie "$1.0 million" oder "1 million" verwenden
2. NIEMALS erfundene oder geschätzte Werte angeben
3. Wenn keine Daten vorhanden: Feld komplett weglassen (nicht erwähnen)
4. Nur KONKRETE Werte aus deinem Fachwissen verwenden
5. Bei Restaurationskosten: NUR wenn du tatsächliche Beträge kennst
6. Bei Koordinaten: NUR echte GPS-Koordinaten, keine Platzhalter
7. Bei Betreiber: NIEMALS "Koordinaten" als Betreiber angeben

WICHTIG: Lieber ein fehlendes Feld als einen falschen Wert!

ANTWORTE IM STRUKTURIERTEN FORMAT wie im System-Prompt beschrieben."""
        
        return enhanced
    
    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            return "🔑 OpenRouter API-Key ungültig.\n→ Bitte prüfen Sie Ihre .env Datei."
        
        elif response.status_code == 429:
            return "⏱️ Rate Limit erreicht.\n→ Zu viele Anfragen. Bitte warten Sie einen Moment."
        
        elif response.status_code == 503:
            return "🔧 OpenRouter API ist momentan nicht verfügbar.\n→ Bitte versuchen Sie es später erneut."
        
        else:
            try:
                error_data = response.json()
                error_msg = error_data.get('error', {}).get('message', 'Unbekannter Fehler')
                return f"OpenRouter Fehler: {error_msg}"
            except json.JSONDecodeError:
                logger.warning(f"[OPENROUTER] Fehlerhafte JSON-Antwort bei Status {response.status_code}: {response.text[:100]}")
                return f"API Fehler: {response.status_code} - Ungültige JSON-Antwort"
            except (KeyError, AttributeError) as e:
                logger.warning(f"[OPENROUTER] Unerwartete Fehler-Struktur: {e}")
                return f"API Fehler: {response.status_code} - {response.text[:200]}"
    
    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models
    
    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[OPENROUTER] Kein API-Key konfiguriert")
            return False
        
        if not self.models:
            logger.error("[OPENROUTER] Keine Modelle konfiguriert")
            return False
        
        return True
    
    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """System-Prompt für OpenRouter (angepasst für Modelle ohne Web-Suche)"""
        currency = options.get('currency', 'USD')
        
        return f"""Du bist ein Mining-Recherche-Experte mit umfassendem Wissen über die globale Bergbauindustrie. 
Antworte auf Deutsch mit STRUKTURIERTEN DATEN.

**VOLLSTÄNDIGE DATEN FÜR [MINENNAME] - ALLE 18 FELDER AUSFÜLLEN:**
- Name: [exakter Name] [Quelle: Fachwissen/Schätzung]
- Country: [Land] [Quelle: Fachwissen/Schätzung]
- Region: [Region/Provinz] [Quelle: Fachwissen/Schätzung]
- Eigentümer: [Eigentümer - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Betreiber: [Betreiber - wenn unbekannt, leer lassen: "" - NIEMALS Koordinaten hier angeben!] [Quelle: Fachwissen/Schätzung]
- x-Koordinate: [Latitude in Dezimalgrad - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- y-Koordinate: [Longitude in Dezimalgrad - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Aktivitätsstatus: [aktiv/geschlossen/geplant - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Restaurationskosten: [NUR realistische Beträge in {currency}$ - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Jahr der Aufnahme der Kosten: [Jahr der Kostenschätzung - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Jahr der Erstellung des Dokumentes: [Jahr des Reports/Studies - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Rohstoffabbau: [NUR spezifische Rohstoffe wie 'Gold', 'Kupfer', 'Eisenerz' - NIEMALS Template-Strukturen oder 'usw.' - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Minentyp: [NUR spezifische Werte wie 'Untertage', 'Open-Pit', 'Hybrid' - NIEMALS Template-Strukturen - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Produktionsstart: [Jahr - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Produktionsende: [Jahr oder 'aktiv' - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Fördermenge/Jahr: [Menge/Jahr mit Einheit - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Fläche der Mine in qkm: [Fläche in km² - wenn unbekannt, leer lassen: ""] [Quelle: Fachwissen/Schätzung]
- Quellenangaben: [Referenzen oder 'Allgemeines Fachwissen'] [Quelle: Fachwissen/Schätzung]

**KRITISCHE REGELN FÜR RESTAURATIONSKOSTEN:**
- NIEMALS "$1 CAD", "$2 CAD", "$3 CAD" oder ähnliche Platzhalter verwenden!
- Nur realistische Schätzungen basierend auf:
  * Minentyp (Open-Pit: 50-500 Mio USD, Untertage: 20-200 Mio USD)
  * Größe der Mine und Umweltvorschriften
- Mindestbetrag: $10,000 - darunter ist unrealistisch
- Wenn unsicher: Feld leer lassen (""), KEINE Minimalwerte!

**VERBOTENE PLATZHALTER UND META-TEXTE:**
- KEINE "k.A.", "n/a", "-", "unbekannt", "nicht gefunden", "LEER"
- KEINE Minimalwerte wie $1, $2, $3
- 🚫 NIEMALS META-ANWEISUNGEN SCHREIBEN:
  * "Feld ausgelassen"
  * "Feld komplett auslassen"
  * "Field omitted" 
  * "Field skipped"
  * Jegliche Kommentare über das Feld selbst
- Wenn keine Daten: Feld mit leerem String ("") ausfüllen

**QUELLEN-SEKTION:**
[Da du keine Web-Suche durchführst, gib an:]
[1] Allgemeines Branchenwissen
[2] Typische Werte für vergleichbare Minen
[3] Schätzung basierend auf Minentyp und Region

Markiere alle unsicheren Daten deutlich als "geschätzt" oder "typischer Wert"."""