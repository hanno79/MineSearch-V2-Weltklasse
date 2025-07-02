"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Unit Tests für Utility-Funktionen
"""

# ÄNDERUNG 01.07.2025: Test-Suite für utils.py erstellt

import pytest
import os
import sys
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from minesearch_v2.backend.utils import (
    generate_name_variants,
    format_date,
    validate_coordinates,
    clean_text,
    extract_number,
    calculate_data_quality,
    merge_data_sources,
    validate_email,
    validate_url,
    extract_domain,
    generate_search_keywords,
    normalize_country_name,
    parse_production_value,
    format_large_number,
    extract_year_from_text,
    clean_html,
    truncate_text,
    calculate_similarity,
    extract_brackets_content,
    remove_duplicates
)


class TestNameVariants:
    """Tests für Namenvarianten-Generierung"""
    
    def test_basic_name_variants(self):
        """Test: Basis-Namenvarianten"""
        variants = generate_name_variants("Eagle Gold Mine")
        
        assert "Eagle Gold Mine" in variants
        assert "Eagle Gold" in variants
        assert "Eagle Mine" in variants
        assert "Eagle" in variants
        assert len(variants) >= 10
    
    def test_name_with_brackets(self):
        """Test: Namen mit Klammern"""
        variants = generate_name_variants("Cerro Negro (Goldcorp)")
        
        assert "Cerro Negro" in variants
        assert "Goldcorp" in variants
        assert "Cerro Negro Goldcorp" in variants
    
    def test_name_with_special_chars(self):
        """Test: Namen mit Sonderzeichen"""
        variants = generate_name_variants("ABC-123 Mine & Quarry")
        
        assert "ABC-123 Mine & Quarry" in variants
        assert "ABC 123 Mine Quarry" in variants
        assert "ABC123" in variants
    
    def test_empty_name(self):
        """Test: Leerer Name"""
        variants = generate_name_variants("")
        assert variants == [""]
    
    def test_name_with_numbers(self):
        """Test: Namen mit Zahlen"""
        variants = generate_name_variants("Mine 2000")
        
        assert "Mine 2000" in variants
        assert "Mine" in variants
        assert any("Two Thousand" in v for v in variants)


class TestDateFormatting:
    """Tests für Datums-Formatierung"""
    
    def test_format_date_valid(self):
        """Test: Gültiges Datum formatieren"""
        assert format_date("2025-01-15") == "15.01.2025"
        assert format_date("2025/01/15") == "15.01.2025"
        assert format_date("15-01-2025") == "15.01.2025"
    
    def test_format_date_invalid(self):
        """Test: Ungültiges Datum"""
        assert format_date("invalid") == "invalid"
        assert format_date("") == ""
        assert format_date(None) == ""


class TestCoordinateValidation:
    """Tests für Koordinaten-Validierung"""
    
    def test_valid_coordinates(self):
        """Test: Gültige Koordinaten"""
        assert validate_coordinates("48.123,-89.456") == True
        assert validate_coordinates("-33.45,151.21") == True
        assert validate_coordinates("0,0") == True
    
    def test_invalid_coordinates(self):
        """Test: Ungültige Koordinaten"""
        assert validate_coordinates("91,180") == False
        assert validate_coordinates("abc,def") == False
        assert validate_coordinates("48.123") == False
        assert validate_coordinates("") == False
        assert validate_coordinates("48.123,181") == False


class TestTextCleaning:
    """Tests für Text-Bereinigung"""
    
    def test_clean_text(self):
        """Test: Text bereinigen"""
        assert clean_text("  Test  ") == "Test"
        assert clean_text("Test\n\nText") == "Test Text"
        assert clean_text("Test\t\tText") == "Test Text"
        assert clean_text(None) == ""
    
    def test_clean_html(self):
        """Test: HTML bereinigen"""
        assert clean_html("<p>Test</p>") == "Test"
        assert clean_html("<b>Bold</b> <i>Italic</i>") == "Bold Italic"
        assert clean_html("No HTML") == "No HTML"


class TestNumberExtraction:
    """Tests für Zahlen-Extraktion"""
    
    def test_extract_number(self):
        """Test: Zahlen extrahieren"""
        assert extract_number("100 Millionen") == 100000000
        assert extract_number("2.5 Mio") == 2500000
        assert extract_number("500k") == 500000
        assert extract_number("1,234.56") == 1234.56
        assert extract_number("no number") == 0
    
    def test_parse_production_value(self):
        """Test: Produktionswerte parsen"""
        assert parse_production_value("100,000 oz") == (100000, "oz")
        assert parse_production_value("2.5 Mio t") == (2500000, "t")
        assert parse_production_value("500 kg Gold") == (500, "kg")


class TestDataQuality:
    """Tests für Datenqualitäts-Berechnung"""
    
    def test_calculate_data_quality(self):
        """Test: Datenqualität berechnen"""
        data = {
            "Minenname": "Test Mine",
            "Land": "Kanada",
            "Koordinaten": "48.123,-89.456",
            "Rohstoffe": "Gold",
            "Status": "Aktiv"
        }
        quality = calculate_data_quality(data, ["source1", "source2"])
        
        assert quality > 0
        assert quality <= 100
    
    def test_data_quality_empty(self):
        """Test: Datenqualität bei leeren Daten"""
        quality = calculate_data_quality({}, [])
        assert quality == 0


class TestDataMerging:
    """Tests für Daten-Zusammenführung"""
    
    def test_merge_data_sources(self):
        """Test: Datenquellen zusammenführen"""
        source1 = {"name": "Mine A", "country": "Canada"}
        source2 = {"name": "Mine A", "region": "Ontario"}
        
        merged = merge_data_sources([source1, source2])
        
        assert merged["name"] == "Mine A"
        assert merged["country"] == "Canada"
        assert merged["region"] == "Ontario"
    
    def test_merge_conflicting_data(self):
        """Test: Konfliktende Daten zusammenführen"""
        source1 = {"production": "100k oz"}
        source2 = {"production": "110k oz"}
        
        merged = merge_data_sources([source1, source2])
        
        # Sollte einen der Werte nehmen
        assert merged["production"] in ["100k oz", "110k oz"]


class TestValidation:
    """Tests für Validierungsfunktionen"""
    
    def test_validate_email(self):
        """Test: E-Mail validieren"""
        assert validate_email("test@example.com") == True
        assert validate_email("invalid.email") == False
        assert validate_email("") == False
    
    def test_validate_url(self):
        """Test: URL validieren"""
        assert validate_url("https://example.com") == True
        assert validate_url("http://test.com/page") == True
        assert validate_url("not a url") == False
        assert validate_url("") == False
    
    def test_extract_domain(self):
        """Test: Domain extrahieren"""
        assert extract_domain("https://example.com/page") == "example.com"
        assert extract_domain("http://sub.example.com") == "sub.example.com"
        assert extract_domain("invalid") == ""


class TestSearchKeywords:
    """Tests für Suchbegriff-Generierung"""
    
    def test_generate_search_keywords(self):
        """Test: Suchbegriffe generieren"""
        keywords = generate_search_keywords("Eagle Gold", "Kanada", ["Gold", "Silber"])
        
        assert "Eagle Gold" in keywords
        assert "Kanada" in keywords
        assert "Gold" in keywords
        assert len(keywords) >= 5


class TestCountryNormalization:
    """Tests für Länder-Normalisierung"""
    
    def test_normalize_country_name(self):
        """Test: Ländernamen normalisieren"""
        assert normalize_country_name("USA") == "United States"
        assert normalize_country_name("UK") == "United Kingdom"
        assert normalize_country_name("Deutschland") == "Germany"
        assert normalize_country_name("Unknown") == "Unknown"


class TestNumberFormatting:
    """Tests für Zahlen-Formatierung"""
    
    def test_format_large_number(self):
        """Test: Große Zahlen formatieren"""
        assert format_large_number(1000000) == "1 Mio"
        assert format_large_number(1500000) == "1.5 Mio"
        assert format_large_number(1000) == "1,000"
        assert format_large_number(100) == "100"


class TestYearExtraction:
    """Tests für Jahr-Extraktion"""
    
    def test_extract_year_from_text(self):
        """Test: Jahr aus Text extrahieren"""
        assert extract_year_from_text("Gegründet 2020") == 2020
        assert extract_year_from_text("Report from 2024") == 2024
        assert extract_year_from_text("No year here") is None


class TestTextUtilities:
    """Tests für Text-Utilities"""
    
    def test_truncate_text(self):
        """Test: Text kürzen"""
        assert truncate_text("Short text", 20) == "Short text"
        assert truncate_text("This is a very long text", 10) == "This is a..."
        assert truncate_text("", 10) == ""
    
    def test_calculate_similarity(self):
        """Test: Ähnlichkeit berechnen"""
        assert calculate_similarity("test", "test") == 1.0
        assert calculate_similarity("test", "text") > 0.5
        assert calculate_similarity("abc", "xyz") < 0.5
    
    def test_remove_duplicates(self):
        """Test: Duplikate entfernen"""
        assert remove_duplicates(["a", "b", "a", "c"]) == ["a", "b", "c"]
        assert remove_duplicates([]) == []
        assert remove_duplicates(["unique"]) == ["unique"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])