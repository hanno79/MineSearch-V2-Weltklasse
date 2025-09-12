"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: Kaskadierende Modell-Strategie für optimale Ergebnisse
"""

import logging
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict
from datetime import datetime

logger = logging.getLogger(__name__)


class ModelTierStrategy:
    """Implementiert kaskadierende Modell-Auswahl basierend auf Performance"""

    def __init__(self):
        """__init__ - TODO: Dokumentation hinzufügen"""
        # ÄNDERUNG 14.07.2025: Kostenlose Modelle als Tier 1 priorisieren - Kimi K2 als primäres Fallback
        self.tier_definitions = {
            'tier_1_free_primary': {
                'models': [
                    'openrouter:kimi-k2',
                    'openrouter:deepseek-free',
                    'openrouter:deepseek-chimera-free',
                    'openrouter:mistral-small-free',
                    'openrouter:cypher-alpha-free'
                ],
                'focus': 'free_fallback',
                'threshold': 0.6  # Kimi K2 zeigt 10-13 Felder Performance
            },
            'tier_1_free_secondary': {
                'models': [
                    'openrouter:deepseek-chat',
                    'tavily:search',
                    'anthropic:claude-3.7-sonnet',
                    'gemini:gemini-2.5-flash-lite'
                ],
                'focus': 'free_backup',
                'threshold': 0.5
            },
            'tier_2_scraping': {
                'models': [
                    'scrapingbee:basic-scrape',
                    'scrapingbee:js-render',
                    'brightdata:web-scraper',
                    'firecrawl:scrape'
                ],
                'focus': 'technical_scraping',
                'threshold': 0.7
            },
            'tier_3_premium_financial': {
                'models': [
                    'perplexity:sonar-pro',
                    'perplexity:sonar-deep-research',
                    'openai:o3-deep-research',
                    'grok:grok-3-fast'
                ],
                'focus': 'premium_financial',
                'threshold': 0.8,
                'cost_warning': True  # Warnung bei Verwendung
            },
            'tier_3_premium_sources': {
                'models': [
                    'perplexity:sonar',
                    'perplexity:sonar-reasoning',
                    'exa:neural-search'
                ],
                'focus': 'premium_sources',
                'threshold': 0.8,
                'cost_warning': True  # Warnung bei Verwendung
            },
            'tier_3_premium_comprehensive': {
                'models': [
                    'anthropic:claude-opus-4',
                    'anthropic:claude-sonnet-4',
                    'gemini:gemini-2.5-pro',
                    'gemini:gemini-2.5-flash',
                    'openai:gpt-4.1'
                ],
                'focus': 'premium_comprehensive',
                'threshold': 0.8,
                'cost_warning': True  # Warnung bei Verwendung
            }
        }

        # Performance-Tracking
        self.model_performance = defaultdict(lambda: {
            'success_rate': 0.0,
            'avg_fields_found': 0.0,
            'avg_sources_found': 0.0,
            'calls': 0,
            'failures': 0
        })

        # Kritische Felder für verschiedene Fokus-Bereiche
        self.critical_fields = {
            'financial': ['Restaurationskosten', 'Marktkapitalisierung', 'Jahresumsatz', 'EBITDA'],
            'technical': ['x-Koordinate', 'y-Koordinate', 'Minentyp', 'Fläche'],
            'operational': ['Eigentümer', 'Betreiber', 'Status', 'Produktionsstart'],
            'production': ['Fördermenge', 'Rohstoffe', 'Produktionsende', 'Reserven']
        }

    def get_models_for_phase(self, phase: str, current_results: Dict[str, Any] = None) -> List[str]:
        """
        Wählt Modelle basierend auf aktueller Phase und bisherigen Ergebnissen

        Args:
            phase: 'source_discovery', 'initial_extraction', 'deep_extraction', 'fallback'
            current_results: Bisherige Ergebnisse für adaptive Auswahl

        Returns:
            Liste von Modell-IDs für diese Phase
        """
        if phase == 'source_discovery':
            # Phase 1: Alle Modelle für maximale Quellenabdeckung
            all_models = []
            for tier in self.tier_definitions.values():
                all_models.extend(tier['models'])
            return list(set(all_models))  # Dedupliziert

        elif phase == 'initial_extraction':
            # Phase 2: Top-Performer für erste Extraktion
            models = []
            models.extend(self.tier_definitions['tier_1_financial']['models'])
            models.extend(self.tier_definitions['tier_1_technical']['models'])
            return models

        elif phase == 'deep_extraction':
            # Phase 3: Umfassende Modelle für fehlende Daten
            missing_fields = self._identify_missing_fields(current_results)
            return self._select_models_for_missing_fields(missing_fields)

        elif phase == 'fallback':
            # Phase 4: Alle verbleibenden Modelle
            return self.tier_definitions['tier_3_fallback']['models']

        else:
            logger.warning(f"Unbekannte Phase: {phase}")
            return []

    def is_premium_model(self, model_id: str) -> bool:
        """
        Prüft ob ein Modell kostenpflichtig ist

        Args:
            model_id: Modell-ID (z.B. 'perplexity:sonar-pro')

        Returns:
            True wenn kostenpflichtig, False wenn kostenlos
        """
        # ÄNDERUNG 14.07.2025: Kostenkontrolle für Premium-Modelle
        for tier_name, tier_config in self.tier_definitions.items():
            if model_id in tier_config['models']:
                return tier_config.get("cost_warning", False)
        return False

    def get_cost_warning_message(self, model_id: str) -> str:
        """
        Erstellt Warnung für kostenpflichtige Modelle

        Args:
            model_id: Modell-ID

        Returns:
            Warnung-String
        """
        if self.is_premium_model(model_id):
            return f"⚠️ KOSTENPFLICHTIG: {model_id} verursacht Kosten! Verwende openrouter:kimi-k2 für kostenlose Alternative."
        return ""

    def should_continue_to_next_tier(self, current_results: Dict[str, Any], current_tier: str) -> bool:
        """should_continue_to_next_tier - TODO: Dokumentation hinzufügen"""
        """
        Entscheidet ob die nächste Tier aktiviert werden soll

        Args:
            current_results: Aktuelle Ergebnisse
            current_tier: Aktuelle Tier

        Returns:
            True wenn nächste Tier aktiviert werden soll
        """
        if not current_results or 'data' not in current_results:
            return True

        data_dict = current_results.get("data", {})

        # Berechne Abdeckung für kritische Felder
        coverage = self._calculate_critical_field_coverage(data)

        # Hole Threshold für aktuelle Tier
        tier_config = self.tier_definitions.get(current_tier, {})
        threshold = tier_config.get("threshold", 0.7)

        # Entscheide basierend auf Coverage
        should_continue = coverage < threshold

        logger.info(f"[TIER-STRATEGY] Coverage: {coverage:.2f}, Threshold: {threshold}, "
                   f"Continue: {should_continue}")

        return should_continue

    def update_model_performance(self, model_id: str, result: Dict[str, Any]):
        """Aktualisiert Performance-Metriken für ein Modell"""
        perf = self.model_performance[model_id]
        perf['calls'] += 1

        if result.get('success'):
            data_dict = result.get("data", {})
            sources = result.get("sources", [])

            # Zähle gefüllte Felder
            filled_fields = len([v for v in data.values() if v and str(v).strip()])

            # Update Durchschnittswerte
            perf['avg_fields_found'] = (
                (perf['avg_fields_found'] * (perf['calls'] - 1) + filled_fields) /
                perf['calls']
            )
            perf['avg_sources_found'] = (
                (perf['avg_sources_found'] * (perf['calls'] - 1) + len(sources)) /
                perf['calls']
            )
            perf['success_rate'] = (perf['calls'] - perf['failures']) / perf['calls']
        else:
            perf['failures'] += 1
            perf['success_rate'] = (perf['calls'] - perf['failures']) / perf['calls']

    def get_specialized_models_for_field(self, field_name: str) -> List[str]:
        """
        Gibt spezialisierte Modelle für ein bestimmtes Feld zurück

        Args:
            field_name: Name des gesuchten Felds

        Returns:
            Liste von Modell-IDs die für dieses Feld gut performen
        """
        field_specializations = {
            'Restaurationskosten': [
                'perplexity:sonar-pro',
                'openai:o3-deep-research',
                'perplexity:sonar-deep-research',
                'tavily:deep-research'
            ],
            'x-Koordinate': [
                'scrapingbee:basic-scrape',
                'exa:neural-search',
                'brightdata:web-scraper'
            ],
            'y-Koordinate': [
                'scrapingbee:basic-scrape',
                'exa:neural-search',
                'brightdata:web-scraper'
            ],
            'Eigentümer': [
                'perplexity:sonar',
                'anthropic:claude-opus-4',
                'openai:gpt-4.1'
            ],
            'Betreiber': [
                'perplexity:sonar',
                'anthropic:claude-opus-4',
                'openai:gpt-4.1'
            ],
            'Fördermenge': [
                'grok:grok-3',
                'gemini:gemini-2.5-pro',
                'perplexity:sonar-pro'
            ]
        }

        return field_specializations.get(field_name,
                                       self.tier_definitions['tier_2_comprehensive']['models'])

    def _identify_missing_fields(self, results: Dict[str, Any]) -> Set[str]:
        """Identifiziert fehlende kritische Felder"""
        if not results or 'data' not in results:
            # Alle kritischen Felder fehlen
            all_critical = set()
            for fields in self.critical_fields.values():
                all_critical.update(fields)
            return all_critical

        data_dict = results.get("data", {})
        missing = set()

        for category, fields in self.critical_fields.items():
            for field in fields:
                if not data.get(field) or not str(data[field]).strip():
                    missing.add(field)

        return missing

    def _select_models_for_missing_fields(self, missing_fields: Set[str]) -> List[str]:
        """Wählt optimale Modelle für fehlende Felder"""
        selected_models = set()

        # Für jedes fehlende Feld, füge spezialisierte Modelle hinzu
        for field in missing_fields:
            specialized = self.get_specialized_models_for_field(field)
            selected_models.update(specialized[:3])  # Top 3 pro Feld

        # Füge einige allgemeine Modelle hinzu
        selected_models.update(self.tier_definitions['tier_2_comprehensive']['models'][:2])

        return list(selected_models)

    def _calculate_critical_field_coverage(self, data: Dict[str, Any]) -> float:
        """Berechnet Abdeckung kritischer Felder (0.0 - 1.0)"""
        if not data:
            return 0.0

        total_critical = 0
        filled_critical = 0

        for fields in self.critical_fields.values():
            for field in fields:
                total_critical += 1
                if data.get(field) and str(data[field]).strip():
                    filled_critical += 1

        return filled_critical / total_critical if total_critical > 0 else 0.0

    def get_tier_summary(self) -> Dict[str, Any]:
        """Gibt Zusammenfassung der Tier-Performance zurück"""
        summary = {}

        for tier_name, tier_config in self.tier_definitions.items():
            tier_performance = []

            for model_id in tier_config['models']:
                if model_id in self.model_performance:
                    perf = self.model_performance[model_id]
                    if perf['calls'] > 0:
                        tier_performance.append({
                            'model': model_id,
                            'success_rate': round(perf['success_rate'], 2),
                            'avg_fields': round(perf['avg_fields_found'], 1),
                            'avg_sources': round(perf['avg_sources_found'], 1),
                            'calls': perf['calls']
                        })

            # Sortiere nach Erfolgsrate
            tier_performance.sort(key=lambda x: x['success_rate'], reverse=True)

            summary[tier_name] = {
                'focus': tier_config['focus'],
                'threshold': tier_config['threshold'],
                'models': tier_performance
            }

        return summary
