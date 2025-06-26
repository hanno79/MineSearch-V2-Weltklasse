"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Debug-Version von MineSearch ohne CSS
"""

import streamlit as st
import sys
import os
from datetime import datetime

# Page configuration MUSS VOR allen anderen st. Aufrufen stehen
st.set_page_config(
    page_title="MineSearch - Debug",
    page_icon="⛏️",
    layout="wide"
)

st.title("🔍 MineSearch Debug Mode")

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Test 1: Basic Streamlit
st.success("✅ Streamlit läuft!")

# Test 2: Session State
with st.expander("Session State Test"):
    if 'test' not in st.session_state:
        st.session_state.test = "OK"
    st.write(f"Session State: {st.session_state.test}")

# Test 3: Imports schrittweise
with st.expander("Import Tests"):
    # nest_asyncio
    try:
        import nest_asyncio
        nest_asyncio.apply()
        st.success("✅ nest_asyncio geladen und angewendet")
    except Exception as e:
        st.error(f"❌ nest_asyncio: {e}")
        
    # Config
    try:
        from src.core.config import Config
        config = Config()
        st.success("✅ Config geladen")
    except Exception as e:
        st.error(f"❌ Config: {e}")
        
    # Database
    try:
        from src.core.database import DatabaseManager
        st.success("✅ DatabaseManager importiert")
        db = DatabaseManager()
        db.initialize()
        st.success("✅ Datenbank initialisiert")
    except Exception as e:
        st.error(f"❌ DatabaseManager: {e}")
        
    # SessionManager
    try:
        from src.utils.session_manager import SessionManager
        sm = SessionManager()
        st.success("✅ SessionManager geladen")
    except Exception as e:
        st.error(f"❌ SessionManager: {e}")

# Test 4: UI Components einzeln
with st.expander("UI Component Tests"):
    # Sidebar
    try:
        from src.ui.components.sidebar import SidebarComponent
        st.success("✅ SidebarComponent importiert")
    except Exception as e:
        st.error(f"❌ SidebarComponent: {e}")
        
    # SearchForm
    try:
        from src.ui.components.search_form import SearchFormComponent
        st.success("✅ SearchFormComponent importiert")
    except Exception as e:
        st.error(f"❌ SearchFormComponent: {e}")
        
    # ResultsDisplay
    try:
        from src.ui.components.results_display import ResultsDisplayComponent
        st.success("✅ ResultsDisplayComponent importiert")
    except Exception as e:
        st.error(f"❌ ResultsDisplayComponent: {e}")

# Test 5: Einfache UI ohne Komponenten
st.header("Einfache UI Test")

col1, col2 = st.columns(2)
with col1:
    if st.button("Test Button"):
        st.balloons()
        
with col2:
    user_input = st.text_input("Test Input")
    if user_input:
        st.write(f"Eingabe: {user_input}")

st.info(f"Zeit: {datetime.now()}")

# Footer
st.divider()
st.caption("MineSearch Debug Mode - Wenn Sie dies sehen, funktioniert Streamlit!")