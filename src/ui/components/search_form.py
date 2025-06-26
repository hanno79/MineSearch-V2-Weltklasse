"""
Author: rahn
Datum: 23.06.2025
Version: 1.3
Beschreibung: Search Form Komponente für MineSearch UI
ÄNDERUNG 23.06.2025: Event Loop Fix mit async_utils
ÄNDERUNG 27.06.2025: SearchProgress Integration
"""
import streamlit as st
from typing import Dict, List, Optional, Callable
import time
from concurrent.futures import ThreadPoolExecutor
from src.agents.base_agent import MineQuery
from src.core.orchestrator import MineSearchOrchestratorV2
from src.core.cancellation import CancellationToken, CancellationException
from src.utils.streamlit_async_wrapper import streamlit_run_async
from src.ui.components.search_progress import SearchProgressComponent
from src.ui.components.live_progress import LiveProgressComponent
from src.core.global_cancellation_registry import get_global_cancellation_registry, RegisteredSearch
from datetime import datetime
import uuid


class SearchFormComponent:
    """Such-Formular mit Status-Updates und Cancellation"""
    
    def __init__(self, config, session_manager):
        self.config = config
        self.session_manager = session_manager
        self.cancellation_token = None
        self.orchestrator = None
        self._orchestrator_initialized = False
        self.progress_component = SearchProgressComponent()
        self.live_progress = LiveProgressComponent()
        
    def render(self, mines_to_search: List[Dict], selected_agents: List[str], 
               advanced_options: Dict) -> Optional[List]:
        """Rendert das Such-Formular und führt Suche aus"""
        
        # ÄNDERUNG 27.06.2025: Session State wird nur in main.py initialisiert
        # Nur prüfen ob Session State existiert
        if 'status_updates' not in st.session_state:
            st.error("Session State nicht initialisiert. Bitte Seite neu laden.")
            st.stop()
        
        # Orchestrator IMMER frisch initialisieren
        from src.core.orchestrator import MineSearchOrchestratorV2
        self.orchestrator = MineSearchOrchestratorV2(self.config, self.session_manager)
        self._orchestrator_initialized = False
        
        # Create a container for dynamic button updates
        button_container = st.container()
        
        with button_container:
            # Search button and controls
            col1, col2, col3 = st.columns([2, 1, 1])
            
            with col1:
                # Start button - disabled during search
                search_clicked = st.button(
                    "🔍 Start Search",
                    type="primary",
                    disabled=(not mines_to_search or not selected_agents or 
                             st.session_state.get('search_in_progress', False)),
                    use_container_width=True,
                    key="start_search_button"
                )
                
                # ÄNDERUNG 23.06.2025: Sofortiges State Update nach Button-Click
                if search_clicked and mines_to_search and selected_agents:
                    st.session_state.search_in_progress = True
            
            with col2:
                # Cancel button - enabled during search
                # ÄNDERUNG 23.06.2025: Vereinfachter Cancel Button ohne Fragment
                is_searching = st.session_state.get('search_in_progress', False)
                
                # Cancel Button mit Hinweis
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
                    # ÄNDERUNG 26.06.2025: Verwende Global Registry für Cancel
                    registry = get_global_cancellation_registry()
                    
                    # Cancel via Registry
                    if st.session_state.get('search_id'):
                        cancelled = registry.cancel_search(st.session_state.search_id, "User clicked cancel")
                        if cancelled:
                            st.success("✅ Suche wurde abgebrochen")
                        else:
                            st.warning("⚠️ Keine aktive Suche gefunden")
                    
                    # Legacy: Cancel via session state token
                    if st.session_state.get('cancellation_token'):
                        st.session_state.cancellation_token.cancel()
                    
                    # Reset states
                    st.session_state.search_cancelled = True
                    st.session_state.search_in_progress = False
                    st.session_state.active_search_task = None
                    st.session_state.search_id = None
                    
                    st.rerun()
            
            with col3:
                # Clear results button
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
            # ÄNDERUNG 23.06.2025: State wird bereits oben gesetzt, direkt Search ausführen
            return self._perform_search(
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
    
    def _perform_search(self, mines_to_search: List[Dict], selected_agents: List[str],
                       advanced_options: Dict, status_container) -> List:
        """Führt die Suche aus mit UI-Updates für Cancel Button"""
        
        # Orchestrator IMMER frisch initialisieren
        from src.core.orchestrator import MineSearchOrchestratorV2
        try:
            self.orchestrator = MineSearchOrchestratorV2(self.config, self.session_manager)
            self._orchestrator_initialized = False
        except Exception as e:
            st.error(f"❌ Fehler beim Initialisieren des Orchestrators: {str(e)}")
            return []
        
        # Session-State-Initialisierung für Status-Updates und Fehlerdetails (erneut für neue Suchläufe)
        if 'status_updates' not in st.session_state:
            st.session_state.status_updates = []
        if 'error_details' not in st.session_state:
            st.session_state.error_details = []
        
        # ÄNDERUNG 26.06.2025: Erstelle eindeutige Search ID und registriere in Global Registry
        search_id = str(uuid.uuid4())
        st.session_state.search_id = search_id
        
        # Create new cancellation token with search ID
        from src.core.cancellation import CancellationToken
        cancellation_token = CancellationToken(name=f"search_{search_id}")
        st.session_state.cancellation_token = cancellation_token
        st.session_state.search_cancelled = False  # Reset cancel flag
        
        # Debug info
        if advanced_options.get('debug_mode', False):
            st.write(f"🔍 Debug: Starting search with {len(mines_to_search)} mines")
            st.write(f"🔍 Debug: Cancellation token created: {cancellation_token}")
            st.write(f"🔍 Debug: Is cancelled: {cancellation_token.is_cancelled()}")
            st.write(f"🔍 Debug: search_in_progress state: {st.session_state.get('search_in_progress', False)}")
            st.write(f"🔍 Debug: search_cancelled flag: {st.session_state.get('search_cancelled', False)}")
        
        try:
            # Show search info
            with status_container.container():
                st.info(f"🔍 Searching {len(mines_to_search)} mines with {len(selected_agents)} agents...")
                
                # Progress Component Container mit Auto-Refresh
                progress_placeholder = st.empty()
                
                # Legacy progress bar
                progress_bar = st.progress(0)
                cancel_hint = st.empty()
                cancel_hint.info("💡 Tipp: Drücke F5 oder aktualisiere die Seite, um die Suche abzubrechen")
            all_results = []
            
            # Reset progress component
            self.progress_component.reset()
            
            for idx, mine_data in enumerate(mines_to_search):
                if cancellation_token.is_cancelled() or st.session_state.get('search_cancelled', False):
                    st.warning("🛑 Search cancelled by user")
                    break
                
                # Update progress tracking
                progress = (idx + 1) / len(mines_to_search)
                progress_bar.progress(progress)
                
                # Reset mine search flag
                st.session_state.mine_search_completed = False
                st.session_state.current_search_mine = mine_data.get('mine_name', 'Unknown')
                
                # Initialize orchestrator once
                if not self._orchestrator_initialized:
                    try:
                        init_success = streamlit_run_async(self.orchestrator.initialize())
                        if not init_success:
                            st.error("❌ Orchestrator Initialisierung fehlgeschlagen")
                            break
                        self._orchestrator_initialized = True
                    except Exception as init_error:
                        st.error(f"❌ Fehler bei Orchestrator Initialisierung: {str(init_error)}")
                        break
                
                # Set context for status callback
                self.current_mine_index = idx
                self.total_mines = len(mines_to_search)
                
                # ÄNDERUNG 26.06.2025: Verwende asyncio.Task statt ThreadPoolExecutor
                # Dies ermöglicht echte Cancellation
                try:
                    # Erstelle Coroutine
                    search_coro = self._search_single_mine(
                        mine_data,
                        selected_agents,
                        cancellation_token
                    )
                    
                    # Verwende RegisteredSearch Context Manager
                    with RegisteredSearch(search_id, cancellation_token) as registered_search:
                        # Erstelle Task mit streamlit_run_async
                        import asyncio
                        
                        # Wrapper für async execution
                        async def search_wrapper():
                            try:
                                return await search_coro
                            except asyncio.CancelledError:
                                logger.info(f"Suche {mine_data['mine_name']} wurde abgebrochen")
                                raise
                        
                        # Führe Search aus mit Polling
                        search_completed = False
                        search_results = None
                        search_error = None
                        
                        # Start search in background
                        from src.utils.streamlit_async_wrapper import StreamlitEventLoopManager
                        loop_manager = StreamlitEventLoopManager()
                        
                        # Erstelle Future für async operation
                        import concurrent.futures
                        with concurrent.futures.ThreadPoolExecutor(max_workers=1) as executor:
                            # Submit the coroutine to run
                            future = executor.submit(loop_manager.run_coroutine, search_wrapper())
                            
                            # Polling loop mit verbesserter Cancellation
                            update_counter = 0
                            while not future.done():
                                # Update LiveProgress
                                with progress_placeholder:
                                    self.live_progress.render_with_polling(True)
                                
                                # Check multiple cancellation sources
                                is_cancelled = (
                                    cancellation_token.is_cancelled() or 
                                    st.session_state.get('search_cancelled', False) or
                                    not st.session_state.get('search_in_progress', True)
                                )
                                
                                if is_cancelled:
                                    # Cancel via registry (will handle everything)
                                    registry = get_global_cancellation_registry()
                                    registry.cancel_search(search_id, "Cancellation detected in polling loop")
                                    # Give time for cancellation to propagate
                                    time.sleep(0.1)
                                    break
                                    
                                time.sleep(0.5)  # Polling interval
                                update_counter += 1
                                
                                # Prevent infinite polling (max 5 minutes)
                                if update_counter > 600:
                                    st.warning("⏱️ Suche dauert länger als erwartet...")
                                    registry = get_global_cancellation_registry()
                                    registry.cancel_search(search_id, "Timeout")
                                    break
                            
                            # Get results
                            try:
                                if not cancellation_token.is_cancelled():
                                    results = future.result(timeout=1)
                                    if results:
                                        all_results.extend(results)
                            except concurrent.futures.TimeoutError:
                                st.error("⏱️ Timeout beim Abrufen der Ergebnisse")
                            except Exception as e:
                                if "CancelledError" not in str(e):
                                    st.error(f"❌ Error getting results: {str(e)}")
                except CancellationException:
                    st.warning("🛑 Search cancelled")
                    break
                except Exception as e:
                    st.error(f"❌ Error searching {mine_data['mine_name']}: {str(e)}")
            status_container.empty()
            if cancellation_token.is_cancelled():
                st.warning("🛑 Search was cancelled")
            elif all_results:
                st.success(f"✅ Search completed! Found {len(all_results)} results")
                st.balloons()
            else:
                st.warning("⚠️ No results found")
            return all_results
        finally:
            # ÄNDERUNG 26.06.2025: Cleanup via Registry
            registry = get_global_cancellation_registry()
            if search_id and registry.is_search_active(search_id):
                # Normale Beendigung - entferne aus Registry
                registry.cleanup_finished_searches()
            
            st.session_state.search_in_progress = False
            st.session_state.cancellation_token = None
            st.session_state.search_id = None
            st.session_state.active_search_task = None
    
    async def _search_single_mine(self, mine_data: Dict, selected_agents: List[str],
                                 cancellation_token) -> List:
        """Sucht eine einzelne Mine"""
        # Vor JEDEM Zugriff auf error_details initialisieren
        if 'error_details' not in st.session_state:
            st.session_state.error_details = []
        # Status-Callback: Nur Status in Session-State schreiben, keine UI-Elemente!
        def status_callback(message, phase=None, agent=None, partial_results=None):
            try:
                if 'status_updates' not in st.session_state:
                    st.session_state.status_updates = []
                from datetime import datetime
                st.session_state.status_updates.append({
                    'mine': mine_data['mine_name'],
                    'message': message,
                    'phase': phase,
                    'agent': agent,
                    'partial_results': partial_results,
                    'timestamp': datetime.now()
                })
                
                # Update live progress in session state (thread-safe)
                if 'live_progress' not in st.session_state:
                    st.session_state.live_progress = {
                        'results_found': 0
                    }
                
                st.session_state.live_progress.update({
                    'current_mine': mine_data['mine_name'],
                    'mine_index': getattr(self, 'current_mine_index', 0),
                    'total_mines': getattr(self, 'total_mines', 1),
                    'phase': phase or st.session_state.live_progress.get('phase', 'Initialisierung'),
                    'agent': agent or st.session_state.live_progress.get('agent', ''),
                    'status_message': message,
                    'partial_results': partial_results or []
                })
                
                # Count total results found
                if partial_results:
                    current_count = st.session_state.live_progress.get('results_found', 0)
                    st.session_state.live_progress['results_found'] = current_count + len(partial_results)
                        
            except Exception as e:
                print(f"[Status-Callback] Fehler beim Status-Update: {e}")
        if not self.orchestrator:
            raise Exception("Orchestrator not initialized")
        self.orchestrator.status_callback = status_callback
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
            status_callback(f"🔍 Starting search for {query.mine_name}")
            results = await self.orchestrator.search_mine(query, search_params)
            status_callback(f"✅ Found {len(results) if results else 0} results")
            return results
        except CancellationException:
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            status_callback(f"❌ Error: {str(e)}")
            # Defensive Initialisierung auch im Exception-Handler
            if 'error_details' not in st.session_state:
                st.session_state.error_details = []
            st.session_state.error_details.append({
                'mine': mine_data['mine_name'],
                'error': error_details,
                'timestamp': datetime.now()
            })
            return []