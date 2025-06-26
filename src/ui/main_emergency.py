"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Emergency Minimal-Version für Debugging
"""

import streamlit as st
print("1. Streamlit importiert")

# Page Config MUSS als erstes kommen
st.set_page_config(
    page_title="MineSearch - Emergency",
    page_icon="⛏️",
    layout="wide"
)
print("2. Page config gesetzt")

def main():
    st.title("⛏️ MineSearch - Emergency Mode")
    st.success("✅ Basis Streamlit funktioniert!")
    
    # Test Session State
    if 'counter' not in st.session_state:
        st.session_state.counter = 0
        
    col1, col2 = st.columns(2)
    with col1:
        if st.button("Test Button"):
            st.session_state.counter += 1
            
    with col2:
        st.metric("Counter", st.session_state.counter)
    
    st.info("Wenn Sie dies sehen, funktioniert Streamlit grundsätzlich.")

if __name__ == "__main__":
    print("3. Main wird aufgerufen")
    main()
    print("4. Main wurde ausgeführt")