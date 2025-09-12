#!/usr/bin/env python3
"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Normalisierter Database Manager für sauberes Schema
"""

import logging
import re
from datetime import datetime
from typing import Dict, Any, List, Optional, Tuple
from sqlalchemy import text
from sqlalchemy.exc import IntegrityError
from sqlalchemy.orm import Session
from minesearch.database.manager import DatabaseManager
from minesearch.value_normalizer import value_normalizer
from minesearch.smart_value_extractor import SmartValueExtractor

logger = logging.getLogger(__name__)

class NormalizedDatabaseManager(DatabaseManager):
    """
    Erweiterte Version des DatabaseManager für normalisiertes Schema
    """
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.smart_extractor = SmartValueExtractor()
    
    def normalize_mine_name(self, name: str) -> str:
        """Normalisiere Mine-Namen für Konsistenz und Deduplizierung"""
        if not name:
            return ""
        
        # Basis-Normalisierung
        normalized = name.strip().lower()
        
        # Akzente entfernen (éléonore → eleonore)
        accent_map = {
            'à': 'a', 'á': 'a', 'â': 'a', 'ã': 'a', 'ä': 'a', 'å': 'a',
            'è': 'e', 'é': 'e', 'ê': 'e', 'ë': 'e',
            'ì': 'i', 'í': 'i', 'î': 'i', 'ï': 'i',
            'ò': 'o', 'ó': 'o', 'ô': 'o', 'õ': 'o', 'ö': 'o',
            'ù': 'u', 'ú': 'u', 'û': 'u', 'ü': 'u',
            'ý': 'y', 'ÿ': 'y',
            'ñ': 'n', 'ç': 'c'
        }
        
        for accented, normal in accent_map.items():
            normalized = normalized.replace(accented, normal)
        
        # Entferne Common Mine Suffixes für bessere Deduplizierung  
        mine_suffixes = ['mine', 'project', 'deposit', 'property', 'complex', 'operation']
        words = normalized.split()
        filtered_words = [word for word in words if word not in mine_suffixes]
        
        if filtered_words:  # Mindestens ein Wort muss bleiben
            normalized = ' '.join(filtered_words)
        
        # Entferne Sonderzeichen außer Zahlen und Buchstaben
        normalized = re.sub(r'[^a-z0-9\s]', '', normalized)
        
        # Entferne doppelte Leerzeichen
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def normalize_company_name(self, name: str) -> str:
        """Normalisiere Unternehmensnamen"""
        if not name or name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None
        
        normalized = name.strip().lower()
        
        # Entferne häufige Firmen-Suffixe für bessere Deduplizierung
        company_suffixes = ['inc', 'ltd', 'corp', 'corporation', 'company', 'co', 'llc', 'gmbh', 'sa', 'ag']
        words = normalized.split()
        filtered_words = [word for word in words if word.rstrip('.,') not in company_suffixes]
        
        if filtered_words:
            normalized = ' '.join(filtered_words)
        
        # Grundlegende Bereinigung - BEHALTE Umlaute und Akzente
        # Entferne nur wirklich problematische Zeichen, behalte aber ä,ö,ü,é,è,etc.
        normalized = re.sub(r'[^\w\s&äöüßàáâãäåæçèéêëìíîïðñòóôõöøùúûüýþÿ]', '', normalized, flags=re.UNICODE)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def _normalize_mine_type(self, type_name: str) -> str:
        """Normalisiere Minentyp mit Synonym-Erkennung"""
        if not type_name:
            return None
        
        # Synonyme für Minentypen
        mine_type_synonyms = {
            # Open Pit Varianten
            'open-pit': 'Open-Pit',
            'open_pit': 'Open-Pit', 
            'openpit': 'Open-Pit',
            'open pit': 'Open-Pit',
            'surface': 'Open-Pit',
            'tagebau': 'Tagebau',
            
            # Underground Varianten
            'underground': 'Untertage',
            'untertage': 'Untertage',
            'untertagebau': 'Untertage',
            'subsurface': 'Untertage',
            
            # Andere Typen
            'placer': 'Placer',
            'quarry': 'Quarry',
            'dredging': 'Dredging',
            'in-situ-leaching': 'In-Situ-Leaching',
            'solution mining': 'In-Situ-Leaching'
        }
        
        # Normalisiere Input
        normalized = type_name.lower().strip()
        
        # Prüfe Synonyme
        if normalized in mine_type_synonyms:
            return mine_type_synonyms[normalized]
        
        # Fallback: Originalnamen mit korrigierter Gross-/Kleinschreibung
        return type_name.title()
    
    def _normalize_activity_status(self, status_name: str) -> str:
        """Normalisiere Aktivitätsstatus mit Synonym-Erkennung"""
        if not status_name:
            return None
        
        # Synonyme für Aktivitätsstatus
        activity_synonyms = {
            # Aktiv Varianten
            'active': 'aktiv',
            'aktiv': 'aktiv',
            'exploitation': 'aktiv',
            'operating': 'aktiv',
            'in betrieb': 'aktiv',
            
            # Geschlossen Varianten
            'closed': 'geschlossen',
            'geschlossen': 'geschlossen',
            'inactive': 'geschlossen',
            'stillgelegt': 'stillgelegt',
            
            # Entwicklung Varianten
            'development': 'in Entwicklung',
            'entwicklung': 'in Entwicklung',
            'in entwicklung': 'in Entwicklung',
            'under development': 'in Entwicklung',
            
            # Exploration Varianten
            'exploration': 'Exploration',
            'erkundung': 'Exploration',
            
            # Geplant Varianten
            'planned': 'geplant',
            'geplant': 'geplant',
            
            # Andere Status
            'feasibility': 'Feasibility',
            'pausiert': 'pausiert',
            'in wartung': 'in Wartung'
        }
        
        # Normalisiere Input
        normalized = status_name.lower().strip()
        
        # Prüfe Synonyme
        if normalized in activity_synonyms:
            return activity_synonyms[normalized]
        
        # Fallback: Originalnamen mit korrigierter Gross-/Kleinschreibung
        return status_name.title()

    def _calculate_confidence_score(self, field_name: str, raw_value: str, atomic_value: str) -> float:
        """
        Berechne dynamischen Confidence Score basierend auf verschiedenen Faktoren
        
        Args:
            field_name: Name des Feldes
            raw_value: Ursprünglicher Wert vor Bereinigung
            atomic_value: Bereinigter atomarer Wert
            
        Returns:
            Confidence Score zwischen 0.0 und 1.0
        """
        confidence = 0.5  # Basis-Confidence
        
        # 1. Faktor: Länge und Vollständigkeit des Wertes
        if len(atomic_value.strip()) > 0:
            confidence += 0.2
            
        if len(atomic_value.strip()) > 10:
            confidence += 0.1
            
        # 2. Faktor: Strukturierte vs. unstrukturierte Daten
        if field_name.lower() in ['country', 'land', 'region', 'state', 'province']:
            # Geografische Daten sind meist zuverlässig
            confidence += 0.2
            
        # 3. Faktor: Numerische Werte (Koordinaten, etc.)
        try:
            float(atomic_value)
            # Numerische Werte sind präzise
            confidence += 0.15
        except:
            pass
            
        # 4. Faktor: Bereinigungsaufwand (mehr Bereinigung = weniger Confidence)
        cleaning_impact = len(raw_value) - len(atomic_value)
        if cleaning_impact > 0:
            # Pro entferntes Zeichen reduziere Confidence leicht
            reduction = min(cleaning_impact * 0.01, 0.15)
            confidence -= reduction
            
        # 5. Faktor: Spezielle Felder mit hoher Zuverlässigkeit
        high_confidence_fields = [
            'name', 'mine_name', 'commodity', 'owner', 'operator', 
            'latitude', 'longitude', 'coordinates'
        ]
        if any(hcf in field_name.lower() for hcf in high_confidence_fields):
            confidence += 0.1
            
        # 6. Faktor: Template-ähnliche Werte (niedrigere Confidence)
        template_indicators = [
            '[placeholder', '[template', 'xxx', 'n/a', 'unknown', 'tbd'
        ]
        if any(indicator in atomic_value.lower() for indicator in template_indicators):
            confidence -= 0.3
            
        # Begrenze auf 0.1 bis 1.0
        return max(0.1, min(1.0, confidence))

    def _detect_template_value(self, field_name: str, atomic_value: str) -> bool:
        """
        Erkenne ob ein Wert ein Template/Platzhalter ist
        
        Args:
            field_name: Name des Feldes
            atomic_value: Zu prüfender Wert
            
        Returns:
            True wenn Template-Wert erkannt wird
        """
        if not atomic_value or not atomic_value.strip():
            return False
            
        value_lower = atomic_value.lower().strip()
        
        # 1. Offensichtliche Template-Indikatoren
        template_indicators = [
            'template', 'placeholder', 'example', 'sample',
            '[template', '[placeholder', '[example',
            'xxx', 'yyy', 'zzz',
            'n/a', 'n.a.', 'not available', 'not applicable',
            'tbd', 'to be determined', 'to be defined',
            'unknown', 'unbekannt', 'nicht bekannt',
            'pending', 'ausstehend', 
            'insert', 'enter', 'add',
            'your ', 'dein ', 'ihre ',
            '[insert', '[enter', '[add'
        ]
        
        for indicator in template_indicators:
            if indicator in value_lower:
                return True
                
        # 2. Wiederholende Zeichen (xxx, 999, ---)
        if len(set(atomic_value.strip())) == 1 and len(atomic_value.strip()) >= 3:
            return True
            
        # 3. Brackets um gesamten Wert
        if atomic_value.startswith('[') and atomic_value.endswith(']'):
            return True
            
        # 4. Spezielle Muster für bestimmte Felder
        if field_name.lower() in ['email', 'e-mail', 'contact']:
            # Template-E-Mails
            if 'example.com' in value_lower or 'test@' in value_lower:
                return True
                
        if field_name.lower() in ['phone', 'telefon', 'telephone']:
            # Template-Telefonnummern
            if value_lower in ['123-456-7890', '+1-xxx-xxx-xxxx', '000-000-0000']:
                return True
                
        # 5. Koordinaten-Templates
        if field_name.lower() in ['latitude', 'longitude', 'lat', 'lon', 'coordinates']:
            if value_lower in ['0.0', '0', '00.0000', 'xx.xxxx']:
                return True
                
        return False
    
    def get_or_create_company(self, company_name: str, db_session: Optional[Session] = None) -> Optional[int]:
        """Hole oder erstelle Unternehmen mit Smart Extractor für Satz-zu-Wert Konvertierung"""
        if not company_name or company_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None
        
        # NEUE LOGIK: Smart Extractor für Sätze
        if self.smart_extractor.is_sentence_like(company_name) or self.smart_extractor.should_reject_value(company_name):
            logger.warning(f"[SMART_COMPANY] Satz erkannt, verwende Smart Extractor: '{company_name[:60]}...'")
            extracted_company = self.smart_extractor.extract_company_from_text(company_name)
            if not extracted_company:
                logger.warning(f"[SMART_COMPANY] Kein Firmenname extrahierbar aus: '{company_name[:60]}...' → ABGELEHNT")
                return None
            company_name = extracted_company
            logger.info(f"[SMART_COMPANY] Erfolgreich extrahiert: '{extracted_company}'")
        
        normalized_name = self.normalize_company_name(company_name)
        if not normalized_name:
            return None
        
        # Externe Transaktion verwenden, falls bereitgestellt
        if db_session is not None:
            # Suche existierende Firma (normalized_name für Vergleich, aber nicht in DB)
            result = db_session.execute(text("""
                SELECT id FROM companies 
                WHERE LOWER(name) = :normalized_name
                LIMIT 1
            """), {'normalized_name': normalized_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = db_session.execute(text("""
                INSERT INTO companies (name) 
                VALUES (:name)
            """), {
                'name': company_name
            })
            db_session.flush()
            return insert_result.lastrowid
        
        # Eigene Session verwalten
        with self.get_session() as session:
            # Suche existierende Firma (normalized_name für Vergleich, aber nicht in DB)
            result = session.execute(text("""
                SELECT id FROM companies 
                WHERE LOWER(name) = :normalized_name
                LIMIT 1
            """), {'normalized_name': normalized_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # Erstelle neue Firma
            insert_result = session.execute(text("""
                INSERT INTO companies (name) 
                VALUES (:name)
            """), {
                'name': company_name
            })
            session.commit()
            return insert_result.lastrowid
    
    def get_or_create_country(self, country_name: str, db_session: Optional[Session] = None) -> Optional[int]:
        """Hole oder erstelle Land und gib ID zurück"""
        if not country_name or country_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None
            
        # Externe Transaktion verwenden, falls bereitgestellt
        if db_session is not None:
            session = db_session
            result = session.execute(text("""
                SELECT id FROM countries WHERE name = :country_name LIMIT 1
            """), {'country_name': country_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO countries (name) VALUES (:country_name)
            """), {'country_name': country_name})
            session.flush()
            return insert_result.lastrowid
        
        # Eigene Session verwalten
        with self.get_session() as session:
            result = session.execute(text("""
                SELECT id FROM countries WHERE name = :country_name LIMIT 1
            """), {'country_name': country_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO countries (name) VALUES (:country_name)
            """), {'country_name': country_name})
            session.commit()
            return insert_result.lastrowid

    def get_or_create_region(self, region_name: str, country_id: Optional[int] = None, db_session: Optional[Session] = None) -> Optional[int]:
        """Hole oder erstelle Region mit Smart Extractor für Satz-zu-Wert Konvertierung"""
        if not region_name or region_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None
            
        # NEUE LOGIK: Smart Extractor für Sätze
        if self.smart_extractor.is_sentence_like(region_name) or self.smart_extractor.should_reject_value(region_name):
            logger.warning(f"[SMART_REGION] Satz erkannt, verwende Smart Extractor: '{region_name[:60]}...'")
            extracted_region = self.smart_extractor.extract_region_from_text(region_name)
            if not extracted_region:
                logger.warning(f"[SMART_REGION] Keine Region extrahierbar aus: '{region_name[:60]}...' → ABGELEHNT")
                return None
            region_name = extracted_region
            logger.info(f"[SMART_REGION] Erfolgreich extrahiert: '{extracted_region}'")
            
        # Externe Transaktion verwenden, falls bereitgestellt
        if db_session is not None:
            session = db_session
            result = session.execute(text("""
                SELECT id FROM regions WHERE name = :region_name LIMIT 1
            """), {'region_name': region_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO regions (name, country_id) VALUES (:region_name, :country_id)
            """), {'region_name': region_name, 'country_id': country_id})
            session.flush()
            return insert_result.lastrowid
        
        # Eigene Session verwalten
        with self.get_session() as session:
            result = session.execute(text("""
                SELECT id FROM regions WHERE name = :region_name LIMIT 1
            """), {'region_name': region_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO regions (name, country_id) VALUES (:region_name, :country_id)
            """), {'region_name': region_name, 'country_id': country_id})
            session.commit()
            return insert_result.lastrowid

    def get_or_create_mine_type(self, type_name: str, db_session: Optional[Session] = None) -> Optional[int]:
        """Hole oder erstelle Minentyp mit Smart Extractor für Satz-zu-Wert Konvertierung"""
        if not type_name:
            return None
        
        # NEUE LOGIK: Smart Extractor für Sätze
        if self.smart_extractor.is_sentence_like(type_name) or self.smart_extractor.should_reject_value(type_name):
            logger.warning(f"[SMART_MINE_TYPE] Satz erkannt, verwende Smart Extractor: '{type_name[:60]}...'")
            extracted_type = self.smart_extractor.extract_mine_type_from_text(type_name)
            if not extracted_type:
                logger.warning(f"[SMART_MINE_TYPE] Kein Minentyp extrahierbar aus: '{type_name[:60]}...' → ABGELEHNT")
                return None
            type_name = extracted_type
            logger.info(f"[SMART_MINE_TYPE] Erfolgreich extrahiert: '{extracted_type}'")
        
        # INTELLIGENTE NORMALISIERUNG: Synonyme erkennen
        normalized_type = self._normalize_mine_type(type_name)
        if not normalized_type:
            return None
            
        # Externe Transaktion verwenden, falls bereitgestellt
        if db_session is not None:
            session = db_session
            # Suche nach dem normalisierten Namen
            result = session.execute(text("""
                SELECT id FROM mine_types WHERE name = :type_name LIMIT 1
            """), {'type_name': normalized_type})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # Falls nicht gefunden, erstelle mit normalisiertem Namen
            insert_result = session.execute(text("""
                INSERT INTO mine_types (name) VALUES (:type_name)
            """), {'type_name': normalized_type})
            session.flush()
            return insert_result.lastrowid
        
        # Eigene Session verwalten
        with self.get_session() as session:
            # Suche nach dem normalisierten Namen
            result = session.execute(text("""
                SELECT id FROM mine_types WHERE name = :type_name LIMIT 1
            """), {'type_name': normalized_type})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # Falls nicht gefunden, erstelle mit normalisiertem Namen
            insert_result = session.execute(text("""
                INSERT INTO mine_types (name) VALUES (:type_name)
            """), {'type_name': normalized_type})
            session.commit()
            return insert_result.lastrowid

    def get_or_create_commodity(self, commodity_name: str, db_session: Optional[Session] = None) -> Optional[int]:
        """Hole oder erstelle Rohstoff mit Smart Extractor für Satz-zu-Wert Konvertierung"""
        if not commodity_name or commodity_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None
        
        # NEUE LOGIK: Smart Extractor für Sätze
        if self.smart_extractor.is_sentence_like(commodity_name) or self.smart_extractor.should_reject_value(commodity_name):
            logger.warning(f"[SMART_COMMODITY] Satz erkannt, verwende Smart Extractor: '{commodity_name[:60]}...'")
            extracted_commodity = self.smart_extractor.extract_commodity_from_text(commodity_name)
            if not extracted_commodity:
                logger.warning(f"[SMART_COMMODITY] Kein Rohstoff extrahierbar aus: '{commodity_name[:60]}...' → ABGELEHNT")
                return None
            commodity_name = extracted_commodity
            logger.info(f"[SMART_COMMODITY] Erfolgreich extrahiert: '{extracted_commodity}'")
        
        # Synonyme für Rohstoffe
        commodity_synonyms = {
            'gold': 'Gold',
            'kupfer': 'Kupfer', 
            'copper': 'Kupfer',
            'silber': 'Silber',
            'silver': 'Silber',
            'eisenerz': 'Eisenerz',
            'iron ore': 'Eisenerz',
            'kohle': 'Kohle',
            'coal': 'Kohle',
            'nickel': 'Nickel',
            'zink': 'Zink',
            'zinc': 'Zink',
            'blei': 'Blei',
            'lead': 'Blei',
            'platin': 'Platin',
            'platinum': 'Platin',
            'palladium': 'Palladium',
            'uran': 'Uran',
            'uranium': 'Uran',
            'lithium': 'Lithium',
            'diamanten': 'Diamanten',
            'diamonds': 'Diamanten'
        }
        
        # Normalisiere Input
        normalized = commodity_name.lower().strip()
        
        # Prüfe Synonyme
        if normalized in commodity_synonyms:
            commodity_name = commodity_synonyms[normalized]
        else:
            # Zusätzliche Validierung für unbekannte Werte
            if len(commodity_name) > 50:
                logger.warning(f"[SMART_COMMODITY] Unbekannter Rohstoff zu lang → ABGELEHNT: '{commodity_name[:60]}...'")
                return None
            # Fallback: Title Case
            commodity_name = commodity_name.title()
            
        # Externe Transaktion verwenden, falls bereitgestellt
        if db_session is not None:
            session = db_session
            result = session.execute(text("""
                SELECT id FROM commodities WHERE name = :commodity_name LIMIT 1
            """), {'commodity_name': commodity_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # Falls nicht gefunden, erstelle neuen Rohstoff
            insert_result = session.execute(text("""
                INSERT INTO commodities (name) VALUES (:commodity_name)
            """), {'commodity_name': commodity_name})
            session.flush()
            return insert_result.lastrowid
        
        # Eigene Session verwalten
        with self.get_session() as session:
            result = session.execute(text("""
                SELECT id FROM commodities WHERE name = :commodity_name LIMIT 1
            """), {'commodity_name': commodity_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO commodities (name) VALUES (:commodity_name)
            """), {'commodity_name': commodity_name})
            session.commit()
            return insert_result.lastrowid

    def get_or_create_activity_status(self, status_name: str, db_session: Optional[Session] = None) -> Optional[int]:
        """Hole oder erstelle Aktivitätsstatus mit Smart Extractor für Satz-zu-Wert Konvertierung"""
        if not status_name:
            return None
        
        # NEUE LOGIK: Smart Extractor für Sätze
        if self.smart_extractor.is_sentence_like(status_name) or self.smart_extractor.should_reject_value(status_name):
            logger.warning(f"[SMART_ACTIVITY] Satz erkannt, verwende Smart Extractor: '{status_name[:60]}...'")
            extracted_status = self.smart_extractor.extract_activity_status_from_text(status_name)
            if not extracted_status:
                logger.warning(f"[SMART_ACTIVITY] Kein Status extrahierbar aus: '{status_name[:60]}...' → ABGELEHNT")
                return None
            status_name = extracted_status
            logger.info(f"[SMART_ACTIVITY] Erfolgreich extrahiert: '{extracted_status}'")
        
        # INTELLIGENTE NORMALISIERUNG: Synonyme erkennen
        normalized_status = self._normalize_activity_status(status_name)
        if not normalized_status:
            return None
            
        # Externe Transaktion verwenden, falls bereitgestellt
        if db_session is not None:
            session = db_session
            # Suche nach dem normalisierten Namen
            result = session.execute(text("""
                SELECT id FROM activity_statuses WHERE status = :status_name LIMIT 1
            """), {'status_name': normalized_status})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # Falls nicht gefunden, erstelle mit normalisiertem Namen
            insert_result = session.execute(text("""
                INSERT INTO activity_statuses (status) VALUES (:status_name)
            """), {'status_name': normalized_status})
            session.flush()
            return insert_result.lastrowid
        
        # Eigene Session verwalten
        with self.get_session() as session:
            result = session.execute(text("""
                SELECT id FROM activity_statuses WHERE status = :status_name LIMIT 1
            """), {'status_name': normalized_status})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = session.execute(text("""
                INSERT INTO activity_statuses (status) VALUES (:status_name)
            """), {'status_name': normalized_status})
            session.commit()
            return insert_result.lastrowid

    def get_or_create_mine(self, mine_name: str, structured_data: Dict[str, Any] = None, db_session: Optional[Session] = None) -> int:
        """
        Erstellt oder findet eine Mine basierend auf dem Namen.
        
        NEUES SCHEMA (04.09.2025): 
        - Mines Tabelle enthält nur noch: ID, Name, Country, Region
        - Alle anderen Daten (Koordinaten, Fläche, etc.) werden in mine_data_fields gespeichert
        
        Args:
            mine_name: Name der Mine
            structured_data: Optional - zusätzliche Daten für Region/Land
            db_session: Optional - vorhandene DB-Session verwenden
            
        Returns:
            Mine-ID
        """
        normalized_name = self.normalize_mine_name(mine_name)
        structured_data = structured_data or {}
        
        # Wenn eine Session übergeben wurde, verwende sie
        if db_session:
            session = db_session
            
            # Suche existierende Mine
            result = session.execute(text("""
                SELECT id FROM mines 
                WHERE name = :mine_name
                LIMIT 1
            """), {'mine_name': mine_name})
            
            existing = result.fetchone()
            if existing:
                return existing[0]
            
            # Extrahiere nur Region für das neue vereinfachte Schema
            region = structured_data.get('Region') or structured_data.get('region')
            
            # Hole IDs für Country und Region
            country = structured_data.get('Country') or structured_data.get('country')
            country_id = None
            region_id = None
            
            if country:
                country_id = self.get_or_create_country(country, db_session=session)
                if region and country_id:
                    region_id = self.get_or_create_region(region, country_id, db_session=session)
            
            # Erstelle Mine nur mit Name, Country, Region
            insert_result = session.execute(text("""
                INSERT INTO mines 
                (name, country_id, region_id)
                VALUES (:name, :country_id, :region_id)
            """), {
                'name': mine_name,
                'country_id': country_id,
                'region_id': region_id
            })
            session.flush()
            logger.info(f"✅ Neue Mine erstellt: {mine_name} (ID: {insert_result.lastrowid})")
            return insert_result.lastrowid
        
        # Ohne externe Session: eigene Session öffnen und committen
        with self.get_session() as session_local:
            # Suche existierende Mine
            result = session_local.execute(text("""
                SELECT id FROM mines 
                WHERE name = :mine_name
                LIMIT 1
            """), {'mine_name': mine_name})
            
            existing = result.fetchone()
            if existing:
                return existing[0]
            
            # Extrahiere nur Region für das neue vereinfachte Schema
            region = structured_data.get('Region') or structured_data.get('region')
            
            # Hole IDs für Country und Region
            country = structured_data.get('Country') or structured_data.get('country')
            country_id = None
            region_id = None
            
            if country:
                country_id = self.get_or_create_country(country, db_session=session_local)
                if region and country_id:
                    region_id = self.get_or_create_region(region, country_id, db_session=session_local)
            
            # Erstelle Mine nur mit Name, Country, Region
            insert_result = session_local.execute(text("""
                INSERT INTO mines 
                (name, country_id, region_id)
                VALUES (:name, :country_id, :region_id)
            """), {
                'name': mine_name,
                'country_id': country_id,
                'region_id': region_id
            })
            
            # CRITICAL FIX 05.09.2025: Commit die Transaktion!
            session_local.commit()
            
            logger.info(f"✅ Neue Mine erstellt: {mine_name} (ID: {insert_result.lastrowid})")
            return insert_result.lastrowid
    
    def save_mine_field_data(self, mine_id: int, search_result_id: int, structured_data: Dict[str, Any], 
                           model_used: str, sources: List[Dict[str, Any]], session_id: str = None, db_session: Optional[Session] = None):
        """Speichere atomare Feldwerte in mine_data_fields - ECHTE 3NF v4.0.0 mit field_type"""
        logger.info(f"[FIELD_SAVE_DEBUG] Called with {len(structured_data) if structured_data else 0} fields, session_id: {session_id}")
        if not structured_data:
            logger.warning("[FIELD_SAVE_DEBUG] No structured_data - returning early")
            return
        
        # KRITISCHER FIX 29.08.2025: Stelle sicher dass field_definitions initialisiert ist
        self._ensure_field_definitions_initialized()
        
        source_name = None
        if sources and len(sources) > 0:
            # NORMALISIERUNG FIX: Handle sowohl String- als auch Dict-Sources
            first_source = sources[0]
            if isinstance(first_source, dict):
                source_name = first_source.get('name') or first_source.get('url')
            else:
                source_name = str(first_source)
        
        # KRITISCHER FIX 29.08.2025: Logik-Reparatur für Session-Handling
        if db_session is not None:
            # Mit externer Session (wird von aufrufender Funktion committed)
            session = db_session
            for field_name, field_value in structured_data.items():
                # FILTER 05.09.2025: Ignoriere System-Felder und Quellenangaben
                if field_name.startswith('_') or field_name in ['source_mapping', 'metadata', 'Quellenangaben', 'sources', 'references']:
                    logger.info(f"System-Feld/Quellenfeld übersprungen: {field_name}")
                    continue
                
                if not field_value or field_value in ['Nicht gefunden', 'Not found', 'X']:
                    continue
                
                # ATOMARE WERTE FILTER 05.09.2025: Nur primitive Datentypen erlauben
                if isinstance(field_value, (dict, list, set, tuple)):
                    logger.warning(f"Nicht-atomares Feld übersprungen: {field_name} = {type(field_value)}")
                    continue
                
                # Value-Normalisierung für atomare Speicherung
                raw_value = str(field_value)
                
                # VERBESSERTE QUELLENREFERENZ-BEREINIGUNG 05.09.2025
                import re
                atomic_value = raw_value
                
                # Entferne alle Quellenreferenzen: [1], [2,3], [1] Text [2], etc.
                atomic_value = re.sub(r'\[\d+(,\s*\d+)*\]', '', atomic_value)
                
                # Entferne mehrzeilige Quellenangaben mit Nummerierung
                atomic_value = re.sub(r'\[\d+\]\s*[^\n]*\n?', '', atomic_value, flags=re.MULTILINE)
                
                # Bereinige überschüssige Whitespace und Zeilenwechsel
                atomic_value = re.sub(r'\n+', ' ', atomic_value)
                atomic_value = re.sub(r'\s+', ' ', atomic_value).strip()
                
                # Überspringe Felder die nur aus Referenzen bestanden
                if not atomic_value or atomic_value in ['', ' ', '\n']:
                    logger.info(f"Feld nach Bereinigung leer übersprungen: {field_name}")
                    continue
                
                normalized_value = atomic_value
                numeric_value = None
                unit = None
                
                # NEUE 3NF v4.0.0: Feld-Typ-Bestimmung und Normalisierung
                field_type = self._determine_field_type(field_name)
                
                # Inizialize alle Werte
                commodity_id = None
                company_id = None
                activity_status_id = None
                mine_type_id = None
                country_id = None
                region_id = None
                primitive_value = None
                
                if field_type == 'normalized':
                    logger.info(f"[FIELD_TYPE] '{field_name}' -> NORMALIZED")
                    
                    # Rohstoff-Normalisierung
                    if 'rohstoffabbau' in field_name.lower() or 'commodity' in field_name.lower():
                        commodity_id = self.get_or_create_commodity(atomic_value, db_session=session)
                        logger.info(f"[NORMALIZATION] Commodity '{atomic_value}' -> ID {commodity_id}")
                    
                    # Firmen-Normalisierung  
                    elif 'eigentümer' in field_name.lower() or 'betreiber' in field_name.lower() or 'owner' in field_name.lower() or 'operator' in field_name.lower():
                        company_type = 'owner' if 'eigentümer' in field_name.lower() or 'owner' in field_name.lower() else 'operator'
                        company_id = self.get_or_create_company(atomic_value, db_session=session)
                        logger.info(f"[NORMALIZATION] Company '{atomic_value}' ({company_type}) -> ID {company_id}")
                    
                    # Status-Normalisierung
                    elif 'aktivitätsstatus' in field_name.lower() or 'activity' in field_name.lower() or 'status' in field_name.lower():
                        activity_status_id = self.get_or_create_activity_status(atomic_value, db_session=session)
                        logger.info(f"[NORMALIZATION] Status '{atomic_value}' -> ID {activity_status_id}")
                    
                    # Minentyp-Normalisierung
                    elif 'minentyp' in field_name.lower() or 'mine_type' in field_name.lower() or 'type' in field_name.lower():
                        mine_type_id = self.get_or_create_mine_type(atomic_value, db_session=session)
                        logger.info(f"[NORMALIZATION] Mine Type '{atomic_value}' -> ID {mine_type_id}")
                    
                    # Country-Normalisierung
                    elif field_name.lower() == 'country' or 'country' in field_name.lower():
                        country_id = self.get_or_create_country(atomic_value, db_session=session)
                        logger.info(f"[NORMALIZATION] Country '{atomic_value}' -> ID {country_id}")
                    
                    # Region-Normalisierung
                    elif field_name.lower() == 'region' or 'region' in field_name.lower():
                        # Hole Country für Region-Zuordnung
                        country_for_region = None
                        if country_id:
                            country_for_region = country_id
                        else:
                            # Versuche Country aus structured_data zu finden
                            country_value = structured_data.get('Country') or structured_data.get('country')
                            if country_value:
                                country_for_region = self.get_or_create_country(country_value, db_session=session)
                        
                        region_id = self.get_or_create_region(atomic_value, country_for_region, db_session=session)
                        logger.info(f"[NORMALIZATION] Region '{atomic_value}' -> ID {region_id}")
                    
                    # Wenn keine Normalisierung gefunden, Fallback zu primitive
                    if not any([commodity_id, company_id, activity_status_id, mine_type_id, country_id, region_id]):
                        logger.warning(f"[FIELD_TYPE] '{field_name}' als normalized klassifiziert aber keine Normalisierung gefunden - Fallback zu primitive")
                        field_type = 'primitive'
                        primitive_value = atomic_value
                    
                else:
                    # field_type == 'primitive'
                    logger.info(f"[FIELD_TYPE] '{field_name}' -> PRIMITIVE")
                    primitive_value = atomic_value
                
                # Erkenne Template-Werte mit neuer Methode
                is_template = self._detect_template_value(field_name, atomic_value)
                validation_status = 'template' if is_template else 'valid'
                
                if is_template:
                    logger.warning(f"Template-Wert erkannt: {field_name} = {atomic_value}")
                
                # Fallback: Prüfe auch mit value_normalizer falls vorhanden
                if value_normalizer and not is_template:
                    try:
                        validation_result = value_normalizer.validate_field_value(field_name, field_value)
                        if not validation_result.get('is_valid', True):
                            is_template = True
                            validation_status = 'template'
                            logger.warning(f"Value-Normalizer Template erkannt: {field_name} = {field_value}")
                    except:
                        pass
                
                # Numerische Werte extrahieren (aus bereinigtem Wert)
                if isinstance(field_value, (int, float)):
                    numeric_value = float(field_value)
                else:
                    # Versuche numerischen Wert aus bereinigtem String zu extrahieren
                    numeric_match = re.search(r'[\d,\.]+', atomic_value)
                    if numeric_match:
                        try:
                            numeric_str = numeric_match.group().replace(',', '.')
                            numeric_value = float(numeric_str)
                        except (ValueError, AttributeError):
                            pass
                
                # Einheit extrahieren (z.B. "150 Millionen CAD" → unit: "CAD") - aus bereinigtem Wert
                if isinstance(atomic_value, str):
                    unit_patterns = [
                        r'(CAD|USD|EUR|AUD|GBP)$',
                        r'(kg|t|oz|g)$',
                        r'(km|m|cm)$',
                        r'(qkm|ha)$'
                    ]
                    for pattern in unit_patterns:
                        match = re.search(pattern, atomic_value, re.IGNORECASE)
                        if match:
                            unit = match.group(1).upper()
                            break
                
                # DYNAMISCHE CONFIDENCE-BERECHNUNG 05.09.2025
                confidence_score = self._calculate_confidence_score(field_name, raw_value, atomic_value)
                
                # Speichere mit neuer 3NF Struktur
                self._insert_mine_data_field_3nf(
                    session,
                    {
                        'search_result_id': search_result_id,
                        'mine_id': mine_id,
                        'field_name': field_name,
                        'field_type': field_type,
                        'session_id': session_id,
                        'confidence_score': confidence_score,
                        'is_template_value': is_template,
                        'validation_status': validation_status,
                        'source_name': source_name,
                        'model_used': model_used,
                        'extraction_timestamp': datetime.now(),
                        'model_id': self._get_or_create_ai_model_id(session, model_used),
                        'source_id': self._get_source_id_by_name(session, source_name),
                        # Für NORMALIZED Felder: nur IDs
                        'commodity_id': commodity_id,
                        'company_id': company_id,
                        'activity_status_id': activity_status_id,
                        'mine_type_id': mine_type_id,
                        'country_id': country_id,
                        'region_id': region_id,
                        # Für PRIMITIVE Felder: nur Wert
                        'primitive_value': primitive_value,
                        'numeric_value': numeric_value,
                        'unit': unit
                    },
                    actor=model_used,
                    reason="save_mine_field_data"
                )
            session.flush()
            logger.info(f"✅ {len(structured_data)} Feldwerte gespeichert für Mine ID {mine_id}")
            return
        
        # Ohne externe Session: eigene Session verwenden
        with self.get_session() as local_session:
            for field_name, field_value in structured_data.items():
                # FILTER 05.09.2025: Ignoriere System-Felder und Quellenangaben (identisch zu erstem Pfad)
                if field_name.startswith('_') or field_name in ['source_mapping', 'metadata', 'Quellenangaben', 'sources', 'references']:
                    logger.info(f"System-Feld/Quellenfeld übersprungen: {field_name}")
                    continue
                
                if not field_value or field_value in ['Nicht gefunden', 'Not found', 'X']:
                    continue
                
                # ATOMARE WERTE FILTER 05.09.2025: Nur primitive Datentypen erlauben
                if isinstance(field_value, (dict, list, set, tuple)):
                    logger.warning(f"Nicht-atomares Feld übersprungen: {field_name} = {type(field_value)}")
                    continue
                
                # Value-Normalisierung für atomare Speicherung (identisch zu erstem Pfad)
                raw_value = str(field_value)
                
                # VERBESSERTE QUELLENREFERENZ-BEREINIGUNG 05.09.2025 (identisch)
                import re
                atomic_value = raw_value
                
                # Entferne alle Quellenreferenzen: [1], [2,3], [1] Text [2], etc.
                atomic_value = re.sub(r'\[\d+(,\s*\d+)*\]', '', atomic_value)
                
                # Entferne mehrzeilige Quellenangaben mit Nummerierung
                atomic_value = re.sub(r'\[\d+\]\s*[^\n]*\n?', '', atomic_value, flags=re.MULTILINE)
                
                # Bereinige überschüssige Whitespace und Zeilenwechsel
                atomic_value = re.sub(r'\n+', ' ', atomic_value)
                atomic_value = re.sub(r'\s+', ' ', atomic_value).strip()
                
                # Überspringe Felder die nur aus Referenzen bestanden
                if not atomic_value or atomic_value in ['', ' ', '\n']:
                    logger.info(f"Feld nach Bereinigung leer übersprungen: {field_name}")
                    continue
                normalized_value = atomic_value
                numeric_value = None
                unit = None
                
                # Erkenne Template-Werte mit neuer Methode
                is_template = self._detect_template_value(field_name, atomic_value)
                validation_status = 'template' if is_template else 'valid'
                
                if is_template:
                    logger.warning(f"Template-Wert erkannt: {field_name} = {atomic_value}")
                
                # Fallback: Prüfe auch mit value_normalizer falls vorhanden
                if value_normalizer and not is_template:
                    try:
                        validation_result = value_normalizer.validate_field_value(field_name, field_value)
                        if not validation_result.get('is_valid', True):
                            is_template = True
                            validation_status = 'template'
                            logger.warning(f"Template-Wert erkannt: {field_name} = {field_value}")
                    except:
                        pass
                if isinstance(field_value, (int, float)):
                    numeric_value = float(field_value)
                else:
                    numeric_match = re.search(r'[\d,\.]+', atomic_value)
                    if numeric_match:
                        try:
                            numeric_str = numeric_match.group().replace(',', '.')
                            numeric_value = float(numeric_str)
                        except (ValueError, AttributeError):
                            pass
                if isinstance(atomic_value, str):
                    unit_patterns = [
                        r'(CAD|USD|EUR|AUD|GBP)$',
                        r'(kg|t|oz|g)$',
                        r'(km|m|cm)$',
                        r'(qkm|ha)$'
                    ]
                    for pattern in unit_patterns:
                        match = re.search(pattern, atomic_value, re.IGNORECASE)
                        if match:
                            unit = match.group(1).upper()
                            break
                # DYNAMISCHE CONFIDENCE-BERECHNUNG 05.09.2025 (identisch zu erstem Pfad)
                confidence_score = self._calculate_confidence_score(field_name, raw_value, atomic_value)
                    
                # NEUE 3NF v4.0.0: Identische Feld-Typ-Bestimmung wie im ersten Pfad
                field_type = self._determine_field_type(field_name)
                
                # Initialize alle Werte
                commodity_id = None
                company_id = None
                activity_status_id = None
                mine_type_id = None
                country_id = None
                region_id = None
                primitive_value = None
                
                if field_type == 'normalized':
                    logger.info(f"[FIELD_TYPE] '{field_name}' -> NORMALIZED")
                    
                    # Rohstoff-Normalisierung
                    if 'rohstoffabbau' in field_name.lower() or 'commodity' in field_name.lower():
                        commodity_id = self.get_or_create_commodity(atomic_value, db_session=local_session)
                        logger.info(f"[NORMALIZATION] Commodity '{atomic_value}' -> ID {commodity_id}")
                    
                    # Firmen-Normalisierung  
                    elif 'eigentümer' in field_name.lower() or 'betreiber' in field_name.lower() or 'owner' in field_name.lower() or 'operator' in field_name.lower():
                        company_type = 'owner' if 'eigentümer' in field_name.lower() or 'owner' in field_name.lower() else 'operator'
                        company_id = self.get_or_create_company(atomic_value, db_session=local_session)
                        logger.info(f"[NORMALIZATION] Company '{atomic_value}' ({company_type}) -> ID {company_id}")
                    
                    # Status-Normalisierung
                    elif 'aktivitätsstatus' in field_name.lower() or 'activity' in field_name.lower() or 'status' in field_name.lower():
                        activity_status_id = self.get_or_create_activity_status(atomic_value, db_session=local_session)
                        logger.info(f"[NORMALIZATION] Status '{atomic_value}' -> ID {activity_status_id}")
                    
                    # Minentyp-Normalisierung
                    elif 'minentyp' in field_name.lower() or 'mine_type' in field_name.lower() or 'type' in field_name.lower():
                        mine_type_id = self.get_or_create_mine_type(atomic_value, db_session=local_session)
                        logger.info(f"[NORMALIZATION] Mine Type '{atomic_value}' -> ID {mine_type_id}")
                    
                    # Country-Normalisierung
                    elif field_name.lower() == 'country' or 'country' in field_name.lower():
                        country_id = self.get_or_create_country(atomic_value, db_session=local_session)
                        logger.info(f"[NORMALIZATION] Country '{atomic_value}' -> ID {country_id}")
                    
                    # Region-Normalisierung
                    elif field_name.lower() == 'region' or 'region' in field_name.lower():
                        # Hole Country für Region-Zuordnung
                        country_for_region = None
                        if country_id:
                            country_for_region = country_id
                        else:
                            # Versuche Country aus structured_data zu finden
                            country_value = structured_data.get('Country') or structured_data.get('country')
                            if country_value:
                                country_for_region = self.get_or_create_country(country_value, db_session=local_session)
                        
                        region_id = self.get_or_create_region(atomic_value, country_for_region, db_session=local_session)
                        logger.info(f"[NORMALIZATION] Region '{atomic_value}' -> ID {region_id}")
                    
                    # Wenn keine Normalisierung gefunden, Fallback zu primitive
                    if not any([commodity_id, company_id, activity_status_id, mine_type_id, country_id, region_id]):
                        logger.warning(f"[FIELD_TYPE] '{field_name}' als normalized klassifiziert aber keine Normalisierung gefunden - Fallback zu primitive")
                        field_type = 'primitive'
                        primitive_value = atomic_value
                    
                else:
                    # field_type == 'primitive'
                    logger.info(f"[FIELD_TYPE] '{field_name}' -> PRIMITIVE")
                    primitive_value = atomic_value
                
                # Speichere mit neuer 3NF Struktur (identisch zum ersten Pfad)
                self._insert_mine_data_field_3nf(
                    local_session,
                    {
                        'search_result_id': search_result_id,
                        'mine_id': mine_id,
                        'field_name': field_name,
                        'field_type': field_type,
                        'session_id': session_id,
                        'confidence_score': confidence_score,
                        'is_template_value': is_template,
                        'validation_status': validation_status,
                        'source_name': source_name,
                        'model_used': model_used,
                        'extraction_timestamp': datetime.now(),
                        'model_id': self._get_or_create_ai_model_id(local_session, model_used),
                        'source_id': self._get_source_id_by_name(local_session, source_name),
                        # Für NORMALIZED Felder: nur IDs
                        'commodity_id': commodity_id,
                        'company_id': company_id,
                        'activity_status_id': activity_status_id,
                        'mine_type_id': mine_type_id,
                        'country_id': country_id,
                        'region_id': region_id,
                        # Für PRIMITIVE Felder: nur Wert
                        'primitive_value': primitive_value,
                        'numeric_value': numeric_value,
                        'unit': unit
                    },
                    actor=model_used,
                    reason="save_mine_field_data"
                )
            local_session.commit()
            logger.info(f"✅ {len(structured_data)} Feldwerte gespeichert für Mine ID {mine_id}")
    
    def _get_or_create_ai_model_id(self, session: Session, model_used: str) -> Optional[int]:
        """Hole oder erstelle ai_model_id für gegebenes model_used."""
        try:
            # Versuche direkte Zuordnung über full_model_id
            result = session.execute(text("""
                SELECT id FROM ai_models 
                WHERE full_model_id = :model_used
                LIMIT 1
            """), {'model_used': model_used}).fetchone()
            
            if result:
                return result[0]
            
            # Versuche Zuordnung über model_name falls model_used nur der Name ist
            result = session.execute(text("""
                SELECT id FROM ai_models 
                WHERE model_name = :model_used
                LIMIT 1
            """), {'model_used': model_used}).fetchone()
            
            if result:
                return result[0]
            
            # Für OpenRouter-Modelle: Versuche mit openrouter: Präfix
            if not model_used.startswith('openrouter:'):
                openrouter_id = f"openrouter:{model_used}"
                result = session.execute(text("""
                    SELECT id FROM ai_models 
                    WHERE full_model_id = :model_used
                    LIMIT 1
                """), {'model_used': openrouter_id}).fetchone()
                
                if result:
                    return result[0]
                
                # Erstelle neuen ai_models Eintrag für OpenRouter
                insert_result = session.execute(text("""
                    INSERT INTO ai_models (provider, model_name, full_model_id)
                    VALUES ('openrouter', :model_name, :full_model_id)
                    RETURNING id
                """), {
                    'model_name': model_used,
                    'full_model_id': openrouter_id
                })
                return insert_result.fetchone()[0]
            else:
                # Modell hat bereits openrouter: Präfix - erstelle neuen Eintrag
                model_name = model_used.replace('openrouter:', '')
                insert_result = session.execute(text("""
                    INSERT INTO ai_models (provider, model_name, full_model_id)
                    VALUES ('openrouter', :model_name, :full_model_id)
                    RETURNING id
                """), {
                    'model_name': model_name,
                    'full_model_id': model_used
                })
                return insert_result.fetchone()[0]
            
            logger.warning(f"[AI_MODEL_MAPPING] Unbekanntes Modell: {model_used}")
            return None
            
        except Exception as e:
            logger.error(f"[AI_MODEL_MAPPING ERROR] Fehler für model '{model_used}': {e}")
            return None

    def _get_source_id_by_name(self, session: Session, source_name: str) -> Optional[int]:
        """
        Hole source_id basierend auf source_name.
        Sucht in der sources Tabelle nach URL die source_name enthält.
        """
        if not source_name:
            return None
            
        try:
            # Suche nach exakter URL-Übereinstimmung
            result = session.execute(text("""
                SELECT id FROM sources 
                WHERE url = :source_name
                LIMIT 1
            """), {'source_name': source_name}).fetchone()
            
            if result:
                return result[0]
            
            # Fallback: Suche nach Domain-Übereinstimmung
            result = session.execute(text("""
                SELECT id FROM sources 
                WHERE url LIKE :source_pattern
                LIMIT 1
            """), {'source_pattern': f'%{source_name}%'}).fetchone()
            
            if result:
                return result[0]
                
            # Weitere Fallback: Suche nach Domain aus URL
            if 'http' in source_name:
                try:
                    from urllib.parse import urlparse
                    domain = urlparse(source_name).netloc
                    if domain:
                        result = session.execute(text("""
                            SELECT id FROM sources 
                            WHERE domain = :domain
                            LIMIT 1
                        """), {'domain': domain}).fetchone()
                        
                        if result:
                            return result[0]
                except:
                    pass
                    
            logger.debug(f"[SOURCE_ID] Keine source_id gefunden für: {source_name}")
            return None
            
        except Exception as e:
            logger.error(f"[SOURCE_ID ERROR] Fehler für source_name '{source_name}': {e}")
            return None

    def _determine_field_type(self, field_name: str) -> str:
        """Bestimme ob ein Feld 'normalized' oder 'primitive' ist basierend auf field_type_mapping"""
        try:
            with self.get_session() as session:
                # Suche in field_type_mapping nach passendem Pattern
                result = session.execute(text("""
                    SELECT field_type FROM field_type_mapping 
                    WHERE LOWER(:field_name) LIKE LOWER(field_pattern)
                    ORDER BY LENGTH(field_pattern) DESC
                    LIMIT 1
                """), {'field_name': field_name}).fetchone()
                
                if result:
                    field_type = result[0]
                    logger.debug(f"[FIELD_TYPE_MAPPING] '{field_name}' -> {field_type}")
                    return field_type
                
                # Fallback: Heuristische Bestimmung
                field_lower = field_name.lower()
                
                # Normalized fields (werden zu FK-IDs)
                if any(pattern in field_lower for pattern in [
                    'rohstoff', 'commodity', 'eigentümer', 'betreiber', 'owner', 'operator',
                    'aktivitätsstatus', 'activity', 'status', 'minentyp', 'mine_type', 'type',
                    'country', 'land', 'region'
                ]):
                    logger.debug(f"[FIELD_TYPE_HEURISTIC] '{field_name}' -> normalized")
                    return 'normalized'
                
                # Primitive fields (bleiben als Text/Zahlen)
                if any(pattern in field_lower for pattern in [
                    'name', 'koordinate', 'coordinate', 'latitude', 'longitude', 'jahr', 'year',
                    'datum', 'date', 'menge', 'volume', 'fläche', 'area', 'kosten', 'cost',
                    'quellen', 'sources'
                ]):
                    logger.debug(f"[FIELD_TYPE_HEURISTIC] '{field_name}' -> primitive")
                    return 'primitive'
                
                # Default: primitive für unbekannte Felder
                logger.debug(f"[FIELD_TYPE_DEFAULT] '{field_name}' -> primitive (default)")
                return 'primitive'
                
        except Exception as e:
            logger.error(f"[FIELD_TYPE_ERROR] Fehler bei Feld-Typ-Bestimmung für '{field_name}': {e}")
            return 'primitive'  # Safe default
    
    def _insert_mine_data_field_3nf(self, session: Session, data: Dict[str, Any], 
                                   actor: Optional[str] = None, reason: Optional[str] = None) -> None:
        """INSERT für mine_data_fields mit neuer 3NF-Struktur und field_type
        
        Args:
            session: Aktive DB-Session (Transaktion). Wird nicht committed.
            data: Alle Spaltenwerte inkl. field_type
            actor: Wer schreibt (z. B. model_used)
            reason: Warum (z. B. save_mine_field_data)
        """
        # DEDUPLIZIERUNG: Prüfe auf bestehende identische Einträge
        check_sql = """
            SELECT id FROM mine_data_fields 
            WHERE mine_id = :mine_id 
              AND field_name = :field_name 
              AND session_id = :session_id
              AND field_type = :field_type
            LIMIT 1
        """
        
        check_params = {
            'mine_id': data['mine_id'],
            'field_name': data['field_name'], 
            'session_id': data['session_id'],
            'field_type': data['field_type']
        }
        
        existing = session.execute(text(check_sql), check_params).fetchone()
        if existing:
            logger.debug(f"[DEDUPLIZIERUNG] Identischer 3NF-Eintrag bereits vorhanden: {data['field_name']}")
            return
        
        # NEUE 3NF-STRUKTUR: field_type und entsprechende Werte
        insert_sql = """
            INSERT INTO mine_data_fields (
                search_result_id, mine_id, field_name, field_type,
                commodity_id, company_id, activity_status_id, mine_type_id, country_id, region_id,
                primitive_value, numeric_value, unit,
                confidence_score, is_template_value, validation_status,
                source_name, model_used, session_id, extraction_timestamp, model_id, source_id
            ) VALUES (
                :search_result_id, :mine_id, :field_name, :field_type,
                :commodity_id, :company_id, :activity_status_id, :mine_type_id, :country_id, :region_id,
                :primitive_value, :numeric_value, :unit,
                :confidence_score, :is_template_value, :validation_status,
                :source_name, :model_used, :session_id, :extraction_timestamp, :model_id, :source_id
            )
        """
        
        try:
            session.execute(text(insert_sql), data)
            logger.debug(f"[mine_data_fields 3NF INSERT] {data['field_type']} Feld '{data['field_name']}' gespeichert")
        except Exception as e:
            logger.error(f"[mine_data_fields 3NF INSERT ERROR] Fehler für Feld '{data['field_name']}': {e}")
            raise
    
    def _insert_or_update_mine_data_field(self, session: Session, key: Dict[str, Any], 
                                          new_values: Dict[str, Any], actor: Optional[str] = None, 
                                          reason: Optional[str] = None) -> None:
        """DEPRECATED: Alte Methode für Kompatibilität - wird durch _insert_mine_data_field_3nf ersetzt"""
        logger.warning("[DEPRECATED] _insert_or_update_mine_data_field wird durch _insert_mine_data_field_3nf ersetzt")
        # Fallback auf alte Logik für Kompatibilität
        pass

    def save_search_result_normalized(self, mine_name: str, model_used: str, 
                                    structured_data: Dict[str, Any],
                                    sources: List[Dict[str, Any]], 
                                    session_id: Optional[str] = None,
                                    country: Optional[str] = None,
                                    search_duration: Optional[float] = None,
                                    db_session: Optional[Session] = None,
                                    **kwargs) -> int:
        """
        NEUE FUNKTION: Speichere Suchergebnis in normalisiertem Schema
        
        Returns: search_result_id aus search_sessions
        """
        try:
            # SESSION-ID FIX 04.09.2025: Generiere EINZIGARTIGE UUID für jede Mine in Batch
            import uuid
            unique_session_id = str(uuid.uuid4())
            
            # Batch-Tracking: Falls session_id bereitgestellt, nutze als batch_reference_id
            if session_id:
                logger.info(f"[NORMALIZED-DB] Batch-Reference: {session_id} -> Unique ID: {unique_session_id} für Mine {mine_name}")
                batch_reference_id = session_id
            else:
                batch_reference_id = unique_session_id
                logger.info(f"[NORMALIZED-DB] Generierte neue session_id: {unique_session_id} für Mine {mine_name}")
            
            # Verwende unique_session_id für DB-Speicherung
            session_id = unique_session_id
            logger.debug(f"[NORMALIZED-DB] Speichere Ergebnis für Mine '{mine_name}' mit session_id: {session_id}")
            # 1. Hole oder erstelle Mine
            # REGEL 10 COMPLIANCE: Keine Dummy-Werte - Skip bei fehlendem Country
            if not country:
                extracted_country = structured_data.get('Country') or structured_data.get('country')
                if not extracted_country:
                    logger.warning(f"[NORMALIZED-DB] Keine Country-Daten für {mine_name} - REGEL 10: Skip ohne Dummy-Werte")
                    raise ValueError(f"Fehlende Country-Daten für {mine_name}")
                country = extracted_country
            
            # Füge country zu structured_data hinzu für das neue Schema
            if country and structured_data:
                structured_data['Country'] = country
            elif country and not structured_data:
                structured_data = {'Country': country}
            mine_id = self.get_or_create_mine(mine_name, structured_data, db_session=db_session)
            
            # 2. Berechne Qualitätsmetriken
            fields_found = len([v for v in structured_data.values() if v and v != 'Nicht gefunden'])
            template_fields_rejected = 0
            
            # Prüfe auf Template-Werte
            if value_normalizer:
                for field_name, field_value in structured_data.items():
                    try:
                        validation_result = value_normalizer.validate_field_value(field_name, field_value)
                        if not validation_result.get('is_valid', True):
                            template_fields_rejected += 1
                    except:
                        pass
            
            # Data Quality Score (0.0 - 1.0)
            total_possible_fields = 15  # Angenommene maximale Feldanzahl
            data_quality_score = min(1.0, fields_found / total_possible_fields)
            
            # Template-Werte reduzieren Score
            if template_fields_rejected > 0:
                penalty = template_fields_rejected * 0.1
                data_quality_score = max(0.0, data_quality_score - penalty)
            
            # 3. Speichere in search_sessions
            if db_session is not None:
                session = db_session
                # CRITICAL FIX 04.09.2025: Use RETURNING clause to get proper search_result_id
                insert_result = session.execute(text("""
                    INSERT INTO search_sessions 
                    (session_id, mine_id, ai_model_id, search_timestamp, search_type, 
                     search_duration_ms, success)
                    VALUES (:session_id, :mine_id, :ai_model_id, :search_timestamp, :search_type,
                           :search_duration_ms, :success)
                    RETURNING id
                """), {
                    'session_id': session_id,
                    'mine_id': mine_id,
                    'ai_model_id': self._get_or_create_ai_model_id(session, model_used),
                    'search_timestamp': datetime.now(),
                    'search_type': 'single',
                    'search_duration_ms': search_duration,
                    'success': True
                })
                search_result_id = insert_result.fetchone()[0]
                logger.debug(f"[NORMALIZED-DB] Created search_session with ID: {search_result_id}")
                session.flush()
                # 4. Speichere atomare Feldwerte in derselben Transaktion
                logger.info(f"[FIELD_SAVE_DEBUG] About to call save_mine_field_data with {len(structured_data)} fields")
                self.save_mine_field_data(mine_id, search_result_id, structured_data, model_used, sources, session_id=session_id, db_session=session)
                logger.info(f"[FIELD_SAVE_DEBUG] Finished save_mine_field_data call")
                # ENTFERNT 04.09.2025: Koordinaten werden nicht mehr in mines Tabelle gespeichert
                # KRITISCHER FIX 04.09.2025: Commit der gesamten Transaktion
                try:
                    session.commit()
                    logger.info(f"[TRANSACTION-DEBUG] Session commit erfolgreich für mine_id={mine_id}")
                except Exception as commit_error:
                    logger.error(f"🔥 SESSION COMMIT FAILED für mine_id={mine_id}: {commit_error}")
                    session.rollback()
                    raise commit_error
            else:
                with self.get_session() as session_local:
                    # CRITICAL FIX 04.09.2025: Use RETURNING clause to get proper search_result_id
                    insert_result = session_local.execute(text("""
                        INSERT INTO search_sessions 
                        (session_id, mine_id, ai_model_id, search_timestamp, search_type, 
                         search_duration_ms, success)
                        VALUES (:session_id, :mine_id, :ai_model_id, :search_timestamp, :search_type,
                               :search_duration_ms, :success)
                        RETURNING id
                    """), {
                        'session_id': session_id,
                        'mine_id': mine_id,
                        'ai_model_id': self._get_or_create_ai_model_id(session_local, model_used),
                        'search_timestamp': datetime.now(),
                        'search_type': 'single',
                        'search_duration_ms': search_duration,
                        'success': True
                    })
                    search_result_id = insert_result.fetchone()[0]
                    logger.debug(f"[NORMALIZED-DB] Created search_session with ID: {search_result_id}")
                    session_local.commit()
                    # 4. Speichere atomare Feldwerte mit eigener Session
                    logger.info(f"[FIELD_SAVE_DEBUG] About to call save_mine_field_data (else branch) with {len(structured_data)} fields")
                    self.save_mine_field_data(mine_id, search_result_id, structured_data, model_used, sources, session_id=session_id)
                    logger.info(f"[FIELD_SAVE_DEBUG] Finished save_mine_field_data call (else branch)")
                    # ENTFERNT 04.09.2025: Koordinaten werden nicht mehr in mines Tabelle gespeichert
            
            logger.info(f"✅ NORMALIZED SAVE: Mine='{mine_name}' Model='{model_used}' Fields={fields_found} Quality={data_quality_score:.2f}")
            
            return search_result_id
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des normalisierten Suchergebnisses: {e}")
            import traceback
            traceback.print_exc()
            raise
    
    def _ensure_field_definitions_initialized(self) -> None:
        """
        KRITISCHER FIX 29.08.2025: Stelle sicher, dass field_definitions Tabelle 
        mit allen Standard-Feldnamen gefüllt ist
        """
        try:
            with self.get_session() as session:
                # Importiere CSV_COLUMNS aus config
                from minesearch.config import CSV_COLUMNS
                
                # Zusätzliche dynamische Feldnamen die bei Batch-Suchen auftreten können
                additional_fields = [
                    # Test-Felder
                    'TEST_Country', 'TEST_Region', 'TEST_Owner', 'DIRECT_TEST',
                    # Häufige Variationen
                    'Mine Name', 'Company', 'Owner', 'Operator', 'Location',
                    'Status', 'Type', 'Commodity', 'Production', 'Capacity'
                ]
                
                # Kombiniere alle Feldnamen
                all_field_names = list(CSV_COLUMNS) + additional_fields
                
                # Füge alle Feldnamen hinzu (OR IGNORE für Duplikate)
                for field_name in all_field_names:
                    session.execute(text("""
                        INSERT OR IGNORE INTO field_definitions (field_name, display_name, data_type)
                        VALUES (:field_name, :display_name, 'text')
                    """), {
                        'field_name': field_name, 
                        'display_name': field_name
                    })
                
                session.commit()
                
                # Prüfe finalen Status
                count_result = session.execute(text('SELECT COUNT(*) FROM field_definitions')).fetchone()
                logger.info(f"✅ field_definitions initialisiert: {count_result[0]} Feldnamen verfügbar")
                
        except Exception as e:
            logger.error(f"❌ Fehler bei field_definitions Initialisierung: {e}")
            # Nicht re-raise, damit der Hauptprozess weiterläuft

    def get_mine_data_with_joins(self, mine_id: int, session_id: Optional[str] = None) -> Dict[str, Any]:
        """Hole Minendaten mit JOINs für lesbare Ausgabe der normalisierten Felder"""
        try:
            with self.get_session() as session:
                # Base Query für alle Feldwerte
                base_conditions = "WHERE mdf.mine_id = :mine_id"
                params = {'mine_id': mine_id}
                
                if session_id:
                    base_conditions += " AND mdf.session_id = :session_id"
                    params['session_id'] = session_id
                
                # Query mit JOINs für normalisierte Felder
                query = f"""
                SELECT 
                    mdf.field_name,
                    mdf.field_type,
                    mdf.primitive_value,
                    mdf.numeric_value,
                    mdf.unit,
                    c.name as commodity_name,
                    comp.name as company_name,
                    ast.status as activity_status,
                    mt.name as mine_type_name,
                    cnt.name as country_name,
                    r.name as region_name,
                    mdf.confidence_score,
                    mdf.is_template_value,
                    mdf.model_used,
                    mdf.extraction_timestamp
                FROM mine_data_fields mdf
                LEFT JOIN commodities c ON mdf.commodity_id = c.id
                LEFT JOIN companies comp ON mdf.company_id = comp.id
                LEFT JOIN activity_statuses ast ON mdf.activity_status_id = ast.id
                LEFT JOIN mine_types mt ON mdf.mine_type_id = mt.id
                LEFT JOIN countries cnt ON mdf.country_id = cnt.id
                LEFT JOIN regions r ON mdf.region_id = r.id
                {base_conditions}
                ORDER BY mdf.field_name
                """
                
                result = session.execute(text(query), params)
                rows = result.fetchall()
                
                # Konvertiere zu lesbarem Dictionary
                readable_data = {}
                for row in rows:
                    field_name = row[0]
                    field_type = row[1]
                    
                    if field_type == 'normalized':
                        # Für normalisierte Felder: Zeige den lesbaren Namen
                        if row[5]:  # commodity_name
                            readable_data[field_name] = row[5]
                        elif row[6]:  # company_name
                            readable_data[field_name] = row[6]
                        elif row[7]:  # activity_status
                            readable_data[field_name] = row[7]
                        elif row[8]:  # mine_type_name
                            readable_data[field_name] = row[8]
                        elif row[9]:  # country_name
                            readable_data[field_name] = row[9]
                        elif row[10]:  # region_name
                            readable_data[field_name] = row[10]
                    else:
                        # Für primitive Felder: Zeige den primitiven Wert
                        value = row[2]  # primitive_value
                        if row[3] and row[4]:  # numeric_value und unit
                            value = f"{row[3]} {row[4]}"
                        readable_data[field_name] = value
                
                return readable_data
                
        except Exception as e:
            logger.error(f"[JOIN_QUERY_ERROR] Fehler beim Abrufen der Minendaten für Mine {mine_id}: {e}")
            return {}
    
    # ENTFERNT 04.09.2025: Koordinaten-Update Funktion nicht mehr benötigt
    # Alle Daten bleiben in mine_data_fields für Konsistenz-Analysen