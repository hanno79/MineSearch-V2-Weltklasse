"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Mixin für Live-Updates in Streamlit während async Operationen
"""
import streamlit as st
import time
from typing import Callable, Any


class LiveUpdateMixin:
    """Mixin für periodische UI-Updates während langer Operationen"""
    
    @staticmethod
    def with_live_updates(update_interval: float = 0.5):
        """
        Decorator für Funktionen die Live-Updates benötigen
        
        Args:
            update_interval: Sekunden zwischen Updates
        """
        def decorator(func: Callable) -> Callable:
            def wrapper(*args, **kwargs):
                # Placeholder für Live-Updates
                placeholder = st.empty()
                
                # Start der Operation
                result = None
                error = None
                done = False
                
                def run_operation():
                    nonlocal result, error, done
                    try:
                        result = func(*args, **kwargs)
                    except Exception as e:
                        error = e
                    finally:
                        done = True
                
                # Starte Operation in separatem Thread
                import threading
                thread = threading.Thread(target=run_operation)
                thread.start()
                
                # Update-Loop
                while not done:
                    with placeholder.container():
                        # Render aktuellen Status aus Session State
                        if 'live_progress' in st.session_state:
                            progress_data = st.session_state.live_progress
                            
                            # Progress Bar
                            if progress_data.get('mine_index') and progress_data.get('total_mines'):
                                progress = progress_data['mine_index'] / progress_data['total_mines']
                                st.progress(progress, text=f"Mine {progress_data['mine_index']}/{progress_data['total_mines']}")
                            
                            # Status Metrics
                            col1, col2, col3 = st.columns(3)
                            
                            with col1:
                                st.metric(
                                    "Aktuelle Mine",
                                    progress_data.get('current_mine', 'Warte...'),
                                    delta=f"{progress_data.get('mine_index', 0)}/{progress_data.get('total_mines', 0)}"
                                )
                            
                            with col2:
                                phase = progress_data.get('phase', 'Initialisierung')
                                agent = progress_data.get('agent', '')
                                st.metric(
                                    "Phase",
                                    phase,
                                    delta=agent if agent else None
                                )
                            
                            with col3:
                                st.metric(
                                    "Gefundene Daten",
                                    progress_data.get('results_found', 0),
                                    delta="Felder"
                                )
                            
                            # Status Message
                            if progress_data.get('status_message'):
                                st.info(progress_data['status_message'])
                    
                    time.sleep(update_interval)
                
                # Warte auf Thread
                thread.join()
                
                # Clear placeholder
                placeholder.empty()
                
                # Raise error if any
                if error:
                    raise error
                
                return result
            
            return wrapper
        return decorator
    
    @staticmethod 
    def render_live_progress(container=None):
        """
        Rendert den aktuellen Progress aus Session State
        
        Args:
            container: Optional Streamlit container
        """
        if 'live_progress' not in st.session_state:
            return
            
        progress_data = st.session_state.live_progress
        
        target = container if container else st
        
        # Overall progress
        if progress_data.get('mine_index') and progress_data.get('total_mines'):
            progress = progress_data['mine_index'] / progress_data['total_mines']
            target.progress(progress, text=f"Mine {progress_data['mine_index']}/{progress_data['total_mines']}")
        
        # Status columns
        col1, col2, col3 = target.columns(3)
        
        with col1:
            target.metric(
                "Aktuelle Mine",
                progress_data.get('current_mine', 'Warte...'),
                delta=f"{progress_data.get('mine_index', 0)}/{progress_data.get('total_mines', 0)}"
            )
        
        with col2:
            phase = progress_data.get('phase', 'Initialisierung')
            agent = progress_data.get('agent', '')
            target.metric(
                "Phase",
                phase,
                delta=agent if agent else None
            )
        
        with col3:
            target.metric(
                "Gefundene Daten",
                progress_data.get('results_found', 0),
                delta="Felder"
            )
        
        # Status message
        if progress_data.get('status_message'):
            target.info(progress_data['status_message'])
        
        # Recent updates
        if 'status_updates' in st.session_state and st.session_state.status_updates:
            with target.expander("Letzte Updates", expanded=False):
                for update in st.session_state.status_updates[-5:]:
                    target.write(f"• {update.get('message', '')}")