"""
Author: rahn
Datum: 27.06.2025
Version: 3.0
Beschreibung: Finale stabile MineSearch UI
"""

import streamlit as st
import sys
import os
from datetime import datetime

# WICHTIG: Page Config MUSS als erstes kommen
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

# ÄNDERUNG 26.06.2025: Global Cancellation Registry für F5-Refresh Handling
from src.core.global_cancellation_registry import register_streamlit_cleanup
register_streamlit_cleanup()

# Imports - OHNE nest_asyncio und cleanup_handler
try:
    from src.utils.session_manager import SessionManager
    from src.core.config import Config
    from src.core.database import DatabaseManager
    
    # Import components
    from src.ui.components.sidebar import SidebarComponent
    from src.ui.components.search_form import SearchFormComponent
    from src.ui.components.results_display import ResultsDisplayComponent
    from src.ui.components.metrics_dashboard import MetricsDashboardComponent
    from src.ui.components.search_progress import SearchProgressComponent
    
    # Import pages
    from src.ui.pages.result_history import ResultHistoryPage
    from src.ui.pages.database_viewer import DatabaseViewerPage
    
    IMPORTS_SUCCESS = True
    IMPORT_ERROR = None
except Exception as e:
    IMPORTS_SUCCESS = False
    IMPORT_ERROR = str(e)
    import traceback
    IMPORT_TRACEBACK = traceback.format_exc()


def initialize_session_state():
    """Initialize session state variables"""
    defaults = {
        'search_results': [],
        'search_history': [],
        'search_in_progress': False,
        'error_details': None,
        'status_updates': [],
        'search_error': None,
        'cancellation_token': None,
        'initialized': True,
        'live_progress': {},
        'mine_search_completed': False,
        'current_search_mine': None,
        'active_search_task': None,  # ÄNDERUNG: Track active task
        'search_id': None,  # ÄNDERUNG: Track search ID
        '_page_refresh': True  # ÄNDERUNG 27.06.2025: Page Refresh Detection
    }
    
    for key, default_value in defaults.items():
        if key not in st.session_state:
            st.session_state[key] = default_value


# Cache-Funktionen OHNE automatische Initialisierung
@st.cache_resource
def get_config():
    """Gibt die globale Config Instanz zurück"""
    return Config()


@st.cache_resource
def get_session_manager():
    """Gibt die globale SessionManager Instanz zurück"""
    return SessionManager()


@st.cache_resource
def get_database_manager():
    """Gibt die globale DatabaseManager Instanz zurück"""
    # Initialisierung erfolgt lazy in main()
    return DatabaseManager()


def render_error_page(error_msg, traceback_msg=None):
    """Zeigt eine Fehlerseite an"""
    st.error("❌ MineSearch konnte nicht geladen werden")
    st.error(f"Fehler: {error_msg}")
    
    if traceback_msg:
        with st.expander("Technische Details"):
            st.code(traceback_msg)
    
    st.info("Mögliche Lösungen:")
    st.write("1. Seite neu laden (F5)")
    st.write("2. Browser-Cache leeren")
    st.write("3. Anwendung neu starten")
    
    if st.button("🔄 Seite neu laden"):
        st.rerun()


