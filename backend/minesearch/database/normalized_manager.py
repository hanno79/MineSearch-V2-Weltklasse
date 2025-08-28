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
        
        # Grundlegende Bereinigung
        normalized = re.sub(r'[^a-z0-9\s&]', '', normalized)
        normalized = re.sub(r'\s+', ' ', normalized).strip()
        
        return normalized
    
    def get_or_create_company(self, company_name: str, company_type: str = 'owner') -> Optional[int]:
        """Hole oder erstelle Unternehmen und gib ID zurück"""
        if not company_name or company_name in ['Nicht gefunden', 'Not found', 'Unknown']:
            return None
        
        normalized_name = self.normalize_company_name(company_name)
        if not normalized_name:
            return None
        
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
    
    def get_or_create_mine(self, mine_name: str, country: str, structured_data: Dict[str, Any]) -> int:
        """Hole oder erstelle Mine und gib ID zurück"""
        normalized_name = self.normalize_mine_name(mine_name)
        
        with self.get_session() as session:
            # Suche existierende Mine
            result = session.execute(text("""
                SELECT id FROM mines_normalized 
                WHERE normalized_name = :normalized_name
                LIMIT 1
            """), {'normalized_name': normalized_name})
            
            existing = result.fetchone()
            if existing:
                return existing[0]
            
            # Extrahiere zusätzliche Daten aus structured_data
            region = structured_data.get('Region') or structured_data.get('region')
            
            # Koordinaten extrahieren
            latitude = None
            longitude = None
            
            lat_raw = structured_data.get('x-Koordinate') or structured_data.get('latitude') or structured_data.get('lat')
            lon_raw = structured_data.get('y-Koordinate') or structured_data.get('longitude') or structured_data.get('lon')
            
            if lat_raw:
                try:
                    latitude = float(str(lat_raw).replace(',', '.'))
                    # Validate latitude range
                    if not (-90 <= latitude <= 90):
                        latitude = None
                except (ValueError, TypeError):
                    pass
            
            if lon_raw:
                try:
                    longitude = float(str(lon_raw).replace(',', '.'))
                    # Validate longitude range
                    if not (-180 <= longitude <= 180):
                        longitude = None
                except (ValueError, TypeError):
                    pass
            
            # Status bestimmen
            status = 'active'
            status_raw = structured_data.get('Aktivitätsstatus') or structured_data.get('status')
            if status_raw:
                status_lower = str(status_raw).lower()
                if 'inaktiv' in status_lower or 'inactive' in status_lower:
                    status = 'inactive'
                elif 'entwicklung' in status_lower or 'development' in status_lower:
                    status = 'development'
                elif 'geschlossen' in status_lower or 'closed' in status_lower:
                    status = 'closed'
            
            # Mine-Typ bestimmen
            mine_type = 'open_pit'
            type_raw = structured_data.get('Minentyp (Untertage/ Open-Pit/ usw.)')
            if type_raw:
                type_lower = str(type_raw).lower()
                if 'untertage' in type_lower or 'underground' in type_lower:
                    mine_type = 'underground'
                elif 'placer' in type_lower:
                    mine_type = 'placer'
            
            # Rohstoff bestimmen
            primary_commodity = 'gold'
            commodity_raw = structured_data.get('Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)')
            if commodity_raw:
                commodity_lower = str(commodity_raw).lower()
                if 'kupfer' in commodity_lower or 'copper' in commodity_lower:
                    primary_commodity = 'copper'
                elif 'silber' in commodity_lower or 'silver' in commodity_lower:
                    primary_commodity = 'silver'
                elif 'eisen' in commodity_lower or 'iron' in commodity_lower:
                    primary_commodity = 'iron'
                elif 'kohle' in commodity_lower or 'coal' in commodity_lower:
                    primary_commodity = 'coal'
                elif 'lithium' in commodity_lower:
                    primary_commodity = 'lithium'
            
            # Eigentümer und Betreiber
            owner_id = None
            operator_id = None
            
            owner_name = structured_data.get('Eigentümer') or structured_data.get('Owner')
            if owner_name:
                owner_id = self.get_or_create_company(owner_name, 'owner')
            
            operator_name = structured_data.get('Betreiber') or structured_data.get('Operator')
            if operator_name:
                operator_id = self.get_or_create_company(operator_name, 'operator')
            
            # Erstelle Mine
            insert_result = session.execute(text("""
                INSERT INTO mines_normalized 
                (name, normalized_name, country, region, latitude, longitude, 
                 status, owner_company_id, operator_company_id, mine_type, primary_commodity)
                VALUES (:name, :normalized_name, :country, :region, :latitude, :longitude,
                        :status, :owner_id, :operator_id, :mine_type, :primary_commodity)
            """), {
                'name': mine_name,
                'normalized_name': normalized_name,
                'country': country,
                'region': region,
                'latitude': latitude,
                'longitude': longitude,
                'status': status,
                'owner_id': owner_id,
                'operator_id': operator_id,
                'mine_type': mine_type,
                'primary_commodity': primary_commodity
            })
            
            session.commit()
            logger.info(f"✅ Neue Mine erstellt: {mine_name} → {normalized_name} (ID: {insert_result.lastrowid})")
            return insert_result.lastrowid
    
    def save_mine_field_data(self, mine_id: int, search_result_id: int, structured_data: Dict[str, Any], 
                           model_used: str, sources: List[Dict[str, Any]]):
        """Speichere atomare Feldwerte in mine_data_fields"""
        if not structured_data:
            return
        
        source_name = None
        if sources and len(sources) > 0:
            source_name = sources[0].get('name') or sources[0].get('url')
        
        with self.get_session() as session:
            for field_name, field_value in structured_data.items():
                if not field_value or field_value in ['Nicht gefunden', 'Not found', 'X']:
                    continue
                
                # Value-Normalisierung für atomare Speicherung
                raw_value = str(field_value)
                normalized_value = raw_value
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
                
                # Numerische Werte extrahieren
                if isinstance(field_value, (int, float)):
                    numeric_value = float(field_value)
                else:
                    # Versuche numerischen Wert aus String zu extrahieren
                    numeric_match = re.search(r'[\d,\.]+', str(field_value))
                    if numeric_match:
                        try:
                            numeric_str = numeric_match.group().replace(',', '.')
                            numeric_value = float(numeric_str)
                        except (ValueError, AttributeError):
                            pass
                
                # Einheit extrahieren (z.B. "150 Millionen CAD" → unit: "CAD")
                if isinstance(field_value, str):
                    unit_patterns = [
                        r'(CAD|USD|EUR|AUD|GBP)$',
                        r'(kg|t|oz|g)$',
                        r'(km|m|cm)$',
                        r'(qkm|ha)$'
                    ]
                    for pattern in unit_patterns:
                        match = re.search(pattern, field_value, re.IGNORECASE)
                        if match:
                            unit = match.group(1).upper()
                            break
                
                # Confidence Score (provisorisch)
                confidence_score = 0.8
                if is_template:
                    confidence_score = 0.1
                
                # Speichere Feldwert
                session.execute(text("""
                    INSERT OR REPLACE INTO mine_data_fields 
                    (search_result_id, mine_id, field_name, raw_value, normalized_value,
                     numeric_value, unit, confidence_score, is_template_value, 
                     validation_status, source_name, model_used)
                    VALUES (:search_result_id, :mine_id, :field_name, :raw_value, :normalized_value,
                           :numeric_value, :unit, :confidence_score, :is_template_value,
                           :validation_status, :source_name, :model_used)
                """), {
                    'search_result_id': search_result_id,
                    'mine_id': mine_id,
                    'field_name': field_name,
                    'raw_value': raw_value,
                    'normalized_value': normalized_value,
                    'numeric_value': numeric_value,
                    'unit': unit,
                    'confidence_score': confidence_score,
                    'is_template_value': is_template,
                    'validation_status': validation_status,
                    'source_name': source_name,
                    'model_used': model_used
                })
            
            session.commit()
            logger.info(f"✅ {len(structured_data)} Feldwerte gespeichert für Mine ID {mine_id}")
    
    def save_search_result_normalized(self, mine_name: str, model_used: str, 
                                    structured_data: Dict[str, Any],
                                    sources: List[Dict[str, Any]], 
                                    session_id: Optional[str] = None,
                                    country: Optional[str] = None,
                                    search_duration: Optional[float] = None,
                                    **kwargs) -> int:
        """
        NEUE FUNKTION: Speichere Suchergebnis in normalisiertem Schema
        
        Returns: search_result_id aus search_results_normalized
        """
        try:
            # 1. Hole oder erstelle Mine
            if not country:
                country = structured_data.get('Country') or structured_data.get('country') or 'Unknown'
            
            mine_id = self.get_or_create_mine(mine_name, country, structured_data)
            
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
            
            # 3. Speichere in search_results_normalized
            with self.get_session() as session:
                insert_result = session.execute(text("""
                    INSERT INTO search_results_normalized 
                    (session_id, mine_id, search_timestamp, model_used, search_type, 
                     search_duration, success, fields_found, template_fields_rejected, 
                     data_quality_score)
                    VALUES (:session_id, :mine_id, :search_timestamp, :model_used, :search_type,
                           :search_duration, :success, :fields_found, :template_fields_rejected,
                           :data_quality_score)
                """), {
                    'session_id': session_id,
                    'mine_id': mine_id,
                    'search_timestamp': datetime.now(),
                    'model_used': model_used,
                    'search_type': 'single',
                    'search_duration': search_duration,
                    'success': True,
                    'fields_found': fields_found,
                    'template_fields_rejected': template_fields_rejected,
                    'data_quality_score': round(data_quality_score, 2)
                })
                
                search_result_id = insert_result.lastrowid
                session.commit()
            
            # 4. Speichere atomare Feldwerte
            self.save_mine_field_data(mine_id, search_result_id, structured_data, model_used, sources)
            
            logger.info(f"✅ NORMALIZED SAVE: Mine='{mine_name}' Model='{model_used}' Fields={fields_found} Quality={data_quality_score:.2f}")
            
            return search_result_id
            
        except Exception as e:
            logger.error(f"❌ Fehler beim Speichern des normalisierten Suchergebnisses: {e}")
            import traceback
            traceback.print_exc()
            raise