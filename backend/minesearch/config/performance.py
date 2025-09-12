"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Performance-Konfiguration für MineSearch
"""

# Performance-Optimierungen
PERFORMANCE_CONFIG = {
    # Datenbank-Optimierungen
    'database': {
        'connection_pool_size': 10,
        'max_overflow': 20,
        'pool_timeout': 30,
        'pool_recycle': 3600
    },
    
    # Cache-Optimierungen
    'cache': {
        'default_timeout': 300,  # 5 Minuten
        'max_size': 1000,
        'enable_compression': True
    },
    
    # API-Optimierungen
    'api': {
        'request_timeout': 30,
        'max_retries': 3,
        'retry_delay': 1,
        'batch_size': 100
    },
    
    # Logging-Optimierungen
    'logging': {
        'level': 'INFO',
        'format': '%(asctime)s - %(name)s - %(levelname)s - %(message)s',
        'max_file_size': 10485760,  # 10MB
        'backup_count': 5
    }
}

# Performance-Metriken
PERFORMANCE_METRICS = {
    'enable_profiling': True,
    'profile_interval': 60,  # Sekunden
    'memory_threshold': 0.8,  # 80% RAM
    'cpu_threshold': 0.8  # 80% CPU
}
