"""
MineSearch Streamlit UI
"""
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
from datetime import datetime
import asyncio
from typing import List, Dict, Any
import sys
import os
import importlib
import hashlib

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ÄNDERUNG 21.06.2025: Fallback für Pfad-Probleme
if not os.path.exists(os.path.join(project_root, 'src')):
    # Wenn src nicht gefunden wird, versuche alternativen Pfad
    alt_root = os.getcwd()
    if os.path.exists(os.path.join(alt_root, 'src')):
        sys.path.insert(0, alt_root)

# ÄNDERUNG 18.06.2025: Force module reload für Entwicklung
def reload_modules():
    """Lädt kritische Module neu"""
    modules_to_reload = [
        'src.core.orchestrator',
        'src.agents.staged_search',
        'src.core.source_manager',
        'src.agents.factory',
        'src.agents.base_agent'
    ]
    
    for module_name in modules_to_reload:
        if module_name in sys.modules:
            try:
                importlib.reload(sys.modules[module_name])
            except Exception as e:
                # Bei Fehler einfach weitermachen
                st.warning(f"Konnte {module_name} nicht neu laden: {str(e)[:50]}...")

# ÄNDERUNG 18.06.2025: Module Reload temporär deaktiviert wegen Enum-Problemen
# Reload modules wenn in Entwicklungsmodus
# if os.environ.get('DEV_MODE', '').lower() == 'true':
#     try:
#         reload_modules()
#     except Exception as e:
#         # Ignoriere Fehler beim initialen Reload
#         pass

