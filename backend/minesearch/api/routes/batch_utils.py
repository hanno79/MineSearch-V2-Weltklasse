"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Utility-Funktionen für Batch-Processing (Refactoring aus batch.py)
"""

import logging
import threading
import os
import tempfile
from typing import Dict, Any

logger = logging.getLogger(__name__)

# Modulweiter Fallback-Lock für plattformübergreifende Serialisierung von Dateischreibzugriffen
file_write_lock = threading.Lock()

try:
    import fcntl
    HAS_FCNTL = True
except ImportError:
    fcntl = None
    HAS_FCNTL = False

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
                    elif mode == 'w':
                        with open(filepath, 'w', encoding='utf-8') as f:
                            f.write(content)
                            f.flush()
                            os.fsync(f.fileno())
                return
            except Exception as e:
                logger.warning(f"fcntl file locking failed, falling back: {e}")
        elif HAS_PORTALOCKER:
            # Cross-platform alternative using portalocker
            try:
                with open(filepath, mode, encoding='utf-8') as f:
                    portalocker.lock(f, portalocker.LOCK_EX | portalocker.LOCK_NB)
                    f.write(content)
                    f.flush()
                    if hasattr(os, 'fsync'):
                        os.fsync(f.fileno())
                    portalocker.unlock(f)
                return
            except Exception as e:
                logger.warning(f"portalocker file locking failed, falling back: {e}")
        elif HAS_FILELOCK:
            # Use filelock library for cross-platform file locking
            try:
                with FileLock(lockfile_path, timeout=lock_timeout_seconds):
                    with open(filepath, mode, encoding='utf-8') as f:
                        f.write(content)
                        f.flush()
                        if hasattr(os, 'fsync'):
                            os.fsync(f.fileno())
                return
            except Exception as e:
                logger.warning(f"filelock file locking failed, falling back: {e}")
    
        # Final fallback: Use in-process thread lock (not multi-process safe)
        with file_write_lock:
            with open(filepath, mode, encoding='utf-8') as f:
                f.write(content)
                f.flush()
                if hasattr(os, 'fsync'):
                    os.fsync(f.fileno())
    
    except Exception as e:
        logger.error(f"All file writing methods failed for {filepath}: {e}")
        # Last resort: log content instead of writing to file
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