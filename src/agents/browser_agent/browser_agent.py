"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für Browser Agent
"""

from typing import List, Dict, Any, Optional
import asyncio
import json
from datetime import datetime
from urllib.parse import urlparse, quote

from ..base_agent import BaseAgent, MineQuery, SearchResult, AgentStatus
from src.core.logger import get_logger
from .models import BrowserConfig, ScrapeResult, PortalConfig, NavigationStep
from .page_analyzer import PageAnalyzer


class BrowserAgent(BaseAgent):
    """Browser-basierter Agent für JavaScript-gerenderte Websites"""
    
    def __init__(self, name: str, config: Dict[str, Any]):
        super().__init__(name, config)
        self.logger = get_logger(f"agent.{name}", agent_type="browser")
        
        # Browser Konfiguration
        browser_config = config.get('browser_config', {})
        self.browser_config = BrowserConfig(
            headless=browser_config.get('headless', True),
            timeout=browser_config.get('timeout', 30000),
            viewport_width=browser_config.get('viewport_width', 1920),
            viewport_height=browser_config.get('viewport_height', 1080)
        )
        
        # Playwright Objekte
        self.playwright = None
        self.browser = None
        self.context = None
        
        # Page Analyzer
        self.analyzer = PageAnalyzer(self.logger)
        
        # Government Portals
        self.government_portals = self._load_government_portals()
        
    async def initialize(self) -> bool:
        """Initialisiert Playwright und Browser"""
        try:
            # Playwright dynamisch importieren
            try:
                from playwright.async_api import async_playwright
                self.playwright = await async_playwright().start()
            except ImportError:
                self.logger.error("Playwright nicht installiert. Bitte 'pip install playwright' ausführen")
                self.status = AgentStatus.DISABLED
                return False
            
            # Browser starten
            self.browser = await self.playwright.chromium.launch(
                headless=self.browser_config.headless,
                args=self.browser_config.args
            )
            
            # Browser-Kontext erstellen
            self.context = await self.browser.new_context(
                viewport={
                    'width': self.browser_config.viewport_width, 
                    'height': self.browser_config.viewport_height
                },
                user_agent=self.browser_config.user_agent,
                locale=self.browser_config.locale
            )
            
            self.status = AgentStatus.ACTIVE
            self.logger.info("Browser Agent erfolgreich initialisiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Browser-Initialisierung: {e}")
            self.status = AgentStatus.ERROR
            return False
    
    async def validate_credentials(self) -> bool:
        """Browser Agent benötigt keine API Credentials"""
        return True
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Führt Browser-basierte Suche durch"""
        return await self.search_mine(query)
    
    async def search_mine(self, query: MineQuery) -> List[SearchResult]:
        """Führt Browser-basierte Suche durch"""
        results = []
        
        # Nutze entdeckte Quellen wenn verfügbar
        discovered_sources = getattr(query, 'discovered_sources', None)
        if discovered_sources:
            # Filtere Quellen die Browser-Rendering benötigen
            browser_sources = [
                s for s in discovered_sources 
                if self.analyzer.needs_browser_rendering(s.url)
            ][:5]  # Max 5 Quellen
            
            for source in browser_sources:
                try:
                    page_results = await self._scrape_dynamic_site(
                        url=source.url,
                        query=query,
                        source_type=source.source_type
                    )
                    results.extend(page_results)
                except Exception as e:
                    self.logger.error(f"Fehler beim Scrapen von {source.url}: {e}")
        
        # Zusätzlich spezielle Portal-Suchen
        portal_results = await self._search_government_portals(query)
        results.extend(portal_results)
        
        # Update Statistiken
        self.stats['total_requests'] += 1
        self.stats['successful_requests'] += 1 if results else 0
        self.stats['total_fields_found'] += len(results)
        
        return results
    
    async def _scrape_dynamic_site(self, url: str, query: MineQuery, 
                                  source_type: str = "web") -> List[SearchResult]:
        """Scrapt eine dynamische Website"""
        results = []
        page = None
        
        try:
            # Neue Seite öffnen
            page = await self.context.new_page()
            
            # Navigiere zur URL
            self.logger.info(f"Lade dynamische Seite: {url}")
            await page.goto(url, wait_until="networkidle", timeout=self.browser_config.timeout)
            
            # Warte auf dynamische Inhalte
            await self._wait_for_content(page)
            
            # Suche nach Mine-spezifischen Informationen
            if await self._search_on_page(page, query.mine_name):
                # Extrahiere Daten
                content = await page.content()
                
                # Nutze Page Analyzer
                extracted = self.analyzer.extract_from_page(
                    content, query, url, source_type
                )
                results.extend(extracted)
                
                # Screenshot für wichtige Seiten
                if results and source_type in ["government", "official"]:
                    screenshot_path = await self._take_screenshot(page, query.mine_name)
                    for result in results:
                        result.metadata["screenshot"] = screenshot_path
            
        except Exception as e:
            self.logger.error(f"Fehler beim Scrapen von {url}: {e}")
        finally:
            if page:
                await page.close()
        
        return results
    
    async def _search_government_portals(self, query: MineQuery) -> List[SearchResult]:
        """Durchsucht Government Portals"""
        results = []
        
        # Finde passende Portale für das Land
        country_portals = [
            p for p in self.government_portals 
            if p.country.lower() == query.country.lower()
        ]
        
        for portal in country_portals[:2]:  # Max 2 Portale
            try:
                portal_results = await self._search_portal(portal, query)
                results.extend(portal_results)
            except Exception as e:
                self.logger.error(f"Fehler bei Portal {portal.name}: {e}")
        
        return results
    
    async def _search_portal(self, portal: PortalConfig, query: MineQuery) -> List[SearchResult]:
        """Durchsucht ein spezifisches Portal"""
        results = []
        page = None
        
        try:
            page = await self.context.new_page()
            
            # Navigiere zum Portal
            search_url = f"{portal.base_url}{portal.search_path}"
            await page.goto(search_url, wait_until="domcontentloaded")
            
            # Führe Suche aus
            if "search_input" in portal.selectors:
                await page.fill(portal.selectors["search_input"], query.mine_name)
                
                if "search_button" in portal.selectors:
                    await page.click(portal.selectors["search_button"])
                else:
                    await page.press(portal.selectors["search_input"], "Enter")
                
                # Warte auf Ergebnisse
                await page.wait_for_load_state("networkidle")
                await asyncio.sleep(2)  # Zusätzliche Wartezeit
                
                # Prüfe ob Ergebnisse vorhanden
                if "result_container" in portal.selectors:
                    results_found = await page.query_selector(portal.selectors["result_container"])
                    
                    if results_found:
                        # Klicke auf erstes Ergebnis wenn vorhanden
                        if "result_link" in portal.selectors:
                            first_result = await page.query_selector(portal.selectors["result_link"])
                            if first_result:
                                await first_result.click()
                                await page.wait_for_load_state("networkidle")
                        
                        # Extrahiere Daten
                        content = await page.content()
                        extracted = self.analyzer.extract_from_page(
                            content, query, portal.base_url, "government"
                        )
                        
                        # Füge Portal-Metadaten hinzu
                        for result in extracted:
                            result.metadata["portal"] = portal.name
                            result.metadata["official_source"] = True
                        
                        results.extend(extracted)
            
        except Exception as e:
            self.logger.error(f"Portal-Suche fehlgeschlagen: {e}")
        finally:
            if page:
                await page.close()
        
        return results
    
    async def _wait_for_content(self, page) -> None:
        """Wartet auf dynamische Inhalte"""
        try:
            # Warte auf typische Indikatoren
            await page.wait_for_load_state("networkidle")
            
            # Prüfe auf bekannte Frameworks
            has_react = await page.evaluate("() => window.React !== undefined")
            has_angular = await page.evaluate("() => window.angular !== undefined")
            has_vue = await page.evaluate("() => window.Vue !== undefined")
            
            if has_react or has_angular or has_vue:
                # Zusätzliche Wartezeit für SPA
                await asyncio.sleep(3)
            
            # Warte auf spezifische Elemente
            common_selectors = ["table", ".data-table", "#results", ".content"]
            for selector in common_selectors:
                try:
                    await page.wait_for_selector(selector, timeout=5000)
                    break
                except:
                    continue
                    
        except Exception as e:
            self.logger.debug(f"Wartezeit abgelaufen: {e}")
    
    async def _search_on_page(self, page, search_term: str) -> bool:
        """Sucht nach Begriff auf der Seite"""
        try:
            # Versuche Suchfeld zu finden
            search_selectors = [
                "input[type='search']",
                "input[placeholder*='search' i]",
                "input[placeholder*='buscar' i]",
                "input[placeholder*='recherche' i]",
                "input#search",
                "input.search"
            ]
            
            for selector in search_selectors:
                search_input = await page.query_selector(selector)
                if search_input:
                    await search_input.fill(search_term)
                    await page.keyboard.press("Enter")
                    await page.wait_for_load_state("networkidle")
                    return True
            
            # Prüfe ob Begriff bereits auf Seite
            content = await page.content()
            if search_term.lower() in content.lower():
                return True
            
            return False
            
        except Exception:
            return False
    
    async def _take_screenshot(self, page, mine_name: str) -> str:
        """Macht Screenshot der Seite"""
        try:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            filename = f"screenshots/{mine_name}_{timestamp}.png"
            await page.screenshot(path=filename, full_page=True)
            return filename
        except Exception as e:
            self.logger.error(f"Screenshot fehlgeschlagen: {e}")
            return ""
    
    def _load_government_portals(self) -> List[PortalConfig]:
        """Lädt Government Portal Konfigurationen"""
        # Beispiel-Portale (würde aus Datei/DB geladen)
        return [
            PortalConfig(
                country="Canada",
                name="Natural Resources Canada",
                base_url="https://www.nrcan.gc.ca",
                search_path="/en/search",
                selectors={
                    "search_input": "input#search-input",
                    "search_button": "button[type='submit']",
                    "result_container": ".search-results",
                    "result_link": ".search-result a"
                }
            ),
            PortalConfig(
                country="Australia",
                name="Geoscience Australia",
                base_url="https://www.ga.gov.au",
                search_path="/search",
                selectors={
                    "search_input": "input[name='query']",
                    "result_container": ".search-results",
                    "result_link": ".result-title a"
                }
            ),
            PortalConfig(
                country="Chile",
                name="SERNAGEOMIN",
                base_url="https://www.sernageomin.cl",
                search_path="/busqueda",
                selectors={
                    "search_input": "input.search-field",
                    "search_button": "button.search-submit",
                    "result_container": "#search-results"
                }
            )
        ]
    
    async def cleanup(self):
        """Cleanup Browser-Ressourcen"""
        try:
            if self.context:
                await self.context.close()
            if self.browser:
                await self.browser.close()
            if self.playwright:
                await self.playwright.stop()
        except Exception as e:
            self.logger.error(f"Cleanup-Fehler: {e}")