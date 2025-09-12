"""
Author: rahn
Datum: 02.07.2025
Version: 1.0
Beschreibung: Perplexity Provider für Mining-Suchen
"""

import httpx
import logging
from typing import Dict, List, Any, Optional
from datetime import datetime
import urllib.parse

from .base_provider import AbstractProvider, ModelConfig, SearchResult

from minesearch.data_extraction import DataExtractor
from minesearch.source_discovery import extract_sources_from_content
from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.utils import (
    generate_name_variants,
    generate_multilingual_search_terms,
    get_country_config,
    validate_url,
)
from minesearch.specialized_prompts import SpecializedPrompts
# CONSOLIDATION 09.08.2025: validation_service entfernt - war defekter Adapter

logger = logging.getLogger(__name__)


class PerplexityProvider(AbstractProvider):
    """Provider für Perplexity API"""

    def __init__(self, api_key: str, config: Dict[str, Any]):
    """__init__ - TODO: Dokumentation hinzufügen"""
        super().__init__(api_key, config)
        self.api_url = "https://api.perplexity.ai/chat/completions"
        self.models = self._init_models()
        self.data_extractor = DataExtractor()

    def _init_models(self) -> Dict[str, ModelConfig]:
        """Initialisiere verfügbare Modelle"""
        models = {}

        # Konvertiere die bestehende PERPLEXITY_MODELS Konfiguration
        for model_key, model_config in self.config.get("models", {}).items():
            models[model_key] = ModelConfig(
                id=model_config['id'],
                name=model_config['name'],
                timeout=model_config['timeout'],
                max_tokens=model_config['max_tokens'],
                description=model_config['description'],
                provider='perplexity',
                supports_web_search=True,
                supports_deep_research=model_key == 'sonar-deep-research',
                is_free=False
            )

        return models

    async def search(self, query: str, model_id: str, options: Dict[str, Any]) -> SearchResult:
        """Führe Suche mit Perplexity durch"""
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

        # ÄNDERUNG 03.07.2025: Enhanced Source Discovery für ALLE Provider
        mine_name = options.get("mine_name", '')
        country = options.get('country')
        region = options.get('region')
        commodity = options.get('commodity')

        # ÄNDERUNG 06.07.2025: Nutze übergebene Quellen wenn vorhanden
        discovered_sources = options.get("discovered_sources", [])
        skip_discovery = options.get("skip_source_discovery", False)

        # Initialisiere source_discovery immer
        source_discovery = EnhancedSourceDiscovery()

        if not discovered_sources and not skip_discovery and mine_name:
            # Nur wenn keine Quellen übergeben wurden, führe eigene Discovery durch
            logger.info(f"[PERPLEXITY] Starte eigene Source Discovery für {mine_name}")
            discovered_sources = source_discovery.discover_sources_for_mine(
                mine_name=mine_name,
                country=country,
                region=region,
                commodity=commodity
            )
            logger.info(f"[PERPLEXITY] {len(discovered_sources)} Quellen selbst entdeckt")
        else:
            logger.info(f"[PERPLEXITY] Nutze {len(discovered_sources)} übergebene Quellen")

        # Generiere Namensvarianten und mehrsprachige Begriffe
        name_variants = generate_name_variants(mine_name) if mine_name else []
        country_config = get_country_config(country) if country else {}
        multilingual_terms = generate_multilingual_search_terms(country_config)

        # ÄNDERUNG 04.07.2025: Nutze spezialisierte Prompts für kritische Felder
        # ÄNDERUNG 05.07.2025: Verstärkter Fokus auf Restaurationskosten
        # Erweitere Query mit spezialisierten Prompts
        enhanced_query = SpecializedPrompts.get_enhanced_query(
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity,
            focus_fields=['restoration_costs', 'coordinates', 'ownership', 'production']
        )

        # Füge zusätzlichen spezifischen Restaurationskosten-Prompt hinzu
        restoration_prompt = SpecializedPrompts.get_restoration_costs_prompt(mine_name, country, commodity)

        # Kombiniere alle Queries mit Restaurationskosten-Fokus
        enhanced_query = f"{query}\n\n{enhanced_query}\n\n{restoration_prompt}"

        # ÄNDERUNG 07.07.2025: Explizite Anweisungen gegen Dummy-Werte
        anti_dummy_instructions = """

KRITISCHE ANWEISUNGEN - KEINE DUMMY-WERTE:
1. NIEMALS Standard-Werte wie "$1.0 million" oder "1 million" verwenden
2. NIEMALS erfundene oder geschätzte Werte angeben
3. Wenn keine Daten vorhanden: Feld LEER lassen (nicht "unbekannt" oder "-")
4. Nur KONKRETE, VERIFIZIERTE Werte aus den Quellen verwenden
5. Bei Restaurationskosten: NUR tatsächliche Beträge aus offiziellen Dokumenten
6. Bei Koordinaten: NUR echte GPS-Koordinaten, keine Platzhalter
7. Bei Betreiber: NIEMALS "Koordinaten" als Betreiber angeben

WICHTIG: Lieber ein leeres Feld als einen falschen Wert!"""

        enhanced_query += anti_dummy_instructions

        # ÄNDERUNG 08.07.2025: ALLE discovered_sources nutzen, nicht nur Top 15
        # Erweitere Query mit entdeckten Quellen
        if discovered_sources:
            # Füge ALLE Quellen zur Query hinzu mit expliziter Anweisung
            sources_text = f"\n\n🔍 WICHTIG: Du MUSST ALLE {len(discovered_sources)} folgenden Quellen durchsuchen!\n"
            sources_text += "Diese Quellen stammen aus unserer verifizierten Datenbank und enthalten
