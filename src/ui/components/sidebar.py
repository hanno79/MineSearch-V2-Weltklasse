"""
Author: rahn
Datum: 22.06.2025
Version: 1.1
Beschreibung: Sidebar-Komponente für MineSearch UI

ÄNDERUNG 27.06.2025: Refactoring für bessere Wartbarkeit
- CSV-Verarbeitung in separate Komponente csv_handler.py ausgelagert
- Agent-Verfügbarkeit vereinfacht
- Agent-Informationen als Klassenkonstante definiert
- Redundanten Code entfernt
- Datei von 515 auf 280 Zeilen reduziert
"""
import streamlit as st
import sys
import os
import hashlib
from datetime import datetime
from typing import List, Dict
from src.core.config import Config
from .csv_handler import CSVHandler


class SidebarComponent:
    """Sidebar mit Konfiguration, Agent-Auswahl und CSV-Upload"""
    
    # ÄNDERUNG 27.06.2025: Agent-Informationen als Klassenkonstante
    AGENT_INFO = {
        "claude": "Claude AI for intelligent analysis",
        "gpt4": "GPT-4 for comprehensive research",
        "perplexity": "Web search with AI summaries",
        "tavily": "Specialized search API",
        "firecrawl": "Advanced web scraping",
        "premium_mining": "Orchestrated mining research",
        "deep_web_crawler": "Deep website crawling",
        "browser": "JavaScript-enabled scraping",
        "document_finder": "PDF and document search"
    }
    
    def __init__(self, config: Config):
        self.config = config
        self.csv_handler = CSVHandler()
        
    def render(self) -> Dict:
        """Rendert die Sidebar und gibt Konfiguration zurück"""
        with st.sidebar:
            # Version Info
            self._render_version_info()
            
            # Cache Management
            self._render_cache_management()
            
            # Debug Mode
            if st.checkbox("🐛 Debug Mode", value=False):
                self._render_debug_info()
            
            st.markdown("---")
            st.header("🔍 Search Configuration")
            
            # Search Mode und Mine Selection
            search_mode = st.radio(
                "Search Mode",
                ["Manual Entry", "CSV Upload"],
                help="Choose how to specify the mines to search"
            )
            
            mines_to_search = []
            
            if search_mode == "Manual Entry":
                mines_to_search = self._handle_manual_entry()
            else:
                mines_to_search = self._handle_csv_upload()
            
            # Agent Selection
            selected_agents = self._render_agent_selection()
            
            # Advanced Options
            advanced_options = self._render_advanced_options()
            
            return {
                'mines_to_search': mines_to_search,
                'selected_agents': selected_agents,
                'advanced_options': advanced_options,
                'search_mode': search_mode
            }
    
    def _render_version_info(self):
        """Zeigt Versions-Information"""
        version_info = "🔄 Version: 22.06.2025-refactored"
        
        # Zeige File-Hash für Verifikation
        try:
            orchestrator_path = os.path.join(
                os.path.dirname(__file__), '..', '..', 'core', 'orchestrator.py'
            )
            with open(orchestrator_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:8]
            version_info += f" (Hash: {file_hash})"
        except:
            pass
        
        st.info(version_info)
    
    def _render_cache_management(self):
        """Cache Management Buttons"""
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear Cache", help="Löscht Streamlit Cache"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✅ Cache gelöscht!")
                st.info("Seite wird neu geladen...")
                st.rerun()
        
        with col2:
            if st.button("🔄 Force Reload", help="Temporär deaktiviert", disabled=True):
                st.warning("⚠️ Force Reload ist temporär deaktiviert")
    
    def _render_debug_info(self):
        """Debug-Informationen anzeigen"""
        # Module Load Status
        st.write("**Module Status:**")
        critical_modules = {
            'orchestrator': 'src.core.orchestrator',
            'staged_search': 'src.agents.staged_search',
            'source_manager': 'src.core.source_manager'
        }
        
        for name, module_path in critical_modules.items():
            if module_path in sys.modules:
                module = sys.modules[module_path]
                if hasattr(module, '__file__'):
                    mtime = datetime.fromtimestamp(os.path.getmtime(module.__file__))
                    st.write(f"✅ {name}: {mtime.strftime('%H:%M:%S')}")
                else:
                    st.write(f"⚠️ {name}: loaded (no file)")
            else:
                st.write(f"❌ {name}: not loaded")
        
        # API Status
        st.write("\n**Agent API Status:**")
        api_status = {
            "Firecrawl": "✅" if self.config.api.firecrawl_key else "❌",
            "Perplexity": "✅" if self.config.api.perplexity_key else "❌",
            "Tavily": "✅" if self.config.api.tavily_key else "❌",
            "OpenRouter": "✅" if self.config.api.openrouter_key else "❌"
        }
        
        for api, status in api_status.items():
            st.write(f"{status} {api}")
    
    def _handle_manual_entry(self) -> List[Dict]:
        """Manuelle Eingabe von Minen-Daten"""
        mine_name = st.text_input("Mine Name", placeholder="e.g., Malartic Mine")
        region = st.text_input("Region/Province", placeholder="e.g., Quebec")
        country = st.text_input("Country", placeholder="e.g., Canada")
        
        if mine_name and region and country:
            return [{
                'mine_name': mine_name,
                'region': region,
                'country': country
            }]
        return []
    
    def _handle_csv_upload(self) -> List[Dict]:
        """CSV Upload und Parsing"""
        # ÄNDERUNG 27.06.2025: CSV-Verarbeitung in separate Komponente ausgelagert
        uploaded_file = st.file_uploader(
            "Upload CSV Template",
            type="csv",
            help="CSV should contain columns: mine_name, region, country"
        )
        
        return self.csv_handler.handle_upload(uploaded_file)
    
    
    def _render_agent_selection(self) -> List[str]:
        """Agent-Auswahl UI"""
        st.markdown("---")
        st.header("🤖 Agent Configuration")
        
        # ÄNDERUNG 27.06.2025: Agent-Verfügbarkeit vereinfacht
        available_agents = self._get_available_agents()
        
        # Select agents
        default_agents = []
        if "perplexity" in available_agents:
            default_agents.append("perplexity")
        if "perplexity_deep" in available_agents:
            default_agents.append("perplexity_deep")
        selected_agents = st.multiselect(
            "Select Agents",
            available_agents,
            default=default_agents,
            help="Choose which agents to use for the search"
        )
        
        # Agent info
        if st.checkbox("ℹ️ Show Agent Info"):
            self._show_agent_info()
        
        return selected_agents
    
    def _get_available_agents(self) -> List[str]:
        """Ermittelt verfügbare Agenten basierend auf API-Keys"""
        agents = []
        
        # API-basierte Agenten
        if self.config.api.openrouter_key:
            agents.extend(["claude", "gpt4", "openrouter"])
        if self.config.api.perplexity_key:
            agents.extend(["perplexity", "perplexity_deep"])
        if self.config.api.tavily_key:
            agents.append("tavily")
        if self.config.api.firecrawl_key:
            agents.append("firecrawl")
        if self.config.api.exa_key:
            agents.append("exa")
        
        # Premium features (immer verfügbar)
        agents.extend([
            "premium_mining",
            "deep_web_crawler",
            "browser",
            "document_finder"
        ])
        
        return agents
    
    def _show_agent_info(self):
        """Zeigt Informationen über Agenten"""
        # ÄNDERUNG 27.06.2025: Agent-Info verwendet jetzt Klassenkonstante
        for agent, info in self.AGENT_INFO.items():
            st.write(f"**{agent}**: {info}")
    
    def _render_advanced_options(self) -> Dict:
        """Erweiterte Optionen"""
        st.markdown("---")
        st.header("⚙️ Advanced Options")
        
        options = {}
        
        # Timeout settings
        options['timeout'] = st.slider(
            "Search Timeout (seconds)",
            min_value=30,
            max_value=300,
            value=120,
            step=30
        )
        
        # Parallel execution
        options['parallel'] = st.checkbox(
            "Enable Parallel Search",
            value=True,
            help="Run agents in parallel for faster results"
        )
        
        # Deep search
        options['deep_search'] = st.checkbox(
            "Enable Deep Search",
            value=False,
            help="Crawl websites deeply for more comprehensive results"
        )
        
        # Export format
        options['export_format'] = st.selectbox(
            "Default Export Format",
            ["CSV", "JSON", "Excel"],
            help="Choose the default format for data export"
        )
        
        # Debug mode
        options['debug_mode'] = st.checkbox(
            "🐛 Enable Debug Mode",
            value=False,
            help="Show detailed debug information during search"
        )
        
        # ÄNDERUNG 27.06.2025: Cache-Einstellungen hinzugefügt
        options['cache_results'] = st.checkbox(
            "💾 Cache Search Results",
            value=True,
            help="Cache results for faster repeated searches"
        )
        
        return options