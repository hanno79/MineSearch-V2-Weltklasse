"""
Author: rahn
Datum: 23.06.2025
Version: 2.0
Beschreibung: Optimized Search Form Component mit verbesserter Cancel-Reaktionszeit
"""
import streamlit as st
from typing import Dict, List, Optional, Callable
import asyncio
import time
from src.agents.base_agent import MineQuery
from src.core.orchestrator import MineSearchOrchestratorV2
from src.core.cancellation_optimized import OptimizedCancellationToken, CancellationException, OptimizedCancellationScope
from src.core.async_utils import run_async


class OptimizedSearchFormComponent:
    """Optimiertes Such-Formular mit schneller Cancel-Reaktion"""
    
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
                
                # Sofortiges State Update nach Button-Click
                if search_clicked and mines_to_search and selected_agents:
                    st.session_state.search_in_progress = True
            
            with col2:
                # Cancel button - enabled during search
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
                    # Sofortige Cancel-Reaktion ohne Delays
                    if st.session_state.get('cancellation_token'):
                        st.session_state.cancellation_token.cancel("User clicked cancel button")
                    st.session_state.search_cancelled = True
                    st.session_state.search_in_progress = False
                    st.warning("🛑 Suche wird abgebrochen...")
                    # Kein rerun() hier - lasse die Suche selbst das handling übernehmen
            
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
        """Führt die Suche aus mit optimierter Cancel-Reaktion"""
        
        # Create new optimized cancellation token
        from src.core.cancellation_optimized import OptimizedCancellationToken
        cancellation_token = OptimizedCancellationToken("search")
        st.session_state.cancellation_token = cancellation_token
        
        # Reset cancel flag
        st.session_state.search_cancelled = False
        
        # Debug info
        if advanced_options.get('debug_mode', False):
            st.write(f"🔍 Debug: Starting search with {len(mines_to_search)} mines")
            st.write(f"🔍 Debug: Using OptimizedCancellationToken")
            st.write(f"🔍 Debug: Cancel reaction time: <10ms")
        
        try:
            # Show search info
            with status_container.container():
                st.info(f"🔍 Searching {len(mines_to_search)} mines with {len(selected_agents)} agents...")
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
                
                # Zeige Cancel-Hinweis während Suche
                cancel_hint = st.empty()
                cancel_hint.info("💡 Tipp: Klicke den Cancel-Button für sofortigen Abbruch")
            
            # Collect all results
            all_results = []
            
            # Async search mit optimierter Cancel-Prüfung
            async def search_all_mines():
                for idx, mine_data in enumerate(mines_to_search):
                    # Check cancellation ohne Delay
                    await cancellation_token.check_cancelled()
                    
                    # Update progress
                    progress = (idx + 1) / len(mines_to_search)
                    progress_bar.progress(progress)
                    
                    # Status update
                    status_text.text(f"Searching mine {idx + 1} of {len(mines_to_search)}")
                    
                    # Create status placeholder for this mine
                    mine_status = status_container.empty()
                    
                    # Initialize orchestrator once
                    if not self._orchestrator_initialized:
                        self.orchestrator = MineSearchOrchestratorV2(self.config)
                        await self.orchestrator.initialize()
                        self._orchestrator_initialized = True
                    
                    # Search with cancellation scope
                    async with OptimizedCancellationScope(cancellation_token) as scope:
                        try:
                            results = await self._search_single_mine(
                                mine_data,
                                selected_agents,
                                mine_status,
                                cancellation_token
                            )
                            
                            if results:
                                all_results.extend(results)
                                
                        except CancellationException:
                            st.warning(f"🛑 Search cancelled at mine {idx + 1} of {len(mines_to_search)}")
                            raise
                
                return all_results
            
            # Run async search mit exception handling
            try:
                results = run_async(search_all_mines())
                all_results = results if results else []
            except CancellationException:
                st.warning("🛑 Search was cancelled by user")
            
            # Clear status and show completion
            status_container.empty()
            
            if cancellation_token.is_cancelled():
                cancel_info = cancellation_token.get_cancel_info()
                st.warning(f"🛑 Search was cancelled: {cancel_info.get('cancel_reason', 'Unknown reason')}")
            elif all_results:
                st.success(f"✅ Search completed! Found {len(all_results)} results")
                st.balloons()
            else:
                st.warning("⚠️ No results found")
            
            return all_results
            
        finally:
            # Cleanup
            st.session_state.search_in_progress = False
            st.session_state.cancellation_token = None
            if cancellation_token:
                cancellation_token.cleanup()
    
    async def _search_single_mine(self, mine_data: Dict, selected_agents: List[str],
                                 status_placeholder, cancellation_token) -> List:
        """Sucht eine einzelne Mine mit optimierter Cancellation"""
        
        # Status callback mit cancellation check
        def status_callback(message):
            # Quick cancellation check
            if cancellation_token.is_cancelled():
                raise CancellationException("Cancelled during status update")
                
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
        
        # Search parameters with cancellation token
        search_params = {
            "enhanced": True,
            "agent_types": selected_agents,
            "include_sources": True,
            "cancellation_token": cancellation_token
        }
        
        # Perform search mit cancellation handling
        try:
            # Register current task with cancellation token
            current_task = asyncio.current_task()
            if current_task:
                cancellation_token.register_task(current_task)
            
            status_callback(f"🔍 Starting search for {query.mine_name}")
            results = await self.orchestrator.search_mine(query, search_params)
            status_callback(f"✅ Found {len(results) if results else 0} results")
            return results
            
        except CancellationException:
            status_callback("🛑 Cancelled")
            raise
        except Exception as e:
            import traceback
            error_details = traceback.format_exc()
            status_callback(f"❌ Error: {str(e)}")
            if status_placeholder:
                with status_placeholder.container():
                    st.error(f"Full error:\n{error_details}")
            return []