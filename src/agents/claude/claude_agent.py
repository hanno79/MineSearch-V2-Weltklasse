"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Claude Agent Implementation via OpenRouter
"""

import aiohttp
import asyncio
import json
from typing import List, Dict, Any
from datetime import datetime

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from ..rate_limiter import RateLimiter
from src.core.logger import get_logger, PerformanceLogger
from ..enhanced_search import get_mining_search_queries, get_mining_domains

from .prompts import ClaudePromptGenerator
from .response_parser import ClaudeResponseParser


class ClaudeAgent(BaseAgent):
    """Claude-3 Agent über OpenRouter API"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.api_key = config['api_config'].openrouter_key
        self.base_url = "https://openrouter.ai/api/v1/chat/completions"
        self.model = "anthropic/claude-3-opus-20240229"
        self._rate_limiter = RateLimiter(rate=30, per=60.0)  # 30 Anfragen pro Minute
        self.logger = get_logger(f"agent.{name}", agent_type="claude")
        self.perf_logger = PerformanceLogger(self.logger)
        self.timeout = aiohttp.ClientTimeout(total=120)  # Längerer Timeout für Mining-Suchen
        self._session = None  # ÄNDERUNG 19.06.2025: Explizit initialisieren
        
        # Komponenten
        self.prompt_generator = ClaudePromptGenerator()
        self.response_parser = ClaudeResponseParser(self.name, self.logger)
        
    async def initialize(self) -> bool:
        """Initialisiert den Agenten"""
        try:
            # Erstelle Session
            self._session = aiohttp.ClientSession()
            
            # Validiere Credentials
            is_valid = await self.validate_credentials()
            if not is_valid:
                self.status = AgentStatus.DISABLED
                return False
                
            self.logger.info("Claude Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Initialisierung: {e}")
            return False
    
    async def validate_credentials(self) -> bool:
        """Validiert API-Key mit Test-Anfrage"""
        if not self.api_key:
            self.logger.warning("Kein OpenRouter API-Key konfiguriert")
            return False
            
        try:
            # Einfache Test-Anfrage
            headers = {
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
                "HTTP-Referer": "https://github.com/yourusername/yourrepo",
                "X-Title": "Mining Research Assistant"
            }
            
            data = {
                "model": self.model,
                "messages": [
                    {"role": "user", "content": "Reply with 'OK' if you receive this."}
                ],
                "max_tokens": 10
            }
            
            async with self._session.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    self.logger.info("Claude API-Key erfolgreich validiert")
                    return True
                else:
                    error_text = await response.text()
                    self.logger.error(f"API-Validierung fehlgeschlagen: {response.status} - {error_text}")
                    return False
                    
        except Exception as e:
            self.logger.error(f"Fehler bei API-Validierung: {e}")
            return False
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt erweiterte Mining-spezifische Suche mit Claude durch"""
        results = []
        
        self.perf_logger.start_timer(f"claude_search_{query.mine_name}")
        
        try:
            # ÄNDERUNG 20.06.2025: Check für Cancellation vor Beginn
            if self._cancellation_token and self._cancellation_token.is_cancelled():
                self.logger.info("Suche wurde abgebrochen bevor sie begann")
                return []
                
            # Hole Mining-spezifische Suchstrategien
            mining_queries = get_mining_search_queries(query.mine_name, query.region, query.country)
            mining_domains = get_mining_domains()
            
            # Erstelle erweiterte Mining-Prompts
            prompts = self.prompt_generator.create_mining_prompts(query, mining_queries, mining_domains)
            
            # Führe Suchen für verschiedene Prompt-Typen durch
            total_prompts = len(prompts)
            completed = 0
            
            for prompt_type, prompt in prompts.items():
                # ÄNDERUNG 20.06.2025: Check für Cancellation in der Schleife
                if self._cancellation_token and self._cancellation_token.is_cancelled():
                    self.logger.info("Suche wurde während der Ausführung abgebrochen")
                    break
                    
                # Status-Update
                if hasattr(self, 'status_callback') and self.status_callback:
                    await self.status_callback(f"Claude: {prompt_type} Suche ({completed + 1}/{total_prompts})")
                
                response = await self._make_api_call(prompt)
                if response:
                    parsed_results = self.response_parser.parse_response(
                        response, query, prompt_type
                    )
                    results.extend(parsed_results)
                
                completed += 1
                await asyncio.sleep(2)  # Respektiere Rate Limits
            
            self.perf_logger.end_timer(
                f"claude_search_{query.mine_name}",
                results_found=len(results)
            )
            
            return results
            
        except Exception as e:
            self.logger.error(f"Fehler bei Claude-Suche: {e}")
            return results
    
    async def _make_api_call(self, prompt: str) -> str:
        """Macht API-Aufruf zu Claude"""
        await self._rate_limiter.acquire()
        
        headers = {
            "Authorization": f"Bearer {self.api_key}",
            "Content-Type": "application/json",
            "HTTP-Referer": "https://github.com/yourusername/yourrepo",
            "X-Title": "Mining Research Assistant"
        }
        
        data = {
            "model": self.model,
            "messages": [
                {
                    "role": "system",
                    "content": """You are a highly skilled mining industry researcher with access to all public mining databases, 
                    government records, company reports, and environmental documents. You provide accurate, verifiable information 
                    with specific sources. Always cite your sources and provide confidence levels for your findings."""
                },
                {
                    "role": "user",
                    "content": prompt
                }
            ],
            "max_tokens": 4000,
            "temperature": 0.3,  # Niedrigere Temperatur für faktische Genauigkeit
            "top_p": 0.9
        }
        
        try:
            async with self._session.post(
                self.base_url,
                headers=headers,
                json=data,
                timeout=self.timeout
            ) as response:
                if response.status == 200:
                    result = await response.json()
                    return result['choices'][0]['message']['content']
                else:
                    error_text = await response.text()
                    self.logger.error(f"API-Fehler: {response.status} - {error_text}")
                    return ""
                    
        except asyncio.TimeoutError:
            self.logger.error("API-Aufruf Timeout")
            return ""
        except Exception as e:
            self.logger.error(f"API-Aufruf Fehler: {e}")
            return ""
    
    async def cleanup(self):
        """ÄNDERUNG 19.06.2025: Explizite cleanup Methode für Session-Management"""
        try:
            if hasattr(self, '_session') and self._session and not self._session.closed:
                await self._session.close()
                self.logger.debug("Session erfolgreich geschlossen")
        except Exception as e:
            self.logger.warning(f"Fehler beim Schließen der Session: {e}")
        finally:
            self._session = None
            await super().cleanup()  # Rufe parent cleanup auf
