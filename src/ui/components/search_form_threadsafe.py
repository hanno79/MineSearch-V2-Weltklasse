"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Thread-safe Search Form Component mit Live-Updates
ÄNDERUNG 27.06.2025: Thread-sichere UI-Updates implementiert
"""
import streamlit as st
from typing import Dict, List, Optional, Callable
import time
import threading
import queue
from src.agents.base_agent import MineQuery
from src.core.orchestrator import MineSearchOrchestratorV2
from src.core.cancellation import CancellationToken, CancellationException
from src.utils.streamlit_async_wrapper import streamlit_run_async
from src.ui.components.search_progress import SearchProgressComponent
from datetime import datetime


class ThreadSafeSearchFormComponent:
    """Such-Formular mit thread-sicheren Status-Updates"""
    
    def __init__(self, config, session_manager):
        self.config = config
        self.session_manager = session_manager
        self.cancellation_token = None
        self.orchestrator = None
        self._orchestrator_initialized = False
        self.progress_component = SearchProgressComponent()
        self.update_queue = queue.Queue()
        
    def render(self, mines_to_search: List[Dict], selected_agents: List[str], 
               advanced_options: Dict) -> Optional[List]:
        """Rendert das Such-Formular und führt Suche aus"""
        
        # Session State Check
        if 'status_updates' not in st.session_state:
            st.error("Session State nicht initialisiert. Bitte Seite neu laden.")
            st.stop()
        
        # Orchestrator frisch initialisieren
        from src.core.orchestrator import MineSearchOrchestratorV2
        self.orchestrator = MineSearchOrchestratorV2(self.config, self.session_manager)
        self._orchestrator_initialized = False
        
        # Button Container
        button_container = st.container()
        
        with button_container:
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                search_clicked = st.button(
                    "🔍 Start Search",
                    type="primary",
                    disabled=(not mines_to_search or not selected_agents or 
                             st.session_state.get('search_in_progress', False)),
                    use_container_width=True,
                    key="start_search_button"
                )
                
                if search_clicked and mines_to_search and selected_agents:
                    st.session_state.search_in_progress = True
            
            with col2:
                is_searching = st.session_state.get('search_in_progress', False)
                cancel_help = "Klicke hier oder drücke F5 um die Suche abzubrechen" if is_searching else "Startet eine Suche um diese Option zu aktivieren"
                
                cancel_clicked = st.button(
                    "⏸️ Cancel Search", 
                    type="secondary", 
                    use_container_width=True,
                    disabled=not is_searching,
                    key="cancel_search_button",
                    help=cancel_help
                )
                
                if cancel_clicked:
                    if st.session_state.get('cancellation_token'):
                        st.session_state.cancellation_token.cancel()
                    st.session_state.search_cancelled = True
                    st.session_state.search_in_progress = False
                    st.warning("🛑 Suche wird abgebrochen...")
                    st.rerun()
            
            with col3:
                if st.button("🗑️ Clear Results", 
                            use_container_width=True,
                            disabled=not st.session_state.get('search_results', []),
                            key="clear_results_button"):
                    st.session_state.search_results = []
                    st.session_state.search_in_progress = False
                    st.rerun()
        
        # Status display area
        status_container = st.empty()
        
        # Handle search
        if search_clicked and mines_to_search and selected_agents:
            return self._perform_search_with_live_updates(
                mines_to_search, 
                selected_agents, 
                advanced_options,
                status_container
            )
        
        # Show info if no mines or agents selected
        if search_clicked:
            if not mines_to_search:
                st.error("❌ Please specify at least one mine to search")
            if not selected_agents:
                st.error("❌ Please select at least one agent")
        
        return None
    
    def _perform_search_with_live_updates(self, mines_to_search: List[Dict], 
                                         selected_agents: List[str],
                                         advanced_options: Dict, 
                                         status_container) -> List:
        """Führt die Suche mit Live-Updates aus"""
        
        # Initialize orchestrator
        from src.core.orchestrator import MineSearchOrchestratorV2
        try:
            self.orchestrator = MineSearchOrchestratorV2(self.config, self.session_manager)
            self._orchestrator_initialized = False
        except Exception as e:
            st.error(f"❌ Fehler beim Initialisieren des Orchestrators: {str(e)}")
            return []
        
        # Session state initialization
        if 'status_updates' not in st.session_state:
            st.session_state.status_updates = []
        if 'error_details' not in st.session_state:
            st.session_state.error_details = []
        if 'live_progress' not in st.session_state:
            st.session_state.live_progress = {
                'current_mine': '',
                'mine_index': 0,
                'total_mines': len(mines_to_search),
                'phase': '',
                'agent': '',
                'message': '',
                'results_found': 0,
                'partial_results': []
            }
        
        # Create cancellation token
        from src.core.cancellation import CancellationToken
        cancellation_token = CancellationToken()
        st.session_state.cancellation_token = cancellation_token
        st.session_state.search_cancelled = False
        
        # Start search in background thread
        all_results = []
        search_thread = threading.Thread(
            target=self._search_thread,
            args=(mines_to_search, selected_agents, cancellation_token, all_results)
        )
        search_thread.start()
        
        # Live update loop
        progress_placeholder = status_container.container()
        
        while search_thread.is_alive():
            # Check for updates
            try:
                while not self.update_queue.empty():
                    update = self.update_queue.get_nowait()
                    if update['type'] == 'progress':
                        st.session_state.live_progress.update(update['data'])
                    elif update['type'] == 'status':
                        st.session_state.status_updates.append(update['data'])
            except queue.Empty:
                pass
            
            # Render current progress
            with progress_placeholder.container():
                progress = st.session_state.live_progress
                
                # Overall progress
                st.progress(
                    progress['mine_index'] / progress['total_mines'],
                    text=f"Mine {progress['mine_index']}/{progress['total_mines']}"
                )
                
                # Current status
                col1, col2, col3 = st.columns(3)
                
                with col1:
                    st.metric(
                        "Aktuelle Mine",
                        progress['current_mine'] or "Warte...",
                        delta=f"{progress['mine_index']}/{progress['total_mines']}"
                    )
                
                with col2:
                    st.metric(
                        "Phase",
                        progress['phase'] or "Initialisierung",
                        delta=progress['agent'] or ""
                    )
                
                with col3:
                    st.metric(
                        "Gefundene Daten",
                        progress['results_found'],
                        delta="Felder"
                    )
                
                # Status message
                if progress['message']:
                    st.info(progress['message'])
                
                # Recent updates
                if st.session_state.status_updates:
                    with st.expander("Letzte Updates", expanded=False):
                        for update in st.session_state.status_updates[-5:]:
                            st.write(f"• {update['message']}")
            
            # Check cancellation
            if st.session_state.get('search_cancelled', False):
                cancellation_token.cancel()
                break
            
            # Small delay to prevent overwhelming the UI
            time.sleep(0.1)
        
        # Wait for thread to complete
        search_thread.join(timeout=1)
        
        # Final status
        status_container.empty()
        
        if cancellation_token.is_cancelled():
            st.warning("🛑 Search was cancelled")
        elif all_results:
            st.success(f"✅ Search completed! Found {len(all_results)} results")
            st.balloons()
        else:
            st.warning("⚠️ No results found")
        
        st.session_state.search_in_progress = False
        st.session_state.cancellation_token = None
        
        return all_results
    
    def _search_thread(self, mines_to_search: List[Dict], 
                      selected_agents: List[str],
                      cancellation_token, 
                      results_list: List):
        """Thread für die eigentliche Suche"""
        
        # Initialize orchestrator once
        if not self._orchestrator_initialized:
            try:
                init_success = streamlit_run_async(self.orchestrator.initialize())
                if not init_success:
                    self.update_queue.put({
                        'type': 'status',
                        'data': {
                            'message': '❌ Orchestrator Initialisierung fehlgeschlagen',
                            'timestamp': datetime.now()
                        }
                    })
                    return
                self._orchestrator_initialized = True
            except Exception as init_error:
                self.update_queue.put({
                    'type': 'status',
                    'data': {
                        'message': f'❌ Fehler bei Orchestrator Initialisierung: {str(init_error)}',
                        'timestamp': datetime.now()
                    }
                })
                return
        
        # Search each mine
        for idx, mine_data in enumerate(mines_to_search):
            if cancellation_token.is_cancelled():
                break
            
            # Update progress
            self.update_queue.put({
                'type': 'progress',
                'data': {
                    'current_mine': mine_data.get('mine_name', 'Unknown'),
                    'mine_index': idx + 1,
                    'phase': 'Initialisierung',
                    'message': f"Starte Suche für {mine_data.get('mine_name', 'Unknown')}"
                }
            })
            
            # Set status callback
            def status_callback(message, phase=None, agent=None, partial_results=None):
                self.update_queue.put({
                    'type': 'status',
                    'data': {
                        'mine': mine_data.get('mine_name', 'Unknown'),
                        'message': message,
                        'timestamp': datetime.now()
                    }
                })
                
                if phase or agent:
                    update_data = {}
                    if phase:
                        update_data['phase'] = phase
                    if agent:
                        update_data['agent'] = agent
                    if message:
                        update_data['message'] = message
                    if partial_results:
                        update_data['results_found'] = st.session_state.live_progress.get('results_found', 0) + len(partial_results)
                    
                    self.update_queue.put({
                        'type': 'progress',
                        'data': update_data
                    })
            
            self.orchestrator.status_callback = status_callback
            
            try:
                results = streamlit_run_async(
                    self._search_single_mine(
                        mine_data,
                        selected_agents,
                        cancellation_token
                    )
                )
                if results:
                    results_list.extend(results)
            except CancellationException:
                break
            except Exception as e:
                self.update_queue.put({
                    'type': 'status',
                    'data': {
                        'message': f"❌ Error searching {mine_data.get('mine_name', 'Unknown')}: {str(e)}",
                        'timestamp': datetime.now()
                    }
                })
    
    async def _search_single_mine(self, mine_data: Dict, selected_agents: List[str],
                                 cancellation_token) -> List:
        """Sucht eine einzelne Mine"""
        if not self.orchestrator:
            raise Exception("Orchestrator not initialized")
        
        query = MineQuery(
            mine_name=mine_data['mine_name'],
            region=mine_data['region'],
            country=mine_data['country'],
            languages=["en", "fr", "es", "de"],
            required_fields=[
                "betreiber", "operator", "owner",
                "koordinaten", "coordinates", "location",
                "rohstofftyp", "commodity", "mineral",
                "aktivitaetsstatus", "status",
                "sanierungskosten", "remediation_costs",
                "environmental_liability", "restoration_costs",
                "production_start", "production_end",
                "reserve", "resource",
                "mining_method", "processing",
                "capacity", "recovery_rate"
            ]
        )
        
        search_params = {
            "enhanced": True,
            "agent_types": selected_agents,
            "include_sources": True,
            "cancellation_token": cancellation_token
        }
        
        try:
            results = await self.orchestrator.search_mine(query, search_params)
            return results
        except CancellationException:
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            if 'error_details' not in st.session_state:
                st.session_state.error_details = []
            st.session_state.error_details.append({
                'mine': mine_data['mine_name'],
                'error': error_details,
                'timestamp': datetime.now()
            })
            return []