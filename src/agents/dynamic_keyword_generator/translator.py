"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Übersetzungsfunktionen für Keyword Generator
"""

from typing import List, Dict, Optional
from src.core.logger import get_logger

class KeywordTranslator:
    """Übersetzt Keywords mit AI-Agenten"""
    
    def __init__(self, ai_agents: Optional[Dict] = None):
        self.ai_agents = ai_agents or {}
        self.logger = get_logger("agent.keyword_translator", agent_type="translator")
        self.cache = {}
        
    async def translate_with_ai(self, terms: List[str], target_languages: List[str], 
                               context: str = "mining") -> Dict[str, List[str]]:
        """Übersetzt Begriffe mit AI-Agenten"""
        # ÄNDERUNG 17.06.2025: Dynamische Übersetzung mit AI
        translations = {lang: [] for lang in target_languages}
        
        # Wähle besten AI-Agent für Übersetzung
        ai_agent = self._select_ai_agent()
        
        if not ai_agent:
            self.logger.warning("⚠️ Kein AI-Agent für Übersetzungen verfügbar, nutze Basis-Keywords")
            return translations
        
        # Erstelle Übersetzungsanfrage
        from ..base_agent import MineQuery
        for lang in target_languages:
            if lang == 'en':  # Englisch ist Ausgangssprache
                translations[lang] = terms
                continue
            
            # Check Cache
            cache_key = f"{','.join(terms)}_{lang}_{context}"
            if cache_key in self.cache:
                translations[lang] = self.cache[cache_key]
                continue
                
            prompt = f"""Translate these mining-related terms to {lang}:
Terms: {', '.join(terms)}
Context: {context} industry terminology
Provide only the translations, separated by commas."""
            
            try:
                query = MineQuery(
                    mine_name=prompt,
                    country="",
                    region="",
                    languages=[lang]
                )
                
                results = await ai_agent.search_mine(query)
                if results:
                    # Parse Übersetzungen aus Antwort
                    translated = results[0].value.split(',')
                    translations[lang] = [t.strip() for t in translated]
                    # Cache Ergebnis
                    self.cache[cache_key] = translations[lang]
            except Exception as e:
                self.logger.error(f"Übersetzungsfehler für {lang}: {e}")
                
        return translations
    
    def _select_ai_agent(self):
        """Wählt den besten verfügbaren AI-Agent"""
        for agent_name in ['claude', 'gpt4', 'openrouter']:
            if agent_name in self.ai_agents and self.ai_agents[agent_name]:
                self.logger.info(f"✅ Nutze {agent_name} für Übersetzungen")
                return self.ai_agents[agent_name]
        return None
    
    async def translate_terms(self, terms: List[str], target_language: str) -> List[str]:
        """Übersetzt Begriffe in Zielsprache"""
        # ÄNDERUNG 22.06.2025: NOT_IMPLEMENTED - Übersetzungs-API erforderlich
        # Benötigt Integration mit Claude/GPT für Übersetzungen
        # Momentan: Gibt Original-Terms zurück
        return terms