"""
Author: rahn
Datum: 27.06.2025
Version: 2.2
Beschreibung: Bereinigte MineSearch UI ohne problematisches CSS
"""

import streamlit as st
import sys
import os
from datetime import datetime

# ÄNDERUNG 27.06.2025: Page Config MUSS als erstes kommen
st.set_page_config(
    page_title="MineSearch - Mining Research System",
    page_icon="⛏️",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Imports mit Fehlerbehandlung
try:
    import nest_asyncio
    nest_asyncio.apply()
    
    from src.utils.session_manager import SessionManager
    from src.core.config import Config
    from src.ui.cleanup_handler import cleanup_on_app_start
    
    # Cleanup beim Start
    try:
        cleanup_on_app_start()
    except:
        pass
    
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
    IMPORT_ERROR = None
except Exception as e:
    IMPORTS_SUCCESS = False
    IMPORT_ERROR = str(e)


def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'search_results': [],
        'search_history': [],
        'search_in_progress': False,
        'error_details': None,
        'status_updates': [],
        'search_error': None,
        'cancellation_token': None
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# Singleton Pattern für Ressourcen
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
    # Prüfe Import-Erfolg
    if not IMPORTS_SUCCESS:
        st.error(f"❌ Fehler beim Laden der Komponenten: {IMPORT_ERROR}")
        st.info("Bitte prüfen Sie die Installation und starten Sie die Anwendung neu.")
        import traceback
        with st.expander("Fehlerdetails"):
            st.code(traceback.format_exc())
        st.stop()
    
    # Initialize session state
    initialize_session_state()
    
    # Header ohne Custom CSS
    st.title("⛏️ MineSearch")
    st.markdown("**Multi-Agent Mining Research System**")
    
    # Navigation
    navigation = st.selectbox(
        "Navigation",
        ["Suche", "Ergebnis-Historie"],
        index=0,
        label_visibility="collapsed"
    )
    
    if navigation == "Ergebnis-Historie":
        # Zeige Historie-Seite
        try:
            db = get_database_manager()
            history_page = ResultHistoryPage(db)
            history_page.render()
        except Exception as e:
            st.error(f"Fehler beim Laden der Historie: {e}")
        return
    
    # Initialize components mit Fehlerbehandlung
    try:
        config = get_config()
        session_manager = get_session_manager()
        sidebar = SidebarComponent(config)
        search_form = SearchFormComponent(config, session_manager)
        results_display = ResultsDisplayComponent()
        metrics_dashboard = MetricsDashboardComponent()
    except Exception as e:
        st.error(f"Fehler beim Initialisieren der Komponenten: {e}")
        st.stop()
    
    # Render sidebar
    try:
        sidebar_config = sidebar.render()
    except Exception as e:
        st.error(f"Fehler beim Rendern der Sidebar: {e}")
        sidebar_config = {
            'mines_to_search': [],
            'selected_agents': [],
            'advanced_options': {}
        }
    
    # Main content area
    if sidebar_config['mines_to_search']:
        st.info(f"Bereit zur Suche: {len(sidebar_config['mines_to_search'])} Mine(n) "
                f"mit {len(sidebar_config['selected_agents'])} Agent(en)")
    
    # Search form
    try:
        search_results = search_form.render(
            mines_to_search=sidebar_config['mines_to_search'],
            selected_agents=sidebar_config['selected_agents'],
            advanced_options=sidebar_config['advanced_options']
        )
        
        # Update results if new search completed
        if search_results:
            st.session_state.search_results = search_results
            st.session_state.search_history.append({
                'timestamp': datetime.now(),
                'mine_count': len(sidebar_config['mines_to_search']),
                'agent_count': len(sidebar_config['selected_agents']),
                'result_count': len(search_results)
            })
    except Exception as e:
        st.error(f"Fehler beim Suchen: {e}")
    
    # Display results
    if st.session_state.search_results:
        st.divider()
        try:
            results_display.render(st.session_state.search_results)
        except Exception as e:
            st.error(f"Fehler beim Anzeigen der Ergebnisse: {e}")
        
        # Metrics section
        st.divider()
        try:
            metrics_dashboard.render(
                st.session_state.search_results,
                st.session_state.search_history
            )
        except Exception as e:
            st.error(f"Fehler beim Anzeigen der Metriken: {e}")
    
    # Footer
    st.divider()
    st.caption(f"MineSearch v2.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")


if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        st.error(f"❌ Kritischer Fehler: {str(e)}")
        st.error("Bitte laden Sie die Seite neu (F5) oder starten Sie die Anwendung neu.")
        import traceback
        with st.expander("Vollständige Fehlerdetails"):
            st.code(traceback.format_exc())