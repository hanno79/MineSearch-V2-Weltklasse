"""
Compact Database Constraints
Kompakte Version der Database Constraints

Author: MineSearch Development Team
Date: 2025-01-11
"""

import sqlite3
import json
import logging
from typing import List, Dict, Any, Optional
from pathlib import Path

logger = logging.getLogger(__name__)


class DatabaseConstraintManager:
    """Datenbank-Constraint-Manager für Feldkontamination-Prävention"""

    def __init__(self, db_path: str = None):
        """Initialisiert den Constraint-Manager"""
        self.db_path = db_path or "mines.db"
        self.constraints = []

    def add_field_constraint(self, table_name: str, field_name: str, constraint_type: str, constraint_value: Any = None):
        """Füge Feld-Constraint hinzu"""
        try:
            constraint = {
                'table_name': table_name,
                'field_name': field_name,
                'constraint_type': constraint_type,
                'constraint_value': constraint_value,
                'created_at': '2025-01-11T12:00:00Z'
            }
            
            self.constraints.append(constraint)
            logger.info(f"✅ Constraint hinzugefügt: {table_name}.{field_name} ({constraint_type})")
            
        except Exception as e:
            logger.error(f"Fehler beim Hinzufügen des Constraints: {e}")

    def remove_field_constraint(self, table_name: str, field_name: str, constraint_type: str):
        """Entferne Feld-Constraint"""
        try:
            self.constraints = [
                c for c in self.constraints
                if not (c['table_name'] == table_name and 
                       c['field_name'] == field_name and 
                       c['constraint_type'] == constraint_type)
            ]
            logger.info(f"✅ Constraint entfernt: {table_name}.{field_name} ({constraint_type})")
            
        except Exception as e:
            logger.error(f"Fehler beim Entfernen des Constraints: {e}")

    def get_constraints_for_table(self, table_name: str) -> List[Dict[str, Any]]:
        """Hole Constraints für Tabelle"""
        try:
            return [c for c in self.constraints if c['table_name'] == table_name]
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Constraints: {e}")
            return []

    def get_constraints_for_field(self, table_name: str, field_name: str) -> List[Dict[str, Any]]:
        """Hole Constraints für Feld"""
        try:
            return [
                c for c in self.constraints
                if c['table_name'] == table_name and c['field_name'] == field_name
            ]
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Feld-Constraints: {e}")
            return []

    def validate_field_value(self, table_name: str, field_name: str, value: Any) -> Dict[str, Any]:
        """Validiere Feldwert gegen Constraints"""
        try:
            validation_result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            field_constraints = self.get_constraints_for_field(table_name, field_name)
            
            for constraint in field_constraints:
                constraint_result = self._validate_constraint(constraint, value)
                
                if not constraint_result['valid']:
                    validation_result['valid'] = False
                    validation_result['errors'].extend(constraint_result['errors'])
                
                validation_result['warnings'].extend(constraint_result['warnings'])
            
            return validation_result
            
        except Exception as e:
            logger.error(f"Fehler bei Feldwert-Validierung: {e}")
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': []
            }

    def _validate_constraint(self, constraint: Dict[str, Any], value: Any) -> Dict[str, Any]:
        """Validiere einzelnen Constraint"""
        try:
            result = {
                'valid': True,
                'errors': [],
                'warnings': []
            }
            
            constraint_type = constraint['constraint_type']
            constraint_value = constraint['constraint_value']
            
            if constraint_type == 'not_null':
                if value is None or value == '':
                    result['valid'] = False
                    result['errors'].append(f"Field cannot be null or empty")
            
            elif constraint_type == 'max_length':
                if value and len(str(value)) > constraint_value:
                    result['valid'] = False
                    result['errors'].append(f"Field length exceeds maximum of {constraint_value}")
            
            elif constraint_type == 'min_length':
                if value and len(str(value)) < constraint_value:
                    result['valid'] = False
                    result['errors'].append(f"Field length below minimum of {constraint_value}")
            
            elif constraint_type == 'pattern':
                if value and not self._matches_pattern(str(value), constraint_value):
                    result['valid'] = False
                    result['errors'].append(f"Field does not match required pattern")
            
            elif constraint_type == 'enum':
                if value and value not in constraint_value:
                    result['valid'] = False
                    result['errors'].append(f"Field value must be one of: {', '.join(constraint_value)}")
            
            elif constraint_type == 'range':
                if value and not self._in_range(value, constraint_value):
                    result['valid'] = False
                    result['errors'].append(f"Field value must be in range {constraint_value}")
            
            return result
            
        except Exception as e:
            logger.error(f"Fehler bei Constraint-Validierung: {e}")
            return {
                'valid': False,
                'errors': [str(e)],
                'warnings': []
            }

    def _matches_pattern(self, value: str, pattern: str) -> bool:
        """Prüfe ob Wert dem Pattern entspricht"""
        try:
            import re
            return bool(re.match(pattern, value))
        except Exception:
            return False

    def _in_range(self, value: Any, range_spec: Dict[str, Any]) -> bool:
        """Prüfe ob Wert im Bereich liegt"""
        try:
            if 'min' in range_spec and value < range_spec['min']:
                return False
            if 'max' in range_spec and value > range_spec['max']:
                return False
            return True
        except Exception:
            return False

    def create_table_constraints(self, table_name: str) -> List[str]:
        """Erstelle SQL-Constraints für Tabelle"""
        try:
            constraints = []
            table_constraints = self.get_constraints_for_table(table_name)
            
            for constraint in table_constraints:
                sql_constraint = self._generate_sql_constraint(constraint)
                if sql_constraint:
                    constraints.append(sql_constraint)
            
            return constraints
            
        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Tabellen-Constraints: {e}")
            return []

    def _generate_sql_constraint(self, constraint: Dict[str, Any]) -> str:
        """Generiere SQL-Constraint"""
        try:
            table_name = constraint['table_name']
            field_name = constraint['field_name']
            constraint_type = constraint['constraint_type']
            constraint_value = constraint['constraint_value']
            
            if constraint_type == 'not_null':
                return f"ALTER TABLE {table_name} ADD CONSTRAINT chk_{field_name}_not_null CHECK ({field_name} IS NOT NULL)"
            
            elif constraint_type == 'max_length':
                return f"ALTER TABLE {table_name} ADD CONSTRAINT chk_{field_name}_max_length CHECK (LENGTH({field_name}) <= {constraint_value})"
            
            elif constraint_type == 'min_length':
                return f"ALTER TABLE {table_name} ADD CONSTRAINT chk_{field_name}_min_length CHECK (LENGTH({field_name}) >= {constraint_value})"
            
            elif constraint_type == 'pattern':
                return f"ALTER TABLE {table_name} ADD CONSTRAINT chk_{field_name}_pattern CHECK ({field_name} REGEXP '{constraint_value}')"
            
            elif constraint_type == 'enum':
                enum_values = "', '".join(constraint_value)
                return f"ALTER TABLE {table_name} ADD CONSTRAINT chk_{field_name}_enum CHECK ({field_name} IN ('{enum_values}'))"
            
            elif constraint_type == 'range':
                min_val = constraint_value.get('min', '')
                max_val = constraint_value.get('max', '')
                if min_val and max_val:
                    return f"ALTER TABLE {table_name} ADD CONSTRAINT chk_{field_name}_range CHECK ({field_name} BETWEEN {min_val} AND {max_val})"
                elif min_val:
                    return f"ALTER TABLE {table_name} ADD CONSTRAINT chk_{field_name}_min CHECK ({field_name} >= {min_val})"
                elif max_val:
                    return f"ALTER TABLE {table_name} ADD CONSTRAINT chk_{field_name}_max CHECK ({field_name} <= {max_val})"
            
            return ""
            
        except Exception as e:
            logger.error(f"Fehler beim Generieren des SQL-Constraints: {e}")
            return ""

    def apply_constraints_to_database(self):
        """Wende Constraints auf Datenbank an"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                cursor = conn.cursor()
                
                for constraint in self.constraints:
                    sql_constraint = self._generate_sql_constraint(constraint)
                    if sql_constraint:
                        try:
                            cursor.execute(sql_constraint)
                            logger.info(f"✅ Constraint angewendet: {sql_constraint}")
                        except sqlite3.Error as e:
                            logger.warning(f"Constraint konnte nicht angewendet werden: {e}")
                
                conn.commit()
                logger.info("✅ Alle Constraints auf Datenbank angewendet")
                
        except Exception as e:
            logger.error(f"Fehler beim Anwenden der Constraints: {e}")

    def get_constraint_statistics(self) -> Dict[str, Any]:
        """Hole Constraint-Statistiken"""
        try:
            stats = {
                'total_constraints': len(self.constraints),
                'constraints_by_table': {},
                'constraints_by_type': {},
                'timestamp': '2025-01-11T12:00:00Z'
            }
            
            # Gruppiere nach Tabelle
            for constraint in self.constraints:
                table_name = constraint['table_name']
                if table_name not in stats['constraints_by_table']:
                    stats['constraints_by_table'][table_name] = 0
                stats['constraints_by_table'][table_name] += 1
            
            # Gruppiere nach Typ
            for constraint in self.constraints:
                constraint_type = constraint['constraint_type']
                if constraint_type not in stats['constraints_by_type']:
                    stats['constraints_by_type'][constraint_type] = 0
                stats['constraints_by_type'][constraint_type] += 1
            
            return stats
            
        except Exception as e:
            logger.error(f"Fehler beim Abrufen der Constraint-Statistiken: {e}")
            return {}

    def export_constraints(self, file_path: str = None) -> str:
        """Exportiere Constraints"""
        try:
            if not file_path:
                file_path = "database_constraints.json"
            
            export_data = {
                'constraints': self.constraints,
                'statistics': self.get_constraint_statistics(),
                'export_timestamp': '2025-01-11T12:00:00Z'
            }
            
            with open(file_path, 'w', encoding='utf-8') as f:
                json.dump(export_data, f, indent=2, ensure_ascii=False)
            
            logger.info(f"✅ Constraints exportiert: {file_path}")
            return file_path
            
        except Exception as e:
            logger.error(f"Fehler beim Exportieren der Constraints: {e}")
            return ""

    def import_constraints(self, file_path: str) -> bool:
        """Importiere Constraints"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                import_data = json.load(f)
            
            if 'constraints' in import_data:
                self.constraints = import_data['constraints']
                logger.info(f"✅ Constraints importiert: {len(self.constraints)} Constraints")
                return True
            else:
                logger.error("Keine Constraints in Import-Datei gefunden")
                return False
                
        except Exception as e:
            logger.error(f"Fehler beim Importieren der Constraints: {e}")
            return False


# Globale Instanz für einfache Verwendung
_constraint_manager = None


def get_constraint_manager() -> DatabaseConstraintManager:
    """Hole globale Constraint-Manager-Instanz"""
    global _constraint_manager
    if _constraint_manager is None:
        _constraint_manager = DatabaseConstraintManager()
    return _constraint_manager


__all__ = [
    "DatabaseConstraintManager",
    "get_constraint_manager"
]
