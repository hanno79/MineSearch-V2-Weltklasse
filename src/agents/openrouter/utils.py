"""
Author: rahn
Datum: 23.06.2025
Version: 1.0
Beschreibung: Utility-Funktionen für OpenRouter Model-Handling
"""

def parse_model_id(model_id: str) -> dict:
    """
    Parst eine OpenRouter Model ID und extrahiert die Komponenten.
    
    Unterstützt folgende Formate:
    - provider/model-name
    - provider/model-name:suffix (z.B. :free)
    
    Args:
        model_id: Die zu parsende Model ID
        
    Returns:
        Dictionary mit:
        - full_id: Die vollständige Model ID
        - provider: Der Provider-Name
        - model_name: Der Model-Name (ohne Provider)
        - model_key: Der Model-Key für Vergleiche (ohne Provider und Suffix)
        - suffix: Der optionale Suffix (z.B. "free")
    """
    if not model_id or '/' not in model_id:
        return {
            'full_id': model_id,
            'provider': '',
            'model_name': model_id or '',
            'model_key': model_id or '',
            'suffix': None
        }
    
    # Teile in Provider und Rest
    parts = model_id.split('/', 1)
    provider = parts[0]
    model_part = parts[1] if len(parts) > 1 else ''
    
    # Prüfe auf Suffix
    suffix = None
    model_name = model_part
    
    if ':' in model_part:
        model_parts = model_part.split(':', 1)
        model_name = model_parts[0]
        suffix = model_parts[1] if len(model_parts) > 1 else None
    
    return {
        'full_id': model_id,
        'provider': provider,
        'model_name': model_name,
        'model_key': model_name,  # Für Vergleiche: nur der Model-Name ohne Provider und Suffix
        'suffix': suffix
    }


def extract_model_key_from_agent_type(agent_type: str) -> str:
    """
    Extrahiert den Model-Key aus einem agent_type String.
    
    Args:
        agent_type: z.B. "openrouter_deepseek-chat" oder "openrouter_gemini-2.0-flash-exp"
        
    Returns:
        Der extrahierte Model-Key, z.B. "deepseek-chat" oder "gemini-2.0-flash-exp"
    """
    if agent_type.startswith("openrouter_"):
        return agent_type.replace("openrouter_", "")
    return agent_type


def find_model_by_key(model_key: str, models_dict: dict) -> tuple:
    """
    Sucht ein Model anhand des Model-Keys in einem Dictionary von Models.
    
    Args:
        model_key: Der zu suchende Model-Key
        models_dict: Dictionary mit Model IDs als Keys
        
    Returns:
        Tuple (model_id, model) wenn gefunden, sonst (None, None)
    """
    # Direkte Übereinstimmung prüfen
    for model_id, model in models_dict.items():
        parsed = parse_model_id(model_id)
        if parsed['model_key'] == model_key:
            return model_id, model
    
    # Falls nicht gefunden, versuche flexiblere Suche
    # z.B. "gemini" könnte zu "gemini-2.0-flash-exp" passen
    for model_id, model in models_dict.items():
        parsed = parse_model_id(model_id)
        if model_key in parsed['model_key'] or parsed['model_key'].startswith(model_key):
            return model_id, model
    
    return None, None