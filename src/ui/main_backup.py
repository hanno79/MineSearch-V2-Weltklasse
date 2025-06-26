"""
Author: rahn
Datum: 23.06.2025
Version: 2.1
Beschreibung: Refactored MineSearch Streamlit UI - Hauptdatei
ÄNDERUNG 23.06.2025: nest_asyncio für Event Loop Kompatibilität
# ÄNDERUNG 27.06.2025: Absolute Importe für Streamlit-Kompatibilität
"""
import streamlit as st
import sys
import os
from datetime import datetime
import nest_asyncio
from src.utils.session_manager import SessionManager
from src.core.config import Config

# ÄNDERUNG 23.06.2025: Aktiviere nested event loops für Streamlit
nest_asyncio.apply()

# ÄNDERUNG 27.06.2025: Cleanup beim Start
try:
    from src.ui.cleanup_handler import cleanup_on_app_start
    cleanup_on_app_start()
except:
    pass  # Ignoriere Fehler beim Cleanup

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# ÄNDERUNG 27.06.2025: Fehlerbehandlung für Importe
try:
    # Import components
    from src.ui.components.sidebar import SidebarComponent
    from src.ui.components.search_form import SearchFormComponent
    from src.ui.components.results_display import ResultsDisplayComponent
    from src.ui.components.metrics_dashboard import MetricsDashboardComponent
    from src.ui.components.search_progress import SearchProgressComponent
    
    # Import pages
    from src.ui.pages.result_history import ResultHistoryPage
    from src.core.database import DatabaseManager
    
    IMPORTS_SUCCESS = True
except ImportError as e:
    IMPORTS_SUCCESS = False
    IMPORT_ERROR = str(e)

# Page configuration
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
    .sub-header {
        text-align: center;
        font-size: 1.2rem;
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
    /* Prevent connection timeout */
    .stApp {
        max-width: 100%;
    }
</style>
""", unsafe_allow_html=True)


def initialize_session_state():
    """Initialize session state variables"""
    if 'search_results' not in st.session_state:
        st.session_state.search_results = []
    if 'search_history' not in st.session_state:
        st.session_state.search_history = []
    if 'search_in_progress' not in st.session_state:
        st.session_state.search_in_progress = False
    # ÄNDERUNG 26.06.2025: Fix für fehlende Session State Variablen
    if 'error_details' not in st.session_state:
        st.session_state.error_details = None
    if 'status_updates' not in st.session_state:
        st.session_state.status_updates = []
    if 'search_error' not in st.session_state:
        st.session_state.search_error = None
    if 'cancellation_token' not in st.session_state:
        st.session_state.cancellation_token = None


# ÄNDERUNG 27.06.2025: Singleton Pattern für Config und DatabaseManager
@st.cache_resource
def get_config():
    """Gibt die globale Config Instanz zurück"""
    return Config()


@st.cache_resource
def get_database_manager():
    """Gibt die globale DatabaseManager Instanz zurück"""
    db = DatabaseManager()
    db.initialize()
    return db


@st.cache_resource
def get_session_manager():
    """Gibt die globale SessionManager Instanz zurück"""
    return SessionManager()


def main():
    """Main application function"""
    # ÄNDERUNG 27.06.2025: Prüfe Import-Erfolg
    if not IMPORTS_SUCCESS:
        st.error(f"❌ Fehler beim Laden der Komponenten: {IMPORT_ERROR}")
        st.info("Bitte prüfen Sie die Installation und starten Sie die Anwendung neu.")
        st.stop()
    
    # Initialize session state
    initialize_session_state()
    
    # Header
    st.markdown('<h1 class="main-header">⛏️ MineSearch</h1>', unsafe_allow_html=True)
    st.markdown('<p class="sub-header">Multi-Agent Mining Research System</p>', 
                unsafe_allow_html=True)
    
    # ÄNDERUNG 26.06.2025: Navigation zwischen Seiten
    navigation = st.selectbox(
        "Navigation",
        ["Suche", "Ergebnis-Historie"],
        index=0,
        label_visibility="collapsed"
    )
    
    if navigation == "Ergebnis-Historie":
        # Zeige Historie-Seite
        db = get_database_manager()  # ÄNDERUNG: Verwende Singleton
        history_page = ResultHistoryPage(db)
        history_page.render()
        return
    
    # Initialize components (create fresh instances, don't store in session_state)
    config = get_config()  # ÄNDERUNG: Verwende Singleton
    session_manager = get_session_manager()  # ÄNDERUNG: Verwende Singleton
    sidebar = SidebarComponent(config)
    search_form = SearchFormComponent(config, session_manager)
    results_display = ResultsDisplayComponent()
    metrics_dashboard = MetricsDashboardComponent()
    
    # Render sidebar and get configuration
    sidebar_config = sidebar.render()
    
    # Main content area
    if sidebar_config['mines_to_search']:
        # Show search info
        st.info(f"Ready to search {len(sidebar_config['mines_to_search'])} mine(s) "
                f"with {len(sidebar_config['selected_agents'])} agent(s)")
    
    # Search form
    search_results = search_form.render(
        mines_to_search=sidebar_config['mines_to_search'],
        selected_agents=sidebar_config['selected_agents'],
        advanced_options=sidebar_config['advanced_options']
    )
    
    # Update results if new search completed
    if search_results:
        st.session_state.search_results = search_results
        
        # Add to search history
        st.session_state.search_history.append({
            'timestamp': datetime.now(),
            'mine_count': len(sidebar_config['mines_to_search']),
            'agent_count': len(sidebar_config['selected_agents']),
            'result_count': len(search_results)
        })
    
    # Display results
    if st.session_state.search_results:
        # Results section
        st.markdown("---")
        results_display.render(st.session_state.search_results)
        
        # Metrics section
        st.markdown("---")
        metrics_dashboard.render(
            st.session_state.search_results,
            st.session_state.search_history
        )
    
    # Footer
    st.markdown("---")
    st.caption("MineSearch v2.0 - Refactored Edition | "
               f"Last update: {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    # ÄNDERUNG 27.06.2025: Robuste Main-Ausführung
    try:
        # Run main app
        main()
    except Exception as e:
        st.error(f"❌ Kritischer Fehler: {str(e)}")
        st.error("Bitte laden Sie die Seite neu (F5) oder starten Sie die Anwendung neu.")
        import traceback
        with st.expander("Fehlerdetails"):
            st.code(traceback.format_exc())