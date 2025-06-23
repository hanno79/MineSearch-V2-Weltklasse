"""
Logging-System für Multi-Agent Mining Research System
"""
import logging
import logging.handlers
from pathlib import Path
from typing import Optional, Dict
from datetime import datetime
import json

from .config import get_config


class ColoredFormatter(logging.Formatter):
    """Formatter mit Farb-Unterstützung für Terminal-Output"""
    
    COLORS = {
        'DEBUG': '\033[36m',     # Cyan
        'INFO': '\033[32m',      # Green
        'WARNING': '\033[33m',   # Yellow
        'ERROR': '\033[31m',     # Red
        'CRITICAL': '\033[35m',  # Magenta
    }
    RESET = '\033[0m'
    
    def format(self, record):
        # Füge Farbe für Terminal-Output hinzu
        if hasattr(record, 'color_output') and record.color_output:
            levelname = record.levelname
            record.levelname = f"{self.COLORS.get(levelname, '')}{levelname}{self.RESET}"
        
        # Formatiere Nachricht
        result = super().format(record)
        
        # Reset levelname für File-Output
        record.levelname = record.levelname.replace(self.RESET, '').replace('\033[36m', '').replace('\033[32m', '').replace('\033[33m', '').replace('\033[31m', '').replace('\033[35m', '')
        
        return result


class StructuredLogger:
    """Strukturiertes Logging mit Kontext-Support"""
    
    def __init__(self, name: str, context: Optional[dict] = None):
        self.logger = logging.getLogger(name)
        self.context = context or {}
    
    def _log_with_context(self, level: int, message: str, **kwargs):
        """Logging mit strukturiertem Kontext"""
        extra = {
            'timestamp': datetime.utcnow().isoformat(),
            'context': {**self.context, **kwargs}
        }
        self.logger.log(level, message, extra=extra)
    
    def debug(self, message: str, **kwargs):
        self._log_with_context(logging.DEBUG, message, **kwargs)
    
    def info(self, message: str, **kwargs):
        self._log_with_context(logging.INFO, message, **kwargs)
    
    def warning(self, message: str, **kwargs):
        self._log_with_context(logging.WARNING, message, **kwargs)
    
    def error(self, message: str, **kwargs):
        self._log_with_context(logging.ERROR, message, **kwargs)
    
    def critical(self, message: str, **kwargs):
        self._log_with_context(logging.CRITICAL, message, **kwargs)
    
    def add_context(self, **kwargs):
        """Fügt permanenten Kontext hinzu"""
        self.context.update(kwargs)
    
    def with_context(self, **kwargs):
        """Erstellt neuen Logger mit erweitertem Kontext"""
        new_context = {**self.context, **kwargs}
        return StructuredLogger(self.logger.name, new_context)


class PerformanceLogger:
    """Logger für Performance-Metriken"""
    
    def __init__(self, logger: StructuredLogger):
        self.logger = logger
        self.timers: Dict[str, datetime] = {}
    
    def start_timer(self, operation: str):
        """Startet Timer für Operation"""
        self.timers[operation] = datetime.utcnow()
    
    def end_timer(self, operation: str, **context):
        """Beendet Timer und loggt Dauer"""
        if operation not in self.timers:
            return
        
        start_time = self.timers.pop(operation)
        duration_ms = (datetime.utcnow() - start_time).total_seconds() * 1000
        
        self.logger.info(
            f"Operation completed: {operation}",
            operation=operation,
            duration_ms=round(duration_ms, 2),
            **context
        )


def setup_logging():
    """Initialisiert das Logging-System"""
    config = get_config()
    
    # Root-Logger konfigurieren
    root_logger = logging.getLogger()
    root_logger.setLevel(getattr(logging, config.logging.level))
    
    # Entferne existierende Handler
    root_logger.handlers.clear()
    
    # File Handler mit Rotation
    file_handler = logging.handlers.RotatingFileHandler(
        filename=config.logging.file_path,
        maxBytes=config.logging.max_size_mb * 1024 * 1024,
        backupCount=config.logging.backup_count,
        encoding='utf-8'
    )
    
    # JSON-Format für File-Output
    file_formatter = logging.Formatter(
        '{"time": "%(asctime)s", "level": "%(levelname)s", "module": "%(name)s", '
        '"message": "%(message)s", "context": %(context)s}',
        datefmt='%Y-%m-%d %H:%M:%S',
        defaults={'context': '{}'}
    )
    file_handler.setFormatter(file_formatter)
    
    # Console Handler
    console_handler = logging.StreamHandler()
    console_formatter = ColoredFormatter(
        '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        datefmt='%H:%M:%S'
    )
    console_handler.setFormatter(console_formatter)
    
    # Handler hinzufügen
    root_logger.addHandler(file_handler)
    root_logger.addHandler(console_handler)
    
    # Setze color_output Flag für Console
    class ColorFilter(logging.Filter):
        def filter(self, record):
            record.color_output = True
            if not hasattr(record, 'context'):
                record.context = {}
            return True
    
    console_handler.addFilter(ColorFilter())
    
    # Logging für externe Libraries reduzieren
    logging.getLogger('urllib3').setLevel(logging.WARNING)
    logging.getLogger('asyncio').setLevel(logging.WARNING)
    logging.getLogger('playwright').setLevel(logging.WARNING)
    
    return root_logger


def get_logger(name: str, **context) -> StructuredLogger:
    """Factory-Funktion für Logger"""
    return StructuredLogger(name, context)


def log_exception(logger: StructuredLogger, exception: Exception, **context):
    """Hilfsfunktion für Exception-Logging"""
    logger.error(
        f"Exception occurred: {type(exception).__name__}",
        exception_type=type(exception).__name__,
        exception_message=str(exception),
        **context
    )


def log_api_call(logger: StructuredLogger, method: str, url: str, 
                 status_code: Optional[int] = None, duration_ms: Optional[float] = None,
                 **context):
    """Hilfsfunktion für API-Call-Logging"""
    logger.info(
        f"API call: {method} {url}",
        method=method,
        url=url,
        status_code=status_code,
        duration_ms=duration_ms,
        **context
    )


# Initialisiere Logging beim Import
_initialized = False
if not _initialized:
    setup_logging()
    _initialized = True