"""
Author: rahn
Datum: 18.06.2025
Version: 1.0
Beschreibung: Manager für Quellenverwaltung bei Mining-Recherche
"""

from typing import Dict, List, Set, Optional
from dataclasses import dataclass, field
from datetime import datetime
import json

@dataclass
class SourceInfo:
    """Information über eine gefundene Quelle"""
    url: str
    source_type: str  # government, company, news, technical_report, database
    relevance_score: float = 1.0
    found_by_agents: List[str] = field(default_factory=list)
    applicable_mines: List[str] = field(default_factory=list)
    discovered_at: datetime = field(default_factory=datetime.now)
    meta_data: Dict = field(default_factory=dict)
    discovered_by: str = ""

class SourceManager:
    """Verwaltet gefundene Quellen für Mining-Recherche"""
    
    def __init__(self):
        # Quellen pro Mine
        self.mine_sources: Dict[str, List[SourceInfo]] = {}
        
        # Globale Quellen (z.B. Regierungsseiten)
        self.global_sources: List[SourceInfo] = []
        
        # Cache für bereits geprüfte URLs
        self.checked_urls: Set[str] = set()
        
    def add_source(self, mine_name: str, source: SourceInfo, is_global: bool = False):
        """Fügt eine neue Quelle hinzu"""
        if source.url in self.checked_urls:
            # URL bereits bekannt, füge nur Mine hinzu
            if mine_name not in source.applicable_mines:
                source.applicable_mines.append(mine_name)
            return
            
        self.checked_urls.add(source.url)
        source.applicable_mines.append(mine_name)
        
        if is_global or self._is_global_source(source):
            self.global_sources.append(source)
        else:
            if mine_name not in self.mine_sources:
                self.mine_sources[mine_name] = []
            self.mine_sources[mine_name].append(source)
    
    def _is_global_source(self, source: SourceInfo) -> bool:
        """Prüft ob eine Quelle global relevant ist"""
        global_indicators = [
            'government', 'gov.', '.gov', 
            'ministry', 'department',
            'statistics', 'census',
            'environmental', 'mining-association'
        ]
        
        url_lower = source.url.lower()
        type_lower = source.source_type.lower()
        
        return any(indicator in url_lower or indicator in type_lower 
                  for indicator in global_indicators)
    
    def get_sources_for_mine(self, mine_name: str) -> List[SourceInfo]:
        """Gibt alle relevanten Quellen für eine Mine zurück"""
        mine_specific = self.mine_sources.get(mine_name, [])
        
        # Füge globale Quellen hinzu
        relevant_global = [s for s in self.global_sources 
                          if mine_name in s.applicable_mines or 
                          len(s.applicable_mines) == 0]  # Noch nicht zugeordnet
        
        return mine_specific + relevant_global
    
    def get_sources_by_type(self, mine_name: str, source_type: str) -> List[SourceInfo]:
        """Gibt Quellen eines bestimmten Typs zurück"""
        all_sources = self.get_sources_for_mine(mine_name)
        return [s for s in all_sources if s.source_type == source_type]
    
    def get_top_sources(self, mine_name: str, limit: int = 10) -> List[SourceInfo]:
        """Gibt die relevantesten Quellen zurück"""
        all_sources = self.get_sources_for_mine(mine_name)
        # Sortiere nach Relevanz und Anzahl der Agenten die sie gefunden haben
        sorted_sources = sorted(
            all_sources, 
            key=lambda s: (s.relevance_score, len(s.found_by_agents)),
            reverse=True
        )
        return sorted_sources[:limit]
    
    def mark_source_used(self, url: str, success: bool = True):
        """Markiert eine Quelle als verwendet"""
        # Finde die Quelle
        for sources in self.mine_sources.values():
            for source in sources:
                if source.url == url:
                    source.meta_data['used'] = True
                    source.meta_data['success'] = success
                    if success:
                        source.relevance_score *= 1.2  # Erhöhe Relevanz bei Erfolg
                    return
        
        for source in self.global_sources:
            if source.url == url:
                source.meta_data['used'] = True
                source.meta_data['success'] = success
                if success:
                    source.relevance_score *= 1.2
                return
    
    def get_statistics(self) -> Dict:
        """Gibt Statistiken über gefundene Quellen zurück"""
        total_sources = len(self.checked_urls)
        mine_specific_count = sum(len(sources) for sources in self.mine_sources.values())
        
        type_counts: Dict[str, int] = {}
        for sources in self.mine_sources.values():
            for source in sources:
                type_counts[source.source_type] = type_counts.get(source.source_type, 0) + 1
        
        for source in self.global_sources:
            type_counts[source.source_type] = type_counts.get(source.source_type, 0) + 1
        
        return {
            'total_sources': total_sources,
            'global_sources': len(self.global_sources),
            'mine_specific_sources': mine_specific_count,
            'sources_by_type': type_counts,
            'mines_covered': len(self.mine_sources)
        }
    
    def export_sources(self, mine_name: Optional[str] = None) -> Dict:
        """Exportiert Quellen als Dictionary"""
        if mine_name:
            sources = self.get_sources_for_mine(mine_name)
            return {
                'mine': mine_name,
                'sources': [
                    {
                        'url': s.url,
                        'type': s.source_type,
                        'relevance': s.relevance_score,
                        'found_by': s.found_by_agents,
                        'metadata': s.meta_data
                    }
                    for s in sources
                ]
            }
        else:
            # Exportiere alle Quellen
            return {
                'global_sources': [
                    {
                        'url': s.url,
                        'type': s.source_type,
                        'relevance': s.relevance_score,
                        'applicable_mines': s.applicable_mines,
                        'metadata': s.meta_data
                    }
                    for s in self.global_sources
                ],
                'mine_sources': {
                    mine: [
                        {
                            'url': s.url,
                            'type': s.source_type,
                            'relevance': s.relevance_score,
                            'found_by': s.found_by_agents,
                            'metadata': s.meta_data
                        }
                        for s in sources
                    ]
                    for mine, sources in self.mine_sources.items()
                }
            }