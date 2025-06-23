"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Search Form Komponente für MineSearch UI
"""
import streamlit as st
from typing import Dict, List, Optional, Callable
import asyncio
from src.agents.base_agent import MineQuery
from src.core.orchestrator import MineSearchOrchestrator
from src.core.cancellation import CancellationToken, CancellationException


class SearchFormComponent:
    """Such-Formular mit Status-Updates und Cancellation"""
    
    def __init__(self, config):
        self.config = config
        self.cancellation_token = None
        
    def render(self, mines_to_search: List[Dict], selected_agents: List[str], 
               advanced_options: Dict) -> Optional[List]:
        """Rendert das Such-Formular und führt Suche aus"""
        
        # Search button and controls
        col1, col2, col3 = st.columns([2, 1, 1])
        
        with col1:
            search_clicked = st.button(
                "🔍 Start Search",
                type="primary",
                disabled=not mines_to_search or not selected_agents,
                use_container_width=True
            )
        
        with col2:
            if st.session_state.get('search_in_progress', False):
                if st.button("⏸️ Cancel Search", type="secondary", use_container_width=True):
                    if self.cancellation_token:
                        self.cancellation_token.cancel()
                        st.warning("🛑 Cancelling search...")
        
        with col3:
            if st.session_state.get('search_results', []):
                if st.button("🗑️ Clear Results", use_container_width=True):
                    st.session_state.search_results = []
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
        """Führt die Suche aus"""
        
        # Initialize search state
        st.session_state.search_in_progress = True
        self.cancellation_token = CancellationToken()
        
        try:
            # Show search info
            with status_container.container():
                st.info(f"🔍 Searching {len(mines_to_search)} mines with {len(selected_agents)} agents...")
                
                # Progress tracking
                progress_bar = st.progress(0)
                status_text = st.empty()
            
            # Collect all results
            all_results = []
            
            for idx, mine_data in enumerate(mines_to_search):
                if self.cancellation_token.is_cancelled:
                    st.warning("🛑 Search cancelled by user")
                    break
                
                # Update progress
                progress = (idx + 1) / len(mines_to_search)
                progress_bar.progress(progress)
                
                # Create status placeholder for this mine
                mine_status = status_container.empty()
                
                # Run async search
                try:
                    results = asyncio.run(
                        self._search_single_mine(
                            mine_data,
                            selected_agents,
                            mine_status,
                            self.cancellation_token
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
            
            if all_results:
                st.success(f"✅ Search completed! Found {len(all_results)} results")
                st.balloons()
            else:
                st.warning("⚠️ No results found")
            
            return all_results
            
        finally:
            st.session_state.search_in_progress = False
            self.cancellation_token = None
    
    async def _search_single_mine(self, mine_data: Dict, selected_agents: List[str],
                                 status_placeholder, cancellation_token) -> List:
        """Sucht eine einzelne Mine"""
        
        # Status callback
        def status_callback(message):
            if status_placeholder:
                with status_placeholder.container():
                    st.write(f"**{mine_data['mine_name']}**: {message}")
        
        # Create orchestrator
        orchestrator = MineSearchOrchestrator(self.config, status_callback=status_callback)
        
        # Initialize
        await orchestrator.initialize()
        
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
            results = await orchestrator.search_mine_staged(query, search_params)
            return results
        except CancellationException:
            raise
        except Exception as e:
            status_callback(f"❌ Error: {str(e)}")
            return []