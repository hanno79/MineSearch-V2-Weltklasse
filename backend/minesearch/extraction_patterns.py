"""
Author: rahn
Datum: 05.07.2025
Version: 1.0
Beschreibung: Pattern-Definitionen für Mining-Datenextraktion
"""

from typing import Dict, List

def get_extraction_patterns() -> Dict[str, List[str]]:
    """
    Gibt alle Extraction-Patterns für Mining-Daten zurück
    
    Returns:
        Dict mit Pattern-Listen für jedes Feld
    """
    patterns = {
        'Country': [
            r'Country:\s*([^\n]+)', 
            r'Land:\s*([^\n]+)', 
            r'(?:in|aus|from)\s+(Chile|Peru|Kanada|Canada|Mexiko|Mexico|USA|Indonesien|Indonesia|Australien|Australia|Botswana|Südafrika|South Africa)'
        ],
        'Region': [
            r'Region:\s*([^\n]+)', 
            r'Provinz:\s*([^\n]+)', 
            r'Province:\s*([^\n]+)', 
            r'in\s+(?:der\s+)?(?:Region|Provinz)\s+([^\n,]+)',
            r'in\s+(Quebec|Québec|Ontario|British Columbia|Alberta|Manitoba|Saskatchewan)[\s,]',
            r'(?:located\s+in|liegt\s+in)\s+(Quebec|Québec|Ontario|British Columbia|Alberta)[\s,]'
        ],
        'Eigentümer': [
            # BUGFIX 17.08.2025: Extract value WITHOUT source references
            r'Eigentümer:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'Owner:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'Propriétaire:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'Propietario:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'Pemilik:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'gehört\s+(?:zu|der|dem)\s+([^\[\n]+?)(?:\s*\[|$)',
            r'owned\s+by\s+([^\[\n]+?)(?:\s*\[|$)',
            r'property\s+of\s+([^\[\n]+?)(?:\s*\[|$)',
            r'belongs\s+to\s+([^\[\n]+?)(?:\s*\[|$)',
            r'possession\s+of\s+([^\[\n]+?)(?:\s*\[|$)',
            r'Eigentum\s+(?:von|der)\s+([^\[\n]+?)(?:\s*\[|$)',
            # Französische Patterns (Quebec)
            r'détenteur\s+(?:du\s+)?titre:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'société\s+(?:propriétaire|détentrice):\s*([^\[\n]+?)(?:\s*\[|$)',
            r'appartient\s+à\s+([^\[\n]+?)(?:\s*\[|$)',
            r'propriété\s+de\s+([^\[\n]+?)(?:\s*\[|$)'
        ],
        'Betreiber': [
            # BUGFIX 17.08.2025: Extract value WITHOUT source references
            r'Betreiber:\s*([^\[\n]+?)(?:\s*\[|$)', 
            r'Operator:\s*([^\[\n]+?)(?:\s*\[|$)', 
            r'betrieben\s+von\s+([^\[\n,]+?)(?:\s*\[|$)', 
            r'operated\s+by\s+([^\[\n,]+?)(?:\s*\[|$)',
            r'opérateur:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'operador:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'dioperasikan\s+oleh\s+([^\[\n]+?)(?:\s*\[|$)',
            # Französische Patterns (Quebec)
            r'exploitant:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'exploité\s+par\s+([^\[\n,]+?)(?:\s*\[|$)',
            r'société\s+exploitante:\s*([^\[\n]+?)(?:\s*\[|$)',
            r'gestion\s+(?:de\s+la\s+mine\s+)?par\s+([^\[\n,]+?)(?:\s*\[|$)'
        ],
        'x-Koordinate': [
            # BUGFIX 17.08.2025: Pattern für aktuelles API Response Format
            r'-\s*x-Koordinate:\s*([-+]?\d+\.?\d+)',
            r'x-Koordinate:\s*([-+]?\d+\.?\d+)',
            # Dezimalgrad-Formate
            r'Latitude:\s*([-+]?\d+\.?\d+)', 
            r'Lat\.?:\s*([-+]?\d+\.?\d+)', 
            r'Breitengrad:\s*([-+]?\d+\.?\d+)',
            r'(?:GPS-)?Koordinaten:\s*([-+]?\d+\.?\d+)\s*[,/]\s*[-+]?\d+\.?\d+',
            # Grad-Minuten-Sekunden Format
            r'(\d+)°\s*\d+[\'′]\s*\d+(?:\.\d+)?[\"″]\s*[NS]',
            # In Tabellen oder Listen
            r'(?:Location|Standort|Position)[\s\S]{0,50}?Lat\.?\s*:?\s*([-+]?\d+\.?\d+)',
            # Koordinaten im Text
            r'(?:liegt bei|located at|position)\s+(?:etwa\s+)?([-+]?\d+\.?\d+)\s*°?\s*[NS]',
            # Weitere Varianten
            r'X\s*[:=]\s*([-+]?\d+\.?\d+)',
            r'(?:North|Nord|N)\s*[:=]\s*([-+]?\d+\.?\d+)'
        ],
        'y-Koordinate': [
            # BUGFIX 17.08.2025: Pattern für aktuelles API Response Format
            r'-\s*y-Koordinate:\s*([-+]?\d+\.?\d+)',
            r'y-Koordinate:\s*([-+]?\d+\.?\d+)',
            # Dezimalgrad-Formate
            r'Longitude:\s*([-+]?\d+\.?\d+)', 
            r'Long?\.?:\s*([-+]?\d+\.?\d+)', 
            r'Längengrad:\s*([-+]?\d+\.?\d+)',
            r'(?:GPS-)?Koordinaten:\s*[-+]?\d+\.?\d+\s*[,/]\s*([-+]?\d+\.?\d+)',
            # Grad-Minuten-Sekunden Format
            r'(\d+)°\s*\d+[\'′]\s*\d+(?:\.\d+)?[\"″]\s*[EW]',
            # In Tabellen oder Listen
            r'(?:Location|Standort|Position)[\s\S]{0,50}?Long?\.?\s*:?\s*([-+]?\d+\.?\d+)',
            # Koordinaten im Text
            r'(?:liegt bei|located at|position)\s+(?:etwa\s+)?[-+]?\d+\.?\d+\s*°?\s*[NS]\s*[,/]\s*([-+]?\d+\.?\d+)\s*°?\s*[EW]',
            # Weitere Varianten
            r'Y\s*[:=]\s*([-+]?\d+\.?\d+)',
            r'(?:East|West|Ost|West|E|W)\s*[:=]\s*([-+]?\d+\.?\d+)'
        ],
        'Aktivitätsstatus': [
            # BUGFIX 17.08.2025: Extract value WITHOUT source references
            r'Status:\s*([^\[\n]+?)(?:\s*\[|$)', 
            r'Aktivitätsstatus:\s*([^\[\n]+?)(?:\s*\[|$)', 
            r'(?:ist\s+)?(?:derzeit\s+)?(aktiv|geschlossen|stillgelegt|in Betrieb|geplant)',
            r'(Geplant[^,\n]*)',
            r'(Akquisition\s+abgeschlossen[^,\n]*)',
            r'(In\s+Entwicklung[^,\n]*)',
            r'(Explorationsphase[^,\n]*)',
            r'(Produktion\s+eingestellt[^,\n]*)',
            r'(Temporär\s+stillgelegt[^,\n]*)'
        ],
        'Restaurationskosten': get_restoration_cost_patterns(),
        'Jahr der Aufnahme der Kosten': [
            r'(?:Kosten|costs?)\s+(?:von|from|Stand)\s+(\d{4})', 
            r'(?:per|as\s+of)\s+(\d{4})',
            r'(?:Stand|status|as\s+of):\s*(?:\w+\s+)?(\d{4})',
            r'(\d{4})\s+(?:Kosten|costs|liabilities)'
        ],
        'Jahr der Erstellung des Dokumentes': [
            r'(?:Dokument|Report|Bericht)\s+(?:vom|von|dated|from)\s+(\b(?:19|20)\d{2}\b)',
            r'(?:Stand|Date|Datum):\s*(?:\w+\s+)?(\b(?:19|20)\d{2}\b)',
            r'(?:erstellt|created|prepared|published)\s+(?:im|in)?\s*(\b(?:19|20)\d{2}\b)',
            r'(\b(?:19|20)\d{2}\b)\s+(?:Report|Bericht|Document|Study)',
            r'(?:Veröffentlicht|Published|Released):\s*(?:\w+\s+)?(\b(?:19|20)\d{2}\b)',
            r'(?:Technical\s+Report|NI\s*43-101).*?(\b(?:19|20)\d{2}\b)',
            r'(?:Report|Document|Bericht).*?\((\b(?:19|20)\d{2}\b)\)'
        ],
        'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)': [
            r'Rohstoffe?:\s*([^\n]+)', 
            r'(?:produziert|fördert|abbaut)\s+([^\n]+(?:Gold|Kupfer|Silber|Zink|Blei|Nickel|Kohle|Eisenerz)[^\n]*)',
            r'Commodity:\s*([^\n]+)',
            r'Commodities:\s*([^\n]+)',
            r'Mineral(?:s|ien)?:\s*([^\n]+)',
            r'(?:haupt|main)\s*(?:rohstoff|commodity):\s*([^\n]+)'
        ],
        'Minentyp (Untertage/ Open-Pit/ usw.)': [
            r'Minentyp:\s*([^\n]+)', 
            r'Type:\s*([^\n]+)',
            r'((?:Open[- ]?Pit|Untertage|Underground|Tagebau)[^\n,]*)'
        ],
        'Produktionsstart': [
            r'Produktionsstart:\s*(\d{4})', 
            r'Start:\s*(\d{4})', 
            r'(?:in\s+Betrieb\s+seit|eröffnet)\s+(\d{4})'
        ],
        'Produktionsende': [
            r'Produktionsende:\s*(\d{4})', 
            r'Ende:\s*(\d{4})', 
            r'geschlossen\s+(?:seit\s+)?(\d{4})'
        ],
        'Fördermenge/Jahr': [
            r'Fördermenge:\s*([\d,]+(?:\.\d+)?)\s*([^\n]+)',
            r'Produktion:\s*([\d,]+(?:\.\d+)?)\s*([^\n]+)',
            r'produziert\s+(?:jährlich\s+)?([\d,]+(?:\.\d+)?)\s*([^\n]+)'
        ],
        'Fläche der Mine in qkm': [
            r'Fläche:\s*([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2)', 
            r'Area:\s*([\d,]+(?:\.\d+)?)\s*(?:km²|qkm|km2)'
        ]
    }
    
    return patterns


def get_restoration_cost_patterns() -> List[str]:
    """
    Spezielle Patterns für Restaurationskosten
    
    Returns:
        Liste mit Regex-Patterns für Restaurationskosten
    """
    return [
        # ÄNDERUNG 06.07.2025: Verbesserte Patterns mit Währungserfassung
        # ARO (Asset Retirement Obligation) Patterns
        r'ARO[:\s]+(?:of\s+)?(?:\$|CAD|USD|EUR)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M|thousand|k)?(?:\s+(?:CAD|USD|EUR))?',
        r'Asset\s+Retirement\s+Obligation[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        
        # Closure Costs Patterns
        r'closure\s+(?:costs?|provision)[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M|thousand|k)?',
        r'mine\s+closure[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        
        # Environmental Liability Patterns
        r'environmental\s+(?:liability|liabilities)[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        r'environmental\s+provisions?[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        
        # Rehabilitation Patterns
        r'rehabilitation\s+(?:costs?|provision)[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        r'site\s+rehabilitation[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        
        # Restoration Costs Patterns (Deutsch/Englisch)
        r'Restaurationskosten[:\s]+(?:\$|CAD|USD|EUR)?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million|M)?',
        r'Sanierungskosten[:\s]+(?:\$|CAD|USD|EUR)?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million|M)?',
        
        # Financial Guarantee/Bond Patterns
        r'(?:financial\s+)?guarantee[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M|thousand|k)?',
        r'closure\s+bond[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        r'environmental\s+bond[:\s]+(?:\$|CAD|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        
        # Patterns für Tausender-Beträge (kleine Minen)
        r'closure[:\s]+(?:\$|CAD|USD)?\s*([\d,]+)\s*(?:thousand|k)',
        r'restoration[:\s]+(?:\$|CAD|USD)?\s*([\d,]+)k',
        r'rehabilitation[:\s]+\$\s*([\d,]+)K\s*(?:CAD|USD)?',
        # Patterns für Explorationsphasen
        r'(?:exploration|initial)\s+closure\s*:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:thousand|k|CAD|CDN|USD)?',
        r'(?:exploration|initial)\s+restoration\s*:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:thousand|k|CAD|CDN|USD)?',
        # Existierende Patterns für bereits bezahlte Kosten (mit Millionen)
        r'Restaurationskosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
        r'Sanierungskosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
        r'(?:Environmental\s+)?liabilities?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
        r'Closure\s+costs?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
        # Patterns für geplante/zukünftige Kosten
        r'(?:geplante|geschätzte|estimated|planned|future)\s+(?:Restaurations|Sanierungs|restoration|remediation|closure)kosten:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:CAD|CDN|\$)?',
        r'(?:Restaurations|Sanierungs)kosten\s+(?:werden|sind)\s+(?:auf|geschätzt)\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
        r'Rückstellungen?\s+(?:für\s+)?(?:Rekultivierung|Sanierung|Stilllegung):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?)?\s*(?:CAD|CDN|\$)?',
        r'(?:Asset\s+)?(?:Retirement|Decommissioning)\s+Obligations?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|Mio\.?)?\s*(?:CAD|CDN)?',
        r'(?:provision|reserve)\s+for\s+(?:site\s+)?(?:restoration|remediation|closure):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million)?\s*(?:CAD|CDN)?',
        # Patterns für "budgetiert" oder "veranschlagt"
        r'(?:budgetiert|veranschlagt|budgeted|allocated)\s+für\s+(?:Restauration|Sanierung|restoration):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:CAD|CDN|\$)?',
        # Zusätzliche flexible Patterns
        r'(?:Umwelt|Environmental).*?(?:Kosten|costs|liabilities).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?',
        r'\$\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?\s*(?:für|for)\s+(?:Restauration|Sanierung|restoration|closure)',
        r'(?:Schätzung|estimate).*?(?:Restauration|Sanierung|closure).*?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:Millionen|Mio\.?|million)?',
        # Französische Patterns (Quebec Mining)
        r'coûts?\s+(?:de\s+)?(?:restauration|fermeture|réhabilitation):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millions?|mio\.?)?\s*(?:CAD|CDN|\$)?',
        r'garantie\s+financière:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millions?|mio\.?)?\s*(?:CAD|CDN)?',
        r'cautionnement:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millions?|mio\.?)?\s*(?:CAD|CDN)?',
        r'provision\s+(?:pour\s+)?(?:fermeture|restauration):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millions?|mio\.?)?\s*(?:CAD|CDN)?',
        r'obligations?\s+(?:de\s+)?(?:restauration|réhabilitation):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millions?|mio\.?)?\s*(?:CAD|CDN)?',
        r'plan\s+(?:de\s+)?fermeture[\s\S]{0,50}?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millions?|mio\.?)?\s*(?:CAD|CDN)?',
        # Spanische Patterns
        r'costos?\s+de\s+cierre:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millones?)?\s*(?:USD|PEN|CLP)?',
        r'pasivos?\s+ambientales?:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millones?)?\s*(?:USD|PEN|CLP)?',
        r'provisión\s+(?:para\s+)?cierre:\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millones?)?\s*(?:USD|PEN|CLP)?',
        r'garantías?\s+(?:financieras?|ambientales?):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:millones?)?\s*(?:USD|PEN|CLP)?',
        # Indonesische Patterns
        r'biaya\s+(?:reklamasi|rehabilitasi|penutupan):\s*(?:Rp|IDR|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:miliar|juta)?',
        r'jaminan\s+(?:reklamasi|lingkungan):\s*(?:Rp|IDR|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:miliar|juta)?',
        r'dana\s+(?:cadangan|jaminan)\s+reklamasi:\s*(?:Rp|IDR|USD)?\s*([\d,]+(?:\.\d+)?)\s*(?:miliar|juta)?',
        # Tabellarische Darstellungen
        r'(?:closure|restoration|ARO|rehabilitation)[\s\S]{0,50}?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        r'(?:environmental|closure)\s+(?:bond|security|guarantee)[\s\S]{0,30}?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|M)?',
        # Footnote/Note Patterns
        r'Note\s+\d+[\s\S]{0,200}?(?:closure|restoration|ARO)[\s\S]{0,100}?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million)?',
        # Multi-line Patterns für komplexe Darstellungen
        r'(?:closure|restoration)\s+(?:costs?|provision|liability)[\s\n\r]{0,20}?\$?\s*([\d,]+(?:\.\d+)?)',
        # Patterns mit Währungszeichen am Ende
        r'([\d,]+(?:\.\d+)?)\s*(?:million|millones?|miliar)?\s*(?:USD|CAD|AUD|PEN|CLP|IDR)\s+(?:for\s+)?(?:closure|restoration|rehabilitation)',
        # Decommissioning und andere Varianten
        r'(?:decommissioning|abandonment|post-mining)\s+(?:costs?|obligations?):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million)?',
        r'(?:mine\s+)?(?:closure|rehabilitation)\s+(?:provision|reserve|fund):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million)?',
        # Progressive/Final rehabilitation
        r'(?:progressive|final)\s+rehabilitation\s+(?:costs?|provision):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million)?',
        # Care and maintenance
        r'care\s+and\s+maintenance\s+(?:costs?|provision):\s*\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million)?',
        # ÄNDERUNG 06.07.2025: Zusätzliche Patterns für kleine Beträge
        # Kompakte Formate mit k/K
        r'\$\s*([\d,]+)k\s+(?:closure|restoration|rehabilitation)',
        r'\$\s*([\d,]+)K\s+(?:CAD|CDN|USD)\s+(?:for\s+)?(?:closure|restoration)',
        # Patterns ohne explizite Millionen-Angabe
        r'(?:closure|restoration)\s+(?:provision|bond|costs?)[\s:]+\$?\s*([\d,]+)\s+(?:CAD|CDN|USD)',
        r'(?:ARO|environmental\s+liability)[\s:]+\$?\s*([\d,]+)\s+(?:dollars|CAD|CDN|USD)',
        # Patterns für Konzessionsdokumente
        r'(?:concession|permit|license)\s+(?:requires?|stipulates?)[\s\S]{0,50}?\$?\s*([\d,]+(?:\.\d+)?)\s*(?:thousand|k|million)?',
        r'(?:financial\s+)?guarantee[\s:]+\$?\s*([\d,]+(?:\.\d+)?)\s*(?:thousand|k|million)?',
        # GESTIM-spezifische Patterns
        r'(?:GESTIM|mining\s+title)[\s\S]{0,100}?(?:restoration|closure)[\s\S]{0,50}?\$?\s*([\d,]+(?:\.\d+)?)',
        # Management Plan Patterns
        r'management\s+plan[\s\S]{0,100}?(?:closure|restoration)[\s\S]{0,50}?\$?\s*([\d,]+(?:\.\d+)?)',
        # ÄNDERUNG 06.07.2025: Zusätzliche Patterns für spezielle Fälle
        # Environmental liability "of" pattern
        r'(?:environmental\s+)?liabilit(?:y|ies)\s+of\s+\$?\s*([\d,]+(?:\.\d+)?)\s*(?:million|thousand|k)?',
        # Financial guarantee patterns
        r'(?:financial\s+)?guarantee[\s:]+\$?\s*([\d,]+(?:\.\d+)?)',
        r'(?:Konzession|concession|permit)\s+requires?\s+\$?\s*([\d,]+(?:\.\d+)?)\s*(?:financial\s+)?guarantee'
    ]


# ÄNDERUNG 05.07.2025: Neue Patterns für verbesserte Koordinaten-Extraktion
def get_enhanced_coordinate_patterns() -> Dict[str, List[str]]:
    """
    Erweiterte Patterns für bessere GPS-Koordinaten-Extraktion
    
    Returns:
        Dict mit Pattern-Listen für Latitude und Longitude
    """
    return {
        'latitude': [
            # Standard Dezimalgrad
            r'(?:latitude|lat|breitengrad|latitud)[\s:]*([+-]?\d{1,2}\.?\d*)',
            # Mit Hemisphäre
            r'(\d{1,2}\.?\d*)\s*°?\s*[NS]',
            # DMS Format
            r'(\d{1,2})°\s*(\d{1,2})[\'′]\s*(\d{1,2}(?:\.\d+)?)[\"″]\s*[NS]',
            # In Koordinatenpaaren
            r'coordinates?:\s*([+-]?\d{1,2}\.?\d*)\s*[,/]\s*[+-]?\d{1,3}\.?\d*',
            # Tabellarisch
            r'(?:lat|latitude)\s*\|\s*([+-]?\d{1,2}\.?\d*)',
            # Mit Labels
            r'[NS]\s*([+-]?\d{1,2}\.?\d*)\s*°?',
            # Quebec GESTIM Format
            r'(?:UTM|NAD\d+)[\s\S]{0,50}?lat[:\s]*([+-]?\d{1,2}\.?\d*)'
        ],
        'longitude': [
            # Standard Dezimalgrad
            r'(?:longitude|long?|längengrad|longitud)[\s:]*([+-]?\d{1,3}\.?\d*)',
            # Mit Hemisphäre
            r'(\d{1,3}\.?\d*)\s*°?\s*[EW]',
            # DMS Format
            r'(\d{1,3})°\s*(\d{1,2})[\'′]\s*(\d{1,2}(?:\.\d+)?)[\"″]\s*[EW]',
            # In Koordinatenpaaren
            r'coordinates?:\s*[+-]?\d{1,2}\.?\d*\s*[,/]\s*([+-]?\d{1,3}\.?\d*)',
            # Tabellarisch
            r'(?:long?|longitude)\s*\|\s*([+-]?\d{1,3}\.?\d*)',
            # Mit Labels
            r'[EW]\s*([+-]?\d{1,3}\.?\d*)\s*°?',
            # Quebec GESTIM Format
            r'(?:UTM|NAD\d+)[\s\S]{0,50}?long?[:\s]*([+-]?\d{1,3}\.?\d*)'
        ]
    }