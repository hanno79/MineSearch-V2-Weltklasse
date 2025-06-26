"""
Author: rahn
Datum: 24.06.2025
Version: 1.0
Beschreibung: Utility-Funktionen für Exa Agent
"""

from typing import List, Optional
from urllib.parse import urlparse
import re


def extract_base_domain(url_or_domain: str) -> str:
    """
    Extrahiert die Basis-Domain aus einer URL oder Domain.
    
    Beispiele:
    - "https://gov.sk.ca/business/agriculture" -> "gov.sk.ca"
    - "www.example.com/path" -> "example.com"
    - "example.com:8080" -> "example.com"
    - "gov.sk.ca" -> "gov.sk.ca"
    
    Args:
        url_or_domain: URL oder Domain-String
        
    Returns:
        Bereinigte Basis-Domain ohne Protokoll, www-Präfix, Pfade oder Ports
    """
    if not url_or_domain:
        return ""
    
    # Entferne führende/nachfolgende Leerzeichen
    url_or_domain = url_or_domain.strip()
    
    # Wenn es eine vollständige URL mit Schema ist
    if url_or_domain.startswith(('http://', 'https://', 'ftp://', '//')):
        try:
            parsed = urlparse(url_or_domain)
            domain = parsed.netloc
            
            # Falls netloc leer ist, versuche hostname
            if not domain:
                domain = parsed.hostname or ""
        except Exception:
            # Falls URL-Parsing fehlschlägt, behandle als Domain
            domain = url_or_domain
    else:
        # Es ist bereits eine Domain (möglicherweise mit Pfad)
        # Entferne alles nach dem ersten /
        domain = url_or_domain.split('/')[0]
        
        # Behandle user:pass@domain Format ohne Schema
        if '@' in domain and ':' in domain.split('@')[0]:
            domain = domain.split('@')[-1]
    
    # Entferne www. Präfix (case-insensitive)
    if domain.lower().startswith('www.'):
        domain = domain[4:]
    
    # Entferne Port falls vorhanden
    if ':' in domain:
        domain = domain.split(':')[0]
    
    # Entferne Benutzerinformationen (user:pass@domain)
    if '@' in domain:
        domain = domain.split('@')[-1]
    
    # Validiere dass es eine gültige Domain ist
    # Muss mindestens einen Punkt enthalten und keine ungültigen Zeichen
    if domain and '.' in domain and re.match(r'^[a-zA-Z0-9.-]+$', domain):
        return domain.lower()  # Normalisiere zu Kleinbuchstaben
    
    return ""


def clean_domain_list(domains: List[str]) -> List[str]:
    """
    Bereinigt eine Liste von Domains/URLs zu Basis-Domains.
    Entfernt Duplikate und leere Einträge.
    
    Args:
        domains: Liste von URLs oder Domains
        
    Returns:
        Liste von bereinigten, eindeutigen Basis-Domains
    """
    cleaned_domains = []
    
    for domain in domains:
        cleaned = extract_base_domain(domain)
        if cleaned and cleaned not in cleaned_domains:
            cleaned_domains.append(cleaned)
    
    return cleaned_domains


def validate_domain(domain: str) -> bool:
    """
    Validiert ob ein String eine gültige Domain ist.
    
    Args:
        domain: Zu validierender Domain-String
        
    Returns:
        True wenn gültige Domain, sonst False
    """
    if not domain:
        return False
    
    # Basis-Validierung: Muss Punkt enthalten und gültige Zeichen
    domain_pattern = re.compile(
        r'^(?:[a-zA-Z0-9](?:[a-zA-Z0-9-]{0,61}[a-zA-Z0-9])?\.)+[a-zA-Z]{2,}$'
    )
    
    return bool(domain_pattern.match(domain))


def normalize_domains_for_exa(domains: List[str], max_domains: int = 20) -> List[str]:
    """
    Normalisiert und bereitet Domains für die Exa API vor.
    
    Args:
        domains: Liste von URLs oder Domains
        max_domains: Maximale Anzahl von Domains (Exa Limit)
        
    Returns:
        Liste von bereinigten, validierten Domains für Exa API
    """
    # Bereinige alle Domains
    cleaned = clean_domain_list(domains)
    
    # Filtere nur valide Domains
    valid_domains = [d for d in cleaned if validate_domain(d)]
    
    # Limitiere auf max_domains
    return valid_domains[:max_domains]