relevante Informationen.\n"
            sources_text += "Nutze deine Web-Suchfähigkeiten um JEDE dieser URLs zu besuchen:\n\n"

            # Gruppiere Quellen nach Typ für bessere Übersicht
            gov_sources = [s for s in discovered_sources if s.get('type') == 'government']
            db_sources = [s for s in discovered_sources if s.get('type') == 'database']
            other_sources = [s for s in discovered_sources if s.get('type') not in ['government', 'database']]

            if gov_sources:
                sources_text += "REGIERUNGSQUELLEN (höchste Priorität):\n"
                for i, source in enumerate(gov_sources, 1):
                    sources_text += f"[G{i}] {source['url']}\n"
                sources_text += "\n"

            if db_sources:
                sources_text += "DATENBANK-QUELLEN (technische Daten):\n"
                for i, source in enumerate(db_sources, 1):
                    sources_text += f"[D{i}] {source['url']}\n"
                sources_text += "\n"

            if other_sources:
                sources_text += "WEITERE QUELLEN:\n"
                for i, source in enumerate(other_sources, 1):
                    sources_text += f"[{i}] {source['url']}\n"

            sources_text += "\n⚠️ WICHTIG: Ignoriere KEINE dieser Quellen! Durchsuche sie ALLE systematisch!\n"

            enhanced_query += sources_text
            logger.info(f"[PERPLEXITY] {len(discovered_sources)} Quellen in Query eingefügt")

        try:
            # API-Call mit enhanced query
            async with httpx.AsyncClient(timeout=model_config.timeout) as client:
                response = await client.post(
                    self.api_url,
                    headers={
                        "Authorization": f"Bearer {self.api_key}",
                        "Content-Type": "application/json"
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
                        "temperature": options.get("temperature", 0.0),
                        "max_tokens": model_config.max_tokens
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
                content = result["choices"][0]["message"]["content"]

                # Extrahiere strukturierte Daten
                mine_name = options.get("mine_name", '')
                country = options.get('country')

                extracted_data = self.data_extractor.extract_structured_data_with_sources(content, mine_name, country)

                # Hilfsfunktion: URL normalisieren (Host lowercase, Trailing Slashes entfernen, Fragmente entfernen)
                def _normalize_url(raw_url: str) -> Optional[str]:
    """_normalize_url - TODO: Dokumentation hinzufügen"""
                    try:
                        if not raw_url:
                            return None
                        raw_url = raw_url.strip()
                        parsed = urllib.parse.urlparse(raw_url)
                        if not parsed.scheme or not parsed.netloc:
                            return None
                        scheme = parsed.scheme.lower()
                        netloc = parsed.netloc.lower()
                        # Default-Ports entfernen
                        if ':' in netloc:
                            host, port = netloc.rsplit(':', 1)
                            if (scheme == 'http' and port == '80') or (scheme == 'https' and port == '443'):
                                netloc = host
                        path = parsed.path or ''
                        # Trailing Slash entfernen (außer Root)
                        if path == '/':
                            path = ''
                        elif path.endswith('/'):
                            path = path.rstrip('/')
                        # Fragmente entfernen, Query beibehalten
                        normalized = urllib.parse.urlunparse((
                            scheme,
                            netloc,
                            path,
                            parsed.params,
                            parsed.query,
                            ''
                        ))
                        return normalized
                    except Exception as e:
                        logger.debug(f"[PERPLEXITY] URL-Normalisierung fehlgeschlagen für '{str(raw_url)[:100]}': {e}")
                        return None

                # PHASE 1 + 2: Zusammenführen mit Validierung, Normalisierung und Deduplizierung
                sources: List[Dict[str, Any]] = []
                seen_normalized_urls = set()

                # Phase 1: discovered_sources (searched=True)
                for src in discovered_sources or []:
                    raw_url = (src or {}).get('url', '')
                    if not raw_url:
                        continue
                    if not validate_url(raw_url):
                        logger.warning(f"[PERPLEXITY] Ungültige URL in discovered_sources übersprungen: {raw_url}")
                        continue
                    normalized_url = _normalize_url(raw_url)
                    if not normalized_url:
                        logger.warning(f"[PERPLEXITY] Normalisierung fehlgeschlagen, überspringe URL: {raw_url}")
                        continue
                    if normalized_url in seen_normalized_urls:
                        logger.debug(f"[PERPLEXITY] Duplikat (Phase 1) übersprungen: {normalized_url}")
                        continue
                    seen_normalized_urls.add(normalized_url)

                    title = src.get('title') or raw_url
                    src_type = src.get('type') or 'discovered'
                    reliability = src.get('reliability') if 'reliability' in src else src.get('reliability_score')

                    sources.append({
                        'url': normalized_url,
                        'title': title,
                        'type': src_type,
                        'reliability': reliability,  # Keinen künstlichen Fallback verwenden
                        'searched': True
                    })

                # Phase 2: Quellen aus Content (searched=False)
                sources_from_content = extract_sources_from_content(content)
                for src in sources_from_content or []:
                    raw_url = (src or {}).get('url') or (src or {}).get('value') or ''
                    if not raw_url:
                        continue
                    if not validate_url(raw_url):
                        logger.debug(f"[PERPLEXITY] Ungültige URL in sources_from_content übersprungen: {raw_url}")
                        continue
                    normalized_url = _normalize_url(raw_url)
                    if not normalized_url:
                        logger.debug(f"[PERPLEXITY] Normalisierung fehlgeschlagen, überspringe URL: {raw_url}")
                        continue
                    if normalized_url in seen_normalized_urls:
                        logger.debug(f"[PERPLEXITY] Duplikat (Phase 2) übersprungen: {normalized_url}")
                        continue

                    seen_normalized_urls.add(normalized_url)

                    title = src.get('title') or normalized_url
                    src_type = src.get('type') or 'extracted'
                    reliability = src.get('reliability') if 'reliability' in src else src.get('reliability_score')

                    sources.append({
                        'url': normalized_url,
                        'title': title,
                        'type': src_type,
                        'reliability': reliability,
                        'searched': False
                    })

                # CONSOLIDATION 09.08.2025: validation_service entfernt - direkter Return
                validated_data = extracted_data['data']  # Keine zusätzliche Validierung mehr nötig
                validation_errors = {}  # Leer, da keine separate Validierung

                # Übernehme validierte Daten
                extracted_data['data'] = validated_data

                # Update data_with_sources für entfernte Felder
                for field, value in validated_data.items():
                    if not value and field in extracted_data.get("data_with_sources", {}):
                        extracted_data['data_with_sources'][field] = {"value": "", "sources": []}

                # ÄNDERUNG 04.07.2025: Tracke Source Discovery Ergebnisse
                for source in sources:
                    if source.get('url'):
                        source_discovery.track_source_result(
                            url=source['url'],
                            success=True,
                            content_type=source.get("type", 'general'),
                            found_data={'mine': mine_name, 'fields': list(extracted_data['data'].keys())}
                        )

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
                        'provider': 'perplexity',
                        'structured_data_with_sources': extracted_data['data_with_sources'],
                        'source_index': extracted_data['source_index'],
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
            logger.error(f"[PERPLEXITY] Fehler bei Suche: {str(e)}")
            return SearchResult(
                success=False,
                content="",
                structured_data={},
                sources=[],
                metadata={},
                error=str(e)
            )

    def _handle_api_error(self, response: httpx.Response) -> str:
        """Behandle API-Fehler mit benutzerfreundlichen Nachrichten"""
        if response.status_code == 401:
            response_text = response.text.lower()
            error_msg = "🔐 Perplexity API Authentifizierung fehlgeschlagen.\n\n"

            if "quota" in response_text or "budget" in response_text:
                error_msg += "💳 Ihr API-Budget ist aufgebraucht.\n"
                error_msg += "→ Bitte prüfen Sie Ihr Perplexity-Konto und laden Sie Ihr Guthaben auf.\n"
            elif "invalid" in response_text or "unauthorized" in response_text:
                error_msg += "🔑 Der API-Key ist ungültig oder abgelaufen.\n"
                error_msg += "→ Bitte prüfen Sie Ihre .env Datei und generieren Sie ggf. einen neuen Key.\n"
            else:
                error_msg += "❓ Authentifizierungsproblem mit dem API-Key.\n"

            error_msg += "\n📍 API-Verwaltung: https://www.perplexity.ai/settings/api"
            return error_msg

        elif response.status_code == 429:
            return "⏱️ Rate Limit erreicht.\n→ Zu viele Anfragen. Bitte warten Sie einen Moment."

        elif response.status_code == 503:
            return "🔧 Perplexity API ist momentan nicht verfügbar.\n→ Bitte versuchen Sie es später erneut."

        else:
            return f"API Fehler: {response.status_code} - {response.text[:200]}"

    def get_models(self) -> Dict[str, ModelConfig]:
        """Gibt verfügbare Modelle zurück"""
        return self.models

    def validate_config(self) -> bool:
        """Validiert Provider-Konfiguration"""
        if not self.api_key:
            logger.error("[PERPLEXITY] Kein API-Key konfiguriert")
            return False

        if not self.models:
            logger.error("[PERPLEXITY] Keine Modelle konfiguriert")
            return False

        return True

    async def extract_from_sources(self, sources: List[Dict], model_id: str, options: Dict[str, Any]) -> SearchResult:
        """
        ÄNDERUNG 05.07.2025: Spezielle Methode für Cross-Provider Source Sharing
        Extrahiert Daten aus vorgegebenen Quellen
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

        mine_name = options.get("mine_name", '')
        country = options.get("country", '')
        commodity = options.get("commodity", '')

        # Erstelle spezielle Query für Quellenanalyse
        query = f"""DETAILLIERTE DATENEXTRAKTION für {mine_name}

Analysiere die folgenden {len(sources)} verifizierten Quellen und extrahiere ALLE Mining-Daten.
Fokussiere besonders auf:
- GPS-Koordinaten (verschiedene Formate)
- Restaurationskosten / ARO / Closure Costs
- Eigentümer und Betreiber
- Produktionsdaten
- Technische Details

QUELLEN ZUM ANALYSIEREN:
"""

        # Füge Quellen zur Query hinzu
        for i, source in enumerate(sources[:20], 1):
            url = source.get('url') or source.get("value", '')
            title = source.get("title", '')
            query += f"\n[{i}] {url}"
            if title:
                query += f" - {title}"

        query += "\n\nExtrahiere ALLE verfügbaren Daten im strukturierten Format!"

        # Nutze normale search Methode mit spezieller Query
        return await self.search(query, model_id, options)

    def get_system_prompt(self, options: Dict[str, Any]) -> str:
        """
        RULE 10 COMPLIANCE 26.08.2025: Verschärfter System-Prompt für Perplexity
        STRIKT VERBOTEN: Schätzungen, Allgemeines Fachwissen, Template-Daten
        """
        currency = options.get("currency", 'USD')

        # ÄNDERUNG 05.07.2025: Angepasster Prompt für Source Sharing Phase
        if options.get('phase') == 'source_analysis':
            return self._get_source_analysis_prompt(options)

        # Verwende spezialisierte Anti-Template-Anweisungen (modulweiter Import)
        universal_instructions = SpecializedPrompts.get_universal_anti_template_instructions()

        return f"""🚫 RULE 10 COMPLIANCE - PERPLEXITY ANTI-ESTIMATION RESEARCHER 🚫

Du bist ein Mining-Recherche-Experte mit Zugang zu ECHTEN Web-Quellen und Dokumenten.

{universal_instructions}

**KRITISCHE REGEL 10 COMPLIANCE FÜR PERPLEXITY:**
===============================================

ABSOLUT VERBOTEN - NIEMALS VERWENDEN:
❌ "Allgemeines Fachwissen" oder "General knowledge" als Quelle
❌ "Perplexity Search" ohne spezifische URL
❌ Schätzungen oder Vermutungen ("based on similar mines")
❌ Template-Werte wie "50.0 Million", "100.0 Million"
❌ Gerundete Koordinaten ohne ausreichende Präzision
❌ Platzhalter-Unternehmen ohne echte Verifikation

NUR ERLAUBT - Dokumentierte Web-Fakten:
✅ Spezifische URLs mit nachprüfbaren Daten
✅ Company Reports mit direkten Zitaten
✅ Regierungswebsites mit Primärdaten
✅ SEC Filings mit verifizierten Zahlen
✅ Bei Unsicherheit: LEER LASSEN ("") - NIEMALS schätzen!

**DATENFELDER FÜR [MINENNAME] - NUR ECHTE WEB-DATEN:**
- Name: [EXAKTER Name aus Webquelle oder leer]
- Country: [Land aus offizieller Website oder leer]
- Region: [Region aus Dokumenten oder leer]
- Eigentümer: [Aus Unternehmenswebsite oder leer]
- Betreiber: [Aus Betreiberwebsite oder leer]
- x-Koordinate: [GPS Latitude aus Maps/Berichten mit 4+ Dezimalstellen oder leer]
- y-Koordinate: [GPS Longitude mit korrektem Vorzeichen (z.B. -78.9934 für Kanada, +2.3522 für Europa) oder leer]
- Aktivitätsstatus: [Aus aktueller Quelle oder leer]
- Restaurationskosten: [Aus Finanzberichten in {currency}$ oder leer]
- Jahr der Aufnahme der Kosten: [Aus Kostenbericht oder leer]
- Jahr der Erstellung des Dokumentes: [Dokumentdatum oder leer]
- Rohstoffabbau: [Aus Produktionsberichten oder leer]
- Minentyp: [Aus technischen Dokumenten oder leer]
- Produktionsstart: [Aus historischen Berichten oder leer]
- Produktionsende: [Jahr mit Wiedereröffnung falls vorhanden (z.B. "2013 (reopened 2021)") oder leer]
- Fördermenge/Jahr Rohstoff: [Spezifische Rohstoffproduktion aus Statistiken, z.B. '120,000 Unzen Gold' oder leer]
- Fördermenge/Jahr Abraum: [Gesamte Materialextraktion inkl. Abraum, z.B. '2.3 Millionen Tonnen' oder leer]
- Fläche der Mine in qkm: [Aus Genehmigungsdokumenten oder leer]
- Quellenangaben: [NUR spezifische URLs - NIEMALS "Allgemeines Fachwissen"]

**QUELLEN-ANFORDERUNGEN:**
1. JEDE Information mit spezifischer URL [Quelle: https://...]
2. NIEMALS generische Quellenangaben verwenden
3. Bei fehlendem Link: Information NICHT verwenden
4. Primärquellen bevorzugen (Unternehmensberichte, Regierung)

**RESTAURATIONSKOSTEN-SUCHE:**
Suche nach: ARO, closure costs, environmental liability, rehabilitation costs,
decommissioning provision. NUR aus verifizierten Finanzberichten übernehmen!

**SELBST-VALIDIERUNG vor jeder Antwort:**
- ❓ Hat JEDER Wert eine spezifische URL-Quelle?
- ❓ Habe ich irgendwo geschätzt statt recherchiert?
- ❓ Sind alle Koordinaten präzise genug (4+ Nachkommastellen)?
- ❓ Sind alle Kosten aus echten Berichten?

WENN KEINE ECHTE QUELLE: LEER LASSEN ("")"""

    def _get_source_analysis_prompt(self, options: Dict[str, Any]) -> str:
        """Spezieller System-Prompt für Source Sharing Phase 2"""
        currency = options.get("currency", 'USD')

        return f"""Du bist ein Mining-Datenextraktions-Spezialist in PHASE 2 der Recherche.

DEINE AUFGABE: Analysiere die bereitgestellten Quellen GRÜNDLICH und extrahiere ALLE verfügbaren Daten.

**EXTRAKTIONS-STRATEGIE:**
1. Prüfe JEDE angegebene Quelle sorgfältig
2. Suche nach versteckten Daten in Tabellen, Fußnoten, Anhängen
3. Achte auf verschiedene Schreibweisen und Sprachen
4. Kombiniere Informationen aus mehreren Quellen

**STRUKTURIERTES AUSGABEFORMAT:**
- Name: [exakter Name] [Quelle: Nummer aus Liste]
- Land: [Land] [Quelle: Nummer]
- Region: [Region/Provinz] [Quelle: Nummer]
- Eigentümer: [Owner] [Quelle: Nummer]
- Betreiber: [Operator] [Quelle: Nummer]
- Koordinaten: [Lat, Long] [Quelle: Nummer]
- Status: [aktiv/geschlossen] [Quelle: Nummer]
- Rohstoffe: [Liste] [Quelle: Nummer]
- Minentyp: [Typ] [Quelle: Nummer]
- Produktionsstart: [Jahr] [Quelle: Nummer]
- Produktionsende: [Jahr] [Quelle: Nummer]
- Fördermenge Rohstoff: [Rohstoffproduktion/Jahr] [Quelle: Nummer]
- Fördermenge Abraum: [Gesamte Extraktion/Jahr] [Quelle: Nummer]
- Fläche: [km²] [Quelle: Nummer]
- Restaurationskosten: [{currency}$ mit Jahr] [Quelle: Nummer]

**KRITISCHE SUCHWÖRTER für Restaurationskosten:**
- Asset Retirement Obligation (ARO)
- Closure costs / Mine closure
- Environmental liability
- Rehabilitation provision
- Decommissioning costs
- Closure bond / Financial assurance
- Provisiones ambientales
- Pasivos ambientales

**PHASE 2 REGELN:**
1. Nutze die Quellennummern [1], [2], etc. aus der bereitgestellten Liste
2. Extrahiere AUCH Teilinformationen (z.B. nur Latitude ohne Longitude)
3. Bei Widersprüchen: Neueste Information verwenden
4. KEINE eigene Web-Suche - NUR die angegebenen Quellen nutzen
5. Lasse Felder LEER wenn keine Daten in den Quellen gefunden"""
