"""
Author: rahn
Datum: 26.06.2025
Version: 1.0
Beschreibung: Live-Fortschrittsanzeige für MineSearch
"""

import streamlit as st
from typing import Optional, Dict, List
from datetime import datetime
import time


class SearchProgressComponent:
    """Komponente für Live-Fortschrittsanzeige während der Suche"""
    
    def __init__(self):
        self.start_time = None
        self.current_phase = None
        self.current_agent = None
        self.results_found = 0
        self.last_partial_results = None
        
    def render_progress(self, 
                       current_mine: str = None,
                       mine_index: int = None, 
                       total_mines: int = None,
                       phase: Optional[str] = None,
                       agent: Optional[str] = None,
                       status_message: Optional[str] = None,
                       partial_results: Optional[List[Dict]] = None):
        """Rendert detaillierte Fortschrittsanzeige"""
        
        # Try to get data from session state if not provided
        if 'live_progress' in st.session_state:
            live_data = st.session_state.live_progress
            current_mine = current_mine or live_data.get('current_mine', 'Unknown')
            mine_index = mine_index if mine_index is not None else live_data.get('mine_index', 0)
            total_mines = total_mines or live_data.get('total_mines', 1)
            phase = phase or live_data.get('phase')
            agent = agent or live_data.get('agent')
            status_message = status_message or live_data.get('status_message')
            partial_results = partial_results or live_data.get('partial_results')
            self.results_found = live_data.get('results_found', self.results_found)
        
        if self.start_time is None:
            self.start_time = time.time()
            
        # Update current state
        if phase:
            self.current_phase = phase
        if agent:
            self.current_agent = agent
        if partial_results and partial_results != self.last_partial_results:
            self.results_found += len(partial_results)
            self.last_partial_results = partial_results
            
        # Calculate progress
        overall_progress = (mine_index + 1) / total_mines
        elapsed_time = time.time() - self.start_time
        
        # Main progress bar
        st.progress(overall_progress, text=f"Mine {mine_index + 1}/{total_mines}")
        
        # Status columns
        col1, col2, col3 = st.columns(3)
        
        with col1:
            st.metric(
                "Aktuelle Mine",
                current_mine,
                delta=f"{mine_index + 1}/{total_mines}"
            )
            
        with col2:
            st.metric(
                "Laufzeit",
                f"{elapsed_time:.1f}s",
                delta=f"~{(elapsed_time/max(1, mine_index+1) * (total_mines-mine_index-1)):.0f}s verbleibend"
            )
            
        with col3:
            st.metric(
                "Gefundene Daten",
                f"{self.results_found}",
                delta="Felder" if self.results_found != 1 else "Feld"
            )
            
        # Detailed status
        if self.current_phase or self.current_agent:
            status_parts = []
            if self.current_phase:
                phase_emoji = self._get_phase_emoji(self.current_phase)
                status_parts.append(f"{phase_emoji} **Phase:** {self.current_phase}")
            if self.current_agent:
                agent_emoji = self._get_agent_emoji(self.current_agent)
                status_parts.append(f"{agent_emoji} **Agent:** {self.current_agent}")
            if status_message:
                status_parts.append(f"📝 **Status:** {status_message}")
                
            status_text = " | ".join(status_parts)
            st.info(status_text)
            
        # Show partial results if available
        if partial_results and len(partial_results) > 0:
            with st.expander(f"🔍 Neue Ergebnisse ({len(partial_results)})", expanded=False):
                for result in partial_results[-5:]:  # Show last 5
                    field = result.get('field_name', 'Unknown')
                    value = result.get('value', 'N/A')
                    confidence = result.get('confidence_score', 0.5)
                    
                    # Color based on confidence
                    if confidence >= 0.8:
                        st.success(f"✅ **{field}**: {value} (Konfidenz: {confidence:.0%})")
                    elif confidence >= 0.6:
                        st.warning(f"⚠️ **{field}**: {value} (Konfidenz: {confidence:.0%})")
                    else:
                        st.error(f"❌ **{field}**: {value} (Konfidenz: {confidence:.0%})")
                        
    def _get_phase_emoji(self, phase: str) -> str:
        """Gibt Emoji für Phase zurück"""
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
            
    def reset(self):
        """Setzt den Fortschritt zurück"""
        self.start_time = None
        self.current_phase = None
        self.current_agent = None
        self.results_found = 0