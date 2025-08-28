"""
SCHEMA-NORMALISIERUNG 28.08.2025: Parser für atomische Feldwerte
Extrahiert saubere Werte aus "Kanada [1,2,3]" Format
"""

import re
from typing import Tuple, List, Optional
import logging

logger = logging.getLogger(__name__)


def extract_atomic_value_and_sources(field_value: str) -> Tuple[str, List[int]]:
    """
    Extrahiert atomischen Wert und Quellenreferenzen aus kombiniertem Format
    
    Args:
        field_value: Wert mit Quellenreferenzen, z.B. "Kanada [1,2,3,4,5]"
    
    Returns:
        Tuple[atomischer_wert, liste_der_quellenreferenzen]
        
    Examples:
        "Kanada [1,2,3]" -> ("Kanada", [1, 2, 3])
        "Gold Mine [5,7,9,11]" -> ("Gold Mine", [5, 7, 9, 11])
        "Kanada" -> ("Kanada", [])
        "" -> ("", [])
    """
    if not field_value or not isinstance(field_value, str):
        return "", []
    
    field_value = field_value.strip()
    if not field_value:
        return "", []
    
    # Regex pattern für Quellenreferenzen in eckigen Klammern
    # Findet [1,2,3,4] oder [1, 2, 3] oder [1,2,3,4,5,6,7,8,9,10]
    source_pattern = r'\[(\d+(?:\s*,\s*\d+)*)\]'
    
    # Suche nach Quellenreferenzen
    source_match = re.search(source_pattern, field_value)
    
    if source_match:
        # Extrahiere atomischen Wert (entferne Quellenreferenzen)
        atomic_value = re.sub(source_pattern, '', field_value).strip()
        
        # Extrahiere Quellenreferenzen
        source_refs_str = source_match.group(1)
        try:
            # Parse Nummern aus "1,2,3,4" -> [1, 2, 3, 4]
            source_refs = [int(num.strip()) for num in source_refs_str.split(',')]
        except (ValueError, AttributeError):
            logger.warning(f"Fehler beim Parsen von Quellenreferenzen: {source_refs_str}")
            source_refs = []
        
        return atomic_value, source_refs
    else:
        # Keine Quellenreferenzen gefunden - gesamter Wert ist atomisch
        return field_value, []


def normalize_atomic_value(atomic_value: str) -> Optional[str]:
    """
    Normalisiert atomische Werte für konsistente Speicherung
    
    Args:
        atomic_value: Roher atomischer Wert
    
    Returns:
        Normalisierter Wert oder None wenn leer/ungültig
    """
    if not atomic_value or not isinstance(atomic_value, str):
        return None
    
    normalized = atomic_value.strip()
    
    # Prüfe auf Platzhalter-Werte (nach REGEL 10)
    placeholder_indicators = [
        '', 'X', 'N/A', 'KEINE ANGABEN', 'NICHT VERFÜGBAR', 'UNBEKANNT', 
        'LEER', 'UNKNOWN', 'NOT FOUND', 'NO DATA', 'K.A.', 'N.A.',
        'NICHTS GEFUNDEN'
    ]
    
    if normalized.upper() in [p.upper() for p in placeholder_indicators]:
        return None  # Leer-Werte werden nicht als atomische Werte gespeichert
    
    return normalized


def build_display_value(atomic_value: str, source_refs: List[int]) -> str:
    """
    Baut Anzeige-Wert aus atomischem Wert und Quellenreferenzen
    
    Args:
        atomic_value: Atomischer Wert, z.B. "Kanada"
        source_refs: Liste der Quellenreferenzen, z.B. [1, 2, 3]
    
    Returns:
        Anzeige-Wert, z.B. "Kanada [1,2,3]"
    """
    if not atomic_value:
        return ""
    
    if source_refs:
        # Sortiere und entferne Duplikate
        unique_refs = sorted(list(set(source_refs)))
        ref_str = ','.join(map(str, unique_refs))
        return f"{atomic_value} [{ref_str}]"
    else:
        return atomic_value


def find_or_create_source_by_url(session, source_url: str):
    """
    Findet oder erstellt Quelle basierend auf URL
    
    Args:
        session: SQLAlchemy Session
        source_url: URL der Quelle
    
    Returns:
        Source-Objekt oder None
    """
    from minesearch.database.models import Source
    import re
    from urllib.parse import urlparse
    
    if not source_url:
        return None
    
    # Versuche existierende Quelle zu finden
    existing_source = session.query(Source).filter(Source.url == source_url).first()
    if existing_source:
        return existing_source
    
    # Erstelle neue Quelle
    try:
        parsed_url = urlparse(source_url)
        domain = parsed_url.netloc.lower() if parsed_url.netloc else "unknown"
        
        # Klassifiziere Quellentyp
        source_type = Source.classify_source_type(source_url, domain)
        
        # Ermittle Land falls möglich
        country = Source.get_country_from_domain(source_url, domain)
        
        new_source = Source(
            url=source_url,
            domain=domain,
            source_type=source_type,
            country=country,
            reliability_score=50.0  # Standard-Score
        )
        
        session.add(new_source)
        session.flush()  # Für ID-Generierung
        
        logger.info(f"Neue Quelle erstellt: {source_url} (ID: {new_source.id})")
        return new_source
        
    except Exception as e:
        logger.error(f"Fehler beim Erstellen der Quelle {source_url}: {e}")
        return None


# Test-Funktionen für Entwicklung
if __name__ == "__main__":
    # Test-Cases
    test_cases = [
        "Kanada [1,2,3,4,5]",
        "Gold Mine [1, 2, 3]", 
        "Barrick Gold Corporation [10,11,12,13,14,15,16]",
        "Kanada",
        "",
        "X",
        "N/A [1,2,3]",
        "123.45 [4,5,6]"
    ]
    
    print("=== ATOMIC VALUE PARSER TESTS ===")
    for test_value in test_cases:
        atomic, sources = extract_atomic_value_and_sources(test_value)
        normalized = normalize_atomic_value(atomic)
        display = build_display_value(atomic, sources) if normalized else "LEER"
        
        print(f"Input: '{test_value}'")
        print(f"  -> Atomic: '{atomic}' | Sources: {sources} | Normalized: {normalized} | Display: '{display}'")
        print()