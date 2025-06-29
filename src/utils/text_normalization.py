"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Text-Normalisierungs-Utilities für flexible Minensuche

Text normalization utilities for flexible mine name searching
"""
import unicodedata
import re

def normalize_mine_name(name: str) -> str:
    """Normalize mine name by removing accents and special characters"""
    # Remove accents
    nfd_form = unicodedata.normalize('NFD', name)
    without_accents = ''.join(char for char in nfd_form if unicodedata.category(char) != 'Mn')
    
    # Keep original with accents AND normalized version
    return without_accents

def get_mine_name_variants(name: str) -> list:
    """Generate variants of mine name for flexible searching"""
    variants = [name]  # Original
    
    # Normalized without accents
    normalized = normalize_mine_name(name)
    if normalized != name:
        variants.append(normalized)
    
    # Common variations
    # Remove "Mine" suffix/prefix
    for word in ["Mine", "mine", "Mines", "mines", "Project", "Projet"]:
        if name.endswith(f" {word}"):
            variants.append(name[:-len(f" {word}")].strip())
        if name.startswith(f"{word} "):
            variants.append(name[len(f"{word} "):].strip())
    
    # Add "Mine" if not present
    if "mine" not in name.lower():
        variants.append(f"{name} Mine")
        variants.append(f"Mine {name}")
    
    # Handle special Quebec mine naming patterns
    # Lac/Lake variations
    if name.startswith("Lac "):
        variants.append(name.replace("Lac ", "Lake "))
    elif name.startswith("Lake "):
        variants.append(name.replace("Lake ", "Lac "))
    
    # Saint/St variations
    name_lower = name.lower()
    if "saint-" in name_lower or "st-" in name_lower:
        if name_lower.startswith("saint-"):
            variants.append("St-" + name[6:])
        elif name_lower.startswith("st-"):
            variants.append("Saint-" + name[3:])
    
    # Common French/English variations
    replacements = [
        ("Grande", "Grand"),
        ("Petite", "Petit"),
        ("Nouvelle", "New"),
        ("Vieille", "Old"),
        ("Nord", "North"),
        ("Sud", "South"),
        ("Est", "East"),
        ("Ouest", "West")
    ]
    
    for fr, en in replacements:
        if fr in name:
            variants.append(name.replace(fr, en))
        if en in name:
            variants.append(name.replace(en, fr))
    
    # Remove duplicates while preserving order
    seen = set()
    unique_variants = []
    for v in variants:
        if v not in seen:
            seen.add(v)
            unique_variants.append(v)
    
    return unique_variants

def get_french_search_terms():
    """Get French mining-specific search terms"""
    return {
        "operator": ["exploitant", "opérateur", "propriétaire", "compagnie minière"],
        "coordinates": ["coordonnées", "localisation", "emplacement", "position GPS"],
        "commodity": ["minerai", "ressource", "métal", "substance", "produit minier"],
        "status": ["statut", "état", "situation", "phase", "stade"],
        "production": ["production", "extraction", "exploitation", "rendement"],
        "closure": ["fermeture", "cessation", "arrêt", "fin d'exploitation"],
        "remediation": ["restauration", "réhabilitation", "assainissement", "remise en état"],
        "environment": ["environnement", "impact environnemental", "étude d'impact"],
        "permit": ["permis", "autorisation", "licence", "certificat"],
        "report": ["rapport", "étude", "document", "analyse"],
        "reserves": ["réserves", "ressources", "gisement", "tonnage"],
        "employees": ["employés", "travailleurs", "main-d'œuvre", "personnel"]
    }