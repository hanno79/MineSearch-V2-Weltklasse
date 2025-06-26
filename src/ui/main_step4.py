"""
Emergency Test - Schritt 4: Teste Config und SessionManager
"""

import streamlit as st
import sys
import os

print("1. Basic imports OK")

st.set_page_config(
    page_title="MineSearch - Step 4",
    page_icon="⛏️",
    layout="wide"
)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Teste imports einzeln
print("2. Teste Config import...")
try:
    from src.core.config import Config
    print("3. Config importiert")
except Exception as e:
    print(f"FEHLER bei Config: {e}")
    import traceback
    traceback.print_exc()

print("4. Teste SessionManager import...")
try:
    from src.utils.session_manager import SessionManager
    print("5. SessionManager importiert")
except Exception as e:
    print(f"FEHLER bei SessionManager: {e}")
    import traceback
    traceback.print_exc()

def main():
    st.title("⛏️ MineSearch - Step 4")
    
    # Teste Config
    try:
        config = Config()
        st.success("✅ Config erstellt")
    except Exception as e:
        st.error(f"❌ Config Error: {e}")
    
    # Teste SessionManager
    try:
        sm = SessionManager()
        st.success("✅ SessionManager erstellt")
    except Exception as e:
        st.error(f"❌ SessionManager Error: {e}")

if __name__ == "__main__":
    print("6. Main wird aufgerufen")
    main()