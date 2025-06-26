"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Produktions-optimierte Einstellungen für MineSearch
"""

# API Rate Limits (Requests pro Minute)
RATE_LIMITS = {
    'tavily': {
        'rate': 5,           # Reduziert von 30
        'per': 60,
        'retry_after_limit': 120  # 2 Minuten Wartezeit nach Limit
    },
    'perplexity': {
        'rate': 5,           # Reduziert von 10
        'per': 60,
        'retry_after_limit': 60
    },
    'openrouter': {
        'rate': 10,
        'per': 60,
        'retry_after_limit': 60
    },
    'claude': {
        'rate': 10,
        'per': 60,
        'retry_after_limit': 60
    },
    'exa': {
        'rate': 10,
        'per': 60,
        'retry_after_limit': 60
    },
    'firecrawl': {
        'rate': 5,
        'per': 60,
        'retry_after_limit': 60
    },
    'brightdata': {
        'rate': 20,
        'per': 60,
        'retry_after_limit': 30
    },
    'scrapingbee': {
        'rate': 10,
        'per': 60,
        'retry_after_limit': 60
    }
}

# Cache Settings
CACHE_SETTINGS = {
    'enabled': True,
    'ttl_seconds': 300,      # 5 Minuten Cache
    'max_size': 1000,        # Max Anzahl gecachter Einträge
    'cache_dir': '/app/data/cache'
}

# Session Management
SESSION_SETTINGS = {
    'timeout_seconds': 60,
    'max_connections': 10,
    'keepalive_timeout': 30,
    'force_close': True,
    'enable_cleanup': True,
    'auto_cleanup_interval': 300  # 5 Minuten
}

# Query Optimization
QUERY_SETTINGS = {
    'max_queries_per_agent': 5,     # Reduziert von 30
    'priority_queries_only': True,
    'deduplicate_queries': True,
    'smart_query_routing': True,
    'min_confidence_threshold': 0.4
}

# Retry Settings
RETRY_SETTINGS = {
    'max_retries': 3,
    'initial_delay': 1,
    'exponential_backoff': True,
    'max_delay': 30,
    'retry_on_status': [429, 500, 502, 503, 504]
}

# Concurrent Request Limits
CONCURRENCY_LIMITS = {
    'max_concurrent_agents': 3,      # Reduziert
    'max_requests_per_agent': 2,
    'semaphore_timeout': 30
}

# Monitoring Settings
MONITORING_SETTINGS = {
    'enabled': True,
    'metrics_interval': 60,          # Jede Minute
    'health_check_interval': 300,    # Alle 5 Minuten
    'export_metrics': True,
    'metrics_export_path': '/app/data/metrics',
    'alert_thresholds': {
        'error_rate': 0.2,           # 20% Fehlerrate
        'response_time': 10.0,       # 10 Sekunden
        'memory_usage': 80,          # 80% RAM
        'cpu_usage': 80              # 80% CPU
    }
}

# Agent Priority (höhere Zahl = höhere Priorität)
AGENT_PRIORITY = {
    'tavily': 8,
    'perplexity': 7,
    'exa': 6,
    'claude': 5,
    'openrouter': 5,
    'firecrawl': 4,
    'scrapingbee': 3,
    'brightdata': 3,
    'scraper': 2,
    'apify': 1
}

# Timeouts (in Sekunden)
TIMEOUT_SETTINGS = {
    'api_timeout': 60,
    'scraping_timeout': 90,
    'total_search_timeout': 300,     # 5 Minuten max pro Suche
    'agent_init_timeout': 30
}

# Error Handling
ERROR_HANDLING = {
    'log_errors': True,
    'detailed_error_logs': True,
    'capture_stack_traces': True,
    'error_notification': False,      # Für Produktion aktivieren
    'max_error_log_size': 100        # MB
}

# Performance Optimization
PERFORMANCE_SETTINGS = {
    'enable_profiling': False,        # Nur für Debugging
    'gc_threshold': 700,             # Garbage Collection
    'max_memory_mb': 2048,           # 2GB max
    'enable_compression': True,
    'batch_processing': True,
    'batch_size': 10
}

# API Fallbacks
API_FALLBACKS = {
    'tavily': ['perplexity', 'exa'],
    'perplexity': ['tavily', 'claude'],
    'claude': ['openrouter', 'perplexity'],
    'openrouter': ['claude', 'perplexity']
}

# Feature Flags
FEATURE_FLAGS = {
    'enable_caching': True,
    'enable_monitoring': True,
    'enable_rate_limiting': True,
    'enable_auto_retry': True,
    'enable_session_pooling': True,
    'enable_query_optimization': True,
    'enable_error_recovery': True,
    'enable_health_checks': True,
    'enable_performance_mode': True,
    'debug_mode': False
}