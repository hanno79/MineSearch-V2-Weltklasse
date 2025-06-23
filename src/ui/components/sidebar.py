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
            
            # Show preview and selection
            if mines_data:
                st.success(f"✅ Loaded {len(mines_data)} mines from CSV")
                
                # Mine Selection
                st.markdown("### Select Mines to Search")
                
                # Initialize session states for two-way sync
                if 'all_selected_mine_indices' not in st.session_state:
                    # All selected mines (persistent)
                    # ÄNDERUNG 23.06.2025: Standard auf 5 Minen reduziert
                    st.session_state['all_selected_mine_indices'] = list(range(min(5, len(mines_data))))
                
                if 'active_mine_indices' not in st.session_state:
                    # Active mines for search (limited by max_mines)
                    # ÄNDERUNG 23.06.2025: Standard auf 5 Minen
                    st.session_state['active_mine_indices'] = st.session_state['all_selected_mine_indices'][:5]
                
                # Select All / Deselect All buttons
                col1, col2, col3 = st.columns(3)
                with col1:
                    if st.button("✅ Select All", use_container_width=True):
                        st.session_state['all_selected_mine_indices'] = list(range(len(mines_data)))
                        st.session_state['active_mine_indices'] = list(range(min(st.session_state.get('max_mines_limit', 20), len(mines_data))))
                with col2:
                    if st.button("❌ Deselect All", use_container_width=True):
                        st.session_state['all_selected_mine_indices'] = []
                        st.session_state['active_mine_indices'] = []
                with col3:
                    if st.button("🔄 Activate All", use_container_width=True):
                        # Activate all selected mines and adjust max_mines
                        num_selected = len(st.session_state['all_selected_mine_indices'])
                        if num_selected > 0:
                            st.session_state['max_mines_limit'] = num_selected
                            st.session_state['active_mine_indices'] = st.session_state['all_selected_mine_indices'].copy()
                            st.info(f"✅ Activated all {num_selected} selected mines")
                
                # Max selection limit with callback
                def on_max_mines_change():
                    new_max = st.session_state['max_mines_input']
                    old_max = st.session_state.get('max_mines_limit', 20)
                    
                    if new_max != old_max:
                        st.session_state['max_mines_limit'] = new_max
                        
                        # Update active mines based on new limit
                        all_selected = st.session_state.get('all_selected_mine_indices', [])
                        
                        if new_max > old_max:
                            # Expanding: activate more mines from all_selected
                            st.session_state['active_mine_indices'] = all_selected[:new_max]
                        else:
                            # Reducing: keep only first new_max mines
                            st.session_state['active_mine_indices'] = st.session_state['active_mine_indices'][:new_max]
                
                # Initialize max_mines_limit if not set
                if 'max_mines_limit' not in st.session_state:
                    st.session_state['max_mines_limit'] = 20
                
                max_mines = st.number_input(
                    "Max mines to search at once",
                    min_value=1,
                    max_value=100,
                    value=st.session_state.get('max_mines_limit', 20),
                    key="max_mines_input",
                    on_change=on_max_mines_change,
                    help="Limit the number of mines for better performance"
                )
                
                # Multi-select for mines
                mine_options = [
                    f"{mine['mine_name']} - {mine['region']}, {mine['country']}"
                    for mine in mines_data
                ]
                
                # Create checkboxes in an expander
                with st.expander(f"Select mines", expanded=True):
                    # Show current status
                    num_all_selected = len(st.session_state.get('all_selected_mine_indices', []))
                    num_active = len(st.session_state.get('active_mine_indices', []))
                    
                    col1, col2 = st.columns(2)
                    with col1:
                        st.metric("Selected Mines", num_all_selected)
                    with col2:
                        st.metric("Active for Search", f"{num_active} / {max_mines}")
                    
                    if num_all_selected > max_mines:
                        st.warning(f"⚠️ {num_all_selected - max_mines} selected mines are inactive. Increase 'Max mines' or click 'Activate All'")
                    
                    st.markdown("---")
                    
                    # Show only first 50 mines with checkboxes, rest in multiselect
                    if len(mines_data) <= 50:
                        # Checkbox interface for smaller lists
                        new_selected_indices = []
                        
                        for idx, mine in enumerate(mines_data):
                            # Determine checkbox state
                            is_selected = idx in st.session_state.get('all_selected_mine_indices', [])
                            is_active = idx in st.session_state.get('active_mine_indices', [])
                            
                            # Create label with status
                            label = f"{mine['mine_name']} - {mine['region']}, {mine['country']}"
                            if is_selected and not is_active:
                                label += " ⚠️ (selected but inactive)"
                            
                            if st.checkbox(label, value=is_selected, key=f"mine_checkbox_{idx}"):
                                new_selected_indices.append(idx)
                        
                        # Update all_selected based on checkboxes
                        st.session_state['all_selected_mine_indices'] = new_selected_indices
                        
                        # Auto-adjust max_mines if more selected
                        if len(new_selected_indices) > max_mines:
                            st.session_state['max_mines_limit'] = len(new_selected_indices)
                            st.session_state['active_mine_indices'] = new_selected_indices
                            st.success(f"✅ Automatically increased max mines to {len(new_selected_indices)}")
                        else:
                            # Update active mines
                            st.session_state['active_mine_indices'] = new_selected_indices[:max_mines]
                    
                    else:
                        # Multiselect for large lists
                        default_selection = [
                            mine_options[i] 
                            for i in st.session_state.get('all_selected_mine_indices', [])
                        ]
                        
                        selected_options = st.multiselect(
                            "Choose mines (no limit on selection)",
                            options=mine_options,
                            default=default_selection,
                            help="Select as many as you want. Active mines will be limited by 'Max mines' setting."
                        )
                        
                        # Convert back to indices
                        new_selected_indices = [
                            idx for idx, option in enumerate(mine_options)
                            if option in selected_options
                        ]
                        
                        st.session_state['all_selected_mine_indices'] = new_selected_indices
                        
                        # Auto-adjust max_mines if more selected
                        if len(new_selected_indices) > max_mines:
                            if st.checkbox("Auto-increase max mines to match selection?", value=True):
                                st.session_state['max_mines_limit'] = len(new_selected_indices)
                                st.session_state['active_mine_indices'] = new_selected_indices
                            else:
                                st.session_state['active_mine_indices'] = new_selected_indices[:max_mines]
                        else:
                            st.session_state['active_mine_indices'] = new_selected_indices[:max_mines]
                
                # Show final summary
                num_active = len(st.session_state.get('active_mine_indices', []))
                if num_active > 0:
                    st.success(f"✅ Ready to search {num_active} mines")
                    
                    # Return only active mines for search
                    active_mines = [
                        mines_data[idx] 
                        for idx in st.session_state.get('active_mine_indices', [])
                    ]
                    return active_mines
                else:
                    st.warning("⚠️ Please select at least one mine to search")
                    return []
            
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
        
        # Debug mode
        options['debug_mode'] = st.checkbox(
            "🐛 Enable Debug Mode",
            value=False,
            help="Show detailed debug information during search"
        )
        
        return options