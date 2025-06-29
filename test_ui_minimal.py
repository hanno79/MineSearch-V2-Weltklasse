"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Minimaler Test für Perplexity in Streamlit
"""

import streamlit as st
import asyncio
from datetime import datetime

st.set_page_config(page_title="Perplexity Test", layout="wide")

# Add project root to path
import sys
import os
project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.core.config import Config
from src.agents.perplexity_agent import PerplexityAgent
from src.agents.base_agent import MineQuery
from src.utils.session_manager import SessionManager
from src.utils.streamlit_async_wrapper import streamlit_run_async

def main():
    st.title("🔍 Perplexity Agent Test")
    
    if st.button("Start Test"):
        with st.spinner("Teste Perplexity Agent..."):
            try:
                # Führe async Test aus
                result = streamlit_run_async(run_test())
                
                if result:
                    st.success("✅ Test erfolgreich!")
                    st.write(f"Gefundene Ergebnisse: {result['count']}")
                    
                    # Zeige erste Ergebnisse
                    if result['results']:
                        st.subheader("Erste Ergebnisse:")
                        for r in result['results'][:3]:
                            st.write(f"- **{r['field']}**: {r['value']}")
                else:
                    st.error("❌ Keine Ergebnisse gefunden")
                    
            except Exception as e:
                st.error(f"❌ Fehler: {str(e)}")
                st.exception(e)

async def run_test():
    """Async Test Funktion"""
    # Config laden
    config = Config()
    
    # SessionManager erstellen
    session_manager = SessionManager()
    
    # Config mit session_manager erweitern
    agent_config = {
        'api_config': config.api,
        'session_manager': session_manager
    }
    
    # Agent erstellen
    agent = PerplexityAgent("test_perplexity", agent_config)
    
    try:
        # Initialisieren
        success = await agent.initialize()
        if not success:
            raise Exception("Agent konnte nicht initialisiert werden")
        
        # Test-Query
        query = MineQuery(
            mine_name="Canadian Malartic",
            region="Quebec",
            country="Canada",
            languages=["en", "fr"],
            required_fields=["betreiber", "koordinaten", "rohstofftyp"]
        )
        
        # Suche durchführen
        results = await agent.search_mine(query)
        
        # Ergebnisse formatieren
        formatted_results = []
        for r in results:
            formatted_results.append({
                'field': r.field_name,
                'value': r.value,
                'source': r.source
            })
        
        return {
            'count': len(results),
            'results': formatted_results
        }
        
    finally:
        # Cleanup
        await agent.cleanup()
        await session_manager.close_all()

if __name__ == "__main__":
    main()