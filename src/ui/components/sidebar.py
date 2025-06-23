"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Sidebar-Komponente für MineSearch UI
"""
import streamlit as st
import pandas as pd
import sys
import os
import hashlib
from datetime import datetime
from typing import List, Dict, Optional
from src.core.config import Config


class SidebarComponent:
    """Sidebar mit Konfiguration, Agent-Auswahl und CSV-Upload"""
    
    def __init__(self, config: Config):
        self.config = config
        
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
        uploaded_file = st.file_uploader(
            "Upload CSV Template",
            type="csv",
            help="CSV should contain columns: mine_name, region, country"
        )
        
        if uploaded_file is None:
            return []
        
        try:
            df = self._parse_csv_file(uploaded_file)
            if df is None:
                return []
            
            # Column mapping
            column_mapping = self._detect_columns(df)
            if not column_mapping.get('mine_name'):
                st.error("CSV must contain a mine name column")
                return []
            
            # Extract mines data
            mines_data = []
            for _, row in df.iterrows():
                mine_data = {
                    'mine_name': row[column_mapping['mine_name']],
                    'region': row.get(column_mapping.get('region', ''), ''),
                    'country': row.get(column_mapping.get('country', ''), '')
                }
                
                # Skip empty rows
                if mine_data['mine_name'] and pd.notna(mine_data['mine_name']):
                    mines_data.append(mine_data)
            
            # Show preview
            if mines_data:
                st.success(f"✅ Loaded {len(mines_data)} mines from CSV")
                with st.expander("Preview loaded mines"):
                    for mine in mines_data[:5]:
                        st.write(f"• {mine['mine_name']} - {mine['region']}, {mine['country']}")
                    if len(mines_data) > 5:
                        st.write(f"... and {len(mines_data) - 5} more")
            
            return mines_data
            
        except Exception as e:
            st.error(f"Error processing CSV: {str(e)}")
            return []
    
    def _parse_csv_file(self, uploaded_file) -> Optional[pd.DataFrame]:
        """Parse CSV mit verschiedenen Encodings und Separatoren"""
        encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
        separators = [';', ',', '\t', '|']
        
        for encoding in encodings:
            for sep in separators:
                try:
                    uploaded_file.seek(0)
                    df = pd.read_csv(uploaded_file, encoding=encoding, sep=sep)
                    
                    # Check if parse was successful
                    if len(df.columns) > 1:
                        # Clean column names
                        df.columns = df.columns.str.strip()
                        if len(df.columns) > 0 and df.columns[0].startswith('\ufeff'):
                            df.columns.values[0] = df.columns[0][1:]
                        return df
                        
                except:
                    continue
        
        st.error("Could not read CSV file. Please check the file encoding.")
        return None
    
    def _detect_columns(self, df: pd.DataFrame) -> Dict[str, str]:
        """Automatische Spalten-Erkennung"""
        column_mapping = {}
        
        # Mine name variants
        mine_variants = ['mine_name', 'name', 'Mine Name', 'Name', 'Mine', 'mine']
        for col in df.columns:
            if col in mine_variants or col.lower() in ['mine_name', 'name', 'mine']:
                column_mapping['mine_name'] = col
                break
        
        # Region variants
        region_variants = ['region', 'Region', 'Province', 'State']
        for col in df.columns:
            if col in region_variants or col.lower() in ['region', 'province', 'state']:
                column_mapping['region'] = col
                break
        
        # Country variants
        country_variants = ['country', 'Country', 'Nation']
        for col in df.columns:
            if col in country_variants or col.lower() in ['country', 'nation']:
                column_mapping['country'] = col
                break
        
        return column_mapping
    
    def _render_agent_selection(self) -> List[str]:
        """Agent-Auswahl UI"""
        st.markdown("---")
        st.header("🤖 Agent Configuration")
        
        # Available agents basierend auf API keys
        available_agents = []
        
        # Check API keys and add available agents
        if self.config.api.openrouter_key:
            available_agents.extend(["claude", "gpt4", "openrouter"])
        if self.config.api.perplexity_key:
            available_agents.extend(["perplexity", "perplexity_deep"])
        if self.config.api.tavily_key:
            available_agents.append("tavily")
        if self.config.api.firecrawl_key:
            available_agents.append("firecrawl")
        if self.config.api.exa_key:
            available_agents.append("exa")
        
        # Premium features
        available_agents.extend([
            "premium_mining",
            "deep_web_crawler",
            "browser",
            "document_finder"
        ])
        
        # Select agents
        selected_agents = st.multiselect(
            "Select Agents",
            available_agents,
            default=["tavily", "perplexity"] if "tavily" in available_agents else [],
            help="Choose which agents to use for the search"
        )
        
        # Agent info
        if st.checkbox("ℹ️ Show Agent Info"):
            self._show_agent_info()
        
        return selected_agents
    
    def _show_agent_info(self):
        """Zeigt Informationen über Agenten"""
        agent_info = {
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
        
        for agent, info in agent_info.items():
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
        
        return options