"""
Datenexport-Modul für Mining Research System
"""
import csv
import json
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Any, Optional
import pandas as pd

from ..core.config import get_config
from ..core.database import get_db_manager, Mine
from ..core.logger import get_logger


class DataExporter:
    """Exportiert aggregierte Daten in verschiedene Formate"""
    
    def __init__(self):
        self.config = get_config()
        self.db_manager = get_db_manager()
        self.logger = get_logger("data_exporter")
        
    def export_to_csv(self, results: List[Dict[str, Any]], 
                     output_path: Optional[Path] = None,
                     column_separator: Optional[str] = None,
                     cell_separator: Optional[str] = None) -> Path:
        """Exportiert Ergebnisse als CSV"""
        
        # Verwende Konfiguration oder übergebene Werte
        col_sep = column_separator or self.config.export.column_separator
        cell_sep = cell_separator or self.config.export.cell_separator
        
        # Output-Pfad
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.export.default_path / f"mine_search_results_{timestamp}.csv"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Erstelle DataFrame-Struktur
        rows = []
        
        for result in results:
            if 'aggregated' not in result or not result['aggregated']:
                continue
                
            mine_id = result.get('mine_id')
            mine = self._get_mine_info(mine_id) if mine_id else {}
            
            row = {
                'Mine Name': mine.get('name', ''),
                'Region': mine.get('region', ''),
                'Country': mine.get('country', ''),
                'Search Date': result.get('timestamp', ''),
                'Quality Score': result.get('metrics', {}).get('quality_score', ''),
                'Completeness': result.get('metrics', {}).get('completeness_score', '')
            }
            
            # Füge aggregierte Felder hinzu
            agg_data = result['aggregated'].get('data', {})
            
            # Standard-Felder
            field_mapping = {
                'betreiber': 'Operator',
                'latitude': 'Latitude',
                'longitude': 'Longitude',
                'aktivitaetsstatus': 'Activity Status',
                'sanierungskosten': 'Environmental Costs',
                'kostenerfassungsjahr': 'Cost Year',
                'rohstofftyp': 'Resource Type',
                'minentyp': 'Mine Type',
                'produktionsbeginn': 'Production Start',
                'jahresproduktion': 'Annual Production',
                'minenflaeche': 'Mine Area (km²)'
            }
            
            for field_key, field_name in field_mapping.items():
                if field_key in agg_data:
                    value = agg_data[field_key]['value']
                    source = agg_data[field_key]['source']
                    confidence = agg_data[field_key]['confidence']
                    
                    # Formatiere Wert mit Quelle und Konfidenz
                    formatted_value = f"{value}{cell_sep}{source}{cell_sep}{confidence}"
                    row[field_name] = formatted_value
                else:
                    row[field_name] = f"nichts gefunden{cell_sep}{cell_sep}"
            
            # Alternative Werte
            alternatives = result['aggregated'].get('alternatives', {})
            if alternatives:
                alt_values = []
                for field, alts in alternatives.items():
                    for alt in alts[:2]:  # Max 2 Alternativen
                        alt_values.append(f"{field}: {alt['value']} ({alt['source']})")
                row['Alternative Values'] = cell_sep.join(alt_values)
            
            rows.append(row)
        
        # Schreibe CSV
        if rows:
            df = pd.DataFrame(rows)
            df.to_csv(output_path, sep=col_sep, index=False, encoding='utf-8-sig')
            self.logger.info(f"Exportiert {len(rows)} Minen nach {output_path}")
        else:
            # Leere CSV mit Headers
            headers = ['Mine Name', 'Region', 'Country', 'Search Date', 
                      'Quality Score', 'Completeness']
            with open(output_path, 'w', newline='', encoding='utf-8-sig') as f:
                writer = csv.writer(f, delimiter=col_sep)
                writer.writerow(headers)
            self.logger.warning("Keine Daten zum Exportieren gefunden")
        
        return output_path
    
    def export_to_json(self, results: List[Dict[str, Any]], 
                      output_path: Optional[Path] = None) -> Path:
        """Exportiert Ergebnisse als JSON"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.export.default_path / f"mine_search_results_{timestamp}.json"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        # Erweitere Daten mit Mine-Informationen
        export_data = []
        for result in results:
            mine_id = result.get('mine_id')
            mine_info = self._get_mine_info(mine_id) if mine_id else {}
            
            export_item = {
                'mine': mine_info,
                'search_metadata': {
                    'search_id': result.get('search_id'),
                    'timestamp': result.get('timestamp'),
                    'agents_used': result.get('aggregated', {}).get('metadata', {}).get('agents_used', [])
                },
                'aggregated_data': result.get('aggregated', {}).get('data', {}),
                'alternatives': result.get('aggregated', {}).get('alternatives', {}),
                'quality_metrics': result.get('metrics', {}),
                'raw_results_count': len(result.get('results', []))
            }
            export_data.append(export_item)
        
        # Schreibe JSON
        with open(output_path, 'w', encoding='utf-8') as f:
            json.dump(export_data, f, ensure_ascii=False, indent=2)
        
        self.logger.info(f"JSON exportiert nach {output_path}")
        return output_path
    
    def export_summary_report(self, results: List[Dict[str, Any]], 
                            output_path: Optional[Path] = None) -> Path:
        """Erstellt zusammenfassenden Bericht"""
        if not output_path:
            timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
            output_path = self.config.export.default_path / f"mine_search_summary_{timestamp}.txt"
        
        output_path = Path(output_path)
        output_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(output_path, 'w', encoding='utf-8') as f:
            f.write("MULTI-AGENT MINING RESEARCH - ZUSAMMENFASSUNG\n")
            f.write("=" * 50 + "\n\n")
            f.write(f"Erstellt am: {datetime.now().strftime('%d.%m.%Y %H:%M:%S')}\n\n")
            
            # Gesamtstatistik
            total_mines = len(results)
            successful_mines = sum(1 for r in results if r.get('aggregated'))
            avg_quality = sum(r.get('metrics', {}).get('quality_score', 0) for r in results) / total_mines if total_mines > 0 else 0
            avg_completeness = sum(r.get('metrics', {}).get('completeness_score', 0) for r in results) / total_mines if total_mines > 0 else 0
            
            f.write("GESAMTSTATISTIK:\n")
            f.write(f"- Minen untersucht: {total_mines}\n")
            f.write(f"- Erfolgreiche Suchen: {successful_mines}\n")
            f.write(f"- Durchschnittliche Qualität: {avg_quality:.1f}%\n")
            f.write(f"- Durchschnittliche Vollständigkeit: {avg_completeness:.1f}%\n\n")
            
            # Details pro Mine
            f.write("ERGEBNISSE PRO MINE:\n")
            f.write("-" * 50 + "\n\n")
            
            for result in results:
                mine_id = result.get('mine_id')
                mine = self._get_mine_info(mine_id) if mine_id else {}
                
                f.write(f"Mine: {mine.get('name', 'Unbekannt')}\n")
                f.write(f"Region: {mine.get('region', '')}, {mine.get('country', '')}\n")
                
                if result.get('aggregated'):
                    agg_data = result['aggregated'].get('data', {})
                    metrics = result.get('metrics', {})
                    
                    f.write(f"Qualität: {metrics.get('quality_score', 0):.1f}% | ")
                    f.write(f"Vollständigkeit: {metrics.get('completeness_score', 0):.1f}%\n")
                    f.write(f"Gefundene Felder: {len(agg_data)}\n")
                    
                    # Wichtigste Daten
                    if 'betreiber' in agg_data:
                        f.write(f"- Betreiber: {agg_data['betreiber']['value']}\n")
                    if 'sanierungskosten' in agg_data:
                        f.write(f"- Sanierungskosten: {agg_data['sanierungskosten']['value']}\n")
                    if 'aktivitaetsstatus' in agg_data:
                        f.write(f"- Status: {agg_data['aktivitaetsstatus']['value']}\n")
                else:
                    f.write("Status: Keine Daten gefunden\n")
                
                f.write("\n")
            
            # Verwendete Agenten
            all_agents = set()
            for result in results:
                agents = result.get('aggregated', {}).get('metadata', {}).get('agents_used', [])
                all_agents.update(agents)
            
            f.write("\nVERWENDETE AGENTEN:\n")
            for agent in sorted(all_agents):
                f.write(f"- {agent}\n")
        
        self.logger.info(f"Zusammenfassung exportiert nach {output_path}")
        return output_path
    
    def _get_mine_info(self, mine_id: int) -> Dict[str, Any]:
        """Holt Mine-Informationen aus DB"""
        try:
            with self.db_manager.get_session() as session:
                mine = session.query(Mine).filter_by(id=mine_id).first()
                if mine:
                    return {
                        'id': mine.id,
                        'name': mine.name,
                        'region': mine.region,
                        'country': mine.country,
                        'languages': mine.languages
                    }
        except Exception as e:
            self.logger.error(f"Fehler beim Abrufen von Mine {mine_id}: {e}")
        
        return {}