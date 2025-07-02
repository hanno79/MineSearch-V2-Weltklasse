"""
Author: rahn
Datum: 30.06.2025
Version: 1.0
Beschreibung: Such-Service für MineSearch - Perplexity API Integration
"""

import logging
import httpx
from datetime import datetime
from typing import Dict, Any, List, Optional

from config import config, Config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES
from utils import normalize_accents, generate_name_variants, generate_multilingual_search_terms, get_country_config
from data_extraction import extract_structured_data_with_sources
from source_discovery import extract_sources_from_content
from enhanced_source_discovery import EnhancedSourceDiscovery

# ÄNDERUNG 30.06.2025: Strukturiertes Logging implementiert (Regel 16)
logger = logging.getLogger(__name__)

# ÄNDERUNG 01.07.2025: CSV_COLUMNS aus config.py importiert

class MineSearchService:
    """Service-Klasse für Mining-Suchen über Perplexity API"""
    
    def __init__(self):
        self.api_key = config.PERPLEXITY_API_KEY
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.enhanced_discovery = EnhancedSourceDiscovery()  # ÄNDERUNG 01.07.2025: Enhanced Source Discovery
        
    async def search_mine(self, mine_name: str, country: Optional[str] = None, 
                         commodity: Optional[str] = None, model: str = "sonar-pro",
                         region: Optional[str] = None, _is_auto_enhanced: bool = False) -> Dict[str, Any]:
        """
        Hauptsuchfunktion für Mining-Informationen
        
        Args:
            mine_name: Name der Mine
            country: Land (optional)
            commodity: Rohstoff (optional)
            model: Perplexity-Modell
            _is_auto_enhanced: INTERN - Verhindert Rekursion bei Auto-Two-Phase
            
        Returns:
            Dict mit Suchergebnissen
        """
        if not self.api_key:
            logger.error("Perplexity API Key nicht konfiguriert")
            raise ValueError("API Key nicht konfiguriert")
        
        # ÄNDERUNG 01.07.2025: Active Source Discovery Phase
        start_time = datetime.now()
        logger.info(f"[SEARCH START] Mine: {mine_name}, Model: {model}, Auto-Enhanced: {_is_auto_enhanced}")
        
        session = self.enhanced_discovery.start_session(mine_name, country, region)
        discovered_sources = self.enhanced_discovery.discover_sources_for_mine(
            mine_name, country, region, commodity
        )
        logger.info(f"[SOURCE DISCOVERY] {len(discovered_sources)} Quellen für {mine_name} entdeckt")
        
        # ÄNDERUNG 01.07.2025: API-Suche für strukturierte Daten
        api_results = {}
        if discovered_sources:
            # Verwende die übergebene Region für API-Suche
            api_results = await self.enhanced_discovery.search_with_apis(mine_name, country, region)
            if api_results:
                logger.info(f"[API SEARCH] {len(api_results)} APIs lieferten Daten")
        
        # ÄNDERUNG 01.07.2025: Tracke alle entdeckten Quellen
        if discovered_sources:
            await self.enhanced_discovery.track_discovered_sources(discovered_sources)
            logger.info(f"[SOURCE TRACKING] {len(discovered_sources)} Quellen als durchsucht markiert")
        
        # ÄNDERUNG 30.06.2025: Try-catch für API-Calls (Regel 13)
        try:
            # Generiere Suchvarianten
            name_variants = generate_name_variants(mine_name)
            multilingual_terms = generate_multilingual_search_terms(mine_name, country)
            
            logger.info(f"[SEARCH] Mine: {mine_name}, Modell: {model}, Varianten: {len(name_variants)}")
            
            # ÄNDERUNG 01.07.2025: Verwende Enhanced Prompt mit discovered sources
            if discovered_sources:
                search_query = self.enhanced_discovery.build_enhanced_prompt(
                    mine_name, discovered_sources, max_sources=15
                )
                # Füge Standard-Suchbegriffe hinzu
                standard_query = self._build_search_query(
                    mine_name, name_variants, multilingual_terms, 
                    country, commodity, model
                )
                search_query += "\n\n" + standard_query
                
                # ÄNDERUNG 01.07.2025: Füge API-Ergebnisse hinzu wenn vorhanden
                if api_results:
                    search_query += "\n\n**VERIFIZIERTE DATEN AUS OFFIZIELLEN QUELLEN:**\n"
                    for api_name, api_data in api_results.items():
                        search_query += f"\n{api_name.upper()}:\n"
                        if isinstance(api_data, dict):
                            for key, value in api_data.items():
                                search_query += f"- {key}: {value}\n"
                    search_query += "\nBitte berücksichtige diese verifizierten Daten in deiner Antwort."
            else:
                # Fallback auf Standard-Query
                search_query = self._build_search_query(
                    mine_name, name_variants, multilingual_terms, 
                    country, commodity, model
                )
            
            # Hole Modell-Konfiguration
            model_config = config.PERPLEXITY_MODELS.get(model, config.PERPLEXITY_MODELS[config.DEFAULT_MODEL])
            
            # ÄNDERUNG 30.06.2025: Performance-Dokumentation (Regel 16)
            # Diese Funktion kann bei Deep Research >30 Minuten dauern
            if model == "sonar-deep-research":
                logger.warning(f"[PERFORMANCE] Deep Research für {mine_name} kann 30+ Minuten dauern")
            
            # ÄNDERUNG 01.07.2025: Bei Deep Research führe mehrere spezialisierte Suchen durch
            if model == "sonar-deep-research" and discovered_sources:
                logger.info(f"[DEEP RESEARCH] Starte mehrere spezialisierte Suchen für {mine_name}")
                
                # Erstelle spezialisierte Prompts
                deep_prompts = self.enhanced_discovery.build_deep_search_prompts(
                    mine_name, discovered_sources, country
                )
                
                # Führe erste Hauptsuche durch
                result = await self._call_perplexity_api(search_query, model_config)
                processed_result = await self._process_search_result(
                    result, mine_name, country, name_variants, search_query, model
                )
                
                # Führe zusätzliche spezialisierte Suchen durch (sequenziell)
                additional_content = ""
                for i, deep_prompt in enumerate(deep_prompts):
                    logger.info(f"[DEEP RESEARCH] Spezialisierte Suche {i+1}/{len(deep_prompts)}")
                    try:
                        deep_result = await self._call_perplexity_api(deep_prompt, model_config)
                        if "choices" in deep_result and deep_result["choices"]:
                            deep_content = deep_result["choices"][0]["message"]["content"]
                            additional_content += f"\n\n### Spezialisierte Suche {i+1}:\n{deep_content}"
                            
                            # Extrahiere und tracke zusätzliche Quellen
                            from source_discovery import extract_sources_from_content
                            additional_sources = extract_sources_from_content(deep_content)
                            for source in additional_sources:
                                if source.get('url'):
                                    self.enhanced_discovery.track_source_result(
                                        url=source['url'],
                                        success=True,
                                        content_type=source.get('type', 'general')
                                    )
                    except Exception as e:
                        logger.error(f"[DEEP RESEARCH] Fehler bei spezialisierter Suche {i+1}: {str(e)}")
                
                # Füge zusätzliche Inhalte zu den Ergebnissen hinzu
                if additional_content and processed_result.get('success'):
                    processed_result['data']['content'] += additional_content
                    # Neu-Extraktion der strukturierten Daten mit allen Inhalten
                    from data_extraction import extract_structured_data_with_sources
                    combined_data = extract_structured_data_with_sources(
                        processed_result['data']['content'], mine_name, country
                    )
                    processed_result['data']['structured_data'] = combined_data['data']
                    processed_result['data']['structured_data_with_sources'] = combined_data['data_with_sources']
            else:
                # Standard-Suche
                result = await self._call_perplexity_api(search_query, model_config)
                processed_result = await self._process_search_result(
                    result, mine_name, country, name_variants, search_query, model
                )
            
            # ÄNDERUNG 01.07.2025: Automatische Two-Phase bei schlechten Ergebnissen
            # ÄNDERUNG 02.07.2025: Rekursionsschutz hinzugefügt
            if (model != "sonar-deep-research" and 
                processed_result.get('success') and 
                not _is_auto_enhanced):  # Verhindere Rekursion!
                
                data_quality = processed_result['data'].get('data_quality', {})
                sources = processed_result['data'].get('sources', [])
                
                # Prüfe ob Two-Phase automatisch aktiviert werden sollte
                should_activate_two_phase = (
                    data_quality.get('completeness_percentage', 0) < 40 or  # Weniger als 40% Daten
                    'Restaurationskosten' in data_quality.get('missing_critical_fields', []) or  # Keine Restaurationskosten
                    len(sources) < 3  # Weniger als 3 Quellen
                )
                
                if should_activate_two_phase:
                    logger.warning(f"[AUTO TWO-PHASE] Aktiviere automatische Two-Phase für {mine_name} (Qualität: {data_quality.get('completeness_percentage', 0)}%)")
                    logger.warning("[AUTO TWO-PHASE] WARNUNG: Dies kann die Suchzeit erheblich verlängern!")
                    
                    # Führe Two-Phase-Suche durch - MIT Rekursionsschutz
                    enhanced_result = await self.enhanced_search(
                        mine_name, country, commodity, model, region, 
                        _from_auto=True  # Markiere als automatisch
                    )
                    
                    # Markiere als automatische Two-Phase
                    if enhanced_result.get('data'):
                        enhanced_result['data']['auto_two_phase'] = True
                        enhanced_result['data']['two_phase_reason'] = {
                            'low_quality': data_quality.get('completeness_percentage', 0) < 40,
                            'missing_restoration': 'Restaurationskosten' in data_quality.get('missing_critical_fields', []),
                            'few_sources': len(sources) < 3
                        }
                    return enhanced_result
            
            # Zeittracking
            search_duration = (datetime.now() - start_time).total_seconds()
            if processed_result.get('data'):
                processed_result['data']['search_duration'] = search_duration
            
            logger.info(f"[SEARCH COMPLETE] Mine: {mine_name}, Duration: {search_duration:.1f}s, Success: {processed_result.get('success', False)}")
            
            return processed_result
            
        except httpx.TimeoutException as e:
            # ÄNDERUNG 30.06.2025: Timeout-Handling (Regel 13)
            timeout = model_config.get("timeout", 120)
            logger.error(f"[TIMEOUT] Perplexity API nach {timeout}s für {mine_name}")
            return {
                "success": False,
                "error": f"Zeitüberschreitung nach {timeout} Sekunden. Bei Deep Research normal.",
                "search_query": search_query
            }
        except Exception as e:
            # ÄNDERUNG 30.06.2025: Aussagekräftige Fehlermeldungen (Regel 13)
            logger.error(f"[ERROR] Suchfehler für {mine_name}: {str(e)}")
            return {
                "success": False,
                "error": f"Fehler bei der Suche: {str(e)}",
                "search_query": search_query if 'search_query' in locals() else ""
            }
    
    def _build_search_query(self, mine_name: str, name_variants: List[str], 
                           multilingual_terms: List[str], country: Optional[str], 
                           commodity: Optional[str], model: str) -> str:
        """Konstruiert die Suchanfrage für Perplexity"""
        
        primary_name = mine_name
        additional_names = [v for v in name_variants if v != primary_name][:2]
        
        # Basis-Suchanfrage
        search_query = f"Finde Informationen über die Mine: {primary_name}"
        
        if additional_names:
            search_query += f" (auch bekannt als: {', '.join(additional_names)})"
        
        if len(multilingual_terms) > 1:
            search_query += f" (Suchbegriffe: {', '.join(multilingual_terms[:3])})"
        
        if country:
            search_query += f" in {country}"
        
        if commodity:
            country_config = get_country_config(country)
            commodity_terms = country_config.get('mining_terms', {}).get('commodity', ['commodity'])
            search_query += f", die {commodity} abbaut ({'/'.join(commodity_terms)}: {commodity})"
        
        # Erweiterte Begriffe für Restaurationskosten
        country_config = get_country_config(country)
        currency = country_config.get('currency', 'USD')
        restoration_terms = country_config.get('mining_terms', {}).get('restoration_costs', [])
        
        key_restoration_terms = restoration_terms[:6] if restoration_terms else [
            'restoration costs', 'closure costs', 'reclamation costs',
            'asset retirement obligation', 'environmental liability', 'closure bond'
        ]
        
        # Modell-spezifische Suchanfrage
        if model == "sonar-deep-research":
            search_query += self._build_deep_research_query(primary_name, currency, key_restoration_terms)
        else:
            search_query += self._build_standard_query(primary_name, currency, key_restoration_terms)
        
        return search_query
    
    def _build_deep_research_query(self, mine_name: str, currency: str, restoration_terms: List[str]) -> str:
        """Baut Deep Research Suchanfrage"""
        query = f". WICHTIG: Suche NUR nach der spezifischen Mine '{mine_name}'! "
        query += f"Ich benötige BESONDERS folgende Finanzdaten in {currency}: "
        query += f"1) {' / '.join(restoration_terms[:3])}, "
        query += f"2) {' / '.join(restoration_terms[3:6])}, "
        query += f"3) Rückstellungen für Rekultivierung / provisions for closure. "
        query += f"Außerdem: Betreiber, exakte Koordinaten, Rohstoffe, Produktionsdaten, Aktivitätsstatus, Fläche in km². "
        query += f"KRITISCH: Suche in verschiedenen Quellen: Regierungsdatenbanken, SEDAR, NI 43-101 Reports, Annual Reports mit ARO Sections, Closure Plans. "
        query += f"Suche auch in: {', '.join(Config.PRIORITY_MINING_DOMAINS['tier1'][:5])}. "
        query += f"Gib für JEDE Information die genaue Quelle mit URL an!"
        return query
    
    def _build_standard_query(self, mine_name: str, currency: str, restoration_terms: List[str]) -> str:
        """Baut Standard-Suchanfrage"""
        query = f". Ich benötige für die Mine '{mine_name}': "
        query += f"1) Betreiber, 2) Koordinaten, 3) Rohstoffe, 4) Status (aktiv/geschlossen), "
        query += f"5) WICHTIG: {' / '.join(restoration_terms[:3])} in {currency} falls verfügbar, "
        query += f"6) Produktionsdaten. "
        query += f"ZUSÄTZLICH: Prüfe offizielle Mining-Datenbanken und Regierungsportale. "
        query += f"Suche nach NI 43-101 Reports und Annual Reports. "
        query += f"Strukturiere die Antwort klar mit Überschriften und gib für jede Information die Quelle an."
        return query
    
    async def _call_perplexity_api(self, search_query: str, model_config: Dict) -> Dict:
        """Führt den API-Call zu Perplexity aus"""
        
        model_id = model_config["id"]
        timeout = model_config["timeout"]
        max_tokens = model_config["max_tokens"]
        
        # ÄNDERUNG 30.06.2025: Timeout-Handling für API (Regel 13)
        async with httpx.AsyncClient(timeout=timeout) as client:
            response = await client.post(
                self.api_url,
                headers={
                    "Authorization": f"Bearer {self.api_key}",
                    "Content-Type": "application/json"
                },
                json={
                    "model": model_id,
                    "messages": [
                        {
                            "role": "system",
                            "content": self._get_system_prompt()
                        },
                        {
                            "role": "user",
                            "content": search_query
                        }
                    ],
                    "temperature": config.PERPLEXITY_TEMPERATURE,
                    "max_tokens": max_tokens
                }
            )
            
            if response.status_code != 200:
                logger.error(f"[API ERROR] Status: {response.status_code}, Response: {response.text[:200]}")
                
                # ÄNDERUNG 02.07.2025: Benutzerfreundliche Fehlermeldungen für API-Fehler
                if response.status_code == 401:
                    error_msg = "🔐 Perplexity API Authentifizierung fehlgeschlagen.\n\n"
                    response_text = response.text.lower()
                    
                    if "quota" in response_text or "budget" in response_text or "limit" in response_text:
                        error_msg += "💳 Ihr API-Budget ist aufgebraucht.\n"
                        error_msg += "→ Bitte prüfen Sie Ihr Perplexity-Konto und laden Sie Ihr Guthaben auf.\n"
                    elif "invalid" in response_text or "unauthorized" in response_text:
                        error_msg += "🔑 Der API-Key ist ungültig oder abgelaufen.\n"
                        error_msg += "→ Bitte prüfen Sie Ihre .env Datei und generieren Sie ggf. einen neuen Key.\n"
                    else:
                        error_msg += "❓ Authentifizierungsproblem mit dem API-Key.\n"
                    
                    error_msg += "\n📍 API-Verwaltung: https://www.perplexity.ai/settings/api"
                    raise ValueError(error_msg)
                
                elif response.status_code == 429:
                    error_msg = "⏱️ Rate Limit erreicht.\n"
                    error_msg += "→ Zu viele Anfragen. Bitte warten Sie einen Moment und versuchen Sie es erneut."
                    raise ValueError(error_msg)
                
                elif response.status_code == 503:
                    error_msg = "🔧 Perplexity API ist momentan nicht verfügbar.\n"
                    error_msg += "→ Bitte versuchen Sie es in einigen Minuten erneut."
                    raise ValueError(error_msg)
                
                else:
                    raise ValueError(f"API Fehler: {response.status_code} - {response.text[:200]}")
            
            return response.json()
    
    def _get_system_prompt(self) -> str:
        """Gibt den System-Prompt für Perplexity zurück"""
        currency = "USD"  # Default, wird überschrieben durch spezifische Anfrage
        
        return f"""Du bist ein Mining-Recherche-Experte. Antworte auf Deutsch mit STRUKTURIERTEN DATEN im folgenden Format:

**GEFUNDENE DATEN FÜR [MINENNAME]:**
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

**QUELLEN-SEKTION:**
[Liste ALLE verwendeten Quellen nummeriert auf]
[1] URL oder Dokumentname
[2] URL oder Dokumentname
[3] URL oder Dokumentname
... etc.

**KRITISCHE QUELLEN-REGELN:**
1. JEDE einzelne Information MUSS mit [Quelle: ...] gekennzeichnet werden!
2. Verwende [Quelle: Perplexity Search] wenn keine spezifische URL verfügbar ist
3. PRIORISIERTE QUELLEN-SUCHE nach Tiers (siehe Dokumentation)
4. Nutze 'k.A.' für nicht gefundene Daten"""
    
    async def _process_search_result(self, result: Dict, mine_name: str, 
                                    country: Optional[str], name_variants: List[str], 
                                    search_query: str, model: str) -> Dict:
        """Verarbeitet das Perplexity API Ergebnis"""
        
        if "choices" not in result or len(result["choices"]) == 0:
            raise ValueError("Keine Antwort von Perplexity API")
        
        content = result["choices"][0]["message"]["content"]
        
        # Validiere Ergebnis
        is_valid, is_not_found = self._validate_result(content, mine_name, name_variants)
        
        if is_not_found or not is_valid:
            logger.warning(f"[VALIDATION] Mine '{mine_name}' nicht gefunden")
            content = f"Keine spezifischen Informationen über die Mine '{mine_name}' gefunden."
        
        # Extrahiere strukturierte Daten mit Quellen
        extended_data = extract_structured_data_with_sources(content, mine_name, country)
        structured_data = extended_data['data']
        data_with_sources = extended_data['data_with_sources']
        source_index = extended_data['source_index']
        
        # Extrahiere Quellen
        extracted_sources = extract_sources_from_content(content)
        
        # ÄNDERUNG 01.07.2025: Tracke gefundene Quellen in der Session
        for source in extracted_sources:
            if source.get('url'):
                self.enhanced_discovery.track_source_result(
                    url=source['url'],
                    success=True,
                    content_type=source.get('type', 'general'),
                    found_data={'mine': mine_name, 'fields': list(structured_data.keys())}
                )
        
        # Berechne Datenqualität
        data_quality = self._calculate_data_quality(structured_data)
        
        logger.info(f"[RESULT] {mine_name}: {data_quality['filled_fields']}/{data_quality['total_fields']} Felder ({data_quality['quality_level']})")
        
        # ÄNDERUNG 01.07.2025: Finalisiere Source Discovery Session
        session_summary = self.enhanced_discovery.finalize_session()
        
        return {
            "success": True,
            "data": {
                "content": content,
                "mine_name": mine_name,
                "structured_data": structured_data,
                "structured_data_with_sources": data_with_sources,
                "source_index": source_index,
                "sources": extracted_sources,
                "source_summary": {
                    "urls": len([s for s in extracted_sources if s['type'] == 'url']),
                    "documents": len([s for s in extracted_sources if s['type'] == 'document']),
                    "organizations": len([s for s in extracted_sources if s['type'] == 'organization']),
                    "total": len(extracted_sources)
                },
                "data_quality": data_quality,
                "search_metadata": {
                    "model_used": model,
                    "search_timestamp": datetime.now().isoformat()
                },
                "api_response": result,
                "validated": is_valid and not is_not_found,
                "source_discovery_session": session_summary  # ÄNDERUNG 01.07.2025: Session-Zusammenfassung
            },
            "search_query": search_query
        }
    
    def _validate_result(self, content: str, mine_name: str, name_variants: List[str]) -> tuple:
        """Validiert ob das Ergebnis die gesuchte Mine betrifft"""
        
        content_lower = content.lower()
        mine_name_lower = mine_name.lower()
        mine_name_normalized = normalize_accents(mine_name).lower()
        
        # Prüfe ob Mine erwähnt wird
        is_valid_result = (
            mine_name_lower in content_lower or
            mine_name_normalized in content_lower or
            any(variant.lower() in content_lower for variant in name_variants[:3])
        )
        
        # Prüfe auf "nicht gefunden" Phrasen
        not_found_phrases = [
            "keine mine mit diesem namen",
            "konnte keine informationen finden",
            "existiert nicht",
            "wurde nicht gefunden"
        ]
        
        is_not_found = any(phrase in content_lower for phrase in not_found_phrases) and not is_valid_result
        
        return is_valid_result, is_not_found
    
    def _calculate_data_quality(self, structured_data: Dict) -> Dict:
        """Berechnet Datenqualitäts-Metriken"""
        
        filled_fields = sum(1 for col in CSV_COLUMNS if structured_data.get(col) and col != 'Name')
        total_fields = len(CSV_COLUMNS) - 1  # Minus Name-Feld
        data_completeness = filled_fields / total_fields if total_fields > 0 else 0
        
        # Bestimme Qualitätsstufe
        if data_completeness >= 0.7:
            quality_level = "Hoch"
        elif data_completeness >= 0.4:
            quality_level = "Mittel"
        else:
            quality_level = "Niedrig"
        
        return {
            "filled_fields": filled_fields,
            "total_fields": total_fields,
            "completeness_percentage": round(data_completeness * 100),
            "quality_level": quality_level,
            "missing_critical_fields": [
                col for col in ['Betreiber', 'Restaurationskosten', 'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)'] 
                if not structured_data.get(col)
            ]
        }
    
    async def enhanced_search(self, mine_name: str, country: Optional[str] = None,
                            commodity: Optional[str] = None, model: str = "sonar-pro",
                            region: Optional[str] = None, _from_auto: bool = False) -> Dict[str, Any]:
        """
        Erweiterte Zwei-Phasen-Suche für umfangreichere Ergebnisse
        
        Phase 1: Basis-Suche mit Quellenfokus
        Phase 2: Vertiefung basierend auf gefundenen Quellen
        
        ÄNDERUNG 01.07.2025: Aus main.py hierher verschoben
        ÄNDERUNG 02.07.2025: Rekursionsschutz hinzugefügt
        
        Args:
            _from_auto: INTERN - True wenn von Auto-Two-Phase aufgerufen
        """
        logger.info(f"Starte erweiterte Zwei-Phasen-Suche für: {mine_name} mit Modell: {model} (from_auto={_from_auto})")
        
        # Phase 1: Initiale Suche - MIT Rekursionsschutz
        phase1_result = await self.search_mine(
            mine_name, country, commodity, model, region, 
            _is_auto_enhanced=_from_auto  # Verhindere weitere Auto-Aktivierung!
        )
        
        if not phase1_result.get('success') or not phase1_result.get('data'):
            return phase1_result
        
        # Extrahiere Quellen für Phase 2
        sources = phase1_result['data'].get('sources', [])
        logger.info(f"Phase 1 Quellen gefunden: {len(sources)}")
        
        # Filtere valide Quellen
        valid_sources = [s for s in sources if 
            s['type'] == 'url' or 
            (s['type'] == 'document' and len(s['value']) > 5)]
        
        if not valid_sources:
            logger.info("Keine validen Quellen für Phase 2 gefunden")
            return phase1_result
        
        # ÄNDERUNG 01.07.2025: Phase 2 mit gezielten Perplexity-Suchen
        # ÄNDERUNG 02.07.2025: Reduziere auf max 3 Quellen für Performance
        max_phase2_sources = 3 if _from_auto else 5  # Weniger bei Auto-Two-Phase
        logger.info(f"Phase 2 - Gezielte Suchen für Top {len(valid_sources[:max_phase2_sources])} Quellen")
        
        phase2_results = []
        for i, source in enumerate(valid_sources[:max_phase2_sources]):
            logger.info(f"Phase 2 - Suche {i+1}/{max_phase2_sources}: {source['type']} - {source['value'][:50]}...")
            
            # Erstelle spezifischen Prompt für diese Quelle
            source_prompt = f"""
            Durchsuche speziell diese Quelle für die Mine "{mine_name}":
            {source['value']}
            
            Extrahiere alle verfügbaren Informationen, besonders:
            - Restaurationskosten / Closure Costs / ARO
            - Betreiber und Eigentümer
            - Koordinaten
            - Produktionsdaten
            - Umweltauflagen
            - Links zu PDF-Dokumenten
            
            Gib die gefundenen Informationen strukturiert zurück.
            """
            
            try:
                # Nutze Standard-Modell für Phase 2 (schneller)
                phase2_config = config.PERPLEXITY_MODELS.get("sonar-pro")
                phase2_result = await self._call_perplexity_api(source_prompt, phase2_config)
                
                if "choices" in phase2_result and phase2_result["choices"]:
                    content = phase2_result["choices"][0]["message"]["content"]
                    phase2_results.append({
                        "source": source,
                        "content": content
                    })
                    
                    # Tracke diese Quelle als erfolgreich durchsucht
                    if source['type'] == 'url':
                        self.enhanced_discovery.track_source_result(
                            url=source['value'],
                            success=True,
                            content_type='phase2'
                        )
            except Exception as e:
                logger.error(f"Fehler in Phase 2 für Quelle {source['value'][:30]}: {e}")
        
        # Kombiniere Ergebnisse
        combined_content = phase1_result['data']['content']
        
        if phase2_results:
            combined_content += "\n\n**ERWEITERTE INFORMATIONEN AUS VERTIEFTER RECHERCHE:**\n\n"
            for i, result in enumerate(phase2_results):
                combined_content += f"\n### Quelle {i+1}: {result['source']['value'][:80]}...\n"
                combined_content += result['content'] + "\n"
        
        # Aktualisiere strukturierte Daten
        enhanced_data = extract_structured_data_with_sources(combined_content, mine_name, country)
        all_sources = extract_sources_from_content(combined_content)
        
        return {
            "success": True,
            "data": {
                "content": combined_content,
                "mine_name": mine_name,
                "structured_data": enhanced_data['data'],
                "structured_data_with_sources": enhanced_data['data_with_sources'],
                "sources": all_sources,
                "source_summary": {
                    "urls": len([s for s in all_sources if s['type'] == 'url']),
                    "documents": len([s for s in all_sources if s['type'] == 'document']),
                    "organizations": len([s for s in all_sources if s['type'] == 'organization']),
                    "total": len(all_sources)
                },
                "search_phases": {
                    "phase1_sources": len(sources),
                    "phase2_searches": len(phase2_results),
                    "total_content_length": len(combined_content)
                },
                "validated": True
            },
            "search_query": f"Erweiterte Suche: {mine_name}"
        }
    
    def _build_phase2_query(self, source: Dict[str, str], mine_name: str, country: Optional[str]) -> str:
        """Erstelle spezifische Phase 2 Suchanfrage basierend auf Quellentyp"""
        country_config = get_country_config(country) if country else {}
        currency = country_config.get('currency', 'USD')
        restoration_terms = country_config.get('mining_terms', {}).get('restoration_costs', [])
        
        if source['type'] == 'document':
            doc_lower = source['value'].lower()
            if 'ni 43-101' in doc_lower or 'technical report' in doc_lower:
                return f"Analysiere das NI 43-101 Technical Report '{source['value']}' für {mine_name}. Extrahiere: Closure Costs, Environmental Obligations in {currency}"
            else:
                return f"Analysiere das Dokument '{source['value']}' für {mine_name}. Fokus auf: {', '.join(restoration_terms[:3])}"
        elif source['type'] == 'url':
            return f"Besuche {source['value']} und finde Informationen über {mine_name}. Priorität: {', '.join(restoration_terms[:3])}"
        else:
            return f"Suche bei {source['value']} nach {mine_name}. Fokus: Restaurationskosten in {currency}"


# Singleton-Instanz
search_service = MineSearchService()