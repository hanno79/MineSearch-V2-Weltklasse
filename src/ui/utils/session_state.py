"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Session State Management für MineSearch UI
"""
import streamlit as st
from typing import Any, Dict, Optional
from ...core.config import Config


class SessionStateManager:
    """Zentrales Session State Management"""
    
    # Default values
    DEFAULTS = {
        'search_results': [],
        'search_history': [],
        'search_in_progress': False,
        'selected_agents': [],
        'mines_to_search': [],
        'cancellation_token': None,
        'last_search_params': {},
        'ui_theme': 'light',
        'export_format': 'CSV'
    }
    
    @classmethod
    def initialize(cls):
        """Initialize all session state variables"""
        # Initialize config first
        if 'config' not in st.session_state:
            st.session_state.config = Config()
        
        # Initialize other values
        for key, default_value in cls.DEFAULTS.items():
            if key not in st.session_state:
                st.session_state[key] = default_value
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        """Get value from session state"""
        return st.session_state.get(key, default)
    
    @classmethod
    def set(cls, key: str, value: Any):
        """Set value in session state"""
        st.session_state[key] = value
    
    @classmethod
    def update(cls, updates: Dict[str, Any]):
        """Update multiple values"""
        for key, value in updates.items():
            st.session_state[key] = value
    
    @classmethod
    def clear_search_results(cls):
        """Clear search-related state"""
        st.session_state.search_results = []
        st.session_state.search_in_progress = False
        st.session_state.cancellation_token = None
    
    @classmethod
    def add_to_history(cls, search_info: Dict):
        """Add entry to search history"""
        if 'search_history' not in st.session_state:
            st.session_state.search_history = []
        
        st.session_state.search_history.append(search_info)
        
        # Keep only last 50 entries
        if len(st.session_state.search_history) > 50:
            st.session_state.search_history = st.session_state.search_history[-50:]
    
    @classmethod
    def get_config(cls) -> Config:
        """Get configuration object"""
        if 'config' not in st.session_state:
            st.session_state.config = Config()
        return st.session_state.config
    
    @classmethod
    def is_search_active(cls) -> bool:
        """Check if search is currently active"""
        return st.session_state.get('search_in_progress', False)
    
    @classmethod
    def get_last_search_params(cls) -> Dict:
        """Get parameters from last search"""
        return st.session_state.get('last_search_params', {})
    
    @classmethod
    def save_search_params(cls, params: Dict):
        """Save current search parameters"""
        st.session_state.last_search_params = params