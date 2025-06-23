"""
Author: rahn
Datum: 23.06.2025
Version: 1.2
Beschreibung: Search Form Komponente für MineSearch UI
ÄNDERUNG 23.06.2025: Event Loop Fix mit async_utils
"""
import streamlit as st
from typing import Dict, List, Optional, Callable
import time
from src.agents.base_agent import MineQuery
from src.core.orchestrator import MineSearchOrchestratorV2
from src.core.cancellation import CancellationToken, CancellationException
from src.core.async_utils import run_async


class SearchFormComponent:
    """Such-Formular mit Status-Updates und Cancellation"""
    
    def __init__(self, config):
        self.config = config
        self.cancellation_token = None
        self.orchestrator = None
        self._orchestrator_initialized = False
        
    def render(self, mines_to_search: List[Dict], selected_agents: List[str], 
               advanced_options: Dict) -> Optional[List]:
        """Rendert das Such-Formular und führt Suche aus"""
        
        # Initialize cancellation token in session state if needed
        if 'cancellation_token' not in st.session_state:
            st.session_state.cancellation_token = None
        
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
                
                if cancel_clicked and st.session_state.get('cancellation_token'):
                    st.session_state.cancellation_token.cancel()
                    st.warning("🛑 Suche wird abgebrochen...")
                    st.session_state.search_in_progress = False
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
            # Set search in progress state BEFORE calling the search function
            st.session_state.search_in_progress = True
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
        
        # Create new cancellation token and store in session state
        from src.core.cancellation import CancellationToken
        cancellation_token = CancellationToken()
        st.session_state.cancellation_token = cancellation_token
        
        # Debug info
        if advanced_options.get('debug_mode', False):
            st.write(f"🔍 Debug: Starting search with {len(mines_to_search)} mines")
            st.write(f"🔍 Debug: Cancellation token created: {cancellation_token}")
            st.write(f"🔍 Debug: Is cancelled: {cancellation_token.is_cancelled()}")
            st.write(f"🔍 Debug: search_in_progress state: {st.session_state.get('search_in_progress', False)}")
        
        try:
            # Show search info
            with status_container.container():
                st.info(f"🔍 Searching {len(mines_to_search)} mines with {len(selected_agents)} agents...")
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # ÄNDERUNG 23.06.2025: Zeige Cancel-Hinweis während Suche
                cancel_hint = st.empty()
                cancel_hint.info("💡 Tipp: Drücke F5 oder aktualisiere die Seite, um die Suche abzubrechen")
            
            # Collect all results
            all_results = []
            
            for idx, mine_data in enumerate(mines_to_search):
                # Check cancellation with small delay to allow UI updates
                if cancellation_token.is_cancelled():
                    st.warning("🛑 Search cancelled by user")
                    break
                
                # ÄNDERUNG 23.06.2025: Optimierte Pause für UI-Updates
                time.sleep(0.2)  # Reduziert für bessere Reaktionsfähigkeit
                
                # Update progress
                progress = (idx + 1) / len(mines_to_search)
                progress_bar.progress(progress)
                
                # ÄNDERUNG 23.06.2025: Erweiterte Status-Anzeige mit Cancel-Info
                status_message = f"Searching mine {idx + 1} of {len(mines_to_search)}"
                if idx % 3 == 0:  # Alle 3 Minen
                    status_message += " | 💡 Tipp: F5 drücken zum Abbrechen"
                status_text.text(status_message)
                
                # Create status placeholder for this mine
                mine_status = status_container.empty()
                
                # Initialize orchestrator once
                if not self._orchestrator_initialized:
                    self.orchestrator = MineSearchOrchestratorV2(self.config)
                    # ÄNDERUNG 23.06.2025: Verwende Event Loop Manager statt asyncio.run
                    run_async(self.orchestrator.initialize())
                    self._orchestrator_initialized = True
                
                # Run async search
                try:
                    # ÄNDERUNG 23.06.2025: Verwende Event Loop Manager für konsistenten Event Loop
                    results = run_async(
                        self._search_single_mine(
                            mine_data,
                            selected_agents,
                            mine_status,
                            cancellation_token
                        )
                    )
                    
                    if results:
                        all_results.extend(results)
                        
                except CancellationException:
                    st.warning("🛑 Search cancelled")
                    break
                except Exception as e:
                    st.error(f"❌ Error searching {mine_data['mine_name']}: {str(e)}")
            
            # Clear status and show completion
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
            st.session_state.search_in_progress = False
            st.session_state.cancellation_token = None
    
    async def _search_single_mine(self, mine_data: Dict, selected_agents: List[str],
                                 status_placeholder, cancellation_token) -> List:
        """Sucht eine einzelne Mine"""
        
        # Status callback
        def status_callback(message):
            if status_placeholder:
                with status_placeholder.container():
                    st.write(f"**{mine_data['mine_name']}**: {message}")
        
        # Use existing orchestrator
        if not self.orchestrator:
            raise Exception("Orchestrator not initialized")
        
        # Set status callback for this mine
        self.orchestrator.status_callback = status_callback
        
        # Create query
        query = MineQuery(
            mine_name=mine_data['mine_name'],
            region=mine_data['region'],
            country=mine_data['country'],
            languages=["en", "fr", "es", "de"],
            required_fields=[
                # Core fields
                "betreiber", "operator", "owner",
                "koordinaten", "coordinates", "location",
                "rohstofftyp", "commodity", "mineral",
                "aktivitaetsstatus", "status",
                
                # Financial/Environmental
                "sanierungskosten", "remediation_costs",
                "environmental_liability", "restoration_costs",
                
                # Production
                "production_start", "production_end",
                "reserve", "resource",
                
                # Technical
                "mining_method", "processing",
                "capacity", "recovery_rate"
            ]
        )
        
        # Search parameters
        search_params = {
            "enhanced": True,
            "agent_types": selected_agents,
            "include_sources": True,
            "cancellation_token": cancellation_token
        }
        
        # Perform search
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
            if status_placeholder:
                with status_placeholder.container():
                    st.error(f"Full error:\n{error_details}")
            return []