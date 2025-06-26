"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Thread-sichere Live-Progress Anzeige für MineSearch
"""

import streamlit as st
from typing import Optional, Dict, List
import time
from datetime import datetime


class LiveProgressComponent:
    """Thread-sichere Live-Progress Anzeige mit Polling"""
    
    def __init__(self):
        self.container = None
        self.last_update_count = 0
        
    def render_with_polling(self, search_in_progress: bool):
        """
        Rendert Live-Progress mit automatischem Polling der Session State
        
        Args:
            search_in_progress: Ob gerade eine Suche läuft
        """
        if not search_in_progress:
            return
            
        # Container für dynamische Updates
        if self.container is None:
            self.container = st.container()
            
        with self.container:
            # Hole live_progress Daten aus Session State
            live_progress = st.session_state.get('live_progress', {})
            status_updates = st.session_state.get('status_updates', [])
            
            # Verwende live_progress für aktuelle Daten
            current_mine = live_progress.get('current_mine', 'Unknown')
            mine_index = live_progress.get('mine_index', 0)
            total_mines = live_progress.get('total_mines', 1)
            current_phase = live_progress.get('phase', 'Initialisierung')
            current_agent = live_progress.get('agent', None)
            message = live_progress.get('status_message', '')
            partial_results = live_progress.get('partial_results', [])
            results_found = live_progress.get('results_found', 0)
            
            # Zeige aktuellen Status
            col1, col2, col3 = st.columns(3)
            
            with col1:
                st.metric(
                    "Aktuelle Mine",
                    current_mine,
                    delta=f"{mine_index + 1}/{total_mines}"
                )
                
            with col2:
                st.metric(
                    "Phase",
                    current_phase,
                    delta=current_agent if current_agent else ""
                )
                
            with col3:
                st.metric(
                    "Gefundene Daten",
                    results_found,
                    delta="Felder"
                )
            
            # Status-Nachricht
            if message:
                phase_emoji = self._get_phase_emoji(current_phase)
                agent_emoji = self._get_agent_emoji(current_agent) if current_agent else ""
                st.info(f"{phase_emoji} {agent_emoji} {message}")
            
            # Zeige neue Ergebnisse
            if partial_results:
                with st.expander(f"🆕 Neue Ergebnisse ({len(partial_results)})", expanded=True):
                    for result in partial_results[:3]:  # Zeige max 3
                        field = result.get('field_name', 'Unknown')
                        value = result.get('value', 'N/A')
                        confidence = result.get('confidence_score', 0.5)
                        
                        if confidence >= 0.8:
                            st.success(f"✅ **{field}**: {value} ({confidence:.0%})")
                        elif confidence >= 0.6:
                            st.warning(f"⚠️ **{field}**: {value} ({confidence:.0%})")
                        else:
                            st.error(f"❌ **{field}**: {value} ({confidence:.0%})")
            
            # Activity Log
            with st.expander("📋 Aktivitäts-Log", expanded=False):
                for update in reversed(latest_updates):
                    timestamp = update.get('timestamp', datetime.now())
                    if isinstance(timestamp, datetime):
                        timestamp = timestamp.strftime("%H:%M:%S")
                    mine = update.get('mine', 'Unknown')
                    msg = update.get('message', '')
                    st.text(f"[{timestamp}] {mine}: {msg}")
            
            # Auto-Refresh Info
            st.caption("🔄 Updates werden automatisch angezeigt...")
    
    def _get_phase_emoji(self, phase: str) -> str:
        """Gibt Emoji für Phase zurück"""
        if not phase:
            return "🔄"
        phase_lower = phase.lower()
        if "discovery" in phase_lower or "quellen" in phase_lower:
            return "🔍"
        elif "basis" in phase_lower or "basic" in phase_lower:
            return "📊"
        elif "produktion" in phase_lower or "production" in phase_lower:
            return "⚙️"
        elif "umwelt" in phase_lower or "environment" in phase_lower:
            return "🌱"
        elif "finanzen" in phase_lower or "financial" in phase_lower:
            return "💰"
        elif "regulierung" in phase_lower or "regulation" in phase_lower:
            return "📜"
        else:
            return "🔄"
    
    def _get_agent_emoji(self, agent: str) -> str:
        """Gibt Emoji für Agent zurück"""
        if not agent:
            return ""
        agent_lower = agent.lower()
        if "perplexity" in agent_lower:
            return "🔮"
        elif "claude" in agent_lower:
            return "🤖"
        elif "gpt" in agent_lower:
            return "🧠"
        elif "tavily" in agent_lower:
            return "🔎"
        elif "exa" in agent_lower:
            return "🌐"
        elif "scraper" in agent_lower:
            return "🕷️"
        elif "browser" in agent_lower:
            return "🌏"
        else:
            return "🤖"