"""
Author: rahn
Datum: 19.07.2025
Version: 1.1
Beschreibung: Batch-Processing Routes für CSV-Upload (FIXED 500 Error)
"""

from fastapi import APIRouter, UploadFile, File, Form, HTTPException, Query
from fastapi.responses import Response, HTMLResponse
import csv
import io
import logging
import asyncio
import random
from ...fallback_detector import validate_data, clean_fallback_values
try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    fcntl = None
    HAS_FCNTL = False
import os
import tempfile
import threading
from typing import Optional, List, Dict, Any
from datetime import datetime

from minesearch.config import CSV_COLUMNS
from minesearch.batch_service import BatchService  # Adapter
from minesearch.search_service import MineSearchService
# 2-PHASEN WORKFLOW IMPORT (29.08.2025)
from minesearch.batch_progress_manager import ProgressState
# CONSOLIDATION 09.08.2025: MultiProviderSearchService entfernt - verwende MineSearchService direkt
from minesearch.providers.registry import provider_registry
from minesearch.database import db_manager
from minesearch.database.normalized_manager import NormalizedDatabaseManager
from minesearch.extraction_validators import is_placeholder_value
from minesearch.html_utils import create_batch_results_table
# BATCH-FIX 23.08.2025: Import MultiModelSearchOrchestrator für Provider-Suche
from minesearch.multi_model_search_orchestrator import MultiModelSearchOrchestrator
# ÄNDERUNG 27.08.2025: Import Sequential Field Orchestrator für neuen Workflow
from minesearch.sequential_field_orchestrator import SequentialFieldOrchestrator
from minesearch.database.sequential_manager import SequentialDatabaseManager
# PROGRESS-FIX 29.08.2025: Import BatchProgressManager für detaillierte Fortschrittsanzeige
from minesearch.batch_progress_manager import batch_progress_manager, ProgressState

logger = logging.getLogger(__name__)
router = APIRouter()

# Konfigurierbares Sicherheitslimit für CSV-Einträge (Default 10.000)
MAX_MINES_LIMIT = int(os.getenv("MAX_MINES_LIMIT", "10000"))

# Anfrage-basiertes Sicherheitslimit pro Batch-Request (Client/Server-Validierung)
BATCH_REQUEST_MAX_COUNT = int(os.getenv("BATCH_MAX_COUNT", "1000"))

# NORMALIZED SCHEMA FIX 28.08.2025: Initialize NormalizedDatabaseManager
normalized_db_manager = NormalizedDatabaseManager()

# Modulweiter Fallback-Lock für plattformübergreifende Serialisierung von Dateischreibzugriffen
file_write_lock = threading.Lock()

def safe_write_to_file(filepath: str, content: str, mode: str = 'a'):
    """
    Thread-safe, cross-platform file writing with locking
    
    Args:
        filepath: Path to the file
        content: Content to write
        mode: File mode ('a' for append, 'w' for overwrite)
    """
    # Prefer lightweight cross-platform file locks if available
    # Order: fcntl (POSIX) -> portalocker -> filelock -> threading.Lock
    try:
        # Lazy import of optional dependencies to avoid hard dependency
        try:
            import portalocker  # type: ignore
            HAS_PORTALOCKER = True
        except Exception:
            portalocker = None  # type: ignore
            HAS_PORTALOCKER = False
        try:
            from filelock import FileLock  # type: ignore
            HAS_FILELOCK = True
        except Exception:
            FileLock = None  # type: ignore
            HAS_FILELOCK = False

        lock_timeout_seconds = 10
        lockfile_path = f"{filepath}.lock"

        if HAS_FCNTL:
            # POSIX path: use fcntl on a dedicated handle to serialize writers
            try:
                with open(filepath, 'a+', encoding='utf-8') as lock_handle:
                    fcntl.flock(lock_handle.fileno(), fcntl.LOCK_EX)
                    if mode == 'a':
                        with open(filepath, 'a', encoding='utf-8') as f:
                            f.write(content)
                            f.flush()
                            os.fsync(f.fileno())
                    else:
                        # Atomic overwrite via temp file + os.replace
                        dir_name = os.path.dirname(filepath) or '.'
                        base_name = os.path.basename(filepath)
                        fd, tmp_path = tempfile.mkstemp(prefix=f".{base_name}.", dir=dir_name, text=True)
                        try:
                            with os.fdopen(fd, 'w', encoding='utf-8') as tmp_f:
                                tmp_f.write(content)
                                tmp_f.flush()
                                os.fsync(tmp_f.fileno())
                            os.replace(tmp_path, filepath)
                        finally:
                            try:
                                if os.path.exists(tmp_path):
                                    os.remove(tmp_path)
                            except Exception:
                                pass
            finally:
                # fcntl lock released on close
                pass
        else:
            # Cross-platform fallback using external or in-process locks
            if 'HAS_PORTALOCKER' in locals() and HAS_PORTALOCKER:
                with portalocker.Lock(lockfile_path, timeout=lock_timeout_seconds):
                    if mode == 'a':
                        with open(filepath, 'a', encoding='utf-8') as f:
                            f.write(content)
                            f.flush()
                            os.fsync(f.fileno())
                    else:
                        dir_name = os.path.dirname(filepath) or '.'
                        base_name = os.path.basename(filepath)
                        fd, tmp_path = tempfile.mkstemp(prefix=f".{base_name}.", dir=dir_name, text=True)
                        try:
                            with os.fdopen(fd, 'w', encoding='utf-8') as tmp_f:
                                tmp_f.write(content)
                                tmp_f.flush()
                                os.fsync(tmp_f.fileno())
                            os.replace(tmp_path, filepath)
                        finally:
                            try:
                                if os.path.exists(tmp_path):
                                    os.remove(tmp_path)
                            except Exception:
                                pass
            elif 'HAS_FILELOCK' in locals() and HAS_FILELOCK:
                with FileLock(lockfile_path, timeout=lock_timeout_seconds):
                    if mode == 'a':
                        with open(filepath, 'a', encoding='utf-8') as f:
                            f.write(content)
                            f.flush()
                            os.fsync(f.fileno())
                    else:
                        dir_name = os.path.dirname(filepath) or '.'
                        base_name = os.path.basename(filepath)
                        fd, tmp_path = tempfile.mkstemp(prefix=f".{base_name}.", dir=dir_name, text=True)
                        try:
                            with os.fdopen(fd, 'w', encoding='utf-8') as tmp_f:
                                tmp_f.write(content)
                                tmp_f.flush()
                                os.fsync(tmp_f.fileno())
                            os.replace(tmp_path, filepath)
                        finally:
                            try:
                                if os.path.exists(tmp_path):
                                    os.remove(tmp_path)
                            except Exception:
                                pass
            else:
                # Last resort: serialize within this process
                with file_write_lock:
                    if mode == 'a':
                        with open(filepath, 'a', encoding='utf-8') as f:
                            f.write(content)
                            f.flush()
                            os.fsync(f.fileno())
                    else:
                        dir_name = os.path.dirname(filepath) or '.'
                        base_name = os.path.basename(filepath)
                        fd, tmp_path = tempfile.mkstemp(prefix=f".{base_name}.", dir=dir_name, text=True)
                        try:
                            with os.fdopen(fd, 'w', encoding='utf-8') as tmp_f:
                                tmp_f.write(content)
                                tmp_f.flush()
                                os.fsync(tmp_f.fileno())
                            os.replace(tmp_path, filepath)
                        finally:
                            try:
                                if os.path.exists(tmp_path):
                                    os.remove(tmp_path)
                            except Exception:
                                pass
    except (IOError, OSError) as e:
        logger.error(f"Failed to write to {filepath}: {e}")
        # Fallback to regular logging
        logger.info(f"[DEBUG-FILE-FALLBACK] {content.strip()}")
    except Exception as e:
        # Logge auch nicht-OS-Fehler (z.B. Lock-Timeouts externer Libraries)
        logger.error(f"Failed to write to {filepath}: {e}")
        logger.info(f"[DEBUG-FILE-FALLBACK] {content.strip()}")

# Alternative: Use application logging infrastructure (recommended)
def create_batch_debug_logger():
    """
    Creates a dedicated logger for batch debug information
    Uses the application's thread-safe logging infrastructure
    """
    debug_logger = logging.getLogger(f"{__name__}.batch_debug")
    
    # Only add handler if not already configured
    if not debug_logger.handlers:
        try:
            handler = logging.FileHandler("/tmp/batch_debug.log", mode='a', encoding='utf-8')
            formatter = logging.Formatter(
                '%(asctime)s - %(levelname)s - %(message)s',
                datefmt='%Y-%m-%d %H:%M:%S'
            )
            handler.setFormatter(formatter)
            debug_logger.addHandler(handler)
            debug_logger.setLevel(logging.INFO)
            debug_logger.propagate = False  # Don't propagate to parent loggers
        except (IOError, OSError) as e:
            # Fallback: If file logging fails, use console logging
            logger.warning(f"Failed to create batch debug log file: {e}")
            handler = logging.StreamHandler()
            formatter = logging.Formatter('[BATCH-DEBUG] %(message)s')
            handler.setFormatter(formatter)
            debug_logger.addHandler(handler)
            debug_logger.setLevel(logging.INFO)
            debug_logger.propagate = False
    
    return debug_logger

