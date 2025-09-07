"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Intelligenter Extraktor für atomare Werte aus AI-generierten Sätzen
"""

import re
import logging
from typing import Optional, List, Set

logger = logging.getLogger(__name__)

class SmartValueExtractor:
    """
    Extrahiert atomare Werte aus AI-generierten Sätzen und Beschreibungen
    für saubere Speicherung in Lookup-Tabellen
    """
    
    def __init__(self):
        # Bekannte Rohstoffe
        self.commodity_keywords = {
            'gold', 'kupfer', 'copper', 'silber', 'silver', 'eisenerz', 'iron ore', 'iron',
            'kohle', 'coal', 'nickel', 'zink', 'zinc', 'blei', 'lead', 'aluminium', 'aluminum',
            'lithium', 'titan', 'titanium', 'platin', 'platinum', 'palladium', 'uran', 'uranium',
            'diamant', 'diamond', 'öl', 'oil', 'gas', 'erdgas', 'steatite', 'graphit', 'graphite',
            'molybdän', 'molybdenum', 'wolfram', 'tungsten', 'kobalt', 'cobalt'
        }
        
        # Bekannte Minentypen
        self.mine_type_keywords = {
            'open-pit', 'open pit', 'openpit', 'surface', 'tagebau', 'à ciel ouvert',
            'underground', 'untertage', 'souterrain', 'shaft', 'schacht', 'quarry', 'steinbruch'
        }
        
        # Bekannte Aktivitätsstatus
        self.activity_status_keywords = {
            'active', 'aktiv', 'exploitation', 'operating', 'in betrieb', 'operational',
            'exploration', 'explorationsphase', 'prospection', 'feasibility', 'entwicklung',
            'closed', 'geschlossen', 'fermé', 'stillgelegt', 'abandoned', 'verlassen',
            'planned', 'geplant', 'proposed', 'vorgeschlagen', 'suspended', 'pausiert',
            'construction', 'bau', 'development', 'care and maintenance', 'wartung'
        }
        
        # Unerwünschte Textmuster die definitiv keine atomaren Werte sind
        self.rejection_patterns = [
            r'dokumentiert\s+im\s+',  # "Dokumentiert im Quebec Bergbauregister"
            r'ist\s+eine?\s+bedeutende?\s+',  # "Ist eine bedeutende Untertage-Goldmine"
            r'war\s+eine?\s+',  # "War ein kleiner Untertagebetrieb"
            r'handelt\s+sich\s+um\s+',  # "Handelt sich um eine Mine"
            r'known\s+to\s+(have\s+)?be(en)?\s+',  # "Is known to have been operational"
            r'exact\s+production\s+figures',  # "exact production figures and current owner"
            r'aber\s+exact\s+',  # "aber exact Production Figures"
            r'project["\s]*\([^)]*\)\s+auf\s+sedar',  # Project" (Maple Gold) auf Sedar
            r'spezifisch\s+als\s+.*\s+in\s+.*berichten',  # "spezifisch als ... in Berichten"
            r'^https?://',  # URLs
            r'\d{4}-\d{4}',  # Jahreszahlen-Bereiche
            r'%\)',  # Prozentzahlen mit Klammer
            r'/\d{4}//',  # "/1998//" Pattern
        ]
        
    def is_sentence_like(self, text: str) -> bool:
        """
        Prüft ob ein Text eher ein Satz als ein atomarer Wert ist
        """
        if not text or len(text.strip()) == 0:
            return False
            
        text = text.strip()
        
        # Längen-Heuristik: Atomare Werte sind meist kurz
        if len(text) > 80:
            return True
        
        # Satzzeichen-Heuristik
        sentence_indicators = ['.', ',', '!', '?', ';', '(', ')', '[', ']']
        if sum(text.count(char) for char in sentence_indicators) >= 3:
            return True
        
        # Verb-Heuristik (deutsche und englische Verben)
        verb_patterns = [
            r'\b(ist|war|wird|wurde|sind|waren|werden|haben|hat|hatte)\b',
            r'\b(is|was|will|were|are|has|had|have|been|being)\b',
            r'\b(handelt|dokumentiert|betrieben|operational|known|exact)\b'
        ]
        
        for pattern in verb_patterns:
            if re.search(pattern, text, re.IGNORECASE):
                return True
        
        # Mehrere Großbuchstaben-Wörter (oft Beschreibungen)
        capitalized_words = re.findall(r'\b[A-ZÄÖÜ][a-zäöüß]*', text)
        if len(capitalized_words) > 4:
            return True
            
        return False
    
    def should_reject_value(self, text: str) -> bool:
        """
        Prüft ob ein Wert definitiv abgelehnt werden soll
        """
        if not text:
            return True
            
        text_lower = text.lower().strip()
        
        # Prüfe gegen Ablehnungsmuster
        for pattern in self.rejection_patterns:
            if re.search(pattern, text_lower):
                logger.info(f"[SMART_EXTRACTOR] Text abgelehnt (Pattern): '{text[:60]}...'")
                return True
        
        # Zusätzliche Ablehnungskriterien
        rejection_conditions = [
            len(text) > 200,  # Zu lange Texte
            text.count('/') > 3,  # Zu viele Schrägstriche
            text.count('(') > 2,  # Zu viele Klammern
            text.lower().startswith('http'),  # URLs
            re.search(r'\d+\.\d+%', text),  # Prozentzahlen
            'sedar' in text_lower,  # Referenz auf Sedar-Datenbank
            'berichten bestätigt' in text_lower,  # "in Berichten bestätigt"
        ]
        
        if any(rejection_conditions):
            logger.info(f"[SMART_EXTRACTOR] Text abgelehnt (Kriterium): '{text[:60]}...'")
            return True
            
        return False
    
    def extract_commodity_from_text(self, text: str) -> Optional[str]:
        """
        Extrahiert Rohstoff-Namen aus beschreibenden Texten
        
        Beispiele:
        - "Ist Eine Bedeutende Untertage-Goldmine" → "Gold"
        - "War Ein Kleiner Untertagebetrieb Für Kupfer Und Zink" → "Kupfer"
        - "Spezifisch Als Steatite In Produktionsberichten" → "Steatite"
        """
        if not text or self.should_reject_value(text):
            return None
            
        text_lower = text.lower()
        
        # Direkte Keyword-Erkennung (prioritär)
        found_commodities = []
        for commodity in self.commodity_keywords:
            # Wort-Grenzen beachten um Teilwörter zu vermeiden
            pattern = r'\b' + re.escape(commodity.lower()) + r'(?:mine|berg|bergbau|abbau|extraction)?\b'
            if re.search(pattern, text_lower):
                # Normalisiere zu Standardform
                if commodity in ['kupfer', 'copper']:
                    found_commodities.append('Kupfer')
                elif commodity in ['gold']:
                    found_commodities.append('Gold')
                elif commodity in ['silber', 'silver']:
                    found_commodities.append('Silber')
                elif commodity in ['kohle', 'coal']:
                    found_commodities.append('Kohle')
                elif commodity in ['eisenerz', 'iron ore', 'iron']:
                    found_commodities.append('Eisenerz')
                elif commodity in ['nickel']:
                    found_commodities.append('Nickel')
                elif commodity in ['zink', 'zinc']:
                    found_commodities.append('Zink')
                elif commodity in ['blei', 'lead']:
                    found_commodities.append('Blei')
                elif commodity in ['steatite']:
                    found_commodities.append('Steatite')
                else:
                    # Kapitalisiere erste Buchstabe
                    found_commodities.append(commodity.capitalize())
        
        if found_commodities:
            # Nehme den ersten gefundenen Rohstoff
            result = found_commodities[0]
            logger.info(f"[SMART_EXTRACTOR] Rohstoff extrahiert: '{text[:60]}...' → '{result}'")
            return result
            
        return None
    
    def extract_company_from_text(self, text: str) -> Optional[str]:
        """
        Extrahiert Firmennamen aus beschreibenden Texten oder lehnt ab
        
        Beispiele:
        - "Dokumentiert Im Quebec Bergbauregister" → None (kein Firmenname)
        - "Newmont Corporation Betrieben Wird" → "Newmont Corporation"
        - "BHP Billiton (57.5%), Rio Tinto (30%)" → "BHP Billiton"
        """
        if not text or self.should_reject_value(text):
            return None
            
        # Spezielle Ablehnungsmuster für Company-Felder
        company_rejection_patterns = [
            'dokumentiert im',
            'bergbauregister',
            'unternehmensberichten',
            'quebec bergbau',
            'mehrdeutige eigentumsverhältnisse',
            'ohne aktuelle primärquellen',
            'government of',
            'regierung',
        ]
        
        text_lower = text.lower()
        for pattern in company_rejection_patterns:
            if pattern in text_lower:
                logger.info(f"[SMART_EXTRACTOR] Company-Text abgelehnt: '{text[:60]}...'")
                return None
        
        # Extrahiere bekannte Firmennamen
        known_companies = [
            'newmont', 'barrick', 'goldcorp', 'kinross', 'yamana',
            'bhp billiton', 'bhp', 'rio tinto', 'freeport-mcmoran',
            'vale', 'glencore', 'anglo american', 'teck', 'antofagasta',
            'southern copper', 'first quantum', 'codelco'
        ]
        
        for company in known_companies:
            pattern = r'\b' + re.escape(company.lower()) + r'(?:\s+(?:corp|corporation|inc|ltd|limited|company|co|ag|sa))?\b'
            match = re.search(pattern, text_lower)
            if match:
                extracted_name = match.group(0)
                # Kapitalisiere erste Buchstaben
                result = ' '.join(word.capitalize() for word in extracted_name.split())
                logger.info(f"[SMART_EXTRACTOR] Company extrahiert: '{text[:60]}...' → '{result}'")
                return result
        
        # Falls kein bekannter Name gefunden, prüfe ob es wie ein Firmenname aussieht
        # Firmen haben oft Corp, Inc, Ltd, etc.
        company_suffix_pattern = r'\b([A-Z][a-zA-Z\s&.-]+(?:Corp|Corporation|Inc|Ltd|Limited|Company|Co|AG|SA|GmbH)\.?)\b'
        match = re.search(company_suffix_pattern, text)
        if match:
            result = match.group(1).strip()
            if len(result) < 60:  # Reasonable Länge
                logger.info(f"[SMART_EXTRACTOR] Company mit Suffix extrahiert: '{text[:60]}...' → '{result}'")
                return result
        
        return None
    
    def extract_mine_type_from_text(self, text: str) -> Optional[str]:
        """
        Extrahiert Minentyp aus beschreibenden Texten
        
        Beispiele:
        - "Open-Pit/1998//5000 T/0.15/Https://..." → "Open-Pit"
        - "Underground/Souterrain" → "Underground"
        - "Proposed Open-Pit/Projet À Ciel Ouvert" → "Open-Pit"
        """
        if not text or self.should_reject_value(text):
            return None
            
        text_lower = text.lower()
        
        # Prioritäts-Reihenfolge für Minentypen
        type_mappings = {
            'open-pit': 'Open-Pit',
            'open pit': 'Open-Pit',
            'openpit': 'Open-Pit',
            'surface': 'Open-Pit',
            'à ciel ouvert': 'Open-Pit',
            'tagebau': 'Tagebau',
            'underground': 'Underground',
            'untertage': 'Underground',
            'souterrain': 'Underground',
            'shaft': 'Underground',
            'schacht': 'Underground',
        }
        
        for keyword, standard_type in type_mappings.items():
            if keyword in text_lower:
                logger.info(f"[SMART_EXTRACTOR] Mine Type extrahiert: '{text[:60]}...' → '{standard_type}'")
                return standard_type
        
        return None
    
    def extract_activity_status_from_text(self, text: str) -> Optional[str]:
        """
        Extrahiert Aktivitätsstatus aus beschreibenden Texten
        
        Beispiele:
        - "Explorationsphase" → "Exploration"
        - "Currently Operating" → "aktiv"
        - "Mine Is Closed Since 1975" → "geschlossen"
        """
        if not text or self.should_reject_value(text):
            return None
            
        text_lower = text.lower().strip()
        
        # Direkte Synonym-Mappings
        status_mappings = {
            'explorationsphase': 'Exploration',
            'exploration': 'Exploration',
            'prospection': 'Exploration',
            'feasibility': 'Feasibility',
            'entwicklung': 'in Entwicklung',
            'development': 'in Entwicklung',
            'construction': 'Bau',
            'bau': 'Bau',
            'active': 'aktiv',
            'aktiv': 'aktiv',
            'operating': 'aktiv',
            'operational': 'aktiv',
            'in betrieb': 'aktiv',
            'exploitation': 'aktiv',
            'closed': 'geschlossen',
            'geschlossen': 'geschlossen',
            'fermé': 'geschlossen',
            'stillgelegt': 'geschlossen',
            'abandoned': 'geschlossen',
            'verlassen': 'geschlossen',
            'planned': 'geplant',
            'geplant': 'geplant',
            'proposed': 'geplant',
            'suspended': 'pausiert',
            'pausiert': 'pausiert',
            'care and maintenance': 'in Wartung',
            'wartung': 'in Wartung',
        }
        
        # Exakte Übereinstimmung zuerst
        if text_lower in status_mappings:
            result = status_mappings[text_lower]
            logger.info(f"[SMART_EXTRACTOR] Activity Status extrahiert: '{text}' → '{result}'")
            return result
        
        # Keyword-basierte Erkennung in längeren Texten
        for keyword, standard_status in status_mappings.items():
            if keyword in text_lower:
                logger.info(f"[SMART_EXTRACTOR] Activity Status aus Text: '{text[:60]}...' → '{standard_status}'")
                return standard_status
        
        return None
    
    def extract_region_from_text(self, text: str) -> Optional[str]:
        """
        Extrahiert Region aus beschreibenden Texten mit Normalisierung
        
        Beispiele:
        - "Québec/Nord-du-Québec" → "Quebec"
        - "Northern Quebec Region" → "Quebec"
        """
        if not text or self.should_reject_value(text):
            return None
            
        text = text.strip()
        
        # Quebec Normalisierung (häufigster Fall)
        quebec_variants = [
            'québec', 'quebec', 'nord-du-québec', 'nord du québec', 
            'northern quebec', 'northern québec'
        ]
        
        text_lower = text.lower()
        for variant in quebec_variants:
            if variant in text_lower:
                logger.info(f"[SMART_EXTRACTOR] Region normalisiert: '{text}' → 'Quebec'")
                return 'Quebec'
        
        # Andere bekannte Regionen
        region_mappings = {
            'south australia': 'South Australia',
            'western australia': 'Western Australia',
            'nevada': 'Nevada',
            'california': 'California',
            'ontario': 'Ontario',
            'british columbia': 'British Columbia',
            'antofagasta': 'Antofagasta',
            'papua': 'Papua',
            'south gobi': 'South Gobi',
        }
        
        for keyword, standard_region in region_mappings.items():
            if keyword in text_lower:
                logger.info(f"[SMART_EXTRACTOR] Region extrahiert: '{text}' → '{standard_region}'")
                return standard_region
        
        # Falls keine spezifische Erkennung, aber Text kurz und sauber → verwenden
        if len(text) < 50 and not self.is_sentence_like(text):
            # Einfache Bereinigung
            cleaned = re.sub(r'[/\\].*', '', text).strip()  # Entferne alles nach / oder \
            if cleaned and len(cleaned) > 2:
                logger.info(f"[SMART_EXTRACTOR] Region bereinigt: '{text}' → '{cleaned}'")
                return cleaned
        
        return None