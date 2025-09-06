#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Duplikate-Prävention Enhancement für NormalizedDatabaseManager
Erweitert die bestehende Klasse um robuste Duplikate-Erkennung
"""

import logging
from typing import Optional, Dict, Any
from sqlalchemy.orm import Session

logger = logging.getLogger(__name__)

class DuplicatePreventionMixin:
    """
    Mixin-Klasse für Duplikate-Prävention in NormalizedDatabaseManager
    Kann als Basis für Verbesserungen verwendet werden
    """
    
    def check_company_duplicates(self, session: Session, name: str, role: str = None) -> Optional[int]:
        """
        Prüft auf Company-Duplikate durch intelligente Namensvergleiche
        Returns: company_id wenn Duplikat gefunden, None sonst
        """
        if not name or not name.strip():
            return None
        
        clean_name = name.strip().lower()
        
        # Definiere bekannte Varianten-Muster
        variant_patterns = {
            # Basis -> Varianten die konsolidiert werden sollen
            'goldcorp': ['goldcorp inc', 'goldcorp inc.', 'goldcorp corporation'],
            'barrick': ['barrick gold', 'barrick gold corp', 'barrick gold corporation'],
            'newmont': ['newmont corp', 'newmont corporation', 'newmont mining'],
            'rio tinto': ['rio tinto group', 'rio tinto plc'],
            'vale': ['vale s.a.', 'vale sa'],
            'bhp': ['bhp billiton', 'bhp group']
        }
        
        # Import hier um zirkuläre Imports zu vermeiden
        from minesearch.models.tables import Company
        
        # Prüfe exakte Duplikate
        existing_company = session.query(Company).filter(
            Company.name.ilike(name.strip())
        ).first()
        
        if existing_company:
            logger.debug(f"Exaktes Company-Duplikat gefunden: {name} -> ID:{existing_company.id}")
            return existing_company.id
        
        # Prüfe Varianten-basierte Duplikate
        for base_name, variants in variant_patterns.items():
            if clean_name == base_name:
                # Suche nach einer der Varianten
                for variant in variants:
                    variant_company = session.query(Company).filter(
                        Company.name.ilike(variant)
                    ).first()
                    if variant_company:
                        logger.debug(f"Varianten-Duplikat gefunden: {name} -> {variant_company.name} (ID:{variant_company.id})")
                        return variant_company.id
            
            elif clean_name in [v.lower() for v in variants]:
                # Suche nach Basis-Name
                base_company = session.query(Company).filter(
                    Company.name.ilike(base_name)
                ).first()
                if base_company:
                    logger.debug(f"Basis-Company gefunden: {name} -> {base_company.name} (ID:{base_company.id})")
                    return base_company.id
                
                # Suche nach anderen Varianten
                for variant in variants:
                    if variant.lower() != clean_name:
                        variant_company = session.query(Company).filter(
                            Company.name.ilike(variant)
                        ).first()
                        if variant_company:
                            logger.debug(f"Andere Variante gefunden: {name} -> {variant_company.name} (ID:{variant_company.id})")
                            return variant_company.id
        
        return None
    
    def check_region_duplicates(self, session: Session, name: str, country_id: int) -> Optional[int]:
        """
        Prüft auf Region-Duplikate (besonders Quebec-Varianten)
        """
        if not name or not name.strip():
            return None
        
        clean_name = name.strip().lower()
        
        from minesearch.models.tables import Region
        
        # Quebec-spezifische Varianten
        quebec_variants = [
            'quebec', 'québec', 'quebec/québec', 'québec/côte-nord'
        ]
        
        if any(quebec_var in clean_name for quebec_var in quebec_variants):
            # Suche nach irgendeiner Quebec-Variante
            for variant in quebec_variants:
                existing_region = session.query(Region).filter(
                    Region.name.ilike(f"%{variant}%"),
                    Region.country_id == country_id
                ).first()
                
                if existing_region:
                    logger.debug(f"Quebec-Variante gefunden: {name} -> {existing_region.name} (ID:{existing_region.id})")
                    return existing_region.id
        
        # Exakter Match
        existing_region = session.query(Region).filter(
            Region.name.ilike(name.strip()),
            Region.country_id == country_id
        ).first()
        
        if existing_region:
            logger.debug(f"Exaktes Region-Duplikat gefunden: {name} -> ID:{existing_region.id}")
            return existing_region.id
        
        return None
    
    def validate_3nf_data_integrity(self, field_data: Dict[str, Any]) -> bool:
        """
        Validiert 3NF-Datenintegrität vor Insert
        """
        field_type = field_data.get('field_type')
        
        if field_type == 'normalized':
            # Normalized Fields müssen mindestens eine FK-ID haben
            fk_fields = [
                'commodity_id', 'company_id', 'activity_status_id', 
                'mine_type_id', 'country_id', 'region_id'
            ]
            
            has_fk = any(field_data.get(fk) is not None for fk in fk_fields)
            has_primitive = field_data.get('primitive_value') is not None
            
            if not has_fk:
                logger.error(f"3NF-Violation: Normalized field '{field_data.get('field_name')}' hat keine FK-ID")
                return False
            
            if has_primitive:
                logger.error(f"3NF-Violation: Normalized field '{field_data.get('field_name')}' hat primitive_value")
                return False
        
        elif field_type == 'primitive':
            # Primitive Fields dürfen keine FK-IDs haben
            fk_fields = [
                'commodity_id', 'company_id', 'activity_status_id', 
                'mine_type_id', 'country_id', 'region_id'
            ]
            
            has_fk = any(field_data.get(fk) is not None for fk in fk_fields)
            has_primitive = field_data.get('primitive_value') is not None
            
            if has_fk:
                logger.error(f"3NF-Violation: Primitive field '{field_data.get('field_name')}' hat FK-IDs")
                return False
            
            if not has_primitive and not field_data.get('numeric_value'):
                logger.error(f"3NF-Violation: Primitive field '{field_data.get('field_name')}' hat weder primitive_value noch numeric_value")
                return False
        
        return True

# Monkey-Patch für bestehenden NormalizedDatabaseManager
def apply_duplicate_prevention_patch():
    """
    Wendet Duplikate-Prävention auf bestehende NormalizedDatabaseManager-Klasse an
    """
    from minesearch.database.normalized_manager import NormalizedDatabaseManager
    
    # Füge Mixin-Methoden hinzu
    mixin = DuplicatePreventionMixin()
    
    NormalizedDatabaseManager.check_company_duplicates = mixin.check_company_duplicates
    NormalizedDatabaseManager.check_region_duplicates = mixin.check_region_duplicates  
    NormalizedDatabaseManager.validate_3nf_data_integrity = mixin.validate_3nf_data_integrity
    
    # Überschreibe get_or_create_company mit Duplikate-Prävention
    original_get_or_create_company = NormalizedDatabaseManager.get_or_create_company
    
    def enhanced_get_or_create_company(self, session, name, role=None):
        """Enhanced get_or_create_company mit Duplikate-Prävention"""
        if not name:
            raise ValueError("Company name cannot be empty")
        
        # Prüfe auf Duplikate BEVOR neue Company erstellt wird
        duplicate_id = self.check_company_duplicates(session, name, role)
        if duplicate_id:
            from minesearch.models.tables import Company
            existing_company = session.query(Company).get(duplicate_id)
            logger.info(f"Company-Duplikat verhindert: '{name}' -> existierende '{existing_company.name}' (ID:{duplicate_id})")
            return existing_company
        
        # Keine Duplikate -> verwende Original-Methode
        return original_get_or_create_company(self, session, name, role)
    
    NormalizedDatabaseManager.get_or_create_company = enhanced_get_or_create_company
    
    logger.info("Duplikate-Prävention Patch erfolgreich angewendet")

if __name__ == "__main__":
    apply_duplicate_prevention_patch()
    print("✅ Duplikate-Prävention Enhancement geladen")
