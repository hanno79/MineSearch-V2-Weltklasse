#!/usr/bin/env python3
"""
Author: rahn
Datum: 08.07.2025
Version: 1.0
Beschreibung: Test für verbesserte Source Classification
"""

import sys
import os
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), '..')))

import logging
from database import db_manager, Source

# Setup Logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def test_source_classification():
    """Teste die neue Source Classification"""
    
    # Test-URLs mit erwarteten Typen
    test_cases = [
        # Government
        ("https://gq.mines.gouv.qc.ca/documents/examine/GM42581/GM42581.pdf", "government", "Canada"),
        ("https://mern.gouv.qc.ca/mines/", "government", "Canada"),
        ("https://www.blm.gov/programs/energy-and-minerals/mining-and-minerals", "government", "USA"),
        
        # Database
        ("https://www.mindat.org/loc-123.html", "database", None),
        ("https://miningdataonline.com/property/123", "database", None),
        ("https://gestim.mines.gouv.qc.ca/", "government", "Canada"),  # GESTIM ist eine Regierungsplattform
        
        # Exchange
        ("https://sedar.com/filings/123", "exchange", "Canada"),
        ("https://www.tsx.com/listings/123", "exchange", "Canada"),
        
        # Industry
        ("https://www.mining.com/article/123", "industry", None),
        ("https://www.miningweekly.com/article/123", "industry", None),
        ("https://www.mining-technology.com/news/123", "industry", None),
        
        # Document
        ("https://mining.ca/documents/report.pdf", "document", "Canada"),
        ("https://diffusion.mern.gouv.qc.ca/public/biblio/DV201402.pdf", "government", "Canada"),  # Regierungsdokument
        
        # Wikipedia
        ("https://en.wikipedia.org/wiki/Canadian_Malartic_mine", "wikipedia", None),
        
        # Media
        ("https://www.youtube.com/watch?v=123", "media", None),
    ]
    
    logger.info("=== Test Source Classification ===")
    
    correct = 0
    total = len(test_cases)
    
    for url, expected_type, expected_country in test_cases:
        # Extrahiere Domain
        from urllib.parse import urlparse
        parsed = urlparse(url)
        domain = parsed.netloc
        
        # Klassifiziere
        detected_type = Source.classify_source_type(url, domain)
        detected_country = Source.get_country_from_domain(url, domain)
        
        # Prüfe Ergebnis
        type_correct = detected_type == expected_type
        country_correct = detected_country == expected_country
        
        if type_correct and (expected_country is None or country_correct):
            correct += 1
            status = "✅"
        else:
            status = "❌"
        
        logger.info(f"{status} {url}")
        logger.info(f"   Erwartet: {expected_type} / {expected_country}")
        logger.info(f"   Erkannt:  {detected_type} / {detected_country}")
        
    logger.info(f"\nErgebnis: {correct}/{total} korrekt ({correct/total*100:.1f}%)")
    
    # Teste add_or_update_source
    logger.info("\n=== Test add_or_update_source ===")
    
    test_url = "https://www.miningweekly.com/article/new-gold-mine-2025"
    
    # Füge mit 'url' type hinzu (sollte automatisch korrigiert werden)
    source = db_manager.add_or_update_source(
        url=test_url,
        domain="www.miningweekly.com",
        source_type="url"  # Sollte zu "industry" korrigiert werden
    )
    
    logger.info(f"URL: {test_url}")
    logger.info(f"Klassifiziert als: {source.source_type}")
    logger.info(f"Land erkannt: {source.country}")
    
    assert source.source_type == "industry", f"Erwartet 'industry', bekommen '{source.source_type}'"
    logger.info("✅ Automatische Korrektur funktioniert!")

if __name__ == "__main__":
    test_source_classification()