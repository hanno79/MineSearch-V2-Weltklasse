#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.09.2025
Version: 1.0
Beschreibung: Application-Level Duplikat-Prevention Guards

🔒 INTELLIGENT DUPLICATE PREVENTION GUARDS
==========================================

Diese Guards werden vor jedem Insert/Update ausgeführt:
1. Normalisierung der Namen
2. Fuzzy-Duplikat-Erkennung
3. Benutzer-Entscheidung bei ähnlichen Werten
4. Safe-Insert mit Rollback-Möglichkeit
"""

import sqlite3
import difflib
import re
from typing import Optional, List, Dict, Tuple


class DuplicatePreventionGuards:
    """🔒 Intelligente Duplikat-Prävention auf Application-Level"""

    def __init__(self, db_path: str = 'mines.db', similarity_threshold: float = 0.85):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.db_path = db_path
        self.similarity_threshold = similarity_threshold

    def safe_insert_company(self, name: str, country_id: Optional[int] = None,
    """safe_insert_company - TODO: Dokumentation hinzufügen"""
                           auto_merge: bool = False) -> Dict:
        """
        🏢 SAFE COMPANY INSERT mit Duplikat-Prävention
        =============================================

        Returns: {'success': bool, 'company_id': int, 'action': str, 'similar_found': List}
        """
        normalized_name = self._normalize_company_name(name)

        conn = sqlite3.connect(self.db_path)
        try:
            # 1. Prüfe auf exakte Duplikate
            cursor = conn.cursor()
            cursor.execute("""
                SELECT id, name FROM companies
                WHERE name = ? OR normalized_name = ?
            """, (name, normalized_name))

            exact_match = cursor.fetchone()
            if exact_match:
                return {
                    'success': False,
                    'company_id': exact_match[0],
                    'action': 'exact_duplicate_found',
                    'message': f'Exaktes Duplikat gefunden: "{exact_match[1]}"'
                }

            # 2. Prüfe auf ähnliche Namen (Fuzzy-Match)
            cursor.execute("SELECT id, name FROM companies")
            existing_companies = cursor.fetchall()

            similar_companies = []
            for comp_id, existing_name in existing_companies:
                similarity = difflib.SequenceMatcher(
                    None,
                    normalized_name.lower(),
                    self._normalize_company_name(existing_name).lower()
                ).ratio()

                if similarity >= self.similarity_threshold:
                    similar_companies.append({
                        'id': comp_id,
                        'name': existing_name,
                        'similarity': similarity
                    })

            # 3. Handle ähnliche Companies
            if similar_companies:
                if auto_merge:
                    # Automatisches Merge mit bester Ähnlichkeit
                    best_match = max(similar_companies, key=lambda x: x['similarity'])
                    return {
                        'success': False,
                        'company_id': best_match['id'],
                        'action': 'auto_merged',
                        'message': f'Auto-Merge mit "{best_match["name"]}" (Ähnlichkeit:
{best_match["similarity"]:.2%})',
                        'similar_found': similar_companies
                    }
                else:
                    # Benutzer-Entscheidung erforderlich
                    return {
                        'success': False,
                        'company_id': None,
                        'action': 'user_decision_required',
                        'message': f'{len(similar_companies)} ähnliche Companies gefunden',
                        'similar_found': similar_companies
                    }

            # 4. Safe Insert - keine Duplikate gefunden
            cursor.execute("""
                INSERT INTO companies (name, normalized_name, country_id, created_at)
                VALUES (?, ?, ?, CURRENT_TIMESTAMP)
            """, (name, normalized_name, country_id))

            new_company_id = cursor.lastrowid
            conn.commit()

            # Log successful insert
            self._log_duplicate_action('companies', name, None, 0.0, 'inserted')

            return {
                'success': True,
                'company_id': new_company_id,
                'action': 'inserted',
                'message': f'Company "{name}" erfolgreich erstellt'
            }

        except Exception as e:
            conn.rollback()
            return {
                'success': False,
                'company_id': None,
                'action': 'error',
                'message': f'Insert-Fehler: {e}'
            }
        finally:
            conn.close()

    def _normalize_company_name(self, name: str) -> str:
        """Normalisiert Company-Namen für Vergleiche"""
        if not name:
            return ""

        # Kleinschreibung, Sonderzeichen entfernen
        normalized = re.sub(r'[^\w\s]', '', name.lower())
        normalized = re.sub(r'\s+', ' ', normalized).strip()

        # Entferne Company-Suffixe
        suffixes = ['ltd', 'limited', 'corp', 'corporation', 'inc', 'incorporated',
                   'co', 'company', 'ag', 'gmbh', 'sa', 'plc', 'llc']

        words = normalized.split()
        filtered_words = [w for w in words if w not in suffixes]

        return ' '.join(filtered_words)

    def _log_duplicate_action(self, table_name: str, attempted_value: str,
    """_log_duplicate_action - TODO: Dokumentation hinzufügen"""
                            similar_value: Optional[str], similarity: float, action: str):
        """Logged Duplikat-Aktionen für Monitoring"""
        conn = sqlite3.connect(self.db_path)
        try:
            cursor = conn.cursor()
            cursor.execute("""
                INSERT INTO duplicate_prevention_log
                (table_name, attempted_value, similar_existing_value, similarity_score, action_taken)
                VALUES (?, ?, ?, ?, ?)
            """, (table_name, attempted_value, similar_value, similarity, action))
            conn.commit()
        except:
            pass  # Logging sollte nicht kritische Operationen unterbrechen
        finally:
            conn.close()


# BEISPIEL-USAGE:
if __name__ == "__main__":
    guards = DuplicatePreventionGuards()

    # Test Safe Insert
    result = guards.safe_insert_company("Rio Tinto Limited")
    print(f"Insert Result: {result}")
