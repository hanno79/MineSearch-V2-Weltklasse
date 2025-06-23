"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Search Handler für Business Logic
"""
import asyncio
from typing import List, Dict, Optional, Callable
from datetime import datetime
import logging

from ...agents.base_agent import MineQuery
from ...core.orchestrator import MineSearchOrchestrator
from ...core.cancellation import CancellationToken, CancellationException
from ...core.config import Config
from ...core.logger import get_logger


class SearchHandler:
    """Handles search business logic separate from UI"""
    
    def __init__(self, config: Config):
        self.config = config
        self.logger = get_logger("search_handler")
        
    async def search_mines(
        self,
        mines_to_search: List[Dict],
        selected_agents: List[str],
        advanced_options: Dict,
        status_callback: Optional[Callable] = None,
        cancellation_token: Optional[CancellationToken] = None
    ) -> List[Dict]:
        """
        Execute search for multiple mines
        
        Args:
            mines_to_search: List of mine dictionaries with name, region, country
            selected_agents: List of agent types to use
            advanced_options: Advanced search options
            status_callback: Callback for status updates
            cancellation_token: Token for search cancellation
            
        Returns:
            List of search results
        """
        all_results = []
        start_time = datetime.now()
        
        for idx, mine_data in enumerate(mines_to_search):
            if cancellation_token and cancellation_token.is_cancelled:
                self.logger.info("Search cancelled by user")
                break
            
            # Update progress
            if status_callback:
                progress = (idx + 1) / len(mines_to_search)
                status_callback({
                    'type': 'progress',
                    'progress': progress,
                    'mine': mine_data['mine_name'],
                    'status': f"Searching mine {idx + 1} of {len(mines_to_search)}"
                })
            
            try:
                # Search single mine
                mine_results = await self._search_single_mine(
                    mine_data,
                    selected_agents,
                    advanced_options,
                    status_callback,
                    cancellation_token
                )
                
                if mine_results:
                    all_results.extend(mine_results)
                    
            except CancellationException:
                self.logger.info("Search cancelled")
                break
            except Exception as e:
                self.logger.error(f"Error searching {mine_data['mine_name']}: {str(e)}")
                if status_callback:
                    status_callback({
                        'type': 'error',
                        'mine': mine_data['mine_name'],
                        'error': str(e)
                    })
        
        # Final status
        duration = (datetime.now() - start_time).total_seconds()
        if status_callback:
            status_callback({
                'type': 'complete',
                'total_results': len(all_results),
                'duration': duration,
                'mines_searched': len(mines_to_search)
            })
        
        return all_results
    
    async def _search_single_mine(
        self,
        mine_data: Dict,
        selected_agents: List[str],
        advanced_options: Dict,
        status_callback: Optional[Callable],
        cancellation_token: Optional[CancellationToken]
    ) -> List[Dict]:
        """Search a single mine"""
        
        # Create mine-specific status callback
        def mine_status_callback(message):
            if status_callback:
                status_callback({
                    'type': 'mine_status',
                    'mine': mine_data['mine_name'],
                    'message': message
                })
        
        # Create orchestrator
        orchestrator = MineSearchOrchestrator(
            self.config,
            status_callback=mine_status_callback
        )
        
        # Initialize orchestrator
        await orchestrator.initialize()
        
        # Build query
        query = self._build_query(mine_data, advanced_options)
        
        # Build search parameters
        search_params = self._build_search_params(
            selected_agents,
            advanced_options,
            cancellation_token
        )
        
        # Execute search
        try:
            results = await orchestrator.search_mine_staged(query, search_params)
            return results
        except Exception as e:
            self.logger.error(f"Search failed for {mine_data['mine_name']}: {e}")
            raise
    
    def _build_query(self, mine_data: Dict, advanced_options: Dict) -> MineQuery:
        """Build MineQuery from mine data and options"""
        
        # Base fields
        required_fields = [
            # Core identification
            "betreiber", "operator", "owner", "company",
            "koordinaten", "coordinates", "location", "GPS",
            "rohstofftyp", "commodity", "mineral", "resource",
            "aktivitaetsstatus", "status", "operational_status",
            
            # Financial/Environmental
            "sanierungskosten", "remediation_costs", "closure_costs",
            "rehabilitation", "environmental_liability", "restoration_costs",
            "environmental_bond", "financial_assurance",
            
            # Production
            "production_start", "production_end", "mine_life", "closure_date",
            "reserve", "resource", "production_volume",
            
            # Technical
            "mining_method", "processing_method", "capacity",
            "recovery_rate", "depth", "area"
        ]
        
        # Add additional fields for deep search
        if advanced_options.get('deep_search'):
            required_fields.extend([
                "employment", "workforce", "contractors",
                "water_usage", "energy_consumption", "emissions",
                "community_investment", "taxes", "royalties",
                "incidents", "safety_record", "certifications"
            ])
        
        # Languages based on country
        languages = self._get_languages_for_country(mine_data.get('country', ''))
        
        return MineQuery(
            mine_name=mine_data['mine_name'],
            region=mine_data.get('region', ''),
            country=mine_data.get('country', ''),
            languages=languages,
            required_fields=required_fields
        )
    
    def _build_search_params(
        self,
        selected_agents: List[str],
        advanced_options: Dict,
        cancellation_token: Optional[CancellationToken]
    ) -> Dict:
        """Build search parameters"""
        
        params = {
            "enhanced": True,
            "agent_types": selected_agents,
            "include_sources": True,
            "cancellation_token": cancellation_token,
            "timeout": advanced_options.get('timeout', 120),
            "parallel": advanced_options.get('parallel', True)
        }
        
        # Add deep search params
        if advanced_options.get('deep_search'):
            params.update({
                "max_depth": 3,
                "follow_links": True,
                "extract_documents": True
            })
        
        return params
    
    def _get_languages_for_country(self, country: str) -> List[str]:
        """Get relevant languages for a country"""
        
        # Country to languages mapping
        country_languages = {
            'canada': ['en', 'fr'],
            'usa': ['en', 'es'],
            'united states': ['en', 'es'],
            'mexico': ['es', 'en'],
            'brazil': ['pt', 'en'],
            'chile': ['es', 'en'],
            'peru': ['es', 'en'],
            'australia': ['en'],
            'south africa': ['en', 'af'],
            'germany': ['de', 'en'],
            'france': ['fr', 'en'],
            'spain': ['es', 'en'],
            'russia': ['ru', 'en'],
            'china': ['zh', 'en'],
            'india': ['en', 'hi']
        }
        
        # Get languages for country (case insensitive)
        country_lower = country.lower()
        for key, langs in country_languages.items():
            if key in country_lower:
                return langs
        
        # Default to English + local language detection
        return ['en', 'local']