"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Minimale Test-Version von MineSearch
"""

import streamlit as st

# Page configuration
st.set_page_config(
    page_title="MineSearch - Test",
    page_icon="⛏️",
    layout="wide"
)

def main():
    """Minimale Main Funktion zum Testen"""
    st.title("⛏️ MineSearch - Minimal Test")
    
    st.success("✅ Streamlit läuft!")
    
    # Test Session State
    if 'counter' not in st.session_state:
        st.session_state.counter = 0
    
    if st.button("Counter erhöhen"):
        st.session_state.counter += 1
    
    st.info(f"Counter: {st.session_state.counter}")
    
    # Test Imports schrittweise
    with st.expander("Import Tests"):
        try:
            import nest_asyncio
            st.success("✅ nest_asyncio")
        except Exception as e:
            st.error(f"❌ nest_asyncio: {e}")
            
        try:
            from src.core.config import Config
            st.success("✅ Config")
        except Exception as e:
            st.error(f"❌ Config: {e}")
            
        try:
            from src.core.database import DatabaseManager
            st.success("✅ DatabaseManager")
        except Exception as e:
            st.error(f"❌ DatabaseManager: {e}")
            
        try:
            from src.utils.session_manager import SessionManager
            st.success("✅ SessionManager")
        except Exception as e:
            st.error(f"❌ SessionManager: {e}")

if __name__ == "__main__":
    main()