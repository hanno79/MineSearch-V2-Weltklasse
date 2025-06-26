"""
Emergency Test - Schritt 6: Teste UI Komponenten Import
"""

import streamlit as st
import sys
import os

st.set_page_config(
    page_title="MineSearch - Step 6",
    page_icon="⛏️",
    layout="wide"
)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Basis imports
from src.core.config import Config
from src.utils.session_manager import SessionManager
from src.core.database import DatabaseManager

print("1. Basis imports OK")

# Teste UI imports einzeln
components_status = {}

# Test 1: Sidebar
try:
    print("2. Importiere SidebarComponent...")
    from src.ui.components.sidebar import SidebarComponent
    components_status["SidebarComponent"] = "✅"
    print("   OK")
except Exception as e:
    components_status["SidebarComponent"] = f"❌ {str(e)}"
    print(f"   FEHLER: {e}")

# Test 2: SearchForm
try:
    print("3. Importiere SearchFormComponent...")
    from src.ui.components.search_form import SearchFormComponent
    components_status["SearchFormComponent"] = "✅"
    print("   OK")
except Exception as e:
    components_status["SearchFormComponent"] = f"❌ {str(e)}"
    print(f"   FEHLER: {e}")

# Test 3: ResultsDisplay
try:
    print("4. Importiere ResultsDisplayComponent...")
    from src.ui.components.results_display import ResultsDisplayComponent
    components_status["ResultsDisplayComponent"] = "✅"
    print("   OK")
except Exception as e:
    components_status["ResultsDisplayComponent"] = f"❌ {str(e)}"
    print(f"   FEHLER: {e}")

# Test 4: MetricsDashboard
try:
    print("5. Importiere MetricsDashboardComponent...")
    from src.ui.components.metrics_dashboard import MetricsDashboardComponent
    components_status["MetricsDashboardComponent"] = "✅"
    print("   OK")
except Exception as e:
    components_status["MetricsDashboardComponent"] = f"❌ {str(e)}"
    print(f"   FEHLER: {e}")

# Test 5: SearchProgress
try:
    print("6. Importiere SearchProgressComponent...")
    from src.ui.components.search_progress import SearchProgressComponent
    components_status["SearchProgressComponent"] = "✅"
    print("   OK")
except Exception as e:
    components_status["SearchProgressComponent"] = f"❌ {str(e)}"
    print(f"   FEHLER: {e}")

# Test 6: ResultHistory
try:
    print("7. Importiere ResultHistoryPage...")
    from src.ui.pages.result_history import ResultHistoryPage
    components_status["ResultHistoryPage"] = "✅"
    print("   OK")
except Exception as e:
    components_status["ResultHistoryPage"] = f"❌ {str(e)}"
    print(f"   FEHLER: {e}")

def main():
    st.title("⛏️ MineSearch - Step 6: UI Components Test")
    
    st.subheader("Import Status:")
    for component, status in components_status.items():
        st.write(f"{component}: {status}")
    
    # Teste Instanziierung
    if all("✅" in status for status in components_status.values()):
        st.success("✅ Alle Komponenten importiert!")
        
        with st.expander("Teste Komponenten-Instanziierung"):
            try:
                config = Config()
                sm = SessionManager()
                st.write("Config und SessionManager erstellt")
                
                sidebar = SidebarComponent(config)
                st.success("✅ SidebarComponent instanziiert")
                
                search_form = SearchFormComponent(config, sm)
                st.success("✅ SearchFormComponent instanziiert")
                
                results = ResultsDisplayComponent()
                st.success("✅ ResultsDisplayComponent instanziiert")
                
                metrics = MetricsDashboardComponent()
                st.success("✅ MetricsDashboardComponent instanziiert")
                
            except Exception as e:
                st.error(f"Instanziierung fehlgeschlagen: {e}")
                import traceback
                st.code(traceback.format_exc())

if __name__ == "__main__":
    print("8. Main wird aufgerufen")
    main()