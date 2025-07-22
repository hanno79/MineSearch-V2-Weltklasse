"""
Author: rahn
Datum: 19.07.2025
Version: 1.0
Beschreibung: CSV Export Service für MineSearch v2 Ergebnisse
"""

import csv
import io
from typing import List, Dict, Any
from datetime import datetime
import logging

logger = logging.getLogger(__name__)


class CSVExportService:
    """Service für CSV-Export von Suchergebnissen mit Pipe-Separatoren"""
    
    def __init__(self):
        """Initialisiere CSV Export Service"""
        self.delimiter = '|'  # Pipe als Separator
        self.quotechar = '"'
        self.quoting = csv.QUOTE_MINIMAL
        
        # Standard CSV-Header definieren
        self.csv_headers = [
            'id',
            'search_timestamp',
            'mine_name',
            'country', 
            'region',
            'commodity',
            'model_used',
            'provider',
            'search_duration',
            'session_id',
            'success',
            'error_message',
            'data_quality',
            'fields_found',
            'sources_count',
            # Strukturierte Datenfelder
            'owner',
            'operator',
            'latitude',
            'longitude',
            'mine_type',
            'status',
            'production_start',
            'production_end',
            'ore_reserves',
            'annual_production',
            'mine_area',
            'restoration_costs',
            'restoration_currency',
            'restoration_year',
            'ore_grade',
            'depth',
            'employees',
            'website',
            'parent_company'
        ]
        
        # FIELD-MAPPING 19.07.2025: Deutsche → Englische Feldnamen Mapping
        self.field_mapping = {
            # Deutsche Feldnamen aus der Datenbank → Englische CSV-Feldnamen
            'Eigentümer': 'owner',
            'Betreiber': 'operator',
            'x-Koordinate': 'longitude',
            'y-Koordinate': 'latitude',
            'Aktivitätsstatus': 'status',
            'Minentyp (Untertage/ Open-Pit/ usw.)': 'mine_type',
            'Produktionsstart': 'production_start',
            'Produktionsende': 'production_end',
            'Restaurationskosten': 'restoration_costs',
            'Jahr der Aufnahme der Kosten': 'restoration_year',
            'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': 'commodity',
            'Fördermenge/Jahr': 'annual_production',
            'Fläche der Mine in qkm': 'mine_area',
            # Zusätzliche deutsche Feldnamen
            'Erzreserven': 'ore_reserves',
            'Erzgehalt': 'ore_grade',
            'Tiefe': 'depth',
            'Mitarbeiter': 'employees',
            'Website': 'website',
            'Muttergesellschaft': 'parent_company',
            'Jahr der Erstellung des Dokumentes': 'document_year',
            # VOLLSTÄNDIGE DEUTSCHE FELDMAPPINGS 19.07.2025
            'Name': 'mine_name',
            'Country': 'country', 
            'Region': 'region',
            'Quellenangaben': 'sources',
            # Fallback für englische Feldnamen (falls schon englisch gespeichert)
            'owner': 'owner',
            'operator': 'operator',
            'latitude': 'latitude',
            'longitude': 'longitude',
            'status': 'status',
            'mine_type': 'mine_type',
            'production_start': 'production_start',
            'production_end': 'production_end',
            'restoration_costs': 'restoration_costs',
            'restoration_currency': 'restoration_currency',
            'restoration_year': 'restoration_year',
            'ore_reserves': 'ore_reserves',
            'annual_production': 'annual_production',
            'mine_area': 'mine_area',
            'ore_grade': 'ore_grade',
            'depth': 'depth',
            'employees': 'employees',
            'website': 'website',
            'parent_company': 'parent_company'
        }
    
    def generate_csv_export(self, results: List[Any]) -> str:
        """
        Generiere CSV-Export aus Suchergebnissen
        
        Args:
            results: Liste der SearchResult ORM-Objekte
            
        Returns:
            CSV-Content als String
        """
        logger.info(f"[CSV-EXPORT] Starte CSV-Generierung für {len(results)} Ergebnisse")
        
        output = io.StringIO()
        writer = csv.DictWriter(
            output,
            fieldnames=self.csv_headers,
            delimiter=self.delimiter,
            quotechar=self.quotechar,
            quoting=self.quoting,
            lineterminator='\n'
        )
        
        # CSV Header schreiben
        writer.writeheader()
        
        # Datenzeilen schreiben
        for result in results:
            try:
                row_data = self._convert_result_to_csv_row(result)
                writer.writerow(row_data)
            except Exception as e:
                logger.error(f"[CSV-EXPORT] Fehler bei Ergebnis {result.id}: {e}")
                # Füge Fehlzeile hinzu
                error_row = self._create_error_row(result, str(e))
                writer.writerow(error_row)
        
        csv_content = output.getvalue()
        output.close()
        
        logger.info(f"[CSV-EXPORT] CSV-Generierung abgeschlossen. Größe: {len(csv_content)} Zeichen")
        return csv_content
    
    def _convert_result_to_csv_row(self, result: Any) -> Dict[str, str]:
        """
        Konvertiere SearchResult zu CSV-Zeile
        
        Args:
            result: SearchResult ORM-Objekt
            
        Returns:
            Dictionary mit CSV-Daten
        """
        # Basis-Informationen
        row = {
            'id': str(result.id),
            'search_timestamp': self._format_timestamp(result.search_timestamp),
            'mine_name': self._sanitize_csv_value(result.mine_name),
            'country': self._sanitize_csv_value(result.country),
            'region': self._sanitize_csv_value(result.region),
            'commodity': self._sanitize_csv_value(result.commodity),
            'model_used': self._sanitize_csv_value(result.model_used),
            'search_duration': str(result.search_duration) if result.search_duration else '',
            'session_id': self._sanitize_csv_value(result.session_id),
            'success': 'Ja' if result.success else 'Nein',
            'error_message': self._sanitize_csv_value(result.error_message),
        }
        
        # Provider extrahieren
        provider = result.model_used.split(':')[0] if result.model_used and ':' in result.model_used else 'unknown'
        row['provider'] = self._sanitize_csv_value(provider)
        
        # Datenqualität und Statistiken
        if result.structured_data:
            structured_data = result.structured_data
            filled_fields = sum(1 for v in structured_data.values() if v and str(v).strip() != '')
            total_fields = len(structured_data)
            row['data_quality'] = f"{round((filled_fields / total_fields) * 100, 1)}%" if total_fields > 0 else '0%'
            row['fields_found'] = str(filled_fields)
            
            # FIELD-MAPPING 19.07.2025: Intelligente Strukturierte Datenfelder-Extraktion
            row['owner'] = self._get_field_value(structured_data, 'owner')
            row['operator'] = self._get_field_value(structured_data, 'operator')
            row['latitude'] = self._get_field_value(structured_data, 'latitude')
            row['longitude'] = self._get_field_value(structured_data, 'longitude')
            row['mine_type'] = self._get_field_value(structured_data, 'mine_type')
            row['status'] = self._get_field_value(structured_data, 'status')
            row['production_start'] = self._get_field_value(structured_data, 'production_start')
            row['production_end'] = self._get_field_value(structured_data, 'production_end')
            row['ore_reserves'] = self._get_field_value(structured_data, 'ore_reserves')
            row['annual_production'] = self._get_field_value(structured_data, 'annual_production')
            row['mine_area'] = self._get_field_value(structured_data, 'mine_area')
            row['restoration_costs'] = self._get_field_value(structured_data, 'restoration_costs')
            row['restoration_currency'] = self._get_field_value(structured_data, 'restoration_currency')
            row['restoration_year'] = self._get_field_value(structured_data, 'restoration_year')
            row['ore_grade'] = self._get_field_value(structured_data, 'ore_grade')
            row['depth'] = self._get_field_value(structured_data, 'depth')
            row['employees'] = self._get_field_value(structured_data, 'employees')
            row['website'] = self._get_field_value(structured_data, 'website')
            row['parent_company'] = self._get_field_value(structured_data, 'parent_company')
            
            # ZUSÄTZLICHE FELDER 19.07.2025: Erweitere um fehlende deutsche Felder  
            # Falls commodity leer ist, versuche deutschen Rohstoffabbau-Feldnamen
            if not row['commodity']:
                row['commodity'] = self._get_field_value(structured_data, 'commodity')
        else:
            row['data_quality'] = '0%'
            row['fields_found'] = '0'
            # Alle strukturierten Felder leer lassen
            for field in ['owner', 'operator', 'latitude', 'longitude', 'mine_type', 'status', 
                         'production_start', 'production_end', 'ore_reserves', 'annual_production',
                         'mine_area', 'restoration_costs', 'restoration_currency', 'restoration_year',
                         'ore_grade', 'depth', 'employees', 'website', 'parent_company']:
                row[field] = ''
        
        # Quellen zählen
        sources_count = 0
        if hasattr(result, 'sources') and result.sources:
            if isinstance(result.sources, list):
                sources_count = len(result.sources)
            elif isinstance(result.sources, str):
                # Falls Sources als JSON-String gespeichert
                try:
                    import json
                    sources_data = json.loads(result.sources)
                    sources_count = len(sources_data) if isinstance(sources_data, list) else 0
                except:
                    sources_count = 0
        
        row['sources_count'] = str(sources_count)
        
        # Stelle sicher, dass alle Header-Felder vorhanden sind
        for header in self.csv_headers:
            if header not in row:
                row[header] = ''
        
        return row
    
    def _sanitize_csv_value(self, value: Any) -> str:
        """
        Sanitize Wert für CSV-Export
        
        Args:
            value: Zu sanitisierender Wert
            
        Returns:
            Gesäuberter String-Wert
        """
        if value is None:
            return ''
        
        # Konvertiere zu String
        str_value = str(value).strip()
        
        # Leere Strings
        if not str_value:
            return ''
        
        # Ersetze problematische Zeichen
        str_value = str_value.replace('\n', ' ')  # Zeilenumbrüche
        str_value = str_value.replace('\r', ' ')  # Carriage Returns
        str_value = str_value.replace('\t', ' ')  # Tabs
        
        # Mehrfache Leerzeichen reduzieren
        import re
        str_value = re.sub(r'\s+', ' ', str_value)
        
        return str_value.strip()
    
    def _get_field_value(self, structured_data: Dict[str, Any], target_field: str) -> str:
        """
        Intelligente Feldwert-Extraktion mit deutschem/englischem Mapping
        
        Args:
            structured_data: Dictionary mit strukturierten Daten
            target_field: Ziel-Feldname (englisch)
            
        Returns:
            Gefundener und sanitisierter Wert oder leerer String
        """
        if not structured_data:
            return ''
        
        # Suche nach passenden deutschen oder englischen Feldnamen
        for source_field, mapped_field in self.field_mapping.items():
            if mapped_field == target_field:
                value = structured_data.get(source_field)
                if value and str(value).strip():
                    # FIELD-MAPPING-FIX 19.07.2025: Zeige auch "X" für vollständige Transparenz
                    if str(value) == 'X':
                        return ''  # Leerer String statt "X" für bessere CSV-Lesbarkeit
                    else:
                        return self._sanitize_csv_value(value)
        
        # Fallback: Direkter Zugriff auf Zielfeld  
        direct_value = structured_data.get(target_field)
        if direct_value and str(direct_value).strip():
            if str(direct_value) == 'X':
                return ''  # Leerer String statt "X"
            else:
                return self._sanitize_csv_value(direct_value)
        
        return ''
    
    def _format_timestamp(self, timestamp: Any) -> str:
        """
        Formatiere Timestamp für CSV-Export
        
        Args:
            timestamp: Datetime-Objekt, String oder None
            
        Returns:
            Formatierter ISO-String
        """
        if timestamp is None:
            return ''
        
        # Wenn bereits String
        if isinstance(timestamp, str):
            return timestamp
        
        # Wenn datetime-Objekt
        try:
            return timestamp.isoformat()
        except:
            # Fallback: Als String verwenden
            return str(timestamp)
    
    def _create_error_row(self, result: Any, error_msg: str) -> Dict[str, str]:
        """
        Erstelle Fehler-Zeile für problematische Ergebnisse
        
        Args:
            result: SearchResult mit Fehler
            error_msg: Fehlermeldung
            
        Returns:
            Fehler-Dictionary für CSV
        """
        error_row = {header: '' for header in self.csv_headers}
        
        # Basis-Informationen wenn verfügbar
        try:
            error_row['id'] = str(result.id) if hasattr(result, 'id') else 'ERROR'
            error_row['mine_name'] = self._sanitize_csv_value(result.mine_name) if hasattr(result, 'mine_name') else 'ERROR'
            error_row['error_message'] = f"CSV-Export Fehler: {error_msg}"
            error_row['success'] = 'Nein'
        except:
            error_row['error_message'] = f"Schwerwiegender CSV-Export Fehler: {error_msg}"
        
        return error_row
    
    def get_csv_headers(self) -> List[str]:
        """
        Gibt die verwendeten CSV-Header zurück
        
        Returns:
            Liste der CSV-Header
        """
        return self.csv_headers.copy()
    
    def estimate_csv_size(self, result_count: int) -> int:
        """
        Schätze CSV-Dateigröße in Bytes
        
        Args:
            result_count: Anzahl der Ergebnisse
            
        Returns:
            Geschätzte Dateigröße in Bytes
        """
        # Durchschnittlich ~500 Zeichen pro Zeile
        avg_row_size = 500
        header_size = len('|'.join(self.csv_headers))
        
        estimated_size = header_size + (result_count * avg_row_size)
        return estimated_size