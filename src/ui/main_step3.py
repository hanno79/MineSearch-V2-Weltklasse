"""
Emergency Test - Schritt 3: Teste nest_asyncio
"""

import streamlit as st
import sys
import os
from datetime import datetime

print("1. Basic imports OK")

st.set_page_config(
    page_title="MineSearch - Step 3",
    page_icon="⛏️",
    layout="wide"
)

project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

# Teste nest_asyncio
print("2. Importiere nest_asyncio...")
try:
    import nest_asyncio
    print("3. nest_asyncio importiert")
    nest_asyncio.apply()
    print("4. nest_asyncio.apply() ausgeführt")
except Exception as e:
    print(f"FEHLER bei nest_asyncio: {e}")

def main():
    st.title("⛏️ MineSearch - Step 3")
    st.success("✅ nest_asyncio Test")
    
    # Zeige asyncio Status
    try:
        import asyncio
        loop = asyncio.get_event_loop()
        st.info(f"Event Loop Running: {loop.is_running()}")
        st.info(f"Event Loop Closed: {loop.is_closed()}")
    except Exception as e:
        st.error(f"Event Loop Error: {e}")

if __name__ == "__main__":
    print("5. Main wird aufgerufen")
    main()