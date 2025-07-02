"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Unit Tests für Source Discovery
"""

# ÄNDERUNG 01.07.2025: Test-Suite für source_discovery.py erstellt

import pytest
import os
import sys
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from minesearch_v2.backend.source_discovery import SourceDiscovery
from minesearch_v2.backend.config import PRIORITY_MINING_DOMAINS


class TestSourceDiscovery:
    """Tests für SourceDiscovery Klasse"""
    
    @pytest.fixture
    def discovery(self):
        """SourceDiscovery Instanz für Tests"""
        return SourceDiscovery()
    
    @pytest.fixture
    def sample_sources(self):
        """Beispiel-Quellen für Tests"""
        return [
            {
                "url": "https://mining.gov.ca/report.pdf",
                "titel": "Government Mining Report",
                "domain": "mining.gov.ca",
                "beschreibung": "Official government report",
                "datum": "2024-01-15"
            },
            {
                "url": "https://tsx.com/eagle-gold",
                "titel": "TSX Listing",
                "domain": "tsx.com",
                "beschreibung": "Stock exchange listing",
                "datum": "2024-02-20"
            },
            {
                "url": "https://miningnews.com/article",
                "titel": "Mining News Article",
                "domain": "miningnews.com",
                "beschreibung": "Industry news",
                "datum": "2024-03-10"
            }
        ]
    
    def test_extract_sources_from_text(self, discovery):
        """Test: Quellen aus Text extrahieren"""
        text = """
        According to the report from https://mining.gov.ca/report.pdf,
        the mine produces 220,000 oz annually. More information at
        www.eaglegold.com and https://tsx.com/eagle-gold.
        """
        
        sources = discovery.extract_sources(text)
        
        assert len(sources) >= 2
        assert any("mining.gov.ca" in s.get("domain", "") for s in sources)
        assert any("tsx.com" in s.get("domain", "") for s in sources)
    
    def test_source_validation(self, discovery):
        """Test: Quellen-Validierung"""
        valid_source = {
            "url": "https://example.com/report.pdf",
            "domain": "example.com"
        }
        
        invalid_source = {
            "url": "not-a-url",
            "domain": ""
        }
        
        assert discovery.validate_source(valid_source) == True
        assert discovery.validate_source(invalid_source) == False
    
    def test_source_ranking(self, discovery, sample_sources):
        """Test: Quellen-Ranking nach Priorität"""
        ranked = discovery.rank_sources(sample_sources)
        
        # Government sources should rank higher
        assert ranked[0]["domain"] == "mining.gov.ca"
        # Stock exchange should be second
        assert ranked[1]["domain"] == "tsx.com"
        # News should be last
        assert ranked[2]["domain"] == "miningnews.com"
    
    def test_domain_priority_tiers(self, discovery):
        """Test: Domain-Prioritäts-Stufen"""
        tier1_domain = "mining.gov.ca"
        tier2_domain = "tsx.com"
        tier3_domain = "reuters.com"
        
        assert discovery.get_domain_tier(tier1_domain) == 1
        assert discovery.get_domain_tier(tier2_domain) == 2
        assert discovery.get_domain_tier(tier3_domain) == 3
    
    def test_extract_urls_patterns(self, discovery):
        """Test: URL-Muster extrahieren"""
        text = """
        Sources:
        - https://example.com/report.pdf
        - http://test.org/data
        - www.mining.com/article
        - ftp://files.com/data.csv
        - [Link](https://markdown.com/link)
        """
        
        urls = discovery.extract_urls(text)
        
        assert "https://example.com/report.pdf" in urls
        assert "http://test.org/data" in urls
        assert any("mining.com" in url for url in urls)
        assert "https://markdown.com/link" in urls
    
    def test_pdf_source_detection(self, discovery):
        """Test: PDF-Quellen erkennen"""
        sources = [
            {"url": "https://example.com/report.pdf", "domain": "example.com"},
            {"url": "https://example.com/page", "domain": "example.com"},
            {"url": "https://example.com/document.PDF", "domain": "example.com"}
        ]
        
        pdf_sources = discovery.filter_pdf_sources(sources)
        
        assert len(pdf_sources) == 2
        assert all(s["url"].lower().endswith(".pdf") for s in pdf_sources)
    
    def test_source_deduplication(self, discovery):
        """Test: Duplikate entfernen"""
        sources = [
            {"url": "https://example.com/report", "domain": "example.com"},
            {"url": "https://example.com/report", "domain": "example.com"},
            {"url": "https://example.com/report/", "domain": "example.com"},
            {"url": "https://example.com/other", "domain": "example.com"}
        ]
        
        unique = discovery.deduplicate_sources(sources)
        
        assert len(unique) == 2
    
    def test_source_metadata_extraction(self, discovery):
        """Test: Metadaten aus Quellen extrahieren"""
        text = """
        [1] Mining Report 2024 - https://mining.gov/report2024.pdf
        Published: January 2024
        
        [2] "Eagle Gold Technical Report" (TSX, Feb 2024)
        Available at: www.tsx.com/eagle-tech-report
        """
        
        sources = discovery.extract_sources_with_metadata(text)
        
        assert len(sources) >= 2
        assert any("2024" in s.get("datum", "") for s in sources)
        assert any("Mining Report" in s.get("titel", "") for s in sources)
    
    def test_context_based_source_extraction(self, discovery):
        """Test: Kontext-basierte Quellenextraktion"""
        text = """
        According to the latest NI 43-101 report (https://sedar.com/ni43101.pdf),
        the proven reserves are 3.3M oz. The company's website 
        (www.eaglegold.com) provides additional details.
        """
        
        sources = discovery.extract_sources_with_context(text)
        
        assert any("NI 43-101" in s.get("beschreibung", "") for s in sources)
        assert any("reserves" in s.get("kontext", "") for s in sources)
    
    def test_source_filtering_by_date(self, discovery):
        """Test: Quellen nach Datum filtern"""
        sources = [
            {"url": "https://old.com", "datum": "2020-01-01"},
            {"url": "https://recent.com", "datum": "2024-01-01"},
            {"url": "https://current.com", "datum": "2024-06-01"}
        ]
        
        recent = discovery.filter_recent_sources(sources, days=365)
        
        assert len(recent) == 2
        assert all("2024" in s["datum"] for s in recent)
    
    def test_mining_specific_domains(self, discovery):
        """Test: Mining-spezifische Domains"""
        mining_domains = [
            "infomine.com",
            "mining.com", 
            "northernminer.com",
            "miningweekly.com"
        ]
        
        for domain in mining_domains:
            tier = discovery.get_domain_tier(domain)
            assert tier <= 3  # Should be recognized as mining-related
    
    def test_gestim_source_priority(self, discovery):
        """Test: GESTIM höchste Priorität für Quebec"""
        sources = [
            {"url": "https://gestim.mines.gouv.qc.ca/mine123", "domain": "gestim.mines.gouv.qc.ca"},
            {"url": "https://mining.gov.ca/report", "domain": "mining.gov.ca"}
        ]
        
        ranked = discovery.rank_sources(sources)
        
        # GESTIM should always be first for Quebec mines
        assert "gestim" in ranked[0]["domain"]
    
    def test_source_quality_scoring(self, discovery):
        """Test: Quellen-Qualitätsbewertung"""
        high_quality = {
            "url": "https://mining.gov.ca/official-report.pdf",
            "domain": "mining.gov.ca",
            "datum": "2024-06-01",
            "titel": "Official Mining Report 2024"
        }
        
        low_quality = {
            "url": "https://random-blog.com/mining-post",
            "domain": "random-blog.com"
        }
        
        assert discovery.calculate_source_quality(high_quality) > discovery.calculate_source_quality(low_quality)
    
    def test_extract_source_references(self, discovery):
        """Test: Quellen-Referenzen extrahieren"""
        text = """
        Data from multiple sources [1,2,3]:
        [1] Government Database - mining.gov.ca
        [2] Company Report - eaglegold.com/2024-report
        [3] Technical Study - ni43101-reports.com
        """
        
        refs = discovery.extract_source_references(text)
        
        assert len(refs) >= 3
        assert any("Government Database" in r.get("titel", "") for r in refs)
    
    def test_handle_malformed_urls(self, discovery):
        """Test: Fehlerhafte URLs behandeln"""
        text = """
        Sources: 
        - htp://wrong-protocol.com
        - https://valid.com
        - www.no-protocol.com
        - just-text-not-url
        """
        
        sources = discovery.extract_sources(text)
        
        # Should still extract valid and fixable URLs
        assert len(sources) >= 2
        assert any("valid.com" in s.get("url", "") for s in sources)


if __name__ == "__main__":
    pytest.main([__file__, "-v"])