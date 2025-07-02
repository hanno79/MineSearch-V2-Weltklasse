"""
Author: rahn
Datum: 01.07.2025
Version: 1.0
Beschreibung: Unit Tests für Datenextraktion
"""

# ÄNDERUNG 01.07.2025: Test-Suite für data_extraction.py erstellt

import pytest
import os
import sys
import json
from unittest.mock import Mock, patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..'))

from minesearch_v2.backend.data_extraction import DataExtractor


class TestDataExtractor:
    """Tests für DataExtractor Klasse"""
    
    @pytest.fixture
    def extractor(self):
        """DataExtractor Instanz für Tests"""
        return DataExtractor()
    
    @pytest.fixture
    def sample_mine_data(self):
        """Beispiel-Minendaten"""
        return {
            "Minenname": "Eagle Gold Mine",
            "Land": "Kanada",
            "Region": "Yukon",
            "Koordinaten": "63.9167,-139.0333",
            "Rohstoffe": "Gold",
            "Eigentümer": "Victoria Gold Corp",
            "Betreiber": "Victoria Gold Corp",
            "Status": "Aktiv",
            "Jahresproduktion": "220,000 oz Gold",
            "Reserven": "3.3 Mio oz Gold",
            "Ressourcen": "4.4 Mio oz Gold",
            "Minenlaufzeit": "2019-2029",
            "Mitarbeiter": "450",
            "Website": "www.vitgoldcorp.com",
            "Kontakt": "info@vitgoldcorp.com",
            "Umweltgenehmigungen": "Erteilt 2016",
            "Sicherheitsleistung": "75 Mio CAD",
            "Restaurationskosten": "120 Mio CAD",
            "Notizen": "Heap Leach Operation"
        }
    
    def test_extract_basic_info(self, extractor, sample_mine_data):
        """Test: Basis-Informationen extrahieren"""
        text = f"""
        Die {sample_mine_data['Minenname']} liegt in {sample_mine_data['Region']}, {sample_mine_data['Land']}.
        Koordinaten: {sample_mine_data['Koordinaten']}
        Hauptrohstoff: {sample_mine_data['Rohstoffe']}
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "Eagle Gold Mine" in str(result.get("Minenname", ""))
        assert "Kanada" in str(result.get("Land", ""))
        assert "Yukon" in str(result.get("Region", ""))
        assert "Gold" in str(result.get("Rohstoffe", ""))
    
    def test_extract_coordinates(self, extractor):
        """Test: Koordinaten-Extraktion"""
        texts = [
            "Koordinaten: 48.123,-89.456",
            "Location: 48.123°N, 89.456°W",
            "Lat: 48.123, Long: -89.456",
            "GPS: N48.123 W89.456"
        ]
        
        for text in texts:
            result = extractor.extract_mine_data(text)
            coords = result.get("Koordinaten", "")
            assert "48.123" in coords or "89.456" in coords
    
    def test_extract_production_data(self, extractor):
        """Test: Produktionsdaten extrahieren"""
        text = """
        Jahresproduktion: 220,000 oz Gold
        Reserven: 3.3 Millionen Unzen Gold
        Ressourcen: 4.4 Mio oz Au
        Verarbeitungskapazität: 29,500 t/Tag
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "220" in str(result.get("Jahresproduktion", ""))
        assert "3.3" in str(result.get("Reserven", ""))
        assert "4.4" in str(result.get("Ressourcen", ""))
        assert "29,500" in str(result.get("Verarbeitungskapazität", ""))
    
    def test_extract_ownership_info(self, extractor):
        """Test: Eigentümer/Betreiber-Informationen"""
        text = """
        Eigentümer: Victoria Gold Corp (100%)
        Betreiber: Victoria Gold Corp
        Joint Venture Partner: Keine
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "Victoria Gold Corp" in str(result.get("Eigentümer", ""))
        assert "Victoria Gold Corp" in str(result.get("Betreiber", ""))
    
    def test_extract_environmental_data(self, extractor):
        """Test: Umweltdaten extrahieren"""
        text = """
        Umweltgenehmigung erteilt: 2016
        Sicherheitsleistung: 75 Millionen CAD
        Geschätzte Restaurationskosten: 120 Mio CAD
        Closure Bond: $75 million
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "2016" in str(result.get("Umweltgenehmigungen", ""))
        assert "75" in str(result.get("Sicherheitsleistung", ""))
        assert "120" in str(result.get("Restaurationskosten", ""))
    
    def test_extract_contact_info(self, extractor):
        """Test: Kontaktinformationen extrahieren"""
        text = """
        Website: www.vitgoldcorp.com
        Email: info@vitgoldcorp.com
        Telefon: +1-867-555-0123
        Adresse: 123 Mining Street, Whitehorse, Yukon
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "vitgoldcorp.com" in str(result.get("Website", ""))
        assert "info@vitgoldcorp.com" in str(result.get("Kontakt", ""))
        assert "867" in str(result.get("Telefon", ""))
        assert "Whitehorse" in str(result.get("Adresse", ""))
    
    def test_extract_timeline_info(self, extractor):
        """Test: Zeitliche Informationen extrahieren"""
        text = """
        Produktionsstart: 2019
        Geplante Minenlaufzeit: 10 Jahre (bis 2029)
        Gründungsjahr: 2009
        Erste Bohrungen: 2010
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "2019" in str(result.get("Gründungsjahr", "")) or "2009" in str(result.get("Gründungsjahr", ""))
        assert "2029" in str(result.get("Minenlaufzeit", "")) or "10" in str(result.get("Minenlaufzeit", ""))
    
    def test_extract_workforce_info(self, extractor):
        """Test: Mitarbeiter-Informationen"""
        text = """
        Mitarbeiter: 450 (davon 350 lokal)
        Contractors: 150
        Gewerkschaft: United Steelworkers Local 1998
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "450" in str(result.get("Mitarbeiter", ""))
        assert "United Steelworkers" in str(result.get("Gewerkschaft", ""))
    
    def test_extract_mining_type(self, extractor):
        """Test: Minentyp extrahieren"""
        texts_and_types = [
            ("Dies ist ein Tagebau-Betrieb", "Tagebau"),
            ("Underground mining operation", "Untertagebau"),
            ("Open pit gold mine", "Tagebau"),
            ("Heap leach operation", "Heap Leach")
        ]
        
        for text, expected_type in texts_and_types:
            result = extractor.extract_mine_data(text)
            mine_type = result.get("Minentyp", "")
            assert expected_type in mine_type or mine_type != ""
    
    def test_extract_certifications(self, extractor):
        """Test: Zertifizierungen extrahieren"""
        text = """
        Zertifizierungen: ISO 14001, OHSAS 18001
        Responsible Mining Certification
        TSM (Towards Sustainable Mining) Mitglied
        """
        
        result = extractor.extract_mine_data(text)
        
        certs = result.get("Zertifizierungen", "")
        assert "ISO 14001" in certs or "Responsible Mining" in certs
    
    def test_extract_infrastructure(self, extractor):
        """Test: Infrastruktur-Informationen"""
        text = """
        Zufahrt: 100km asphaltierte Straße
        Stromversorgung: 69kV Leitung vorhanden
        Wasserquelle: Yukon River (5km entfernt)
        Nächster Flughafen: Whitehorse (400km)
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "100km" in str(result.get("Infrastruktur", "")) or "Straße" in str(result.get("Infrastruktur", ""))
        assert "Yukon River" in str(result.get("Wasserquelle", ""))
    
    def test_extract_financial_info(self, extractor):
        """Test: Finanzielle Informationen"""
        text = """
        Investitionsvolumen: 500 Millionen USD
        CAPEX: $500M
        OPEX: $750/oz
        NPV: $1.2 Milliarden
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "500" in str(result.get("Investitionsvolumen", ""))
    
    def test_extract_multiple_commodities(self, extractor):
        """Test: Mehrere Rohstoffe extrahieren"""
        text = """
        Hauptrohstoffe: Gold, Silber, Kupfer
        Nebenprodukte: Zink, Blei
        Jahresproduktion: 200k oz Au, 2M oz Ag, 50M lbs Cu
        """
        
        result = extractor.extract_mine_data(text)
        
        commodities = result.get("Rohstoffe", "")
        assert "Gold" in commodities
        assert "Silber" in commodities or "Ag" in commodities
        assert "Kupfer" in commodities or "Cu" in commodities
    
    def test_extract_from_json_response(self, extractor):
        """Test: Extraktion aus JSON-Response"""
        json_text = json.dumps({
            "mine_data": {
                "name": "Test Mine",
                "location": "Canada",
                "production": "100k oz/year"
            }
        })
        
        result = extractor.extract_mine_data(json_text)
        
        # Sollte JSON erkennen und parsen können
        assert result is not None
    
    def test_handle_empty_input(self, extractor):
        """Test: Leere Eingabe behandeln"""
        result = extractor.extract_mine_data("")
        assert isinstance(result, dict)
        assert len(result) == 0 or all(v == "" for v in result.values())
    
    def test_handle_none_input(self, extractor):
        """Test: None-Eingabe behandeln"""
        result = extractor.extract_mine_data(None)
        assert isinstance(result, dict)
    
    def test_extract_multilingual_content(self, extractor):
        """Test: Mehrsprachige Inhalte"""
        text = """
        Mine name: Eagle Gold / Mine d'or Eagle
        Producción anual: 220,000 oz
        Reservas: 3.3 milhões oz
        """
        
        result = extractor.extract_mine_data(text)
        
        assert "Eagle Gold" in str(result.get("Minenname", ""))
        assert "220" in str(result.get("Jahresproduktion", ""))
    
    def test_normalize_units(self, extractor):
        """Test: Einheiten normalisieren"""
        text = """
        Produktion: 6.5 Tonnen Gold pro Jahr
        Reserven: 100 Millionen Pfund Kupfer
        Kapazität: 10,000 tonnes per day
        """
        
        result = extractor.extract_mine_data(text)
        
        # Sollte Einheiten erkennen und beibehalten
        production = result.get("Jahresproduktion", "")
        assert "6.5" in production or "Tonnen" in production


if __name__ == "__main__":
    pytest.main([__file__, "-v"])