# Initialize the batch debug logger with error handling
try:
    batch_debug_logger = create_batch_debug_logger()
except Exception as e:
    logger.error(f"Failed to initialize batch debug logger: {e}")
    # Create a minimal fallback logger
    batch_debug_logger = logging.getLogger(f"{__name__}.batch_debug_fallback")
    batch_debug_logger.addHandler(logging.NullHandler())  # Silent fallback

def count_filled_fields(structured_data):
    """Zählt echte (nicht-leere) Felder in structured_data"""
    if not structured_data:
        return 0
    return len([v for v in structured_data.values() 
                if v and str(v).strip() and str(v).strip() not in ['', 'None', 'null', 'nichts gefunden']])

def is_weak_result(result_data):
    """
    Prüft ob ein Suchergebnis Enhancement benötigt
    
    Returns True wenn:
    - Weniger als 8 echte Felder gefüllt sind
    - 3 oder mehr kritische Felder fehlen
    """
    if not result_data or not result_data.get('success', False):
        return True
        
    data = result_data.get('data', {})
    structured_data = data.get('structured_data', {})
    
    # Zähle gefüllte Felder
    filled_fields = count_filled_fields(structured_data)
    
    # Definiere kritische Felder
    critical_fields = [
        'Restaurationskosten', 
        'Jahr der Aufnahme der Kosten', 
        'Jahr der Erstellung des Dokumentes', 
        'Fläche der Mine in qkm', 
        'Fördermenge/Jahr'
    ]
    
    # Zähle fehlende kritische Felder
    missing_critical = [f for f in critical_fields 
                       if f not in structured_data or not structured_data[f] 
                       or str(structured_data[f]).strip() in ['', 'None', 'null', 'nichts gefunden']]
    
    return filled_fields < 8 or len(missing_critical) >= 3

async def fallback_search_if_needed(mine_name, country, commodity, region, current_best_data):
    """
    Führt Fallback-Suche mit deepseek-free durch, wenn aktuelles Ergebnis schwach ist
    
    Returns: Verbessertes result_data oder None wenn kein Fallback nötig/möglich
    """
    try:
        logger.info(f"[FALLBACK] Starte deepseek-free Fallback für {mine_name}")
        
        # Provider Registry Setup
        from minesearch.providers.registry import provider_registry
        from minesearch.config import config
        
        if not provider_registry._providers:
            provider_registry.initialize(config.PROVIDERS)
        
        provider = provider_registry.get_provider_for_model('openrouter:deepseek-free')
        if not provider:
            logger.error(f"[FALLBACK] Kein deepseek-free Provider verfügbar")
            return None
        
        # Fallback-Suche ausführen
        query = f"{mine_name} mine {country} {commodity} restoration costs area production"
        options = {
            'mine_name': mine_name,
            'country': country,
            'commodity': commodity, 
            'region': region
        }
        
        search_result = await provider.search(query, 'deepseek-free', options)
        
        if search_result and search_result.success and search_result.structured_data:
            # DEBUG: Log Restaurationskosten vor dem Return
            resto_value = search_result.structured_data.get('Restaurationskosten', '')
            logger.info(f"[FALLBACK-DEBUG] Restaurationskosten vor Return: '{resto_value}'")
            
            fallback_filled = count_filled_fields(search_result.structured_data)
            current_filled = count_filled_fields(current_best_data.get('structured_data', {}))
            
            if fallback_filled > current_filled:
                logger.info(f"[FALLBACK-SUCCESS] deepseek-free better: {fallback_filled} vs {current_filled} Felder")
                
                # DEBUG: Log alle kritischen Felder
                critical_fields = ['Restaurationskosten', 'Jahr der Aufnahme der Kosten', 'Fläche der Mine in qkm']
                for field in critical_fields:
                    value = search_result.structured_data.get(field, '(leer)')
                    logger.info(f"[FALLBACK-DEBUG] {field}: '{value}'")
                
                return {
                    'structured_data': search_result.structured_data,
                    'raw_content': search_result.content,
                    'field_count': len(search_result.structured_data),
                    'filled_field_count': fallback_filled,
                    'enhanced_via_fallback': True
                }
            else:
                logger.info(f"[FALLBACK] deepseek-free nicht besser: {fallback_filled} vs {current_filled} Felder")
        else:
            logger.warning(f"[FALLBACK] deepseek-free Suche fehlgeschlagen für {mine_name}")
            
    except Exception as e:
        logger.error(f"[FALLBACK] Fehler bei Fallback-Suche für {mine_name}: {str(e)}")
    
    return None

@router.get("/test")
async def test_batch_endpoint():
    """Test-Endpoint um zu prüfen ob die Route funktioniert"""
    return {"status": "ok", "message": "Batch endpoints are working"}

# Temporärer Speicher für CSV-Daten (in Production würde man Redis/DB nutzen)
uploaded_mines_cache = {}
batch_results_cache = {}

# Batch Service
batch_service = BatchService(uploaded_mines_cache, batch_results_cache)

