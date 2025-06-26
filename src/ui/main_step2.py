"""
Emergency Test - Schritt 2: Füge sys/os imports hinzu
"""

import streamlit as st
import sys
import os
from datetime import datetime

print("1. Basic imports OK")

st.set_page_config(
    page_title="MineSearch - Step 2",
    page_icon="⛏️",
    layout="wide"
)

# Add project root to path
project_root = os.path.dirname(os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
if project_root not in sys.path:
    sys.path.insert(0, project_root)
print(f"2. Project root added: {project_root}")

def main():
    st.title("⛏️ MineSearch - Step 2")
    st.success("✅ Basic imports funktionieren!")
    st.info(f"Zeit: {datetime.now()}")
    st.write(f"Python Path enthält: {len(sys.path)} Einträge")

if __name__ == "__main__":
    main()