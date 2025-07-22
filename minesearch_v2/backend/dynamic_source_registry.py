"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: Dynamic Source Registry - Automatische Quellensammlung und -bewertung
"""

import logging
from typing import Dict, List, Any, Optional, Set
from datetime import datetime, timedelta
from dataclasses import dataclass, asdict
import json

logger = logging.getLogger(__name__)

@dataclass
class SourceQualityMetrics:
    """Qualitäts-Metriken für eine Quelle"""
    url: str
    total_searches: int = 0
    successful_extractions: int = 0
    fields_extracted: Dict[str, int] = None
    last_successful: Optional[datetime] = None
    avg_response_time: float = 0.0
    reliability_score: float = 0.0
    quebec_mining_relevance: float = 0.0
    
    def __post_init__(self):
        if self.fields_extracted is None:
            self.fields_extracted = {}

class DynamicSourceRegistry:
    """
    Dynamisches Quellenregister mit automatischer Qualitätsbewertung
    und kontinuierlicher Verbesserung
    """
    
    def __init__(self):
        self.source_metrics: Dict[str, SourceQualityMetrics] = {}
        self.quebec_mining_domains = {
            'gestim.mines.gouv.qc.ca': 0.95,
            'mern.gouv.qc.ca': 0.90,
            'sedar.com': 0.85,
            'newmont.com': 0.80,
            'agnicoeagle.com': 0.80,
            'barrick.com': 0.75,
            'mining.com': 0.70,
            'infomine.com': 0.65,
            'naturalresources.canada.ca': 0.75
        }
        
        # Feld-spezifische Quellen-Prioritäten
        self.field_source_priorities = {
            'Restaurationskosten': ['sedar.com', 'gestim.mines.gouv.qc.ca', 'company_annual_reports'],
            'Eigentümer': ['sedar.com', 'company_websites', 'mining.com'],
            'Betreiber': ['company_websites', 'mining.com', 'naturalresources.canada.ca'],
            'x-Koordinate': ['gestim.mines.gouv.qc.ca', 'mern.gouv.qc.ca', 'technical_reports'],
            'y-Koordinate': ['gestim.mines.gouv.qc.ca', 'mern.gouv.qc.ca', 'technical_reports'],
            'Aktivitätsstatus': ['company_websites', 'mining.com', 'sedar.com'],
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': ['technical_reports', 'company_websites', 'mining.com']
        }
    
    def register_search_attempt(self, sources: List[str], field_type: str, 
                               successful_extractions: Dict[str, str] = None) -> None:
        """
        Registriere einen Suchversuch und dessen Ergebnisse
        
        Args:
            sources: Liste der verwendeten Quellen
            field_type: Art des gesuchten Feldes
            successful_extractions: Erfolgreich extrahierte Werte pro Quelle
        """
        if successful_extractions is None:
            successful_extractions = {}
        
        for source in sources:
            # Erstelle oder aktualisiere Metrik
            if source not in self.source_metrics:
                self.source_metrics[source] = SourceQualityMetrics(
                    url=source,
                    fields_extracted={}
                )
            
            metrics = self.source_metrics[source]
            metrics.total_searches += 1
            
            # War die Extraktion erfolgreich?
            if source in successful_extractions:
                metrics.successful_extractions += 1
                metrics.last_successful = datetime.now()
                
                # Feld-spezifische Statistiken
                if field_type not in metrics.fields_extracted:
                    metrics.fields_extracted[field_type] = 0
                metrics.fields_extracted[field_type] += 1
            
            # Aktualisiere Reliability Score
            self._update_reliability_score(metrics)
            
            # Aktualisiere Quebec Mining Relevance
            self._update_quebec_relevance(metrics)
    
    def _update_reliability_score(self, metrics: SourceQualityMetrics) -> None:
        """Aktualisiere Zuverlässigkeits-Score"""
        if metrics.total_searches == 0:
            metrics.reliability_score = 0.0
            return
        
        base_score = metrics.successful_extractions / metrics.total_searches
        
        # Bonus für konsistente Performance
        if metrics.total_searches >= 10:
            consistency_bonus = 0.1
        elif metrics.total_searches >= 5:
            consistency_bonus = 0.05
        else:
            consistency_bonus = 0.0
        
        # Bonus für aktuelle Erfolge
        recency_bonus = 0.0
        if metrics.last_successful:
            days_since_success = (datetime.now() - metrics.last_successful).days
            if days_since_success <= 7:
                recency_bonus = 0.1
            elif days_since_success <= 30:
                recency_bonus = 0.05
        
        metrics.reliability_score = min(1.0, base_score + consistency_bonus + recency_bonus)
    
    def _update_quebec_relevance(self, metrics: SourceQualityMetrics) -> None:
        """Aktualisiere Quebec Mining Relevance Score"""
        url = metrics.url.lower()
        
        # Domain-basierte Relevanz
        domain_score = 0.0
        for domain, score in self.quebec_mining_domains.items():
            if domain in url:
                domain_score = score
                break
        
        # Keyword-basierte Relevanz
        quebec_keywords = ['quebec', 'québec', 'gestim', 'mern', 'canadian', 'newmont', 'agnico']
        keyword_score = sum(0.1 for keyword in quebec_keywords if keyword in url)
        keyword_score = min(0.5, keyword_score)  # Max 0.5 aus Keywords
        
        # Feld-spezifische Performance
        field_score = 0.0
        if metrics.fields_extracted:
            critical_fields = ['Restaurationskosten', 'Eigentümer', 'Betreiber']
            critical_extractions = sum(metrics.fields_extracted.get(field, 0) for field in critical_fields)
            if critical_extractions > 0:
                field_score = min(0.3, critical_extractions * 0.1)
        
        metrics.quebec_mining_relevance = min(1.0, domain_score + keyword_score + field_score)
    
    def get_recommended_sources(self, field_type: str, count: int = 5) -> List[Dict[str, Any]]:
        """
        Hole empfohlene Quellen für einen spezifischen Feldtyp
        
        Args:
            field_type: Art des Feldes
            count: Anzahl empfohlener Quellen
            
        Returns:
            Liste empfohlener Quellen sortiert nach Qualität
        """
        # Filtere und bewerte Quellen
        scored_sources = []
        
        for url, metrics in self.source_metrics.items():
            # Kombinierter Score
            combined_score = (
                metrics.reliability_score * 0.4 +
                metrics.quebec_mining_relevance * 0.4 +
                (metrics.fields_extracted.get(field_type, 0) / 10) * 0.2  # Feld-spezifische Erfahrung
            )
            
            scored_sources.append({
                'url': url,
                'combined_score': combined_score,
                'reliability_score': metrics.reliability_score,
                'quebec_relevance': metrics.quebec_mining_relevance,
                'field_extractions': metrics.fields_extracted.get(field_type, 0),
                'total_searches': metrics.total_searches,
                'success_rate': metrics.successful_extractions / max(1, metrics.total_searches)
            })
        
        # Sortiere nach Combined Score
        scored_sources.sort(key=lambda x: x['combined_score'], reverse=True)
        
        # Füge prioritäre Quellen hinzu falls nicht vorhanden
        priority_sources = self.field_source_priorities.get(field_type, [])
        recommended = []
        
        # Erst bewährte Quellen
        for source in scored_sources[:count]:
            recommended.append(source)
        
        # Dann prioritäre Quellen falls Platz
        for priority_source in priority_sources:
            if len(recommended) >= count:
                break
            if not any(priority_source in rec['url'] for rec in recommended):
                recommended.append({
                    'url': priority_source,
                    'combined_score': 0.8,  # Hoher Standard-Score
                    'reliability_score': 0.8,
                    'quebec_relevance': 0.9,
                    'field_extractions': 0,
                    'total_searches': 0,
                    'success_rate': 0.0,
                    'source_type': 'priority_recommendation'
                })
        
        return recommended[:count]
    
    def get_source_statistics(self) -> Dict[str, Any]:
        """Hole Gesamtstatistiken des Quellenregisters"""
        if not self.source_metrics:
            return {
                'total_sources': 0,
                'avg_reliability': 0.0,
                'avg_quebec_relevance': 0.0,
                'high_quality_sources': 0
            }
        
        total_sources = len(self.source_metrics)
        avg_reliability = sum(m.reliability_score for m in self.source_metrics.values()) / total_sources
        avg_quebec_relevance = sum(m.quebec_mining_relevance for m in self.source_metrics.values()) / total_sources
        high_quality_sources = len([m for m in self.source_metrics.values() if m.reliability_score > 0.7])
        
        # Top-Quellen pro Feld
        field_leaders = {}
        for field in self.field_source_priorities.keys():
            recommended = self.get_recommended_sources(field, 1)
            if recommended:
                field_leaders[field] = recommended[0]['url']
        
        return {
            'total_sources': total_sources,
            'avg_reliability': round(avg_reliability, 3),
            'avg_quebec_relevance': round(avg_quebec_relevance, 3),
            'high_quality_sources': high_quality_sources,
            'field_leaders': field_leaders,
            'total_searches': sum(m.total_searches for m in self.source_metrics.values()),
            'total_successful_extractions': sum(m.successful_extractions for m in self.source_metrics.values())
        }
    
    def export_source_database(self) -> Dict[str, Any]:
        """Exportiere Quellendatenbank für Persistierung"""
        return {
            'source_metrics': {
                url: {
                    **asdict(metrics),
                    'last_successful': metrics.last_successful.isoformat() if metrics.last_successful else None
                }
                for url, metrics in self.source_metrics.items()
            },
            'quebec_mining_domains': self.quebec_mining_domains,
            'field_source_priorities': self.field_source_priorities,
            'export_timestamp': datetime.now().isoformat()
        }
    
    def import_source_database(self, data: Dict[str, Any]) -> None:
        """Importiere Quellendatenbank"""
        try:
            for url, metrics_data in data.get('source_metrics', {}).items():
                # Konvertiere datetime zurück
                last_successful = None
                if metrics_data.get('last_successful'):
                    last_successful = datetime.fromisoformat(metrics_data['last_successful'])
                
                metrics_data['last_successful'] = last_successful
                self.source_metrics[url] = SourceQualityMetrics(**metrics_data)
            
            # Aktualisiere Konfigurationen falls vorhanden
            if 'quebec_mining_domains' in data:
                self.quebec_mining_domains.update(data['quebec_mining_domains'])
            
            if 'field_source_priorities' in data:
                self.field_source_priorities.update(data['field_source_priorities'])
            
            logger.info(f"[SOURCE-REGISTRY] {len(self.source_metrics)} Quellen importiert")
            
        except Exception as e:
            logger.error(f"[SOURCE-REGISTRY] Fehler beim Import: {e}")

# Singleton-Instanz
dynamic_source_registry = DynamicSourceRegistry()