@router.post("/upload-csv")
async def upload_csv(file: UploadFile = File(...)):
    """CSV Datei hochladen und analysieren"""
    # REPARATUR 04.09.2025: Parameter-Name zurück zu 'file' für Standard-Kompatibilität
    try:
        # DEBUG FIX 04.09.2025: Erweiterte Validierung
        if not file:
            logger.error("[CSV-UPLOAD] File parameter is None")
            raise HTTPException(status_code=422, detail="File parameter is required")
        
        if not file.filename:
            logger.error("[CSV-UPLOAD] File has no filename")
            raise HTTPException(status_code=422, detail="File must have a filename")
        
        logger.info(f"CSV Upload empfangen: {file.filename}, Size: {file.size if hasattr(file, 'size') else 'unknown'}")
        
        # Verarbeite CSV direkt hier statt batch_service zu nutzen
        contents = await file.read()
        csv_content = contents.decode('utf-8-sig')  # FIX: UTF-8-SIG entfernt BOM automatisch
        
        # FIX: Auto-detect CSV-Delimiter (Semikolon vs Komma)
        delimiter = ';' if ';' in csv_content.split('\n')[0] else ','
        logger.info(f"[CSV-PARSER] Detected delimiter: '{delimiter}'")
        
        # Parse CSV mit korrektem Delimiter
        csv_reader = csv.DictReader(io.StringIO(csv_content), delimiter=delimiter)
        mines = []
        columns = []
        
        for i, row in enumerate(csv_reader):
            if i == 0:
                columns = list(row.keys())
            mines.append(row)
            # Abbruch bei Erreichen des konfigurierten Limits, um Systemüberlastung zu vermeiden
            if i + 1 >= MAX_MINES_LIMIT:
                logger.warning(
                    "MAX_MINES_LIMIT erreicht (%d). Verarbeitung wird gestoppt, um das System zu schützen.",
                    MAX_MINES_LIMIT,
                )
                break
        
        # Erstelle Session
        import uuid
        session_id = str(uuid.uuid4())
        
        # Speichere in Cache
        from datetime import datetime
        uploaded_mines_cache[session_id] = {
            'mines': mines,
            'columns': columns,
            'timestamp': datetime.now()
        }
        
        mine_count = len(mines)
        logger.info(f"CSV processed: {mine_count} mines, session: {session_id}")
        
        # Erstelle HTML-Interface für Batch-Suche
        session_id = session_id
        mine_count = mine_count
        columns = columns
        
        # HTML für Batch-Search-Interface generieren
        html_content = f"""
        <div class="csv-upload-success">
            <div class="alert alert-success">
                <h3>✅ CSV erfolgreich hochgeladen!</h3>
                <p><strong>{mine_count} Minen</strong> wurden erkannt mit <strong>{len(columns)} Spalten</strong></p>
                <p><em>Session ID: {session_id}</em></p>
            </div>
            
            <div class="batch-search-interface" style="margin-top: 20px;">
                <h3>🔍 Batch-Suche konfigurieren</h3>
                
                <form id="batch-form" 
                      hx-post="/api/batch-search"
                      hx-target="#batch-results"
                      hx-indicator="#loading">
                    
                    <input type="hidden" name="session_id" value="{session_id}">
                    <input type="hidden" name="selected_models" value="">
                    <input type="hidden" name="sequential_workflow" value="false">
                    
                    <div class="form-group">
                        <label><strong>Mine-Auswahl-Modus:</strong></label>
                        <div style="margin: 10px 0;">
                            <label><input type="radio" name="selection_mode" value="first_n" checked onchange="toggleSelectionOptions()"> Erste X Minen</label>
                            <div id="first_n_options" style="margin-left: 25px; margin-top: 5px;">
                                Anzahl: <input type="number" name="count" value="5" min="1" max="1000" style="width: 60px;">
                            </div>
                        </div>
                        <div style="margin: 10px 0;">
                            <label><input type="radio" name="selection_mode" value="range" onchange="toggleSelectionOptions()"> Range-Auswahl (Von-Bis)</label>
                            <div id="range_options" style="margin-left: 25px; margin-top: 5px; display: none;">
                                Start-Mine: <input type="number" name="start_position" value="1" min="1" style="width: 60px;">
                                Anzahl: <input type="number" name="range_count" value="20" min="1" max="1000" style="width: 60px;">
                                <div style="font-size: 12px; color: #666; margin-top: 2px;" id="range_info">Sucht Minen 1-20 aus der CSV</div>
                            </div>
                        </div>
                        <div style="margin: 10px 0;">
                            <label><input type="radio" name="selection_mode" value="random" onchange="toggleSelectionOptions()"> Zufällige Auswahl</label>
                            <div id="random_options" style="margin-left: 25px; margin-top: 5px; display: none;">
                                Anzahl: <input type="number" name="random_count" value="10" min="1" max="1000" style="width: 60px;"> zufällige Minen
                            </div>
                        </div>
                        <div style="margin: 10px 0;">
                            <label><input type="radio" name="selection_mode" value="all" onchange="toggleSelectionOptions()"> <strong>Alle {mine_count} Minen durchsuchen</strong></label>
                        </div>
                        <div style="margin-top: 10px; padding: 8px; background: #f0f8ff; border-radius: 3px; font-size: 12px;" id="selection_summary">
                            CSV enthält <strong>{mine_count} Minen</strong>. Maximale Batch-Größe pro Anfrage: <strong>1000 Minen</strong>.
                        </div>
                    </div>
                    
                    <div class="form-group">
                        <label><strong>Suchtyp:</strong></label>
                        <select name="search_type" style="width: 300px; padding: 5px;">
                            <option value="standard">Standard-Suche (parallel)</option>
                            <option value="comprehensive">Umfassende Suche</option>
                            <option value="sequential">🔥 Sequential Workflow (NEU)</option>
                        </select>
                        <div style="margin-top: 5px; font-size: 12px; color: #666;">
                            <div id="search-type-help">Standard: Alle Modelle parallel | Sequential: Quellen akkumulieren → Feld-für-Feld suchen</div>
                        </div>
                    </div>
                    
                    <div style="margin: 20px 0;">
                        <button type="submit" class="batch-search-button" style="background: #4CAF50; color: white; padding: 15px 30px; font-size: 18px; border: none; border-radius: 5px; cursor: pointer;">
                            🚀 Batch-Suche starten
                        </button>
                    </div>
                </form>
            </div>
            
            <div class="csv-info-details" style="margin-top: 20px; background: #f5f5f5; padding: 15px; border-radius: 5px;">
                <h4>📋 CSV Details:</h4>
                <p><strong>Spalten gefunden:</strong></p>
                <ul>
                    {"".join([f"<li>{col}</li>" for col in columns[:10]])}
                    {f"<li><em>... und {len(columns) - 10} weitere</em></li>" if len(columns) > 10 else ""}
                </ul>
            </div>
        </div>
        
        <div id="batch-results" style="margin-top: 30px;"></div>
        
        <script>
        document.addEventListener('DOMContentLoaded', function() {{
            const searchTypeSelect = document.querySelector('select[name="search_type"]');
            const sequentialWorkflowInput = document.querySelector('input[name="sequential_workflow"]');
            
            if (searchTypeSelect && sequentialWorkflowInput) {{
                searchTypeSelect.addEventListener('change', function() {{
                    if (this.value === 'sequential') {{
                        sequentialWorkflowInput.value = 'true';
                    }} else {{
                        sequentialWorkflowInput.value = 'false';
                    }}
                }});
            }}
            
            // Mine Selection Options Toggle & Validation
            const mineCount = {mine_count};
            const maxBatchSize = 1000;
            
            // Input Elements
            const startPositionInput = document.querySelector('input[name="start_position"]');
            const rangeCountInput = document.querySelector('input[name="range_count"]');
            const randomCountInput = document.querySelector('input[name="random_count"]');
            const countInput = document.querySelector('input[name="count"]');
            
            // Add event listeners for live validation
            if (startPositionInput && rangeCountInput) {{
                startPositionInput.addEventListener('input', updateRangeInfo);
                rangeCountInput.addEventListener('input', updateRangeInfo);
            }}
            
            if (randomCountInput) {{
                randomCountInput.addEventListener('input', function() {{
                    validateAndCorrect(this, 1, Math.min(mineCount, maxBatchSize));
                }});
            }}
            
            if (countInput) {{
                countInput.addEventListener('input', function() {{
                    validateAndCorrect(this, 1, Math.min(mineCount, maxBatchSize));
                }});
            }}
            
            function updateRangeInfo() {{
                const startPos = parseInt(startPositionInput.value) || 1;
                const count = parseInt(rangeCountInput.value) || 20;
                
                // Validate and correct start position
                const correctedStart = Math.max(1, Math.min(startPos, mineCount));
                if (correctedStart !== startPos) {{
                    startPositionInput.value = correctedStart;
                }}
                
                // Validate and correct count based on available mines
                const maxPossibleCount = Math.min(mineCount - correctedStart + 1, maxBatchSize);
                const correctedCount = Math.max(1, Math.min(count, maxPossibleCount));
                if (correctedCount !== count) {{
                    rangeCountInput.value = correctedCount;
                }}
                
                const endPos = correctedStart + correctedCount - 1;
                const rangeInfo = document.getElementById('range_info');
                if (rangeInfo) {{
                    rangeInfo.textContent = `Sucht Minen ${{correctedStart}}-${{endPos}} aus der CSV (von ${{mineCount}} verfügbar)`;
                    if (correctedCount >= maxBatchSize) {{
                        rangeInfo.style.color = '#ff6600';
                        rangeInfo.textContent += ' - MAX ERREICHT';
                    }} else {{
                        rangeInfo.style.color = '#666';
                    }}
                }}
            }}
            
            function validateAndCorrect(input, min, max) {{
                const value = parseInt(input.value) || min;
                const corrected = Math.max(min, Math.min(value, max));
                if (corrected !== value) {{
                    input.value = corrected;
                    // Show brief feedback
                    const originalColor = input.style.borderColor;
                    input.style.borderColor = '#ff6600';
                    setTimeout(() => input.style.borderColor = originalColor, 1000);
                }}
            }}
            
            // Initialize range info on page load
            if (startPositionInput && rangeCountInput) {{
                updateRangeInfo();
            }}
        }});
        
        function toggleSelectionOptions() {{
            const modes = ['first_n', 'range', 'random'];
            const selectedMode = document.querySelector('input[name="selection_mode"]:checked')?.value;
            
            modes.forEach(mode => {{
                const element = document.getElementById(mode + '_options');
                if (element) {{
                    element.style.display = (mode === selectedMode) ? 'block' : 'none';
                }}
            }});
        }}
        </script>
        """
        
        from fastapi.responses import HTMLResponse
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Fehler beim CSV Upload: {str(e)}")
        raise HTTPException(status_code=400, detail=str(e))

