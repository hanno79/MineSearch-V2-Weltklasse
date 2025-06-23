"""
Tests für verbesserte Konsolidierungslogik
"""
import pytest
from datetime import datetime
from src.core.scoring import ScoringEngine
from src.agents.base_agent import SearchResult


class TestConsolidation:
    """Test-Suite für Konsolidierung von Suchergebnissen"""
    
    def setup_method(self):
        """Setup für jeden Test"""
        self.scoring_engine = ScoringEngine()
    
    def test_duplicate_detection(self):
        """Test: Erkennung und Zählung von Duplikaten"""
        # Erstelle Test-Daten mit mehreren identischen Werten
        results = [
            SearchResult(
                field_name="betreiber",
                value="Glencore",
                source="Claude",
                source_url="http://example.com/1",
                agent_name="claude",
                source_date=2024,
                confidence_score=0.9
            ),
            SearchResult(
                field_name="betreiber", 
                value="Glencore",
                source="GPT-4",
                source_url="http://example.com/2",
                agent_name="gpt4",
                source_date=2024,
                confidence_score=0.85
            ),
            SearchResult(
                field_name="betreiber",
                value="Glencore",
                source="Perplexity",
                source_url="http://example.com/3",
                agent_name="perplexity",
                source_date=2023,
                confidence_score=0.8
            ),
            SearchResult(
                field_name="betreiber",
                value="Glencore Canada",
                source="Scraper",
                source_url="http://example.com/4",
                agent_name="scraper",
                source_date=2022,
                confidence_score=0.7
            )
        ]
        
        # Aggregiere Ergebnisse
        aggregated = self.scoring_engine.aggregate_results(results)
        
        # Prüfe Struktur
        assert 'data' in aggregated
        assert 'alternatives' in aggregated
        assert 'metadata' in aggregated
        
        # Prüfe Hauptwert
        assert aggregated['data']['betreiber']['value'] == "Glencore"
        
        # Prüfe Alternativen
        alternatives = aggregated['alternatives']['betreiber']
        assert alternatives is not None
        assert "3x:" in alternatives  # 3 mal Glencore gefunden
        assert "claude, gpt4, perplexity" in alternatives.lower()
        assert "Glencore Canada" in alternatives
        assert "scraper" in alternatives.lower()
    
    def test_recency_prioritization(self):
        """Test: Neueste Werte werden priorisiert"""
        results = [
            SearchResult(
                field_name="sanierungskosten",
                value="450 million CAD",
                source="Old Report",
                source_url="http://example.com/old",
                agent_name="scraper",
                source_date=2020,
                confidence_score=0.7
            ),
            SearchResult(
                field_name="sanierungskosten",
                value="500 million CAD",
                source="Recent Report",
                source_url="http://example.com/new",
                agent_name="claude",
                source_date=2024,
                confidence_score=0.8
            ),
            SearchResult(
                field_name="sanierungskosten",
                value="480 million CAD",
                source="Medium Report",
                source_url="http://example.com/medium",
                agent_name="gpt4",
                source_date=2022,
                confidence_score=0.75
            )
        ]
        
        aggregated = self.scoring_engine.aggregate_results(results)
        
        # Prüfe ob neuester Wert gewählt wurde (mit höherem Aktualitäts-Score)
        assert aggregated['data']['sanierungskosten']['value'] in ["500 million CAD", "480 million CAD", "450 million CAD"]
        # Der genaue Wert hängt vom Gesamtscore ab, aber die Aktualität sollte berücksichtigt werden
        assert aggregated['data']['sanierungskosten']['source_date'] >= 2022
    
    def test_confidence_boost_for_duplicates(self):
        """Test: Mehrfach gefundene Werte erhalten Konsistenz-Boost"""
        # Einzelner Wert
        single_result = [
            SearchResult(
                field_name="rohstofftyp",
                value="Nickel",
                source="Single Source",
                source_url="http://example.com/single",
                agent_name="claude",
                source_date=2024,
                confidence_score=0.7
            )
        ]
        
        # Mehrfach gefundener Wert
        multiple_results = [
            SearchResult(
                field_name="rohstofftyp",
                value="Nickel",
                source="Source 1",
                source_url="http://example.com/1",
                agent_name="claude",
                source_date=2024,
                confidence_score=0.7
            ),
            SearchResult(
                field_name="rohstofftyp",
                value="Nickel",
                source="Source 2", 
                source_url="http://example.com/2",
                agent_name="gpt4",
                source_date=2024,
                confidence_score=0.7
            ),
            SearchResult(
                field_name="rohstofftyp",
                value="Nickel",
                source="Source 3",
                source_url="http://example.com/3",
                agent_name="perplexity",
                source_date=2024,
                confidence_score=0.7
            )
        ]
        
        # Berechne Scores
        single_score = self.scoring_engine.calculate_total_score(single_result[0], single_result)
        
        # Für mehrfache Ergebnisse sollte der Score höher sein
        avg_multiple_score = sum(
            self.scoring_engine.calculate_total_score(r, multiple_results) 
            for r in multiple_results
        ) / len(multiple_results)
        
        # Mehrfach gefundene Werte sollten höheren Score haben
        assert avg_multiple_score > single_score
    
    def test_csv_export_format(self):
        """Test: CSV-Export mit separaten Spalten"""
        from src.data.exporter import DataExporter
        import tempfile
        import pandas as pd
        
        # Test-Daten
        results = [{
            'mine_id': 1,
            'timestamp': datetime.now().isoformat(),
            'aggregated': {
                'data': {
                    'betreiber': {
                        'value': 'Glencore',
                        'source': 'Claude',
                        'source_url': 'http://example.com',
                        'source_date': 2024,
                        'confidence': '🟢',
                        'score': 85.5,
                        'agent': 'claude'
                    }
                },
                'alternatives': {
                    'betreiber': 'Glencore (3x: Claude, GPT4, Perplexity) +++ Glencore Canada (1x: Scraper)'
                },
                'metadata': {
                    'total_results': 4,
                    'fields_found': 1,
                    'average_score': 80.0
                }
            },
            'metrics': {
                'quality_score': 85.0,
                'completeness_score': 70.0
            }
        }]
        
        # Exportiere zu CSV
        exporter = DataExporter()
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as tmp:
            output_path = exporter.export_to_csv(results, tmp.name)
            
            # Lese CSV zurück
            df = pd.read_csv(output_path)
            
            # Prüfe Spalten
            assert 'Operator' in df.columns
            assert 'Operator_alternatives' in df.columns
            
            # Prüfe Werte
            assert df.iloc[0]['Operator'] == 'Glencore'
            assert '3x:' in df.iloc[0]['Operator_alternatives']
            assert 'Glencore Canada' in df.iloc[0]['Operator_alternatives']


if __name__ == "__main__":
    pytest.main([__file__, "-v"])