from src.core.config import Config
from src.core.orchestrator import MineSearchOrchestrator
from src.agents.base_agent import MineQuery
from src.data.models import Mine, SearchResultDB, Search
from src.data.exporter import DataExporter
from src.core.cancellation import CancellationToken, CancellationException
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Page config
st.set_page_config(
    page_title="MineSearch - Mining Research System",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 2rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin-bottom: 1rem;
    }
    .result-card {
        background-color: #ffffff;
        padding: 1.5rem;
        border-radius: 0.5rem;
        border: 1px solid #e0e0e0;
        margin-bottom: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'search_results' not in st.session_state:
    st.session_state.search_results = []
if 'search_history' not in st.session_state:
    st.session_state.search_history = []
if 'config' not in st.session_state:
    st.session_state.config = Config()


def init_database():
    """Initialize database connection"""
    engine = create_engine('sqlite:///data/minesearch.db')
    Session = sessionmaker(bind=engine)
    return Session()


async def perform_search(mine_name: str, region: str, country: str, selected_agents: List[str], status_placeholder=None, cancellation_token=None):
    """Perform async search with enhanced queries and status updates"""
    config = st.session_state.config
    
    # Create status callback function
    status_messages = []
    source_discovery_active = False
    discovered_sources = []
    
    def status_callback(message):
        nonlocal source_discovery_active, discovered_sources
        status_messages.append(message)
        
        # ÄNDERUNG 18.06.2025: Erweiterte Source Discovery Erkennung
        if "PHASE 0: QUELLEN-DISCOVERY" in message:
            source_discovery_active = True
        elif "QUELLENSUCHE ABGESCHLOSSEN" in message:
            source_discovery_active = False
        elif source_discovery_active and ("http" in message or ".com" in message or ".org" in message):
            discovered_sources.append(message)
        
        if status_placeholder:
            # Spezielle Anzeige für Source Discovery
            if source_discovery_active:
                with status_placeholder.container():
                    st.markdown("### 🔍 PHASE 0: QUELLEN-DISCOVERY")
                    st.info("Suche nach relevanten Datenquellen für diese Mine...")
                    
                    # Zeige Progress
                    col1, col2 = st.columns([2, 1])
                    with col1:
                        st.markdown("**Status:**")
                        # Zeige letzte Status-Nachrichten
                        recent_messages = [msg for msg in status_messages[-5:] if not msg.strip().startswith("===")]
                        for msg in recent_messages:
                            if "✅" in msg or "📊" in msg:
                                st.success(msg)
                            elif "⚡" in msg or "🤖" in msg:
                                st.info(msg)
                            else:
                                st.write(msg)
                    
                    with col2:
                        st.metric("Gefundene Quellen", len(discovered_sources))
                    
                    # Zeige gefundene Quellen in Expander
                    if discovered_sources:
                        with st.expander(f"📚 Gefundene Quellen ({len(discovered_sources)})", expanded=False):
                            for source in discovered_sources[-10:]:  # Zeige letzte 10
                                st.write(f"• {source}")
            else:
                # Normale Status-Anzeige
                status_text = "\n".join(status_messages[-20:])  # Letzte 20 Nachrichten
                status_placeholder.text(status_text)
    
    # Create orchestrator with status callback
    orchestrator = MineSearchOrchestrator(config, status_callback=status_callback)
    
    # Initialize orchestrator with status update
    if status_placeholder:
        with status_placeholder.container():
            st.info("🔄 Initializing search agents...")
            st.info(f"📡 Connecting to {len(selected_agents)} agents...")
    
    await orchestrator.initialize()
    
    # Create focused query with priority fields
    # Split into essential fields for better results
    query = MineQuery(
        mine_name=mine_name,
        region=region,
        country=country,
        languages=["en", "fr", "es", "de"],  # Multi-language support
        required_fields=[
            # Priority 1: Core identification
            "betreiber", "operator", "owner", "company",
            "koordinaten", "coordinates", "location", "GPS",
            "rohstofftyp", "commodity", "mineral", "resource",
            "aktivitaetsstatus", "status", "operational_status",
            
            # Priority 2: Financial/Environmental (most important for user)
            "sanierungskosten", "remediation_costs", "closure_costs", 
            "rehabilitation", "environmental_liability", "restoration_costs",
            "environmental_bond", "financial_assurance",
            
            # Priority 3: Production timeline
            "production_start", "production_end", "mine_life", "closure_date",
            
            # Priority 4: Technical data
            "mine_type", "annual_production", "capacity",
            "reserves", "resources", "employees"
        ]
    )
    
    # Set active agents using proper method
    orchestrator.set_active_agents(selected_agents)
    
    # Log active agents
    if status_placeholder:
        with status_placeholder.container():
            st.info(f"✅ Active agents set: {len(orchestrator.active_agents)} agents ready")
    
    if status_placeholder:
        with status_placeholder.container():
            st.info(f"🚀 Starting deep search for **{mine_name}** with {len(selected_agents)} agents...")
            st.info("🌐 Searching mining databases, government records, technical reports, news archives...")
            
            # Show which agents are being used
            agent_list = ", ".join(selected_agents[:5])
            if len(selected_agents) > 5:
                agent_list += f" and {len(selected_agents) - 5} more"
            st.info(f"🤖 Active agents: {agent_list}")
    
    # Run staged search for better results
    if status_placeholder:
        with status_placeholder.container():
            st.info("🔍 Starting staged deep search...")
            st.info("📊 Phase 1: Core information (operator, location, commodity)")
            st.info("💰 Phase 2: Financial & environmental data")
            st.info("📈 Phase 3: Production & technical details")
            st.info("⏳ This may take several minutes for thorough results...")
    
    # Use staged search for comprehensive results
    # ÄNDERUNG 18.06.2025: Füge active_agents zu search_params hinzu
    search_params = {
        'timeout': 900,  # 15 minutes for thorough search
        'use_coordinator': True,
        'active_agents': selected_agents  # Explizit aktive Agenten übergeben
    }
    
    # ÄNDERUNG 19.06.2025: Füge Cancellation Token hinzu
    if cancellation_token:
        search_params['cancellation_token'] = cancellation_token
    
    # ÄNDERUNG 19.06.2025: Try-finally für sicheres Cleanup
    try:
        results = await orchestrator.search_mine_staged(query, search_params)
        return results
    finally:
        # Cleanup wird immer ausgeführt, auch bei Fehlern
        await orchestrator.cleanup()


def main():
    """Main app function"""
    
    # Header
    st.markdown('<h1 class="main-header">⛏️ MineSearch</h1>', unsafe_allow_html=True)
    st.markdown('<p style="text-align: center; font-size: 1.2rem;">Multi-Agent Mining Research System</p>', unsafe_allow_html=True)
    
    # Debug: Test if buttons work at all
    if st.checkbox("🐛 Show Debug Tools", value=False):
        col1, col2, col3 = st.columns(3)
        with col1:
            if st.button("Test Button 1"):
                st.success("✅ Test Button 1 works!")
                st.balloons()
        with col2:
            if st.button("Test Button 2"):
                st.info("ℹ️ Test Button 2 works!")
        with col3:
            st.write("**Session State Info:**")
            st.write(f"Search clicked: {st.session_state.get('search_clicked', False)}")
            st.write(f"Has form data: {'form_data' in st.session_state}")
            st.write(f"Mines count: {len(st.session_state.get('mines_to_search', []))}")
            st.write(f"Agents count: {len(st.session_state.get('selected_agents', []))}")
    
    # Sidebar
    with st.sidebar:
        # Version und Status Info mit File-Hash
        version_info = "🔄 Version: 18.06.2025-v3"
        
        # ÄNDERUNG 18.06.2025: Zeige File-Hash für Verifikation
        try:
            orchestrator_path = os.path.join(os.path.dirname(__file__), '..', 'core', 'orchestrator.py')
            with open(orchestrator_path, 'rb') as f:
                file_hash = hashlib.md5(f.read()).hexdigest()[:8]
            version_info += f" (Hash: {file_hash})"
        except:
            pass
        
        st.info(version_info)
        
        # Cache Management
        col1, col2 = st.columns(2)
        with col1:
            if st.button("🧹 Clear Cache", help="Löscht Streamlit Cache"):
                st.cache_data.clear()
                st.cache_resource.clear()
                st.success("✅ Cache gelöscht!")
                st.info("Seite wird neu geladen...")
                st.rerun()
        
        with col2:
            # ÄNDERUNG 18.06.2025: Force Reload temporär deaktiviert
            if st.button("🔄 Force Reload", help="Temporär deaktiviert", disabled=True):
                st.warning("⚠️ Force Reload ist temporär deaktiviert. Bitte nutze restart_with_cleanup.sh")
        
        # Debug Agent Status
        if st.checkbox("🐛 Debug Mode", value=False):
            config = st.session_state.config
            
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
            
            st.write("\n**Agent API Status:**")
            
            # Direkte API-Key Prüfung
            api_status = {
                "Firecrawl": "✅" if config.api.firecrawl_key else "❌",
                "Perplexity": "✅" if config.api.perplexity_key else "❌",
                "Tavily": "✅" if config.api.tavily_key else "❌",
                "OpenRouter": "✅" if config.api.openrouter_key else "❌"
            }
            
            for api, status in api_status.items():
                st.write(f"{status} {api}")
        
        st.markdown("---")
        st.header("🔍 Search Configuration")
        
        # Search mode selection
        search_mode = st.radio(
            "Search Mode",
            ["Manual Entry", "CSV Upload"],
            help="Choose how to specify the mines to search"
        )
        
        mines_to_search = []
        
        if search_mode == "Manual Entry":
            # Input fields
            mine_name = st.text_input("Mine Name", placeholder="e.g., Malartic Mine")
            region = st.text_input("Region/Province", placeholder="e.g., Quebec")
            country = st.text_input("Country", placeholder="e.g., Canada")
            if mine_name and region and country:
                mines_to_search = [{
                    'mine_name': mine_name,
                    'region': region,
                    'country': country
                }]
        
        else:  # CSV Upload
            uploaded_file = st.file_uploader(
                "Upload CSV Template",
                type="csv",
                help="CSV should contain columns: mine_name, region, country"
            )
            
            if uploaded_file is not None:
                try:
                    # Reset file pointer and read with encoding handling
                    uploaded_file.seek(0)
                    
                    # Try different encodings and separators
                    encodings = ['utf-8', 'utf-8-sig', 'latin-1', 'cp1252']
                    separators = [';', ',', '\t', '|']
                    df = None
                    
                    for encoding in encodings:
                        for sep in separators:
                            try:
                                uploaded_file.seek(0)
                                df = pd.read_csv(uploaded_file, encoding=encoding, sep=sep)
                                
                                # Check if parse was successful (more than 1 column)
                                if len(df.columns) > 1:
                                    break
                                    
                            except (UnicodeDecodeError, pd.errors.EmptyDataError):
                                continue
                            except Exception as e:
                                continue
                        
                        if df is not None and len(df.columns) > 1:
                            break
                    
                    if df is None:
                        st.error("Could not read CSV file. Please check the file encoding.")
                        return
                    
                    # Strip whitespace and remove BOM from column names
                    df.columns = df.columns.str.strip()
                    # Remove BOM if present
                    if len(df.columns) > 0:
                        first_col = df.columns[0]
                        if first_col.startswith('\ufeff'):
                            df.columns.values[0] = first_col[1:]
                    
                    
                    # Flexible column mapping
                    column_mapping = {}
                    
                    # Find mine name column (required) - with better detection
                    mine_name_variants = ['mine_name', 'name', 'Mine Name', 'Name', 'Mine', 'mine', 'MINE_NAME', 'NAME']
                    mine_name_col = None
                    
                    # First try exact match
                    for variant in mine_name_variants:
                        if variant in df.columns:
                            mine_name_col = variant
                            column_mapping['mine_name'] = variant
                            break
                    
                    # If not found, try case-insensitive match
                    if not mine_name_col:
                        df_columns_lower = [col.lower() for col in df.columns]
                        for col_idx, col_name in enumerate(df.columns):
                            if col_name.lower() in ['mine_name', 'name', 'mine', 'minename']:
                                mine_name_col = col_name
                                column_mapping['mine_name'] = col_name
                                break
                    
                    if not mine_name_col:
                        st.error(f"CSV must contain a mine name column. Found columns: {', '.join(df.columns)}")
                        st.info("Looking for columns like: 'Name', 'mine_name', 'Mine Name', 'Mine', etc.")
                    else:
                        # Find region column (optional) - with case-insensitive fallback
                        region_variants = ['region', 'Region', 'REGION', 'Province', 'province', 'State', 'state']
                        for variant in region_variants:
                            if variant in df.columns:
                                column_mapping['region'] = variant
                                break
                        
                        # Case-insensitive fallback for region
                        if 'region' not in column_mapping:
                            for col in df.columns:
                                if col.lower() in ['region', 'province', 'state', 'location']:
                                    column_mapping['region'] = col
                                    break
                        
                        # Find country column (optional) - with case-insensitive fallback
                        country_variants = ['country', 'Country', 'COUNTRY', 'Nation', 'nation']
                        for variant in country_variants:
                            if variant in df.columns:
                                column_mapping['country'] = variant
                                break
                        
                        # Case-insensitive fallback for country
                        if 'country' not in column_mapping:
                            for col in df.columns:
                                if col.lower() in ['country', 'nation', 'pays']:
                                    column_mapping['country'] = col
                                    break
                        
                        # Normalize dataframe columns
                        normalized_df = pd.DataFrame()
                        normalized_df['mine_name'] = df[column_mapping['mine_name']]
                        
                        # Add region and country if available, otherwise use defaults
                        if 'region' in column_mapping:
                            normalized_df['region'] = df[column_mapping['region']]
                        else:
                            normalized_df['region'] = 'Unknown'
                            st.info("No region column found. Using 'Unknown' as default.")
                        
                        if 'country' in column_mapping:
                            normalized_df['country'] = df[column_mapping['country']]
                        else:
                            normalized_df['country'] = 'Global'
                            st.info("No country column found. Using 'Global' as default.")
                        
                        # Use normalized dataframe for the rest of the processing
                        df = normalized_df
                        # Show column mapping info
                        detected_info = f"Detected columns: Mine Name='{column_mapping.get('mine_name')}'"
                        if 'region' in column_mapping:
                            detected_info += f", Region='{column_mapping['region']}'"
                        else:
                            detected_info += ", Region='Not found (using default)'"
                        if 'country' in column_mapping:
                            detected_info += f", Country='{column_mapping['country']}'"
                        else:
                            detected_info += ", Country='Not found (using default)'"
                        st.success(detected_info)
                        
                        # Show preview
                        st.write("CSV Preview (normalized):")
                        st.dataframe(df.head(), use_container_width=True)
                        
                        # Mine selection
                        total_mines = len(df)
                        st.write(f"Total mines in CSV: {total_mines}")
                        
                        mine_selection = st.radio(
                            "Select mines to search",
                            ["All mines", "Custom number"]
                        )
                        
                        if mine_selection == "All mines":
                            num_mines = total_mines
                        else:
                            num_mines = st.number_input(
                                "Number of mines to search",
                                min_value=1,
                                max_value=total_mines,
                                value=min(5, total_mines),
                                step=1
                            )
                        
                        # Convert to search list
                        mines_to_search = df.head(num_mines).to_dict('records')
                        
                        # Show selected mines
                        st.write(f"Selected {len(mines_to_search)} mines:")
                        for i, mine in enumerate(mines_to_search, 1):
                            st.text(f"{i}. {mine['mine_name']} - {mine['region']}, {mine['country']}")
                        
                except Exception as e:
                    st.error(f"Error reading CSV: {str(e)}")
        
        # Agent selection
        st.subheader("Select Agents")
        
        # ÄNDERUNG 21.06.2025: Zeige API-Key Status
        st.write("### 🔑 API Status")
        api_status = st.session_state.config.api.validate()
        cols = st.columns(4)
        for idx, (api, is_configured) in enumerate(api_status.items()):
            col = cols[idx % 4]
            with col:
                if is_configured:
                    st.success(f"✅ {api}")
                else:
                    st.error(f"❌ {api}")
        
        # Check if OpenRouter is configured
        has_openrouter = bool(st.session_state.config.api.openrouter_key)
        
        # Base agents
        available_agents = {
            "claude": "Claude (AI Analysis)",
            "gpt4": "GPT-4 (AI Analysis)",
            "perplexity": "Perplexity (Web Search)",
            "scraper": "Basic Web Scraper",
            "tavily": "Tavily (Advanced Search)",
            "exa": "Exa (Semantic Search)",
            "apify": "Apify (Web Scraping)",
            "scrapingbee": "ScrapingBee (JS Rendering)",
            "firecrawl": "Firecrawl (Deep Crawling)",
            "brightdata": "Bright Data (Enterprise)",
        }
        
        # Get availability status
        from src.agents.factory import AgentFactory
        agent_availability = AgentFactory.get_available_agents(st.session_state.config)
        
        # Count all potential agents
        all_agent_count = len(available_agents) + (8 + 8 + 1 if has_openrouter else 0)  # Base + OpenRouter free + premium + thinking
        available_count = len([a for a in available_agents if agent_availability.get(a, False)])
        if has_openrouter:
            available_count += len([k for k in agent_availability.keys() if k.startswith("openrouter_")])
        
        # Show availability info
        st.info(f"✅ {available_count} von {all_agent_count} Agenten verfügbar")
        st.markdown("---")
        
        # Add OpenRouter models if available
        if has_openrouter:
            st.subheader("🌐 OpenRouter Models")
            from src.agents.openrouter_agent import OpenRouterAgent
            
            # Free models
            openrouter_free_models = {
                "openrouter_deepseek-chat": "DeepSeek Chat (Best Free Model) 🆓",
                "openrouter_qwen-2.5-72b-instruct": "Qwen 2.5 72B (Alibaba) 🆓",
                "openrouter_mistral-7b-instruct": "Mistral 7B Instruct 🆓",
                "openrouter_llama-3.2-90b-instruct": "Llama 3.2 90B (Meta) 🆓",  # ÄNDERUNG 21.06.2025: Korrigiert auf existierendes Modell
                "openrouter_gemma-2-27b-it": "Gemma 2 27B (Google) 🆓",
                "openrouter_hermes-3-llama-3.1-70b": "Hermes 3 Llama 70B 🆓",
                "openrouter_gemini-2.0-flash-exp": "Gemini 2.0 Flash (1M context) 🆓"
            }
            
            # Premium models
            openrouter_premium_models = {
                "openrouter_claude-3.5-sonnet-20241022": "Claude 3.5 Sonnet Latest (200k) 💎🆕",
                "openrouter_claude-3-opus": "Claude 3 Opus (Most Powerful) 💎🔥",
                "openrouter_gemini-pro-1.5": "Gemini 1.5 Pro (2M context!) 💎🌟",
                "openrouter_grok-2-1212": "Grok 2 (Real-time search) 💎🔍",
                "openrouter_gpt-4o-2024-11-20": "GPT-4o Latest (Nov 2024) 💎🆕",
                "openrouter_o1": "OpenAI o1 (Advanced Reasoning) 💎🧠",
                "openrouter_o1-preview": "OpenAI o1 Preview 💎",
                "openrouter_llama-3.1-405b-instruct": "Llama 3.1 405B (Largest Open) 💎🦙"
            }
            
            # Add new free thinking model - temporarily disabled due to API issues
            # openrouter_free_models["openrouter_gemini-2.0-flash-thinking-exp-1219"] = "Gemini 2.0 Thinking (Reasoning) 🆓🧠"
        
        # Initialize or migrate session state for agent selection
        if 'selected_agents' in st.session_state:
            # Migration: Convert old list format to new dict format
            if isinstance(st.session_state.selected_agents, list):
                old_list = st.session_state.selected_agents
                st.session_state.selected_agents = {}
                # Set old selections in new format
                for agent_id in old_list:
                    st.session_state.selected_agents[agent_id] = True
                # Set defaults for agents not in old list
                for agent_id in available_agents.keys():
                    if agent_id not in st.session_state.selected_agents:
                        st.session_state.selected_agents[agent_id] = False
                if has_openrouter:
                    for model_id in openrouter_free_models.keys():
                        if model_id not in st.session_state.selected_agents:
                            st.session_state.selected_agents[model_id] = False
                    for model_id in openrouter_premium_models.keys():
                        if model_id not in st.session_state.selected_agents:
                            st.session_state.selected_agents[model_id] = False
        else:
            # Fresh initialization
            st.session_state.selected_agents = {}
            # Set default selections
            for agent_id in available_agents.keys():
                st.session_state.selected_agents[agent_id] = agent_id in ["scraper", "tavily"]
            if has_openrouter:
                for model_id in openrouter_free_models.keys():
                    st.session_state.selected_agents[model_id] = model_id == "openrouter_deepseek-chat"
                for model_id in openrouter_premium_models.keys():
                    st.session_state.selected_agents[model_id] = False
        
        selected_agents = []
        
        # Global selection buttons
        st.write("### 🎯 Schnellauswahl")
        col1, col2, col3, col4 = st.columns(4)
        with col1:
            if st.button("✅ Alle Agenten", key="select_all_global"):
                for agent_id in available_agents.keys():
                    st.session_state.selected_agents[agent_id] = True
                if has_openrouter:
                    for model_id in {**openrouter_free_models, **openrouter_premium_models}.keys():
                        st.session_state.selected_agents[model_id] = True
        with col2:
            if st.button("❌ Keine Agenten", key="deselect_all_global"):
                for key in st.session_state.selected_agents.keys():
                    st.session_state.selected_agents[key] = False
        with col3:
            if st.button("🆓 Nur Kostenlose", key="select_free_only"):
                # Deselect all first
                for key in st.session_state.selected_agents.keys():
                    st.session_state.selected_agents[key] = False
                # Select only free agents
                # ÄNDERUNG 21.06.2025: Nur wirklich kostenlose Agenten (keine API-Keys benötigt)
                free_traditional = ["scraper"]
                for agent_id in available_agents.keys():
                    if agent_id in free_traditional:
                        st.session_state.selected_agents[agent_id] = True
                if has_openrouter:
                    for model_id in openrouter_free_models.keys():
                        st.session_state.selected_agents[model_id] = True
        
        # ÄNDERUNG 21.06.2025: Info über kostenlose Agenten
        st.info("ℹ️ **Hinweis**: Wirklich kostenlos (ohne API-Key) ist nur der Scraper Agent. Alle anderen Agenten benötigen API-Keys.")
        
        st.markdown("---")
        
        # Traditional agents
        st.write("**Traditional Agents:**")
        
        # Bulk selection buttons for traditional agents
        col1, col2, col3 = st.columns([1, 1, 3])
        with col1:
            if st.button("✅ Alle", key="select_all_traditional"):
                for agent_id in available_agents.keys():
                    st.session_state.selected_agents[agent_id] = True
        with col2:
            if st.button("❌ Keine", key="deselect_all_traditional"):
                for agent_id in available_agents.keys():
                    st.session_state.selected_agents[agent_id] = False
        
        # Traditional agent checkboxes
        for agent_id, agent_name in available_agents.items():
            # Update session state when checkbox changes
            checked = st.checkbox(agent_name, 
                                value=st.session_state.selected_agents.get(agent_id, False),
                                key=f"agent_{agent_id}")
            st.session_state.selected_agents[agent_id] = checked
            if checked:
                selected_agents.append(agent_id)
        
        # OpenRouter models
        if has_openrouter:
            st.write("**Free LLM Models via OpenRouter:**")
            
            # Bulk selection buttons for free models
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("✅ Alle", key="select_all_free"):
                    for model_id in openrouter_free_models.keys():
                        st.session_state.selected_agents[model_id] = True
            with col2:
                if st.button("❌ Keine", key="deselect_all_free"):
                    for model_id in openrouter_free_models.keys():
                        st.session_state.selected_agents[model_id] = False
            
            # Free model checkboxes
            for model_id, model_name in openrouter_free_models.items():
                checked = st.checkbox(model_name, 
                                    value=st.session_state.selected_agents.get(model_id, False),
                                    key=f"agent_{model_id}")
                st.session_state.selected_agents[model_id] = checked
                if checked:
                    selected_agents.append(model_id)
            
            st.write("**Premium LLM Models via OpenRouter:**")
            st.caption("💎 These models have usage costs")
            
            # Bulk selection buttons for premium models
            col1, col2, col3 = st.columns([1, 1, 3])
            with col1:
                if st.button("✅ Alle", key="select_all_premium"):
                    for model_id in openrouter_premium_models.keys():
                        st.session_state.selected_agents[model_id] = True
            with col2:
                if st.button("❌ Keine", key="deselect_all_premium"):
                    for model_id in openrouter_premium_models.keys():
                        st.session_state.selected_agents[model_id] = False
            
            # Premium model checkboxes
            for model_id, model_name in openrouter_premium_models.items():
                checked = st.checkbox(model_name, 
                                    value=st.session_state.selected_agents.get(model_id, False),
                                    key=f"agent_{model_id}")
                st.session_state.selected_agents[model_id] = checked
                if checked:
                    selected_agents.append(model_id)
        
        # Live counter for selected agents
        st.markdown("---")
        st.subheader("📊 Ausgewählte Agenten")
        
        # Kategorisierung
        free_agents = []
        premium_agents = []
        
        # Define premium keywords
        premium_keywords = ['premium', 'claude-3.5', 'claude-3-opus', 'gpt-4o', 'o1', 'gemini-pro-1.5', 
                          'grok', 'llama-3.1-405b', 'perplexity_deep', 'premium_mining', 'brightdata']
        
        for agent in selected_agents:
            # Check if agent is premium
            is_premium = False
            for keyword in premium_keywords:
                if keyword in agent.lower():
                    is_premium = True
                    break
            
            # Also check if it's marked with 💎 in the display name
            if agent in available_agents and '💎' in available_agents[agent]:
                is_premium = True
            elif has_openrouter and agent.startswith("openrouter_"):
                # Check if it's in the premium list based on model name
                if any(pm in agent for pm in ['claude-3.5', 'claude-3-opus', 'gemini-pro-1.5', 
                                               'grok', 'gpt-4o', 'o1', 'llama-3.1-405b']):
                    is_premium = True
            
            if is_premium:
                premium_agents.append(agent)
            else:
                free_agents.append(agent)
        
        # Display counters
        col1, col2, col3 = st.columns(3)
        with col1:
            st.metric("Gesamt", len(selected_agents))
        with col2:
            st.metric("Kostenlos", len(free_agents), help="🆓 Keine Kosten")
        with col3:
            st.metric("Kostenpflichtig", len(premium_agents), help="💎 Mit Kosten verbunden")
        
        # Store mines_to_search in session state so it's accessible outside sidebar
        if 'mines_to_search' not in st.session_state:
            st.session_state.mines_to_search = []
        
        # Update session state with current mines - direct assignment
        st.session_state.mines_to_search = mines_to_search
        st.session_state.selected_agents = selected_agents
        
        # Search button using form for better reliability
        with st.form("search_form"):
            st.write("Ready to search?")
            search_submitted = st.form_submit_button("🚀 Start Search", type="primary", use_container_width=True)
            if search_submitted:
                st.session_state.search_clicked = True
                st.session_state.form_data = {
                    'mines': mines_to_search,
                    'agents': selected_agents
                }
        
        # Progress tracking for batch searches
        if 'batch_progress' not in st.session_state:
            st.session_state.batch_progress = 0
    
    # Main content area
    col1, col2 = st.columns([2, 1])
    
    with col1:
        # Search results
        st.header("📊 Search Results")
        
        # Check if search was clicked (from session state)
        if st.session_state.get('search_clicked', False):
            # Debug output
            st.info("🔍 Search button clicked - processing request...")
            
            # Get values from form data if available, otherwise from session state
            if 'form_data' in st.session_state:
                mines_to_search = st.session_state.form_data.get('mines', [])
                selected_agents = st.session_state.form_data.get('agents', [])
            else:
                mines_to_search = st.session_state.get('mines_to_search', [])
                selected_agents = st.session_state.get('selected_agents', [])
            
            # Debug: Show what we have
            with st.expander("Debug Info", expanded=False):
                st.write(f"Mines to search: {len(mines_to_search)}")
                st.write(f"Selected agents: {len(selected_agents)}")
                if mines_to_search:
                    st.write(f"First mine: {mines_to_search[0]}")
                if selected_agents:
                    st.write(f"Agents: {', '.join(selected_agents[:5])}")
            
            if not mines_to_search:
                st.error("❌ Please provide mine information to search!")
                st.info("Enter mine details in the sidebar or upload a CSV file")
            elif not selected_agents:
                st.error("❌ Please select at least one agent!")
                st.info("Select agents in the sidebar")
            else:
                st.success(f"✅ Starting search for {len(mines_to_search)} mine(s) with {len(selected_agents)} agent(s)")
                
                try:
                    # Clear previous results
                    st.session_state.search_results = []
                
                    # ÄNDERUNG 19.06.2025: Erstelle Cancellation Token
                    cancellation_token = CancellationToken(f"search_{datetime.now().timestamp()}")
                    
                    # Container für Abbrechen-Button
                    cancel_container = st.container()
                    with cancel_container:
                        cancel_col1, cancel_col2 = st.columns([3, 1])
                        with cancel_col2:
                            if st.button("🛑 Abbrechen", key="cancel_search", type="secondary"):
                                cancellation_token.cancel("Benutzer hat die Suche abgebrochen")
                                st.warning("⏸️ Suche wird abgebrochen...")
                    
                    # Progress bar for batch searches
                    if len(mines_to_search) > 1:
                        progress_bar = st.progress(0)
                        status_text = st.empty()
                    
                    all_results = []
                    
                    # Search each mine
                    for idx, mine in enumerate(mines_to_search):
                        # Check if cancelled
                        if cancellation_token.is_cancelled():
                            st.warning("🛑 Suche wurde abgebrochen")
                            break
                            
                        mine_name = mine['mine_name']
                        region = mine['region']
                        country = mine['country']
                        
                        if len(mines_to_search) > 1:
                            status_text.text(f"Searching for {mine_name} ({idx+1}/{len(mines_to_search)})...")
                            progress_bar.progress((idx + 1) / len(mines_to_search))
                        else:
                            st.spinner(f"Searching for {mine_name}...")
                        
                        # Create a placeholder for status updates
                        status_container = st.container()
                        
                        # Run async search with status updates
                        with status_container:
                            status_placeholder = st.empty()
                            
                            # Fix async handling
                            try:
                                loop = asyncio.get_event_loop()
                            except RuntimeError:
                                loop = asyncio.new_event_loop()
                                asyncio.set_event_loop(loop)
                            
                            try:
                                results = loop.run_until_complete(
                                    perform_search(mine_name, region, country, selected_agents, status_placeholder, cancellation_token)
                                )
                            except CancellationException:
                                # Abbruch wurde angefordert
                                st.warning(f"🛑 Suche für {mine_name} wurde abgebrochen")
                                break  # Beende die Schleife
                        
                        # Keep status updates visible, don't clear them!
                        
                        # Store results with mine info
                        for result in results:
                            result.mine_name = mine_name
                            result.region = region
                            result.country = country
                        
                        all_results.extend(results)
                        
                        # ÄNDERUNG 21.06.2025: Debug-Ausgabe für gefundene Ergebnisse
                        if results:
                            st.success(f"✅ {mine_name}: {len(results)} Ergebnisse gefunden")
                        else:
                            st.warning(f"❌ {mine_name}: Keine Ergebnisse gefunden")
                        
                        # Add to history
                        st.session_state.search_history.append({
                            'mine_name': mine_name,
                            'region': region,
                            'country': country,
                            'timestamp': datetime.now(),
                            'results_count': len(results)
                        })
                    
                    st.session_state.search_results = all_results
                    
                    if len(mines_to_search) > 1:
                        progress_bar.empty()
                        status_text.empty()
                    
                    # Verstecke Abbrechen-Button nach Abschluss
                    cancel_container.empty()
                    
                    if cancellation_token.is_cancelled():
                        st.warning(f"🛑 Suche wurde abgebrochen. {len(all_results)} Ergebnisse bis zum Abbruch gefunden.")
                    else:
                        st.success(f"Search complete! Found {len(all_results)} total results for {len(mines_to_search)} mine(s).")
                    
                except Exception as e:
                    st.error(f"❌ Error during search: {type(e).__name__}: {str(e)}")
                    st.exception(e)
                finally:
                    # Reset search clicked state
                    st.session_state.search_clicked = False
                    # Verstecke Abbrechen-Button
                    if 'cancel_container' in locals():
                        cancel_container.empty()
                    # ÄNDERUNG 21.06.2025: Cleanup Cancellation Token
                    if cancellation_token:
                        cancellation_token.cleanup()
        
        # Display results
        if st.session_state.search_results:
            # Mining Information Table
            st.subheader("⛏️ Mining Information Summary")
            
            # Create structured mining data
            mining_data = {}
            for result in st.session_state.search_results:
                mine_key = getattr(result, 'mine_name', 'Unknown')
                if mine_key not in mining_data:
                    mining_data[mine_key] = {
                        'Mine Name': mine_key,
                        'Region': getattr(result, 'region', 'Unknown'),
                        'Country': getattr(result, 'country', 'Unknown'),
                        'Betreiber/Operator': '',
                        'Koordinaten/Coordinates': '',
                        'Rohstofftyp/Commodity': '',
                        'Aktivitaetsstatus/Status': '',
                        'Sanierungskosten/Remediation': '',
                        'Production Start': '',
                        'Production End': '',
                        'Mine Type': '',
                        'Annual Production': '',
                        'Employees': '',
                        'Website': '',
                        'Sources': set()
                    }
                
                # Map fields to structured data
                field_lower = result.field_name.lower()
                value = result.value
                
                if any(term in field_lower for term in ['betreiber', 'operator', 'owner', 'company']):
                    if not mining_data[mine_key]['Betreiber/Operator']:
                        mining_data[mine_key]['Betreiber/Operator'] = value
                elif any(term in field_lower for term in ['koordinaten', 'coordinates', 'location', 'gps']):
                    if not mining_data[mine_key]['Koordinaten/Coordinates']:
                        mining_data[mine_key]['Koordinaten/Coordinates'] = value
                elif any(term in field_lower for term in ['rohstoff', 'commodity', 'mineral', 'resource']):
                    if not mining_data[mine_key]['Rohstofftyp/Commodity']:
                        mining_data[mine_key]['Rohstofftyp/Commodity'] = value
                elif any(term in field_lower for term in ['status', 'aktivitaet', 'operational']):
                    if not mining_data[mine_key]['Aktivitaetsstatus/Status']:
                        mining_data[mine_key]['Aktivitaetsstatus/Status'] = value
                elif any(term in field_lower for term in ['sanierung', 'remediation', 'closure', 'rehabilitation']):
                    if not mining_data[mine_key]['Sanierungskosten/Remediation']:
                        mining_data[mine_key]['Sanierungskosten/Remediation'] = value
                elif any(term in field_lower for term in ['production_start', 'start', 'began']):
                    if not mining_data[mine_key]['Production Start']:
                        mining_data[mine_key]['Production Start'] = value
                elif any(term in field_lower for term in ['production_end', 'closure_date', 'ended']):
                    if not mining_data[mine_key]['Production End']:
                        mining_data[mine_key]['Production End'] = value
                elif any(term in field_lower for term in ['mine_type', 'type', 'open_pit', 'underground']):
                    if not mining_data[mine_key]['Mine Type']:
                        mining_data[mine_key]['Mine Type'] = value
                elif any(term in field_lower for term in ['annual_production', 'production', 'capacity']):
                    if not mining_data[mine_key]['Annual Production']:
                        mining_data[mine_key]['Annual Production'] = value
                elif any(term in field_lower for term in ['employees', 'workforce', 'jobs']):
                    if not mining_data[mine_key]['Employees']:
                        mining_data[mine_key]['Employees'] = value
                elif any(term in field_lower for term in ['website', 'web', 'url']):
                    if not mining_data[mine_key]['Website']:
                        mining_data[mine_key]['Website'] = value
                
                # Add source
                mining_data[mine_key]['Sources'].add(result.agent_name)
            
            # Convert to dataframe and fill empty fields
            mining_df_data = []
            for mine_data in mining_data.values():
                mine_data['Sources'] = ', '.join(mine_data['Sources']) if mine_data['Sources'] else 'No sources'
                
                # Fill empty fields with "No information found"
                for key in mine_data:
                    if key not in ['Mine Name', 'Region', 'Country', 'Sources'] and not mine_data[key]:
                        mine_data[key] = 'No information found'
                
                mining_df_data.append(mine_data)
            
            mining_df = pd.DataFrame(mining_df_data)
            
            # Display mining information table
            st.dataframe(
                mining_df,
                use_container_width=True,
                height=300,
                column_config={
                    "Website": st.column_config.LinkColumn("Website")
                }
            )
            
            # Download mining data
            csv_mining = mining_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Mining Data as CSV",
                data=csv_mining,
                file_name=f"mining_data_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            st.divider()
            
            # Raw results table
            st.subheader("📋 Detailed Search Results")
            
            # Create dataframe from results
            results_data = []
            for result in st.session_state.search_results:
                results_data.append({
                    'Mine': getattr(result, 'mine_name', 'Unknown'),
                    'Field': result.field_name,
                    'Value': result.value[:100] + '...' if len(result.value) > 100 else result.value,
                    'Source': result.source,
                    'Agent': result.agent_name,
                    'Confidence': f"{result.confidence_score:.2f}",
                    'URL': result.source_url if result.source_url else 'N/A'
                })
            
            results_df = pd.DataFrame(results_data)
            
            # Add filters
            col1, col2, col3 = st.columns(3)
            with col1:
                agent_filter = st.multiselect(
                    "Filter by Agent",
                    options=results_df['Agent'].unique() if len(results_df) > 0 else [],
                    default=results_df['Agent'].unique() if len(results_df) > 0 else []
                )
            with col2:
                field_filter = st.multiselect(
                    "Filter by Field",
                    options=results_df['Field'].unique() if len(results_df) > 0 else [],
                    default=results_df['Field'].unique() if len(results_df) > 0 else []
                )
            with col3:
                confidence_threshold = st.slider(
                    "Minimum Confidence",
                    min_value=0.0,
                    max_value=1.0,
                    value=0.0,
                    step=0.1
                )
            
            # Apply filters
            filtered_df = results_df
            if agent_filter:
                filtered_df = filtered_df[filtered_df['Agent'].isin(agent_filter)]
            if field_filter:
                filtered_df = filtered_df[filtered_df['Field'].isin(field_filter)]
            if confidence_threshold > 0:
                filtered_df = filtered_df[filtered_df['Confidence'].astype(float) >= confidence_threshold]
            
            # Display filtered table
            st.dataframe(
                filtered_df,
                use_container_width=True,
                height=400,
                column_config={
                    "URL": st.column_config.LinkColumn("Source URL"),
                    "Confidence": st.column_config.NumberColumn(
                        "Confidence",
                        format="%.2f",
                        min_value=0,
                        max_value=1,
                    ),
                }
            )
            
            # Download filtered results
            csv = filtered_df.to_csv(index=False)
            st.download_button(
                label="💾 Download Detailed Results as CSV",
                data=csv,
                file_name=f"mining_results_detailed_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv",
                mime="text/csv"
            )
            
            # Show agent distribution
            st.info(f"🤖 Results from agents: {', '.join(filtered_df['Agent'].unique())}")
            
            st.divider()
            # Filter options for batch results
            if len(set(r.mine_name for r in st.session_state.search_results if hasattr(r, 'mine_name'))) > 1:
                unique_mines = sorted(set(r.mine_name for r in st.session_state.search_results if hasattr(r, 'mine_name')))
                selected_mine_filter = st.selectbox(
                    "Filter by mine",
                    ["All mines"] + unique_mines
                )
                
                if selected_mine_filter != "All mines":
                    filtered_results = [r for r in st.session_state.search_results if hasattr(r, 'mine_name') and r.mine_name == selected_mine_filter]
                else:
                    filtered_results = st.session_state.search_results
            else:
                filtered_results = st.session_state.search_results
            
            # Group results by mine and field
            mine_groups = {}
            for result in filtered_results:
                mine_key = getattr(result, 'mine_name', 'Unknown Mine')
                if mine_key not in mine_groups:
                    mine_groups[mine_key] = {}
                
                field = result.field_name
                if field not in mine_groups[mine_key]:
                    mine_groups[mine_key][field] = []
                mine_groups[mine_key][field].append(result)
            
            # Display by mine and field
            for mine_name, field_groups in mine_groups.items():
                if len(mine_groups) > 1:
                    st.subheader(f"🏔️ {mine_name}")
                
                for field, results in field_groups.items():
                    with st.expander(f"**{field.replace('_', ' ').title()}** ({len(results)} results)", expanded=True):
                        for result in results:
                            st.markdown(f"""
                            <div class="result-card">
                                <h4>{result.value}</h4>
                                <p><strong>Source:</strong> {result.source}</p>
                                <p><strong>Confidence:</strong> {result.confidence_score:.2f}</p>
                                <p><strong>Agent:</strong> {result.agent_name}</p>
                                {f'<p><strong>URL:</strong> <a href="{result.source_url}">{result.source_url}</a></p>' if result.source_url else ''}
                            </div>
                            """, unsafe_allow_html=True)
    
    with col2:
        # Statistics
        st.header("📈 Statistics")
        
        if st.session_state.search_results:
            # Metrics
            st.metric("Total Results", len(st.session_state.search_results))
            unique_fields = set()
            for mine_data in mine_groups.values():
                unique_fields.update(mine_data.keys())
            st.metric("Unique Fields", len(unique_fields))
            st.metric("Mines Searched", len(mine_groups))
            
            # Agent performance with all agents shown
            agent_counts = {}
            agent_confidence = {}
            for result in st.session_state.search_results:
                agent = result.agent_name
                if agent not in agent_counts:
                    agent_counts[agent] = 0
                    agent_confidence[agent] = []
                agent_counts[agent] += 1
                agent_confidence[agent].append(result.confidence_score)
            
            # Show agent summary
            st.subheader("🤖 Agent Performance")
            agent_summary = []
            for agent, count in agent_counts.items():
                avg_conf = sum(agent_confidence[agent]) / len(agent_confidence[agent])
                agent_summary.append({
                    'Agent': agent,
                    'Results': count,
                    'Avg Confidence': f"{avg_conf:.2f}"
                })
            
            agent_df = pd.DataFrame(agent_summary)
            agent_df = agent_df.sort_values('Results', ascending=False)
            st.dataframe(agent_df, use_container_width=True)
            
            # Create agent performance chart
            fig = go.Figure()
            agents = list(agent_counts.keys())
            counts = list(agent_counts.values())
            avg_confidence = [sum(agent_confidence[a])/len(agent_confidence[a]) for a in agents]
            
            fig.add_trace(go.Bar(
                x=agents,
                y=counts,
                name='Results Found',
                marker_color='lightblue'
            ))
            
            fig.update_layout(
                title="Agent Performance",
                xaxis_title="Agent",
                yaxis_title="Number of Results",
                showlegend=False,
                height=300
            )
            st.plotly_chart(fig, use_container_width=True)
            
            # Field coverage visualization
            st.subheader("📈 Field Coverage")
            field_counts = {}
            for result in st.session_state.search_results:
                field = result.field_name
                if field not in field_counts:
                    field_counts[field] = 0
                field_counts[field] += 1
            
            if field_counts:
                fig_fields = px.bar(
                    x=list(field_counts.values()),
                    y=list(field_counts.keys()),
                    orientation='h',
                    title="Results by Field",
                    labels={'x': 'Number of Results', 'y': 'Field'}
                )
                fig_fields.update_layout(height=400)
                st.plotly_chart(fig_fields, use_container_width=True)
            
            # Confidence distribution
            all_confidence = [r.confidence_score for r in st.session_state.search_results]
            fig2 = px.histogram(
                all_confidence,
                nbins=20,
                title="Confidence Score Distribution",
                labels={'value': 'Confidence Score', 'count': 'Count'}
            )
            fig2.update_layout(height=300)
            st.plotly_chart(fig2, use_container_width=True)
        
        # Export options
        st.header("💾 Export")
        if st.session_state.search_results:
            export_format = st.selectbox("Format", ["JSON", "CSV", "Excel"])
            
            if st.button("Export Results", use_container_width=True):
                exporter = DataExporter()
                
                # Convert results to dict
                results_dict = []
                for r in st.session_state.search_results:
                    r_dict = r.to_dict()
                    # Add mine info if available
                    if hasattr(r, 'mine_name'):
                        r_dict['mine_name'] = r.mine_name
                        r_dict['region'] = r.region
                        r_dict['country'] = r.country
                    results_dict.append(r_dict)
                
                # Generate filename
                if len(mine_groups) == 1:
                    base_name = list(mine_groups.keys())[0].replace(' ', '_')
                else:
                    base_name = f"batch_search_{len(mine_groups)}_mines"
                
                if export_format == "JSON":
                    file_path = f"data/output/{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json"
                    exporter.export_to_json(results_dict, file_path)
                    st.success(f"Exported to {file_path}")
                
                elif export_format == "CSV":
                    file_path = f"data/output/{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
                    exporter.export_to_csv(results_dict, file_path)
                    st.success(f"Exported to {file_path}")
                
                elif export_format == "Excel":
                    file_path = f"data/output/{base_name}_{datetime.now().strftime('%Y%m%d_%H%M%S')}.xlsx"
                    exporter.export_to_excel(results_dict, file_path)
                    st.success(f"Exported to {file_path}")
    
    # Search history with enhanced table
    with st.expander("🕐 Search History", expanded=True):
        if st.session_state.search_history:
            # Create enhanced history dataframe
            history_data = []
            for entry in st.session_state.search_history:
                history_data.append({
                    'Mine': entry['mine_name'],
                    'Region': entry['region'],
                    'Country': entry['country'],
                    'Time': entry['timestamp'].strftime('%Y-%m-%d %H:%M'),
                    'Results': entry['results_count'],
                    'Status': '✅ Found' if entry['results_count'] > 0 else '❌ No Results'
                })
            
            history_df = pd.DataFrame(history_data)
            
            # Style the dataframe
            def style_results(val):
                if isinstance(val, str):
                    if '✅' in val:
                        return 'color: green; font-weight: bold'
                    elif '❌' in val:
                        return 'color: red; font-weight: bold'
                elif isinstance(val, int) and val > 0:
                    return 'color: green; font-weight: bold'
                elif isinstance(val, int) and val == 0:
                    return 'color: red'
                return ''
            
            styled_df = history_df.style.applymap(style_results, subset=['Results', 'Status'])
            st.dataframe(styled_df, use_container_width=True, height=300)
            
            # Summary statistics
            col1, col2, col3, col4 = st.columns(4)
            with col1:
                st.metric("Total Searches", len(history_df))
            with col2:
                successful = len(history_df[history_df['Results'] > 0])
                st.metric("Successful", successful)
            with col3:
                st.metric("No Results", len(history_df) - successful)
            with col4:
                total_results = history_df['Results'].sum()
                st.metric("Total Results", total_results)
        else:
            st.info("No search history yet.")


if __name__ == "__main__":
    main()