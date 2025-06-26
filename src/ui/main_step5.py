"""
Emergency Test - Schritt 5: Teste @st.cache_resource
"""

import streamlit as st
import sys
import os

st.set_page_config(
    page_title="MineSearch - Step 5",
    page_icon="⛏️",
    layout="wide"
)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.config import Config
from src.utils.session_manager import SessionManager
from src.core.database import DatabaseManager

print("1. Alle imports OK")

# Teste cache_resource
@st.cache_resource
def get_config():
    print("2. get_config() wird aufgerufen")
    return Config()

@st.cache_resource
def get_database_manager():
    print("3. get_database_manager() wird aufgerufen")
    db = DatabaseManager()
    print("4. DatabaseManager erstellt, initialisiere...")
    db.initialize()
    print("5. DatabaseManager initialisiert")
    return db

@st.cache_resource
def get_session_manager():
    print("6. get_session_manager() wird aufgerufen")
    return SessionManager()

def main():
    st.title("⛏️ MineSearch - Step 5")
    
    # Teste Config
    with st.spinner("Teste Config..."):
        try:
            config = get_config()
            st.success("✅ Config Cache funktioniert")
        except Exception as e:
            st.error(f"❌ Config Cache Error: {e}")
    
    # Teste SessionManager
    with st.spinner("Teste SessionManager..."):
        try:
            sm = get_session_manager()
            st.success("✅ SessionManager Cache funktioniert")
        except Exception as e:
            st.error(f"❌ SessionManager Cache Error: {e}")
    
    # Teste DatabaseManager
    with st.spinner("Teste DatabaseManager..."):
        try:
            db = get_database_manager()
            st.success("✅ DatabaseManager Cache funktioniert")
        except Exception as e:
            st.error(f"❌ DatabaseManager Cache Error: {e}")
            import traceback
            st.code(traceback.format_exc())

if __name__ == "__main__":
    print("7. Main wird aufgerufen")
    main()