def main():
    """Main application function"""
    # Initialize session state als erstes
    initialize_session_state()
    
    # ÄNDERUNG 27.06.2025: Cancel alle aktiven Suchen bei Page Refresh
    # Dies stoppt Token-Verbrauch bei F5
    try:
        from src.core.global_cancellation_registry import get_global_cancellation_registry
        registry = get_global_cancellation_registry()
        
        # Bei erstem Seitenaufruf oder Refresh
        if st.session_state.get('_page_refresh', True):
            active_count = registry.get_active_searches_count()
            if active_count > 0:
                registry.cancel_all("Page refresh detected - stopping all searches")
                st.info(f"🛑 {active_count} aktive Suche(n) wurden gestoppt")
            st.session_state._page_refresh = False
    except Exception as e:
        # Silent fail - don't break app startup
        pass
    
    # Prüfe Import-Erfolg
    if not IMPORTS_SUCCESS:
        render_error_page(IMPORT_ERROR, IMPORT_TRACEBACK)
        return
    
    # Header
    st.title("⛏️ MineSearch")
    st.markdown("**Multi-Agent Mining Research System**")
    
    # Navigation
    col1, col2, col3 = st.columns([2, 6, 2])
    with col2:
        navigation = st.selectbox(
            "Navigation",
            ["🔍 Suche", "📊 Ergebnis-Historie", "🗄️ Datenbank"],
            index=0,
            label_visibility="collapsed"
        )
    
    # Historie-Seite
    if navigation == "📊 Ergebnis-Historie":
        try:
            db = get_database_manager()
            # Lazy initialization
            if not hasattr(db, '_initialized'):
                with st.spinner("Initialisiere Datenbank..."):
                    db.initialize()
                    db._initialized = True
                    
            history_page = ResultHistoryPage(db)
            history_page.render()
        except Exception as e:
            st.error(f"Fehler beim Laden der Historie: {e}")
        return
    
    # Datenbank-Viewer Seite
    elif navigation == "🗄️ Datenbank":
        try:
            db = get_database_manager()
            # Lazy initialization
            if not hasattr(db, '_initialized'):
                with st.spinner("Initialisiere Datenbank..."):
                    db.initialize()
                    db._initialized = True
                    
            viewer_page = DatabaseViewerPage(db)
            viewer_page.render()
        except Exception as e:
            st.error(f"Fehler beim Laden des Datenbank-Viewers: {e}")
        return
    
    # Hauptseite - Suche
    try:
        # Komponenten initialisieren
        config = get_config()
        session_manager = get_session_manager()
        
        # Lazy DB initialization
        db = get_database_manager()
        if not hasattr(db, '_initialized'):
            with st.spinner("Initialisiere Datenbank..."):
                db.initialize()
                db._initialized = True
        
        # UI Komponenten
        sidebar = SidebarComponent(config)
        search_form = SearchFormComponent(config, session_manager)
        results_display = ResultsDisplayComponent()
        metrics_dashboard = MetricsDashboardComponent()
        
    except Exception as e:
        render_error_page(f"Fehler beim Initialisieren: {e}")
        return
    
    # Sidebar rendern
    try:
        sidebar_config = sidebar.render()
    except Exception as e:
        st.error(f"Fehler in der Sidebar: {e}")
        sidebar_config = {
            'mines_to_search': [],
            'selected_agents': [],
            'advanced_options': {}
        }
    
    # Hauptbereich
    if sidebar_config['mines_to_search']:
        st.info(f"📍 Bereit zur Suche: **{len(sidebar_config['mines_to_search'])}** Mine(n) "
                f"mit **{len(sidebar_config['selected_agents'])}** Agent(en)")
    else:
        st.info("👈 Bitte wählen Sie mindestens eine Mine in der Sidebar aus")
    
    # Such-Formular
    try:
        search_results = search_form.render(
            mines_to_search=sidebar_config['mines_to_search'],
            selected_agents=sidebar_config['selected_agents'],
            advanced_options=sidebar_config['advanced_options']
        )
        
        if search_results:
            st.session_state.search_results = search_results
            st.session_state.search_history.append({
                'timestamp': datetime.now(),
                'mine_count': len(sidebar_config['mines_to_search']),
                'agent_count': len(sidebar_config['selected_agents']),
                'result_count': len(search_results)
            })
            
    except Exception as e:
        st.error(f"Fehler bei der Suche: {e}")
    
    # Ergebnisse anzeigen
    if st.session_state.search_results:
        st.divider()
        
        # Results Display
        try:
            results_display.render(st.session_state.search_results)
        except Exception as e:
            st.error(f"Fehler beim Anzeigen der Ergebnisse: {e}")
        
        # Metrics Dashboard
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
    col1, col2, col3 = st.columns(3)
    with col2:
        st.caption(f"MineSearch v3.0 | {datetime.now().strftime('%Y-%m-%d %H:%M')}")


# Haupt-Ausführung mit Fehlerbehandlung
if __name__ == "__main__":
    try:
        main()
    except Exception as e:
        # Fallback Fehlerbehandlung
        st.error(f"❌ Kritischer Fehler: {str(e)}")
        st.error("Bitte laden Sie die Seite neu (F5)")
        
        import traceback
        with st.expander("Technische Details"):
            st.code(traceback.format_exc())
            
        if st.button("🔄 Neu laden"):
            st.rerun()