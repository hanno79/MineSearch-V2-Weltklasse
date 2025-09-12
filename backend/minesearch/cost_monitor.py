"""
Author: rahn
Datum: 14.07.2025
Version: 1.0
Beschreibung: Kostenüberwachung für Premium-Modelle
"""

import logging
from typing import Dict, Set, List
from minesearch.model_tier_strategy import ModelTierStrategy

logger = logging.getLogger(__name__)

class CostMonitor:
    """Überwacht Kosten für Premium-Modelle"""

    def __init__(self):
        """__init__ - TODO: Dokumentation hinzufügen"""
        self.tier_strategy = ModelTierStrategy()
        self.usage_warnings: Dict[str, int] = {}
        self.premium_models_used: Set[str] = set()

    def check_model_costs(self, model_id: str, operation: str = "search") -> bool:
        """
        Prüft ob ein Modell kostenpflichtig ist und gibt Warnung aus

        Args:
            model_id: Modell-ID (z.B. 'perplexity:sonar-pro')
            operation: Art der Operation ('search', 'batch', etc.)

        Returns:
            True wenn Verwendung erlaubt, False wenn blockiert
        """
        if self.tier_strategy.is_premium_model(model_id):
            # Warnung ausgeben
            warning_msg = self.tier_strategy.get_cost_warning_message(model_id)
            logger.warning(f"[COST-MONITOR] {warning_msg}")

            # Verwendung tracken
            self.premium_models_used.add(model_id)
            self.usage_warnings[model_id] = self.usage_warnings.get(model_id, 0) + 1

            # Für jetzt warnen, aber nicht blockieren
            # In Production könnte hier eine Blockierung implementiert werden
            return True

        return True

    def get_usage_summary(self) -> Dict[str, any]:
        """
        Erstellt Zusammenfassung der Premium-Modell-Verwendung

        Returns:
            Dictionary mit Verwendungsstatistiken
        """
        return {
            'premium_models_used': list(self.premium_models_used),
            'total_premium_calls': sum(self.usage_warnings.values()),
            'model_usage_counts': self.usage_warnings.copy(),
            'cost_warnings_issued': len(self.usage_warnings)
        }

    def suggest_free_alternatives(self, model_id: str) -> List[str]:
        """
        Schlägt kostenlose Alternativen vor

        Args:
            model_id: Kostenpflichtiges Modell

        Returns:
            Liste von kostenlosen Alternativen
        """
        if self.tier_strategy.is_premium_model(model_id):
            # Immer Kimi K2 als erste Alternative
            alternatives = ["openrouter:kimi-k2"]

            # Weitere kostenlose Alternativen basierend auf Tier 1
            tier_1_primary = self.tier_strategy.tier_definitions['tier_1_free_primary']['models']
            tier_1_secondary = self.tier_strategy.tier_definitions['tier_1_free_secondary']['models']

            alternatives.extend([m for m in tier_1_primary if m not in alternatives])
            alternatives.extend([m for m in tier_1_secondary if m not in alternatives])

            return alternatives[:5]  # Top 5 Alternativen

        return []

# Globale Instanz
cost_monitor = CostMonitor()
