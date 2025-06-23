"""
Author: rahn
Datum: 22.06.2025
Version: 1.0
Beschreibung: Hauptklasse für Premium Mining Research
"""

from typing import List, Dict, Any, Optional
from datetime import datetime

from ..base_agent import BaseAgent, MineQuery, SearchResult
from .models import ResearchMetadata, QualityIndicators
from .research_phases import ResearchPhaseManager
from .query_optimizer import QueryOptimizer
from src.core.logger import get_logger


class PremiumMiningResearch(BaseAgent):
    """
    Premium Mining Research System
    
    - KEINE hardcodierten Listen
    - Dynamische Quellenentdeckung
    - Multi-Layer Crawling
    - Intelligente Keyword-Generierung
    - Flexibel für ALLE Länder
    """
    
    def __init__(self, name: str, config: Dict[str, Any], agents: Dict[str, BaseAgent] = None):
        super().__init__(name, config)
        self.agents = agents or {}
        
        # ÄNDERUNG 17.06.2025: Integration aller Premium-Komponenten
        self.phase_manager = ResearchPhaseManager(agents, config)
        self.query_optimizer = QueryOptimizer(agents)
        
        # Logger
        self.logger = get_logger(f"agent.{name}", agent_type="premium_research")
    
    async def search(self, query: MineQuery) -> List[SearchResult]:
        """Führt Premium-Recherche durch"""
        results = await self.research_mine(query)
        
        # Konvertiere zu SearchResult Format
        search_results = []
        mine_data = results.get("mine_data", {})
        
        for field, values in mine_data.items():
            if isinstance(values, list):
                for value_info in values:
                    search_results.append(SearchResult(
                        field_name=field,
                        value=value_info.get("value"),
                        source=value_info.get("source", "Premium Research"),
                        confidence_score=value_info.get("confidence", 0.8),
                        metadata=value_info.get("metadata", {})
                    ))
            else:
                # Einzelwert
                search_results.append(SearchResult(
                    field_name=field,
                    value=values,
                    source="Premium Research",
                    confidence_score=0.8,
                    metadata={}
                ))
        
        return search_results
    
    async def research_mine(self, query: MineQuery) -> Dict[str, Any]:
        """
        Führt Premium-Recherche für eine Mine durch
        
        Vollständig dynamisch und flexibel!
        """
        research_id = f"{query.mine_name}_{query.country}_{datetime.now().isoformat()}"
        
        self.logger.info(f"\n🚀 Starte Premium Mining Research für: {query.mine_name}")
        self.logger.info(f"Land: {query.country}, Region: {query.region}")
        self.logger.info(f"Sprachen: {', '.join(query.languages)}")
        
        all_results = []
        research_metadata = ResearchMetadata(start_time=datetime.now())
        
        # ÄNDERUNG 17.06.2025: Umfassende Fehlerbehandlung
        try:
            # Phase 1: Discovery - Entdecke Quellen dynamisch
            self.logger.info("\n📍 Phase 1: Dynamische Quellenentdeckung...")
            discovered_sources = await self.phase_manager.execute_discovery_phase(query)
            research_metadata.sources_discovered = len(discovered_sources)
            research_metadata.phases_completed.append("Discovery")
            self.logger.info(f"✅ {len(discovered_sources)} relevante Quellen entdeckt")
            
            # Phase 2: Keyword-Generierung
            self.logger.info("\n🔤 Phase 2: Intelligente Keyword-Generierung...")
            keywords = await self.phase_manager.execute_keyword_generation(query, discovered_sources)
            research_metadata.keywords_used = sum(len(kw_list) for kw_list in keywords.values())
            research_metadata.phases_completed.append("Keyword_Generation")
            self.logger.info(f"✅ {research_metadata.keywords_used} Keywords in {len(query.languages)} Sprachen generiert")
            
            # Phase 3: Deep Dive - Tauche tief ein
            self.logger.info("\n🏊 Phase 3: Deep Web Crawling...")
            crawl_results = await self.phase_manager.execute_deep_dive(query, discovered_sources, keywords)
            research_metadata.documents_analyzed = len(crawl_results)
            research_metadata.phases_completed.append("Deep_Dive")
            self.logger.info(f"✅ {len(crawl_results)} Dokumente/Seiten analysiert")
            
            # Phase 4: Intelligente Suche mit optimierten Queries
            self.logger.info("\n🔍 Phase 4: Intelligente Multi-Agent Suche...")
            search_results = await self.phase_manager.execute_intelligent_search(
                query, keywords, discovered_sources, self.query_optimizer
            )
            all_results.extend(search_results)
            research_metadata.phases_completed.append("Intelligent_Search")
            self.logger.info(f"✅ {len(search_results)} Suchergebnisse gefunden")
            
            # Phase 5: Analyse komplexer Dokumente
            self.logger.info("\n🧠 Phase 5: KI-gestützte Dokumentenanalyse...")
            analysis_results = await self.phase_manager.execute_analysis_phase(query, crawl_results)
            all_results.extend(analysis_results)
            research_metadata.phases_completed.append("Analysis")
            self.logger.info(f"✅ {len(analysis_results)} zusätzliche Erkenntnisse gewonnen")
            
            # Phase 6: Verifikation und Konsolidierung
            self.logger.info("\n✓ Phase 6: Ergebnisverifikation...")
            verified_results = await self.phase_manager.execute_verification_phase(all_results, query)
            research_metadata.phases_completed.append("Verification")
            
            # Finale Aggregation mit Mehrfachwerten
            self.logger.info("\n📊 Finale Aggregation...")
            final_results = self._aggregate_premium_results(verified_results)
            
            research_metadata.end_time = datetime.now()
            research_metadata.total_duration = (
                research_metadata.end_time - research_metadata.start_time
            ).total_seconds()
            
            self.logger.info(f"\n✨ Premium Research abgeschlossen in {research_metadata.total_duration:.1f} Sekunden")
            self.logger.info(f"📈 Gefundene Felder: {len(final_results)}")
            
            return {
                "mine_data": final_results,
                "research_metadata": research_metadata.__dict__,
                "discovered_sources": [
                    {
                        "url": s.url,
                        "type": s.source_type.value,
                        "relevance": s.relevance_score
                    }
                    for s in discovered_sources[:10]  # Top 10
                ],
                "quality_indicators": self._calculate_quality_indicators(final_results).__dict__
            }
            
        except Exception as e:
            self.logger.error(f"❌ Kritischer Fehler in Premium Research: {e}")
            research_metadata.errors.append(str(e))
            research_metadata.end_time = datetime.now()
            
            # Gebe teil-Ergebnisse zurück wenn möglich
            return {
                "mine_data": self._aggregate_premium_results(all_results) if all_results else {},
                "research_metadata": research_metadata.__dict__,
                "discovered_sources": [],
                "quality_indicators": {},
                "error": str(e)
            }
    
    def _aggregate_premium_results(self, results: List[SearchResult]) -> Dict[str, Any]:
        """
        Aggregiert Ergebnisse mit Unterstützung für Mehrfachwerte
        
        Premium-Feature: Behält alle relevanten Werte mit Metadaten
        """
        aggregated = {}
        
        # Gruppiere nach Feld
        field_results = {}
        for result in results:
            field = result.field_name
            field_results.setdefault(field, []).append(result)
        
        # Aggregiere mit Premium-Features
        for field, field_data in field_results.items():
            if len(field_data) == 1:
                # Einzelwert
                result = field_data[0]
                aggregated[field] = {
                    "value": result.value,
                    "source": result.source,
                    "confidence": result.confidence_score,
                    "metadata": result.metadata
                }
            else:
                # Mehrfachwerte - Premium Feature
                # Sortiere nach Konfidenz
                sorted_data = sorted(field_data, key=lambda x: x.confidence_score, reverse=True)
                
                # Dedupliziere aber behalte Varianten
                unique_values = {}
                for result in sorted_data:
                    value_key = str(result.value).lower().strip()
                    
                    if value_key not in unique_values:
                        unique_values[value_key] = []
                    
                    unique_values[value_key].append({
                        "value": result.value,
                        "source": result.source,
                        "confidence": result.confidence_score,
                        "metadata": result.metadata
                    })
                
                # Wenn alle Werte übereinstimmen (normalisiert)
                if len(unique_values) == 1:
                    # Nehme Version mit höchster Konfidenz
                    best_variant = sorted_data[0]
                    aggregated[field] = {
                        "value": best_variant.value,
                        "source": best_variant.source,
                        "confidence": best_variant.confidence_score,
                        "metadata": best_variant.metadata,
                        "consensus": True,
                        "source_count": len(sorted_data)
                    }
                else:
                    # Mehrere unterschiedliche Werte - behalte alle
                    all_variants = []
                    for value_variants in unique_values.values():
                        # Beste Variante pro unique value
                        best = max(value_variants, key=lambda x: x["confidence"])
                        all_variants.append(best)
                    
                    # Sortiere nach Konfidenz
                    all_variants.sort(key=lambda x: x["confidence"], reverse=True)
                    
                    aggregated[field] = all_variants
        
        return aggregated
    
    def _calculate_quality_indicators(self, results: Dict[str, Any]) -> QualityIndicators:
        """Berechnet Qualitätsindikatoren für die Recherche"""
        # Berechne Vollständigkeit
        total_fields = len(results)
        fields_with_high_confidence = sum(
            1 for field_data in results.values()
            if isinstance(field_data, dict) and field_data.get("confidence", 0) > 0.8
        )
        completeness = fields_with_high_confidence / total_fields if total_fields > 0 else 0
        
        # Berechne Quellen-Diversität
        all_sources = set()
        for field_data in results.values():
            if isinstance(field_data, dict):
                all_sources.add(field_data.get("source", "unknown"))
            elif isinstance(field_data, list):
                for item in field_data:
                    all_sources.add(item.get("source", "unknown"))
        
        source_diversity = min(len(all_sources) / 10, 1.0)  # Normalisiert auf max 10 Quellen
        
        # Berechne durchschnittliche Konfidenz
        confidence_values = []
        for field_data in results.values():
            if isinstance(field_data, dict):
                confidence_values.append(field_data.get("confidence", 0))
            elif isinstance(field_data, list):
                for item in field_data:
                    confidence_values.append(item.get("confidence", 0))
        
        avg_confidence = sum(confidence_values) / len(confidence_values) if confidence_values else 0
        
        # Berechne Verifikations-Ratio
        verified_fields = sum(
            1 for field_data in results.values()
            if isinstance(field_data, dict) and field_data.get("consensus", False)
        )
        verification_ratio = verified_fields / total_fields if total_fields > 0 else 0
        
        # Sprach-Abdeckung (vereinfacht)
        language_coverage = 1.0  # Würde basierend auf tatsächlichen Sprachen berechnet
        
        return QualityIndicators(
            completeness_score=completeness,
            source_diversity=source_diversity,
            confidence_average=avg_confidence,
            verification_ratio=verification_ratio,
            language_coverage=language_coverage
        )