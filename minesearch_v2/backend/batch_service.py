"""
Author: rahn  
Datum: 01.07.2025
Version: 1.0
Beschreibung: Batch-Service für MineSearch - CSV-Upload und Batch-Verarbeitung
"""

import logging
import csv
import io
import uuid
from typing import Dict, List, Any, Optional
from datetime import datetime
from fastapi import UploadFile, HTTPException
from fastapi.responses import HTMLResponse

from config import config, CSV_COLUMNS, FIELDS_WITHOUT_SOURCES

# ÄNDERUNG 01.07.2025: Strukturiertes Logging (Regel 16)
logger = logging.getLogger(__name__)

class BatchService:
    """Service-Klasse für Batch-Operationen und CSV-Verarbeitung"""
    
    def __init__(self, uploaded_mines_cache: Dict, batch_results_cache: Dict):
        self.uploaded_mines_cache = uploaded_mines_cache
        self.batch_results_cache = batch_results_cache
    
    async def process_csv_upload(self, csv_file: UploadFile) -> HTMLResponse:
        """
        CSV Datei hochladen und analysieren.
        Erwartet Spalten: mine_name (Pflicht), country, commodity (optional)
        """
        if not csv_file.filename.endswith('.csv'):
            raise HTTPException(status_code=400, detail="Nur CSV Dateien erlaubt")
        
        try:
            # Lese CSV Inhalt
            contents = await csv_file.read()
            text_content = contents.decode('utf-8-sig')  # Handle BOM
            
            # Erkenne Delimiter
            first_line = text_content.split('\n')[0]
            delimiter = ';' if ';' in first_line else ','
            logger.info(f"CSV Delimiter erkannt: '{delimiter}'")
            
            # Parse CSV
            mines = self._parse_csv_content(text_content, delimiter)
            
            if not mines:
                raise ValueError("Keine gültigen Minen in der CSV gefunden")
            
            # Generiere Session-ID und speichere
            session_id = str(uuid.uuid4())
            self.uploaded_mines_cache[session_id] = mines
            logger.info(f"CSV mit {len(mines['mines'])} Minen in Session {session_id} gespeichert")
            
            # Erstelle Response HTML
            return self._create_upload_response(session_id, mines)
            
        except Exception as e:
            logger.error(f"Fehler beim CSV Upload: {e}")
            return HTMLResponse(
                content=f'<div class="result-card error"><h3>❌ Fehler beim Laden der CSV</h3><p>{str(e)}</p></div>'
            )
    
    def _parse_csv_content(self, text_content: str, delimiter: str) -> Dict[str, Any]:
        """Parse CSV Inhalt und extrahiere Minen-Daten"""
        csv_reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)
        mines = []
        
        # Erkenne mögliche Spaltennamen
        first_row = next(csv_reader, None)
        if not first_row:
            raise ValueError("CSV ist leer")
            
        # Zurück zum Anfang
        csv_reader = csv.DictReader(io.StringIO(text_content), delimiter=delimiter)
        
        # Finde relevante Spalten
        columns = {k.lower(): k for k in first_row.keys()}
        
        # Spalten-Mapping
        column_mappings = self._find_column_mappings(columns)
        
        if not column_mappings['mine_column']:
            available = list(first_row.keys())
            raise ValueError(f"Keine Spalte für Minennamen gefunden. Verfügbare Spalten: {', '.join(available)}")
        
        logger.info(f"CSV Spalten gefunden: {column_mappings}")
        
        # Lese Minen-Daten
        for row in csv_reader:
            mine_name = row.get(column_mappings['mine_column'], '').strip()
            if not mine_name:
                continue
                
            mine = {
                'mine_name': mine_name,
                'country': row.get(column_mappings['country_column'], '').strip() if column_mappings['country_column'] else '',
                'region': row.get(column_mappings['region_column'], '').strip() if column_mappings['region_column'] else '',
                'owner': row.get(column_mappings['owner_column'], '').strip() if column_mappings['owner_column'] else '',
                'commodity': row.get(column_mappings['commodity_column'], '').strip() if column_mappings['commodity_column'] else '',
                'all_data': row
            }
            mines.append(mine)
        
        return {
            'mines': mines,
            'columns': list(first_row.keys()),
            **column_mappings
        }
    
    def _find_column_mappings(self, columns: Dict[str, str]) -> Dict[str, Optional[str]]:
        """Finde Spalten-Mappings für verschiedene Sprachen"""
        mappings = {
            'mine_column': None,
            'country_column': None,
            'region_column': None,
            'owner_column': None,
            'commodity_column': None
        }
        
        # Mögliche Namen für verschiedene Spalten
        possibilities = {
            'mine_column': ['name', 'mine', 'mine_name', 'site', 'mine site', 'nom', 'nom de la mine', 'site minier', 'minenname'],
            'country_column': ['country', 'land', 'pays', 'staat', 'país', 'negara'],
            'region_column': ['region', 'province', 'provinz', 'état', 'bundesland', 'territorio', 'wilayah', 'departamento', 'región'],
            'owner_column': ['owner', 'eigentümer', 'propriétaire', 'propietario', 'pemilik', 'dueño', 'belongs to', 'property of', 'gehört'],
            'commodity_column': ['commodity', 'rohstoff', 'rohstoffabbau', 'material', 'substance', 'mineral', 'produit', 'minerai', 'ressource']
        }
        
        # Suche passende Spalten
        for mapping_key, possible_names in possibilities.items():
            for possible in possible_names:
                if possible.lower() in columns:
                    mappings[mapping_key] = columns[possible.lower()]
                    break
        
        return mappings
    
    def _create_upload_response(self, session_id: str, mines_data: Dict) -> HTMLResponse:
        """Erstelle HTML Response für erfolgreichen Upload"""
        mines = mines_data['mines']
        
        html_response = f"""
        <div class="csv-info-card">
            <h3>✓ CSV erfolgreich geladen</h3>
            <p><strong>{len(mines)}</strong> Minen gefunden</p>
            
            <form id="batch-form" 
                  hx-post="/api/batch-search" 
                  hx-target="#results"
                  hx-indicator="#batch-loading">
                
                <input type="hidden" name="session_id" value="{session_id}">
                <input type="hidden" name="selected_models" id="batch_selected_models" value="">
                
                <div class="model-info" style="margin-bottom: 15px; padding: 10px; background: #e8f4f8; border-radius: 5px;">
                    <p style="margin: 0;"><strong>Hinweis:</strong> Die Batch-Suche verwendet die oben ausgewählten Modelle.</p>
                    <p style="margin: 5px 0 0 0; font-size: 14px; color: #666;">
                        ⚠️ Bei Abacus AI: Rechne mit bis zu 5 Minuten pro Mine!
                    </p>
                </div>
                
                <div class="form-group">
                    <label>Anzahl zu suchender Minen:</label>
                    <div style="display: flex; gap: 10px; align-items: center;">
                        <input type="number" 
                               name="count" 
                               min="1" 
                               max="{len(mines)}"
                               value="{min(5, len(mines))}"
                               style="width: 100px;">
                        <span>von {len(mines)} Minen</span>
                        <button type="submit" name="search_all" value="false" class="batch-search-button">
                            Suche starten
                        </button>
                        <button type="submit" name="search_all" value="true" class="batch-search-button">
                            Alle suchen
                        </button>
                    </div>
                </div>
            </form>
            
            <div id="batch-loading" class="htmx-indicator">
                <div class="spinner"></div>
                <p>Batch-Suche läuft...</p>
            </div>
            
            <details style="margin-top: 20px;">
                <summary>Erste 5 Minen anzeigen</summary>
                <ul>
                    {"".join([f"<li>{m['mine_name']} ({m['country'] or 'Kein Land'}) - {m['commodity'] or 'Kein Rohstoff'}</li>" for m in mines[:5]])}
                </ul>
            </details>
        </div>
        """
        
        return HTMLResponse(content=html_response)
    
    def save_batch_results(self, session_id: str, results: List[Dict], errors: List[Dict], model: str):
        """Speichere Batch-Ergebnisse für späteren Download"""
        if session_id in self.uploaded_mines_cache:
            columns = self.uploaded_mines_cache[session_id].get('columns', [])
        else:
            columns = []
            
        self.batch_results_cache[session_id] = {
            'results': results,
            'errors': errors,
            'timestamp': datetime.now(),
            'model': model,
            'columns': columns
        }
    
    def get_csv_download_content(self, session_id: str) -> str:
        """Erstelle CSV-Content für Download"""
        if session_id not in self.batch_results_cache:
            raise ValueError("Keine Ergebnisse gefunden")
        
        cache_data = self.batch_results_cache[session_id]
        results = cache_data['results']
        
        # CSV erstellen
        output = io.StringIO()
        writer = csv.writer(output, delimiter='|', quoting=csv.QUOTE_MINIMAL)
        
        # Header schreiben
        writer.writerow(CSV_COLUMNS)
        
        # Für jedes Ergebnis eine Zeile
        for result in results:
            if result['data'].get('success', True) and 'structured_data' in result['data']:
                row = []
                structured_data = result['data']['structured_data']
                data_with_sources = result['data'].get('structured_data_with_sources', {})
                
                for col in CSV_COLUMNS:
                    val = structured_data.get(col, '')
                    
                    # Füge Quellennummern hinzu
                    if (col not in FIELDS_WITHOUT_SOURCES and 
                        col in data_with_sources and
                        val and val != '-'):
                        sources = data_with_sources[col].get('sources', [])
                        if sources:
                            val += f" [{','.join(map(str, sources))}]"
                    
                    row.append(val)
                
                writer.writerow(row)
        
        csv_content = output.getvalue()
        output.close()
        
        return csv_content