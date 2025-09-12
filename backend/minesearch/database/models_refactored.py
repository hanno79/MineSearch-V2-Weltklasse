"""
Author: rahn
Datum: 11.09.2025
Version: 2.0
Beschreibung: Refaktorisierte Datenbank-Modelle für MineSearch v2 (REGEL 1 konform: <500 Zeilen)
"""

# Importiere alle Modelle aus den aufgeteilten Modulen
from .models_base import Base, Source, SearchSession
from .models_search import SearchResult, ModelPerformance
from .models_normalized import NormalizedMine, NormalizedFieldValue

# Exportiere alle Modelle für einfachen Import
__all__ = [
    'Base',
    'Source',
    'SearchSession',
    'SearchResult',
    'ModelPerformance',
    'NormalizedMine',
    'NormalizedFieldValue'
]

# Registriere alle Modelle für SQLAlchemy
def get_all_models():
    """Gibt alle Modelle zurück für Datenbank-Initialisierung"""
    return [
        Source,
        SearchSession,
        SearchResult,
        ModelPerformance,
        NormalizedMine,
        NormalizedFieldValue
    ]

def get_model_by_name(model_name: str):
    """Gibt ein Modell anhand des Namens zurück"""
    models = {
        'Source': Source,
        'SearchSession': SearchSession,
        'SearchResult': SearchResult,
        'ModelPerformance': ModelPerformance,
        'NormalizedMine': NormalizedMine,
        'NormalizedFieldValue': NormalizedFieldValue
    }
    return models.get(model_name)

# Hilfsfunktionen für Datenbank-Operationen
def create_tables(engine):
    """Erstellt alle Tabellen"""
    Base.metadata.create_all(bind=engine)

def drop_tables(engine):
    """Löscht alle Tabellen"""
    Base.metadata.drop_all(bind=engine)

def get_table_names():
    """Gibt alle Tabellennamen zurück"""
    return list(Base.metadata.tables.keys())

# Model-Validierung
def validate_model_data(model_class, data: dict) -> bool:
    """Validiert Daten für ein Modell"""
    try:
        # Erstelle eine Instanz ohne sie zu speichern
        instance = model_class(**data)
        return True
    except Exception as e:
        print(f"Validierungsfehler für {model_class.__name__}: {e}")
        return False

# Export-Funktionen
def export_model_to_dict(instance) -> dict:
    """Exportiert eine Modell-Instanz zu Dictionary"""
    if hasattr(instance, 'to_dict'):
        return instance.to_dict()
    else:
        # Fallback für Modelle ohne to_dict Methode
        return {c.name: getattr(instance, c.name) for c in instance.__table__.columns}

def export_all_models_to_dict(instances: list) -> list:
    """Exportiert eine Liste von Modell-Instanzen zu Dictionary-Liste"""
    return [export_model_to_dict(instance) for instance in instances]