@router.post("/batch-search")
async def batch_search(
    session_id: str = Form(...),
    model: Optional[str] = Form(None, description="Einzelnes Modell (Legacy)"),
    search_type: str = Form("standard"),
    count: Optional[int] = Form(None),
    search_all: Optional[str] = Form("false"),
    start_index: Optional[int] = Form(0),
    selected_models: Optional[str] = Form(None, description="Komma-getrennte Modell-Liste"),
    # ÄNDERUNG 07.07.2025: Option für Mehrfach-Durchlauf
    consistency_check: Optional[str] = Form("false"),
    consistency_runs: Optional[int] = Form(3),
    # PHASE 2.3: COMPREHENSIVE SEARCH Option
    comprehensive_search: Optional[str] = Form("false"),
    # ÄNDERUNG 27.08.2025: Sequential Field Orchestrator Option
    sequential_workflow: Optional[str] = Form("false"),
    # BATCH-TRANSPARENCY FIX 30.08.2025: Session-Isolation und Cache-Control
    use_cache: Optional[str] = Form("false", description="Use cached results from database"),
    force_new_session: Optional[str] = Form("false", description="Force new unique session for isolation"),
    # ENHANCED BATCH SELECTION 06.09.2025: Neue Auswahl-Modi
    selection_mode: Optional[str] = Form("first_n", description="first_n, range, random, all"),
    start_position: Optional[int] = Form(1, description="Start-Position für Range-Modus"),
    range_count: Optional[int] = Form(20, description="Anzahl Minen für Range-Modus"),
    random_count: Optional[int] = Form(10, description="Anzahl zufällige Minen")
):
    """
    Batch-Suche für mehrere Minen aus CSV
    FIXED 19.07.2025: 500 Error consensus Variable behoben
    """
    try:
        logger.info(f"[BATCH API] Received request: session_id='{session_id}', model='{model}', selected_models='{selected_models}', use_cache='{use_cache}', force_new_session='{force_new_session}'")
        
        # BATCH-TRANSPARENCY FIX 30.08.2025: Session-Isolation implementieren
        original_session_id = session_id
        if force_new_session == "true":
            import uuid
            batch_session_id = f"batch_{str(uuid.uuid4())}"
            logger.info(f"[BATCH-SESSION] Neue Session erstellt für Isolation: {batch_session_id} (original: {original_session_id})")
        else:
            batch_session_id = session_id
        
        # Hole Minen-Daten aus dem Cache
        if session_id not in uploaded_mines_cache:
            raise ValueError("Session abgelaufen. Bitte CSV erneut hochladen.")
        
        session_data = uploaded_mines_cache[session_id]
        mines = session_data['mines']
        columns = session_data['columns']
        logger.info(f"Batch-Suche für Session {session_id} (batch_session: {batch_session_id}) mit {len(mines)} Minen")
        
        # ENHANCED BATCH SELECTION 06.09.2025: Neue Auswahl-Modi
        logger.info(f"[ENHANCED-BATCH-SELECTION] Mode: '{selection_mode}', CSV: {len(mines)} Minen")
        logger.info(f"[ENHANCED-BATCH-SELECTION] Parameters - start_position: {start_position}, range_count: {range_count}, random_count: {random_count}, count: {count}")
        
        # Mine-Auswahl basierend auf selection_mode
        try:
            if selection_mode == "all":
                # Alle Minen (mit Pagination für große CSVs)
                effective_start = int(start_index or 0)
                if effective_start < 0:
                    effective_start = 0
                end_index = min(len(mines), effective_start + BATCH_REQUEST_MAX_COUNT)
                mines_to_search = mines[effective_start:end_index]
                logger.info(f"[ENHANCED-BATCH] ✅ ALL MODE - {len(mines_to_search)} Minen (Start {effective_start}, max {BATCH_REQUEST_MAX_COUNT})")
                
            elif selection_mode == "range":
                # Range-basierte Auswahl
                safe_start = max(1, min(start_position or 1, len(mines)))
                safe_count = max(1, min(range_count or 20, BATCH_REQUEST_MAX_COUNT))
                
                # Automatische Korrektur wenn Range über CSV-Grenzen hinausgeht
                max_possible_count = len(mines) - safe_start + 1
                if safe_count > max_possible_count:
                    safe_count = max(1, max_possible_count)
                    logger.warning(f"[ENHANCED-BATCH] Range count korrigiert: {range_count} -> {safe_count} (CSV-Grenzen)")
                
                start_idx = safe_start - 1  # Convert to 0-based index
                end_idx = start_idx + safe_count
                mines_to_search = mines[start_idx:end_idx]
                logger.info(f"[ENHANCED-BATCH] ✅ RANGE MODE - Minen {safe_start}-{safe_start + len(mines_to_search) - 1} ({len(mines_to_search)} Minen)")
                
            elif selection_mode == "random":
                # Zufällige Auswahl
                safe_random_count = max(1, min(random_count or 10, len(mines), BATCH_REQUEST_MAX_COUNT))
                if safe_random_count != random_count:
                    logger.warning(f"[ENHANCED-BATCH] Random count korrigiert: {random_count} -> {safe_random_count}")
                
                mines_to_search = random.sample(mines, safe_random_count)
                logger.info(f"[ENHANCED-BATCH] ✅ RANDOM MODE - {len(mines_to_search)} zufällige Minen aus {len(mines)}")
                
            else:  # "first_n" oder fallback
                # Erste X Minen (klassischer Modus)
                safe_count = max(1, min(count or 5, BATCH_REQUEST_MAX_COUNT))
                if safe_count > len(mines):
                    safe_count = len(mines)
                    logger.warning(f"[ENHANCED-BATCH] First-N count korrigiert: {count} -> {safe_count} (CSV-Größe)")
                
                mines_to_search = mines[:safe_count]
                logger.info(f"[ENHANCED-BATCH] ✅ FIRST_N MODE - erste {len(mines_to_search)} Minen")
                
        except Exception as e:
            logger.error(f"[ENHANCED-BATCH] Fehler bei Mine-Auswahl: {e}")
            # Fallback: Erste 5 Minen
            mines_to_search = mines[:min(5, len(mines))]
            logger.warning(f"[ENHANCED-BATCH] FALLBACK - erste {len(mines_to_search)} Minen verwendet")
            
        logger.info(f"[ENHANCED-BATCH] 🎯 FINALE AUSWAHL: {len(mines_to_search)} Minen werden durchsucht")
        
        # IMPROVED 19.07.2025: Vereinfachte und robuste Model-Auswahl
        models_to_use = []
        
        # 1. Priorität: selected_models (Frontend Liste)
        if selected_models and selected_models.strip():
            models_to_use = [m.strip() for m in selected_models.split(',') if m.strip()]
            logger.info(f"[BATCH-MODELS] Frontend ausgewählt: {len(models_to_use)} Modelle")
            logger.info(f"[BATCH-MODELS] User erwartete {len(models_to_use)} Modelle, prüfe Provider-Verfügbarkeit...")
        
        # 2. Fallback: einzelnes model Parameter (Legacy)
        elif model and model.strip():
            models_to_use = [model.strip()]
            logger.info(f"[BATCH-MODELS] Legacy single model: {models_to_use}")
        
        # 3. Default: FIX 02.09.2025 - OpenRouter DeepSeek statt BrightData
        else:
            models_to_use = ["openrouter:deepseek-free"]
            logger.warning(f"[BATCH-MODELS] No models specified, using default: {models_to_use[0]}")
        
        # Final validation
        if not models_to_use or not any(m.strip() for m in models_to_use):
            raise HTTPException(
                status_code=400, 
                detail="Mindestens ein gültiges Modell muss ausgewählt werden. Frontend-Parameter: selected_models, model"
            )

        # ENHANCED BATCH VALIDATION 06.09.2025: Erweiterte Validierung für alle Modi
        # Legacy-Kompatibilität: search_all="true" wird automatisch zu selection_mode="all"
        if search_all == "true" and selection_mode == "first_n":
            selection_mode = "all"
            logger.info(f"[ENHANCED-BATCH] Legacy-Kompatibilität: search_all=true -> selection_mode=all")
        
        # Validiere finale Mine-Anzahl gegen Limits
        if len(mines_to_search) > BATCH_REQUEST_MAX_COUNT:
            raise HTTPException(
                status_code=400,
                detail=f"Zu viele Minen ausgewählt ({len(mines_to_search)}). Maximale Batch-Größe: {BATCH_REQUEST_MAX_COUNT}."
            )
        
        # PROGRESS-FIX 29.08.2025: Erstelle Progress Session für detaillierte Fortschrittsanzeige
        total_operations = len(mines_to_search) * len(models_to_use)
        progress_session = batch_progress_manager.create_session(
            session_id=session_id,
            total_mines=len(mines_to_search),
            total_models=len(models_to_use)
        )
        logger.info(f"[BATCH-PROGRESS] Progress Session erstellt: {total_operations} Operationen ({len(mines_to_search)} Minen × {len(models_to_use)} Modelle)")
        
        # DEBUG: Schaue erste Minen an
        logger.info(f"[BATCH-DEBUG] Erste 3 Minen: {mines_to_search[:3]}")
        if mines_to_search:
            first_mine = mines_to_search[0]
            logger.info(f"[BATCH-DEBUG] Erste Mine Keys: {list(first_mine.keys())}")
            logger.info(f"[BATCH-DEBUG] Erste Mine Values: {first_mine}")
        
        # Führe Suchen durch - ALLE IMPORTS HIER
        results = []
        
        logger.info("[BATCH-DEBUG] Vor Import-Bereich")
        logger.info(f"[BATCH-DEBUG] Verwende {len(models_to_use)} Modelle: {models_to_use}")
        logger.info(f"[BATCH-DEBUG] Comprehensive Search: {comprehensive_search}")
        logger.info(f"[BATCH-DEBUG] Search Type: {search_type}")
        
        # PHASE 2.3: COMPREHENSIVE SEARCH ORCHESTRATOR Integration
        # Optional: nur wenn vorhanden (Legacy)
        try:
            from minesearch_v2.backend.comprehensive_search_orchestrator import comprehensive_search_orchestrator
        except ImportError:
            comprehensive_search_orchestrator = None
            logger.info("[BATCH] Comprehensive search orchestrator nicht verfügbar")
        except ModuleNotFoundError:
            comprehensive_search_orchestrator = None
            logger.info("[BATCH] Comprehensive search orchestrator Modul nicht gefunden")
        except Exception as e:
            comprehensive_search_orchestrator = None
            logger.warning(f"[BATCH] Unerwarteter Fehler beim Import des Orchestrators: {e}")
            
        # =========================================================================
        # 2-PHASEN BATCH-WORKFLOW IMPLEMENTATION (29.08.2025)
        # =========================================================================
        
        # PHASE 1: GLOBALE QUELLEN-SAMMLUNG von ALLEN Modellen
        logger.info("=" * 80)
        logger.info("[BATCH-2-PHASE] 🚀 STARTE 2-PHASEN BATCH-WORKFLOW")
        logger.info("[BATCH-2-PHASE] PHASE 1: Sammle Quellen von ALLEN Modellen")
        logger.info("=" * 80)
        
        batch_progress_manager.update_progress(
            session_id=session_id,
            state=ProgressState.COLLECTING_SOURCES,
            message=f"Sammle Quellen von {len(models_to_use)} Modellen für {len(mines_to_search)} Minen..."
        )
        
        # Import und initialisiere BatchSourceCollector
        from minesearch.batch_source_collector import BatchSourceCollector
        
        source_collector = BatchSourceCollector()
        mine_names = [
            (mine.get("mine_name", "") or 
             mine.get("Name", "") or 
             mine.get("name", "") or 
             mine.get("Mine Name", "")).strip()
            for mine in mines_to_search
        ]
        
        # Filtere leere Namen
        valid_mine_names = [name for name in mine_names if name]
        logger.info(f"[BATCH-2-PHASE] Verarbeite {len(valid_mine_names)} gültige Minen-Namen")
        
        # Sammle Quellen von allen Modellen
        source_collection_start = datetime.now()
        collection_results = await source_collector.collect_sources_from_all_models(
            mine_names=valid_mine_names,
            models=models_to_use
        )
        source_collection_duration = (datetime.now() - source_collection_start).total_seconds()
        
        # Statistiken der Quellen-Sammlung
        successful_models = [r for r in collection_results.values() if r.success]
        total_new_sources = sum(r.new_sources_added for r in successful_models)
        
        logger.info(f"[BATCH-2-PHASE] 📊 PHASE 1 ABGESCHLOSSEN:")
        logger.info(f"[BATCH-2-PHASE]   ✅ Erfolgreiche Modelle: {len(successful_models)}/{len(models_to_use)}")
        logger.info(f"[BATCH-2-PHASE]   🔗 Neue Quellen hinzugefügt: {total_new_sources}")
        logger.info(f"[BATCH-2-PHASE]   ⏱️ Dauer: {source_collection_duration:.2f}s")
        
        # PHASE 2: LADE ALLE QUELLEN aus DB für Daten-Extraktion
        logger.info("=" * 80)
        logger.info("[BATCH-2-PHASE] PHASE 2: Lade ALLE Quellen aus DB")
        logger.info("=" * 80)
        
        all_db_sources = source_collector.get_all_sources_from_db()
        logger.info(f"[BATCH-2-PHASE] 📚 {len(all_db_sources)} Quellen aus DB geladen")
        
        # Quellen-Statistiken für Transparenz
        source_stats = source_collector.get_sources_stats()
        logger.info(f"[BATCH-2-PHASE] 📈 QUELLEN-STATISTIKEN:")
        logger.info(f"[BATCH-2-PHASE]   📄 Gesamt Quellen: {source_stats['total_sources']}")
        logger.info(f"[BATCH-2-PHASE]   🌐 Einzigartige Domains: {source_stats['unique_domains']}")
        logger.info(f"[BATCH-2-PHASE]   🤖 Beitragende Modelle: {source_stats['contributing_models']}")
        
        # Update Progress für Phase 2
        batch_progress_manager.update_progress(
            session_id=session_id,
            state=ProgressState.EXTRACTING_DATA,
            message=f"Extrahiere Daten mit {len(all_db_sources)} Quellen aus {len(models_to_use)} Modellen..."
        )
        
        # =========================================================================
        # PHASE 2: DATEN-EXTRAKTION mit ALLEN DB-Quellen
        # =========================================================================
        
        logger.info("[BATCH] Starte Mine-Processing-Schleife mit ALLEN DB-Quellen")
        logger.info(f"[BATCH-DEBUG] mines_to_search count: {len(mines_to_search)}")
        logger.info(f"[BATCH-DEBUG] search_all: {search_all}, count: {count}")
        logger.info(f"[BATCH-2-PHASE] 🔥 Jedes Modell wird ALLE {len(all_db_sources)} DB-Quellen durchsuchen!")
        
        # THREAD-SAFE DEBUG-LOGGING (using application logging infrastructure)
        batch_debug_logger.info(f"[BATCH-ROUTE] Batch-Route aufgerufen! mines_to_search: {len(mines_to_search)}")
        batch_debug_logger.info(f"[BATCH-ROUTE] Modelle: {models_to_use}")
        
        # Alternative: File locking approach (commented out - use logging above instead)
        # debug_content = (
        #     f"[BATCH-ROUTE] Batch-Route aufgerufen! mines_to_search: {len(mines_to_search)}\n"
        #     f"[BATCH-ROUTE] Modelle: {models_to_use}\n"
        # )
        # safe_write_to_file("/tmp/batch_debug.log", debug_content, mode='w')
        
        for idx, mine in enumerate(mines_to_search):
            # ERWEITERTE FIELD-MAPPING für Quebec-CSV und internationale Formate
            mine_name = (mine.get("mine_name", "") or 
                        mine.get("Name", "") or 
                        mine.get("name", "") or 
                        mine.get("Mine Name", "") or 
                        mine.get("MINE_NAME", "") or
                        mine.get("Mine", "") or
                        mine.get("Site", "")).strip()
            
            # CSV-FIX 29.08.2025: Intelligente Fallback-Logik ohne harte Defaults
            country = (mine.get("country", "") or 
                      mine.get("Country", "") or 
                      mine.get("COUNTRY", "") or 
                      mine.get("Land", "") or
                      mine.get("Pays", "") or  # Französisch
                      mine.get("Staat", "") or  # Deutsch
                      mine.get("Nation", "") or  # Deutsch
                      mine.get("País", "")).strip()  # Spanisch/Portugiesisch
            
            commodity = (mine.get("commodity", "") or 
                        mine.get("Commodity", "") or 
                        mine.get("Rohstoff", "") or
                        mine.get("Rohstoff", "") or
                        mine.get("Produit", "") or  # Französisch
                        mine.get("Mineral", "") or
                        mine.get("Producto", "")).strip()  # Spanisch
            
            region = (mine.get("region", "") or 
                     mine.get("Region", "") or 
                     mine.get("REGION", "") or
                     mine.get("Province", "") or
                     mine.get("État", "") or  # Französisch
                     mine.get("Bundesland", "") or  # Deutsch
                     mine.get("Provinz", "") or  # Deutsch
                     mine.get("Estado", "")).strip()  # Spanisch/Portugiesisch
            
            # CSV-FIX 29.08.2025: Prüfe ob Land/Region aus CSV verfügbar sind
            has_country_from_csv = bool(country)
            has_region_from_csv = bool(region)
            needs_location_search = not has_country_from_csv or not has_region_from_csv
            
            logger.info(f"[CSV-ANALYSIS] {mine_name}: Country='{country}' (from CSV: {has_country_from_csv}), Region='{region}' (from CSV: {has_region_from_csv}), needs search: {needs_location_search}")
            
            if not mine_name:
                logger.warning(f"[BATCH] Mine {idx+1} hat keinen Namen, überspringe. Keys: {list(mine.keys())[:5]}...")
                logger.debug(f"[BATCH-DEBUG] Mine {idx+1} Values: {dict(list(mine.items())[:3])}")
                continue
                
            # BEDINGTE LAND/REGION-SUCHE - wenn nicht in CSV vorhanden
            if needs_location_search:
                logger.info(f"[LOCATION-SEARCH] Suche Land/Region für {mine_name}...")
                try:
                    # Verwende ersten verfügbaren Model für Location-Suche
                    location_model = models_to_use[0] if models_to_use else "openrouter:deepseek-free"
                    location_prompt = f"What country and region/province is the {mine_name} mine located in? Please respond with just: Country: [country name], Region: [region/province name]"
                    
                    # Simple Location Search mit erstem Model
                    from minesearch.providers.registry import provider_registry
                    provider = provider_registry.get_provider_for_model(location_model)
                    if provider:
                        location_response = await provider.search(location_prompt, mine_name)
                        if location_response.get('success') and location_response.get('content'):
                            content = location_response['content']
                            # Parse Country/Region aus Response
                            import re
                            country_match = re.search(r'Country:\s*([^,\n]+)', content, re.IGNORECASE)
                            region_match = re.search(r'Region:\s*([^,\n]+)', content, re.IGNORECASE)
                            
                            if not has_country_from_csv and country_match:
                                country = country_match.group(1).strip()
                                logger.info(f"[LOCATION-FOUND] Country: {country}")
                            
                            if not has_region_from_csv and region_match:
                                region = region_match.group(1).strip()
                                logger.info(f"[LOCATION-FOUND] Region: {region}")
                                
                except Exception as e:
                    logger.warning(f"[LOCATION-SEARCH] Fehler bei Location-Suche für {mine_name}: {e}")
                    # Fallback: Lass Land/Region leer, statt hardcodierte Werte zu verwenden
                    if not has_country_from_csv:
                        country = ""
                    if not has_region_from_csv:
                        region = ""
            
            # SUCCESS: Mine erfolgreich geparst
            logger.info(f"[BATCH-SUCCESS] Mine {idx+1}: '{mine_name}' in '{country}', '{region}'")
            
            # PROGRESS-FIX 29.08.2025: Progress-Update für Mine-Start
            batch_progress_manager.mark_mine_started(
                session_id=session_id,
                mine_index=idx,
                mine_name=mine_name
            )
            
            # THREAD-SAFE DEBUG-LOGGING (using application logging infrastructure)
            batch_debug_logger.info(f"[BATCH-MINE] Processing mine {idx+1}: '{mine_name}'")
                
            logger.info(f"Suche {idx+1}/{len(mines_to_search)}: {mine_name}")
            
            try:
                # PHASE 2.3: COMPREHENSIVE SEARCH Option
                # FIX 29.08.2025: Auch search_type="comprehensive" unterstützen
                if (comprehensive_search == "true" or search_type == "comprehensive") and comprehensive_search_orchestrator is not None:
                    logger.info(f"[COMPREHENSIVE] Starte systematische Vollsuche für {mine_name}")
                    try:
                        comprehensive_result = await comprehensive_search_orchestrator.orchestrate_comprehensive_search(
                            mine_name=mine_name,
                            country=country or "",
                            region=region or "", 
                            commodity=commodity,
                            available_models=models_to_use
                        )
                        
                        if comprehensive_result.get('success'):
                            # Formatiere für Batch-Ergebnisse
                            result_data = {
                                "mine_name": mine_name,
                                "country": country,
                                "commodity": commodity,
                                "region": region,
                                "success": True,
                                "data": {
                                    "structured_data": comprehensive_result['data'],
                                    "field_completion_status": comprehensive_result['field_completion_status'],
                                    "completion_report": comprehensive_result['completion_report'],
                                    "source_quality_report": comprehensive_result['source_quality_report'],
                                    "search_strategy": "comprehensive_systematic"
                                }
                            }
                            results.append(result_data)
                            
                            # LEGACY DATABASE REMOVED 03.09.2025: Nur noch normalisierte DB
                            # Speicherung erfolgt automatisch in den entsprechenden Services
                        else:
                            # Fallback auf Standard-Suche
                            logger.warning(f"[COMPREHENSIVE] Comprehensive search für {mine_name} fehlgeschlagen, verwende Standard-Suche")
                            comprehensive_search = "false"  # Fallback für diese Mine
                            # Zusätzlich search_type zurücksetzen für DB-FIRST Fallback
                            if search_type == "comprehensive":
                                search_type = "standard"
                    
                    except Exception as e:
                        logger.error(f"[COMPREHENSIVE] Fehler bei comprehensive search für {mine_name}: {str(e)}")
                        # Fallback auf Standard-Suche
                        comprehensive_search = "false"
                        # Zusätzlich search_type zurücksetzen für DB-FIRST Fallback
                        if search_type == "comprehensive":
                            search_type = "standard"
                
                # FIX 29.08.2025: Fallback wenn comprehensive requested aber Orchestrator nicht verfügbar
                elif (comprehensive_search == "true" or search_type == "comprehensive") and comprehensive_search_orchestrator is None:
                    logger.warning(f"[COMPREHENSIVE] Comprehensive search requested für {mine_name}, aber Orchestrator nicht verfügbar - fallback auf Standard-Suche")
                    comprehensive_search = "false"
                    if search_type == "comprehensive":
                        search_type = "standard"
                
                # ÄNDERUNG 27.08.2025: SEQUENTIAL FIELD ORCHESTRATOR Option
                elif search_type == "sequential" or sequential_workflow == "true":
                    logger.info(f"[SEQUENTIAL] Starte Sequential Field Orchestrator für {mine_name}")
                    try:
                        # Erstelle Sequential Database Manager
                        with db_manager.get_session() as db_session:
                            seq_db_manager = SequentialDatabaseManager(db_session)
                            
                            # Erstelle Sequential Field Orchestrator
                            orchestrator = SequentialFieldOrchestrator()
                            
                            # Führe Sequential Search durch
                            sequential_result = await orchestrator.orchestrate_sequential_search(
                                mine_name=mine_name,
                                models=models_to_use,
                                country=country,
                                region=region,
                                commodity=commodity,
                                session_id=session_id
                            )
                            
                            if sequential_result.success:
                                # Formatiere für Batch-Ergebnisse
                                result_data = {
                                    "mine_name": mine_name,
                                    "country": country,
                                    "commodity": commodity,
                                    "region": region,
                                    "success": True,
                                    "data": {
                                        "structured_data": sequential_result.consolidated_data,
                                        "field_confidence_scores": sequential_result.field_confidence,
                                        "sources_discovered": sequential_result.total_sources_discovered,
                                        "models_used": sequential_result.total_models_used,
                                        "search_strategy": "sequential_field_orchestrator",
                                        "performance_metrics": sequential_result.performance_metrics,
                                        "quality_score": sequential_result.quality_score
                                    }
                                }
                                results.append(result_data)
                                
                                logger.info(f"[SEQUENTIAL] Sequential search für {mine_name} erfolgreich abgeschlossen: Quality Score {sequential_result.quality_score}")
                                
                                # LEGACY DATABASE REMOVED 03.09.2025: Nur noch normalisierte DB
                                # Sequential Orchestrator speichert bereits in der normalisierten Datenbank
                            else:
                                # Sequential search fehlgeschlagen, fallback auf Standard-Suche
                                logger.warning(f"[SEQUENTIAL] Sequential search für {mine_name} fehlgeschlagen: {sequential_result.error_message}")
                                sequential_workflow = "false"  # Fallback für diese Mine
                            
                    except Exception as e:
                        logger.error(f"[SEQUENTIAL] Fehler bei sequential search für {mine_name}: {str(e)}")
                        # Fallback auf Standard-Suche
                        sequential_workflow = "false"
                
                # KRITISCHER FIX 23.08.2025: Verwende EXISTIERENDE Datenbank-Ergebnisse statt neue API-Calls
                # FIX 29.08.2025: Auch search_type="comprehensive" berücksichtigen
                # BATCH-TRANSPARENCY FIX 30.08.2025: Cache-Control Implementation
                if (comprehensive_search != "true" and search_type != "comprehensive") and (search_type != "sequential" and sequential_workflow != "true"):
                    
                    # 1. PRÜFE CACHE-CONTROL PARAMETER
                    use_cache_enabled = use_cache == "true"
                    logger.info(f"[BATCH-CACHE-CONTROL] Mine: {mine_name} | use_cache: {use_cache_enabled} | force_new_session: {force_new_session}")
                    
                    # 2. PRÜFE DATENBANK-ERGEBNISSE NUR WENN CACHE AKTIVIERT
                    db_results = []
                    if use_cache_enabled:
                        logger.info(f"[BATCH-DB-CACHE] Prüfe Datenbank für existierende {mine_name} Ergebnisse")
                        try:
                            # SESSION-ISOLATION FIX 30.08.2025: Hole existierende Ergebnisse NUR für aktuelle Session
                            existing_results = db_manager.get_recent_search_results(
                                mine_name=mine_name, 
                                hours_back=24,  # Suche in letzten 24 Stunden
                                limit=5,
                                session_id=batch_session_id  # KRITISCH: Session-Filter für Batch-Isolation
                            )
                        
                            logger.info(f"[BATCH-DB-CACHE] Gefunden: {len(existing_results)} existierende DB-Ergebnisse für {mine_name}")
                            
                            # Konvertiere DB-Ergebnisse zu Batch-Format mit Transparenz-Markierung
                            for db_result in existing_results:
                                if db_result.success and db_result.structured_data:
                                    structured_data = db_result.structured_data
                                    filled_fields = count_filled_fields(structured_data)
                                    
                                    if filled_fields >= 5:  # Nur gute Ergebnisse verwenden
                                        db_results.append({
                                            'model_id': db_result.model_used,
                                            'success': True,
                                            'data': {
                                                'structured_data': structured_data,
                                                'field_count': len(structured_data),
                                                'filled_field_count': filled_fields,
                                                'source': 'database_cache',
                                                # TRANSPARENCY FIX 30.08.2025: Datenherkunft markieren
                                                'data_source': 'cached',
                                                'cache_timestamp': db_result.created_at.isoformat() if db_result.created_at else None,
                                                'original_session': getattr(db_result, 'session_id', 'unknown')
                                            }
                                        })
                                        logger.info(f"[BATCH-DB-CACHE] Verwende DB-Ergebnis: {db_result.model_used} mit {filled_fields} Feldern (cached from {db_result.created_at})")
                            
                        except Exception as e:
                            logger.warning(f"[BATCH-DB-CACHE] DB-Abfrage fehlgeschlagen: {e}")
                    else:
                        logger.info(f"[BATCH-CACHE-CONTROL] Cache deaktiviert für {mine_name} - erzwinge neue Provider-Suche")
                        db_results = []
                    
                    # 3. VERWENDE DB-ERGEBNISSE NUR WENN VORHANDEN UND CACHE AKTIVIERT
                    if db_results and use_cache_enabled:
                        logger.info(f"[BATCH-DB-CACHE] Verwende {len(db_results)} existierende DB-Ergebnisse statt neue API-Calls")
                        individual_results = db_results
                        
                        # NORMALIZED SCHEMA FIX 28.08.2025: Speichere existierende Ergebnisse auch in normalized schema
                        for db_result in db_results:
                            try:
                                # BUGFIX: structured_data ist verschachtelt in 'data'
                                data_section = db_result.get('data', {})
                                structured_data = data_section.get('structured_data', {})
                                
                                if not structured_data:
                                    logger.warning(f"[BATCH-DB-FIRST-NORMALIZED] ⚠️ No structured_data found for {db_result['model_id']}, skipping")
                                    continue
                                
                                normalized_result_id = normalized_db_manager.save_search_result_normalized(
                                    mine_name=mine_name,
                                    model_used=db_result['model_id'],
                                    structured_data=structured_data,
                                    sources=db_result.get('sources', []),
                                    session_id=session_id,
                                    country=country,
                                    search_duration=db_result.get('search_duration')
                                )
                                logger.info(f"[BATCH-DB-FIRST-NORMALIZED] ✅ DB-Result saved to normalized schema: {db_result['model_id']} (ID: {normalized_result_id})")
                            except Exception as normalized_error:
                                logger.error(f"[BATCH-DB-FIRST-NORMALIZED] ❌ Failed to save {db_result['model_id']} to normalized: {normalized_error}")
                                # Debug-Info bei Fehlern
                                logger.debug(f"[BATCH-DB-FIRST-NORMALIZED] Debug - db_result keys: {list(db_result.keys())}")
                                if 'data' in db_result:
                                    logger.debug(f"[BATCH-DB-FIRST-NORMALIZED] Debug - data keys: {list(db_result['data'].keys())}")
                    else:
                        # 4. FALLBACK: Neue Provider-Suche wenn kein Cache oder keine guten DB-Ergebnisse
                        if use_cache_enabled:
                            logger.info(f"[BATCH-FALLBACK] Keine ausreichenden DB-Ergebnisse - starte Provider-Suche für {mine_name}")
                        else:
                            logger.info(f"[BATCH-NEW-SEARCH] Cache deaktiviert - starte frische Provider-Suche für {mine_name}")
                        individual_results = []
                        
                        # BATCH-FIX 23.08.2025: Provider-Suche mit MultiModelSearchOrchestrator reaktiviert
                        try:
                            logger.info(f"[BATCH-ORCHESTRATOR] Starte Provider-Suche für {mine_name} mit {len(models_to_use)} Modellen")
                            
                            # PROGRESS-FIX 29.08.2025: Source Discovery Phase beginnt
                            batch_progress_manager.update_progress(
                                session_id=session_id,
                                state=ProgressState.SOURCE_DISCOVERY,
                                message=f"Suche Quellen für {mine_name}..."
                            )
                            
                            orchestrator = MultiModelSearchOrchestrator()
                            
                            # 2-PHASEN WORKFLOW FIX (29.08.2025): Nutze ALLE DB-Quellen
                            orchestration_result = await orchestrator.orchestrate_multi_model_search(
                                mine_name=mine_name,
                                models=models_to_use,
                                country=country,
                                region=region,
                                commodity=commodity,
                                # SESSION-ID FIX 04.09.2025: Übergebe batch_session_id für DB-Konsistenz
                                session_id=batch_session_id,
                                # KRITISCH: Verwende alle gesammelten DB-Quellen
                                use_all_db_sources=True,
                                db_sources=all_db_sources
                            )
                            
                            logger.info(f"[BATCH-2-PHASE] ✅ {mine_name}: Orchestrator nutzte {len(all_db_sources)} DB-Quellen")
                            
                            # Konvertiere Orchestration-Ergebnisse zu individual_results Format
                            individual_results = []
                            
                            # Erfolgreiche Modelle
                            for model_result in orchestration_result.successful_models:
                                result_data = model_result.data.copy() if model_result.data else {}
                                # TRANSPARENCY FIX 30.08.2025: Markiere neue Suchergebnisse
                                result_data.update({
                                    'data_source': 'fresh_search',
                                    'search_timestamp': datetime.now().isoformat(),
                                    'batch_session_id': batch_session_id
                                })
                                
                                individual_results.append({
                                    'model_id': model_result.model_id,
                                    'success': True,
                                    'data': result_data,
                                    'sources': model_result.sources
                                })
                            
                            # Fehlgeschlagene Modelle
                            for model_result in orchestration_result.failed_models:
                                individual_results.append({
                                    'model_id': model_result.model_id,
                                    'success': False,
                                    'error': model_result.error or 'Search failed',
                                    'data_source': 'fresh_search',
                                    'search_timestamp': datetime.now().isoformat(),
                                    'batch_session_id': batch_session_id
                                })
                            
                            logger.info(f"[BATCH-ORCHESTRATOR] Orchestrierung erfolgreich: {len(orchestration_result.successful_models)} erfolgreich, {len(orchestration_result.failed_models)} fehlgeschlagen")
                            
                            # PROGRESS-FIX 29.08.2025: Source Discovery abgeschlossen - Modell-Execution beginnt
                            batch_progress_manager.mark_source_discovery_complete(
                                session_id=session_id,
                                sources_found=len(orchestration_result.shared_sources)
                            )
                            
                            # PROGRESS-FIX 29.08.2025 + FEHLER-KLASSIFIKATION 06.09.2025: Markiere Modell-Completions
                            for idx, model_result in enumerate(orchestration_result.successful_models + orchestration_result.failed_models):
                                batch_progress_manager.mark_model_complete(
                                    session_id=session_id,
                                    model_name=model_result.model_id,
                                    success=model_result.success,
                                    error_message=model_result.error if not model_result.success else None
                                )
                        
                        except Exception as orchestrator_error:
                            logger.error(f"[BATCH-ORCHESTRATOR] Orchestrator fehler für {mine_name}: {str(orchestrator_error)}")
                            # Fallback: Verwende Fallback-Daten bei Orchestrator-Fehler
                            individual_results = [{"model_id": "fallback", "success": False, "error": f"Orchestrator failed: {str(orchestrator_error)}"}]
                    
                    # Verarbeite direkte Provider-Ergebnisse
                    successful_models = [r for r in individual_results if r['success']]
                    failed_models = [r for r in individual_results if not r['success']]
                    batch_success = len(successful_models) > 0
                    
                    logger.info(f"[BATCH-DIRECT] Direkter Provider-Aufruf abgeschlossen für '{mine_name}': {len(successful_models)} erfolgreich, {len(failed_models)} fehlgeschlagen")
                    
                    # KRITISCHER FIX 22.08.2025: Extrahiere structured_data für HTML-Generator
                    best_structured_data = {}
                    if successful_models:
                        # Wähle das erfolgreichste Modell (das mit den meisten gefüllten Feldern)
                        best_model = None
                        max_filled_fields = 0
                        
                        for model_result in successful_models:
                            model_data = model_result.get('data', {})
                            structured_data = model_data.get('structured_data', {})
                            
                            if structured_data:
                                filled_fields = len([v for v in structured_data.values() if v and str(v).strip() and str(v).strip() not in ['-', '', 'None', 'null', 'nichts gefunden']])
                                
                                if filled_fields > max_filled_fields:
                                    max_filled_fields = filled_fields
                                    best_model = model_result
                                    best_structured_data = structured_data
                        
                        logger.info(f"[BATCH-CONSOLIDATION] Selected best model for {mine_name}: {best_model['model_id'] if best_model else 'None'} with {max_filled_fields} filled fields")
                        
                        # LAND/REGION-ERGÄNZUNG: Stelle sicher, dass CSV/gefundene Werte in structured_data stehen
                        if best_structured_data is None:
                            best_structured_data = {}
                            
                        if country and country.strip():
                            best_structured_data['Land'] = country.strip()
                            best_structured_data['Country'] = country.strip()  # Beide Varianten für Kompatibilität
                            logger.info(f"[LAND-ERGÄNZUNG] {mine_name}: Land/Country = '{country}'")
                            
                        if region and region.strip():
                            best_structured_data['Region'] = region.strip()
                            logger.info(f"[REGION-ERGÄNZUNG] {mine_name}: Region = '{region}'")
                        
                        # DEBUG: Log sample fields from best model
                        if best_structured_data:
                            sample_fields = ['Country', 'Land', 'Region', 'Rohstoff', 'Restaurationskosten', 'Eigentümer']
                            for field in sample_fields:
                                if field in best_structured_data:
                                    value = best_structured_data[field]
                                    logger.info(f"[BATCH-CONSOLIDATION] {mine_name} final - {field}: '{value}'")
                                else:
                                    logger.warning(f"[BATCH-CONSOLIDATION] {mine_name} missing field: {field}")
                        
                        # INTELLIGENT FALLBACK: Prüfe ob Ergebnis Enhancement benötigt
                        temp_result_data = {
                            "success": batch_success,
                            "data": {"structured_data": best_structured_data}
                        }
                        
                        if is_weak_result(temp_result_data):
                            logger.info(f"[SMART-FALLBACK] {mine_name} benötigt Enhancement - teste deepseek-free")
                            fallback_data = await fallback_search_if_needed(mine_name, country, commodity, region, {"structured_data": best_structured_data})
                            
                            if fallback_data:
                                best_structured_data = fallback_data['structured_data']
                                logger.info(f"[SMART-FALLBACK] {mine_name} verbessert durch deepseek-free!")
                        else:
                            logger.info(f"[SMART-FALLBACK] {mine_name} bereits ausreichend - kein Fallback nötig")
                        
                        # LEGACY FALLBACK: Wenn kein Modell structured_data hat, kombiniere alle verfügbaren Daten
                        if not best_structured_data and successful_models:
                            logger.warning(f"[BATCH-CONSOLIDATION] No structured_data found, attempting data consolidation for {mine_name}")
                            for model_result in successful_models:
                                model_data = model_result.get('data', {})
                                # Füge alle non-empty Felder zusammen
                                for key, value in model_data.items():
                                    if key != 'structured_data' and value and str(value).strip():
                                        best_structured_data[key] = value
                    
                    result_data = {
                        "mine_name": mine_name,
                        "country": country,
                        "commodity": commodity,
                        "region": region,
                        "success": batch_success,
                        "data": {
                            "structured_data": best_structured_data,  # KRITISCH: Für HTML-Generator
                            "individual_results": individual_results,
                            "successful_models": len(successful_models),
                            "failed_models": len(failed_models),
                            "total_models": len(models_to_use)
                        },
                        "model_info": {
                            "models_used": models_to_use,
                            "search_strategy": "individual_batch",
                            "processing_type": "individual_per_model"
                        }
                    }
                    
                    if not batch_success:
                        result_data["error"] = f"All {len(models_to_use)} models failed for {mine_name}"
                    
                    results.append(result_data)
                    logger.info(f"[BATCH-INDIVIDUAL] Completed {mine_name}: {len(successful_models)}/{len(models_to_use)} models successful")
                    
                    # LEGACY DATABASE REMOVED 03.09.2025: Nur noch normalisierte DB
                    # Speicherung erfolgt automatisch in den entsprechenden Services
                    if not (batch_success and best_structured_data):
                        logger.warning(f"[BATCH-STANDARD-DB] ⚠️ No successful results to save for {mine_name} (batch_success: {batch_success}, has_data: {bool(best_structured_data)})")
                
                # PROGRESS-FIX 29.08.2025: Mine vollständig abgeschlossen
                batch_progress_manager.mark_mine_complete(
                    session_id=session_id,
                    mine_name=mine_name
                )
                
            except Exception as e:
                logger.error(f"Fehler bei Suche für {mine_name}: {str(e)}")
                results.append({
                    "mine_name": mine_name,
                    "country": country,
                    "commodity": commodity,
                    "region": region,
                    "success": False,
                    "error": str(e)
                })
        
        # Debug: Log die Struktur der Ergebnisse
        logger.info(f"[BATCH-DEBUG] Anzahl Ergebnisse: {len(results)}")
        if results:
            first_result = results[0]
            logger.info(f"[BATCH-DEBUG] Erstes Ergebnis - Keys: {list(first_result.keys())}")
            if 'data' in first_result and first_result['data']:
                logger.info(f"[BATCH-DEBUG] Data Keys: {list(first_result['data'].keys())}")
        
        # CRITICAL-FIX 19.08.2025: Validiere Batch-Ergebnisse gegen Regressionen
        try:
            from minesearch.batch_validation import validate_batch_results, log_validation_summary
            validation_result = validate_batch_results(results)
            log_validation_summary(validation_result)
            
            # Bei kritischen Validierungsfehlern, warnen aber nicht blocken
            if validation_result.critical_count > 0:
                logger.error(f"[BATCH-VALIDATION] {validation_result.critical_count} kritische Probleme in Batch-Ergebnissen erkannt!")
        except ImportError:
            logger.warning("[BATCH-VALIDATION] batch_validation module nicht verfügbar")
        
        # PROGRESS-FIX 29.08.2025: Gesamte Batch-Suche abgeschlossen
        batch_progress_manager.mark_batch_complete(session_id=session_id)
        
        # OPTIMIERT: Fallback-Logik bereits in Hauptschleife integriert - keine doppelten Provider-Aufrufe mehr
        
        # Erstelle HTML-Antwort mit optimierten results (Fallback bereits in Hauptschleife integriert)
        # Note: create_batch_results_table is imported at module scope (line 26)
        html_content = create_batch_results_table(results)
        
        # SESSION-ISOLATION FIX 30.08.2025: Speichere Ergebnisse session-spezifisch
        session_cache_key = f"{session_id}_{batch_session_id}"  # Eindeutiger Key pro Session+Batch
        batch_results_cache[session_cache_key] = {
            'results': results,
            'columns': columns,
            'timestamp': datetime.now(),
            'session_id': session_id,
            'batch_session_id': batch_session_id  # Tracking für Debug
        }
        logger.info(f"[SESSION-ISOLATION] Cached batch results under key: {session_cache_key}")
        
        # Debug: Log einen Teil des generierten HTML
        logger.info(f"[BATCH-DEBUG] HTML-Länge: {len(html_content)}")
        
        return HTMLResponse(content=html_content)
        
    except Exception as e:
        logger.error(f"Fehler bei Batch-Suche: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.post("/process-batch")
async def process_batch(
    cache_key: str = Form(...),
    model: str = Form(..., description="Modell-ID (z.B. 'openrouter:deepseek-free')")
):
    """Batch-Verarbeitung der hochgeladenen Minen"""
    try:
        return await batch_service.process_batch(cache_key, model)
    except Exception as e:
        logger.error(f"Fehler bei Batch-Verarbeitung: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))

@router.get("/batch-results/{cache_key}")
async def get_batch_results(cache_key: str):
    """SESSION-ISOLATION FIX 30.08.2025: Batch-Ergebnisse session-spezifisch abrufen"""
    
    # Suche nach session-spezifischen Cache-Keys (unterstützt alte und neue Formate)
    matching_keys = [key for key in batch_results_cache.keys() if cache_key in key]
    
    if not matching_keys:
        logger.warning(f"[SESSION-ISOLATION] No results found for cache_key: {cache_key}")
        logger.debug(f"[SESSION-ISOLATION] Available keys: {list(batch_results_cache.keys())}")
        raise HTTPException(status_code=404, detail="Keine Ergebnisse gefunden")
    
    # Verwende den neuesten/ersten passenden Key
    actual_key = matching_keys[0]
    logger.info(f"[SESSION-ISOLATION] Using cache key: {actual_key} for request: {cache_key}")
    
    # Note: create_batch_results_table is imported at module scope (line 26)
    cached_data = batch_results_cache[actual_key]
    results = cached_data.get('results', cached_data)  # Backward compatibility
    html = create_batch_results_table(results)
    
    return {"html": html, "results": results}

@router.get("/batch-results/{cache_key}/download")
async def download_batch_results(cache_key: str):
    """SESSION-ISOLATION FIX 30.08.2025: Batch-Ergebnisse session-spezifisch als CSV herunterladen"""
    
    # Suche nach session-spezifischen Cache-Keys (unterstützt alte und neue Formate)
    matching_keys = [key for key in batch_results_cache.keys() if cache_key in key]
    
    if not matching_keys:
        logger.warning(f"[SESSION-ISOLATION] No download results found for cache_key: {cache_key}")
        raise HTTPException(status_code=404, detail="Keine Ergebnisse gefunden")
    
    # Verwende den neuesten/ersten passenden Key
    actual_key = matching_keys[0]
    logger.info(f"[SESSION-ISOLATION] Downloading from cache key: {actual_key}")
    
    cached_data = batch_results_cache[actual_key]
    results = cached_data.get('results', cached_data)  # Backward compatibility
    
    # CSV erstellen
    output = io.StringIO()
    writer = csv.DictWriter(output, fieldnames=CSV_COLUMNS)
    writer.writeheader()
    
    for result in results:
        if result["success"]:
            row = {
                "Mine Name": result["mine_name"],
                "Country": result.get("country", ""),
                "Commodity": result.get("commodity", ""),
                "Region": result.get("region", "")
            }
            
            # Strukturierte Daten hinzufügen
            structured_data = result["data"].get("structured_data", {})
            for key in CSV_COLUMNS[4:]:  # Skip die ersten 4 (Mine Name, Country, etc.)
                row[key] = structured_data.get(key, "k.A.")
            
            writer.writerow(row)
    
    content = output.getvalue()
    
    return Response(
        content=content,
        media_type="text/csv",
        headers={
            "Content-Disposition": f"attachment; filename=mine_search_results_{cache_key}.csv"
        }
    )