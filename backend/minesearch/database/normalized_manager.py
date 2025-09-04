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

logger = logging.getLogger(__name__)

class NormalizedDatabaseManager(DatabaseManager):
    """
    Erweiterte Version des DatabaseManager für normalisiertes Schema
    """
    
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
    
    def get_or_create_company(self, company_name: str, company_type: str = 'owner', db_session: Optional[Session] = None) -> Optional[int]:
        """Hole oder erstelle Unternehmen und gib ID zurück"""
        if not company_name or company_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None
        
        normalized_name = self.normalize_company_name(company_name)
        if not normalized_name:
            return None
        
        # Externe Transaktion verwenden, falls bereitgestellt
        if db_session is not None:
            # Suche existierende Firma
            result = db_session.execute(text("""
                SELECT id FROM companies 
                WHERE normalized_name = :normalized_name
                LIMIT 1
            """), {'normalized_name': normalized_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            insert_result = db_session.execute(text("""
                INSERT INTO companies (name, normalized_name, company_type) 
                VALUES (:name, :normalized_name, :company_type)
            """), {
                'name': company_name,
                'normalized_name': normalized_name,
                'company_type': company_type
            })
            db_session.flush()
            return insert_result.lastrowid
        
        # Eigene Session verwalten
        with self.get_session() as session:
            # Suche existierende Firma
            result = session.execute(text("""
                SELECT id FROM companies 
                WHERE normalized_name = :normalized_name
                LIMIT 1
            """), {'normalized_name': normalized_name})
            existing = result.fetchone()
            if existing:
                return existing[0]
            # Erstelle neue Firma
            insert_result = session.execute(text("""
                INSERT INTO companies (name, normalized_name, company_type) 
                VALUES (:name, :normalized_name, :company_type)
            """), {
                'name': company_name,
                'normalized_name': normalized_name,
                'company_type': company_type
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
        """Hole oder erstelle Region und gib ID zurück"""
        if not region_name or region_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None
            
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
        """Hole oder erstelle Minentyp und gib ID zurück - mit intelligenter Synonym-Erkennung"""
        if not type_name:
            return None
        
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

    def get_or_create_activity_status(self, status_name: str, db_session: Optional[Session] = None) -> Optional[int]:
        """Hole oder erstelle Aktivitätsstatus und gib ID zurück - mit intelligenter Synonym-Erkennung"""
        if not status_name:
            return None
        
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
            
            logger.info(f"✅ Neue Mine erstellt: {mine_name} (ID: {insert_result.lastrowid})")
            return insert_result.lastrowid
    
    def save_mine_field_data(self, mine_id: int, search_result_id: int, structured_data: Dict[str, Any], 
                           model_used: str, sources: List[Dict[str, Any]], session_id: str = None, db_session: Optional[Session] = None):
        """Speichere atomare Feldwerte in mine_data_fields"""
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
                if not field_value or field_value in ['Nicht gefunden', 'Not found', 'X']:
                    continue
                
                # Value-Normalisierung für atomare Speicherung
                raw_value = str(field_value)
                
                # CRITICAL: Entferne Quellenreferenzen für atomare Speicherung
                # "Aktiv [1,2,3,4,5]" → "Aktiv"
                import re
                atomic_value = re.sub(r'\s*\[\d+(,\d+)*\]$', '', raw_value).strip()
                
                normalized_value = atomic_value
                numeric_value = None
                unit = None
                is_template = False
                validation_status = 'valid'
                
                # Prüfe auf Template-Werte (REGEL 10 Compliance!)
                if value_normalizer:
                    try:
                        validation_result = value_normalizer.validate_field_value(field_name, field_value)
                        if not validation_result.get('is_valid', True):
                            is_template = True
                            validation_status = 'template'
                            logger.warning(f"Template-Wert erkannt: {field_name} = {field_value}")
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
                
                # Confidence Score (provisorisch)
                confidence_score = 0.8
                if is_template:
                    confidence_score = 0.1
                
                # Selektiere existierenden Datensatz und führe gezieltes UPDATE oder INSERT durch
                self._insert_or_update_mine_data_field(
                    session,
                    {
                        'search_result_id': search_result_id,
                        'mine_id': mine_id,
                        'field_name': field_name
                    },
                    {
                        'session_id': session_id,  # CRITICAL FIX 04.09.2025: Add session_id 
                        'raw_value': raw_value,
                        'normalized_value': normalized_value,
                        'numeric_value': numeric_value,
                        'unit': unit,
                        'confidence_score': confidence_score,
                        'is_template_value': is_template,
                        'validation_status': validation_status,
                        'source_name': source_name,
                        'model_used': model_used
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
                if not field_value or field_value in ['Nicht gefunden', 'Not found', 'X']:
                    continue
                raw_value = str(field_value)
                import re
                atomic_value = re.sub(r'\s*\[\d+(,\d+)*\]$', '', raw_value).strip()
                normalized_value = atomic_value
                numeric_value = None
                unit = None
                is_template = False
                validation_status = 'valid'
                if value_normalizer:
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
                confidence_score = 0.8
                if is_template:
                    confidence_score = 0.1
                    
                # KONSISTENZ-FIX 04.09.2025: Verwende gleiche _insert_or_update_mine_data_field wie IF-Zweig
                self._insert_or_update_mine_data_field(
                    local_session,
                    {
                        'search_result_id': search_result_id,
                        'mine_id': mine_id,
                        'field_name': field_name
                    },
                    {
                        'raw_value': raw_value,
                        'normalized_value': normalized_value,
                        'numeric_value': numeric_value,
                        'unit': unit,
                        'confidence_score': confidence_score,
                        'is_template_value': is_template,
                        'validation_status': validation_status,
                        'source_name': source_name,
                        'model_used': model_used,
                        'session_id': session_id
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

    def _insert_or_update_mine_data_field(self, session: Session, key: Dict[str, Any], 
                                          new_values: Dict[str, Any], actor: Optional[str] = None, 
                                          reason: Optional[str] = None) -> None:
        """INSERT-only für mine_data_fields - jede Suche speichert separate Feldwerte.

        Args:
            session: Aktive DB-Session (Transaktion). Wird nicht committed.
            key: Primärschlüsselwerte: {search_result_id, mine_id, field_name}
            new_values: Zu schreibende Spaltenwerte (inkl. session_id)
            actor: Wer schreibt (z. B. model_used)
            reason: Warum (z. B. save_mine_field_data)
        """
        # INSERT-only Logik - da jede Suche eigene search_result_id hat
        insert_sql = """
            INSERT INTO mine_data_fields (
                search_result_id, mine_id, field_name, raw_value, normalized_value,
                numeric_value, unit, confidence_score, is_template_value,
                validation_status, source_name, model_used, session_id
            ) VALUES (
                :search_result_id, :mine_id, :field_name, :raw_value, :normalized_value,
                :numeric_value, :unit, :confidence_score, :is_template_value,
                :validation_status, :source_name, :model_used, :session_id
            )
        """
        params = {**key, **new_values}
        try:
            session.execute(text(insert_sql), params)
            logger.debug(
                f"[mine_data_fields INSERT] Feldwert gespeichert für key={key} actor={actor or 'unknown'}"
            )
        except Exception as e:
            logger.error(f"[mine_data_fields INSERT ERROR] Fehler für key={key}: {e}")
            raise

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
                session.commit()
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

    # ENTFERNT 04.09.2025: Koordinaten-Update Funktion nicht mehr benötigt
    # Alle Daten bleiben in mine_data_fields für Konsistenz-Analysen