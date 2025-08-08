#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.07.2025
Version: 1.0
Beschreibung: Data-Validator Agent - Comprehensive Live-Tests mit Debug-Validation
"""

import sys
import os
import sqlite3
import json
import time
import uuid
from datetime import datetime
from typing import Dict, List, Any, Optional
import asyncio

# Add project root to path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from config.models import MODELS_CONFIG
from enhanced_search_operations import EnhancedSearchOperations

class DataValidator:
    """
    Data-Validator Agent für umfassende Live-Tests mit Debug-Validation
    """
    
    def __init__(self):
        self.db_path = 'mines.db'
        self.validator = DatabaseValidator()
        self.search_service = EnhancedSearchOperations()
        self.validation_results = []
        self.session_id = f"data_validator_{int(time.time())}"
        
        # Modelle für Multi-Model-Test auswählen (5+ verschiedene Provider)
        self.test_models = [
            ('perplexity', 'sonar-pro'),
            ('openrouter', 'deepseek-free'),
            ('openrouter', 'mistral-small-free'),
            ('openrouter', 'cypher-alpha-free'),
            ('openai', 'gpt-4o-mini'),
            ('anthropic', 'claude-3-haiku'),
            ('gemini', 'gemini-1.5-flash'),
            ('grok', 'grok-3-mini')
        ]
        
        # Test-Minen aus CSV
        self.test_mines = [
            {'mine_name': 'Kiena Mine', 'country': 'Canada', 'region': 'Quebec', 'commodity': 'Gold'},
            {'mine_name': 'Borden Mine', 'country': 'Canada', 'region': 'Ontario', 'commodity': 'Gold'},
            {'mine_name': 'Mount Gibson', 'country': 'Australia', 'region': 'Western Australia', 'commodity': 'Iron Ore'}
        ]
        
    def log_validation(self, message: str, level: str = "INFO"):
        """Validation-Ereignis loggen"""
        timestamp = datetime.now().isoformat()
        log_entry = f"[{timestamp}] [{level}] [DATA-VALIDATOR] {message}"
        print(log_entry)
        
        self.validation_results.append({
            'timestamp': timestamp,
            'level': level,
            'message': message
        })
        
    def get_database_snapshot(self) -> Dict[str, Any]:
        """Vollständigen Database-Snapshot erstellen"""
        snapshot = {}
        
        try:
            conn = sqlite3.connect(self.db_path)
            cursor = conn.cursor()
            
            # Alle Tabellen durchgehen
            tables = ['sources', 'mines', 'search_results', 'model_statistics', 
                     'field_consistency', 'model_summary', 'field_statistics']
            
            for table in tables:
                cursor.execute(f"SELECT COUNT(*) FROM {table}")
                count = cursor.fetchone()[0]
                snapshot[f"{table}_count"] = count
                
                # Letzte 5 Records für Detailanalyse
                cursor.execute(f"SELECT * FROM {table} ORDER BY id DESC LIMIT 5")
                records = cursor.fetchall()
                snapshot[f"{table}_latest"] = records
                
            conn.close()
            
        except Exception as e:
            self.log_validation(f"Fehler beim Database-Snapshot: {str(e)}", "ERROR")
            
        return snapshot
        
    def validate_model_call(self, provider: str, model_id: str, mine_data: Dict, 
                          result: Dict) -> Dict[str, Any]:
        """Einzelnen Modell-Aufruf in Echtzeit validieren"""
        validation = {
            'provider': provider,
            'model_id': model_id,
            'mine_name': mine_data['mine_name'],
            'timestamp': datetime.now().isoformat(),
            'call_successful': False,
            'data_extracted': False,
            'fields_found': 0,
            'sources_count': 0,
            'response_time_ms': 0,
            'errors': [],
            'data_quality': {}
        }
        
        try:
            # Erfolg des API-Aufrufs prüfen
            if result and 'success' in result:
                validation['call_successful'] = result['success']
                
            # Response-Zeit validieren
            if 'response_time_ms' in result:
                validation['response_time_ms'] = result['response_time_ms']
                
            # Strukturierte Daten prüfen
            if result and 'structured_data' in result and result['structured_data']:
                validation['data_extracted'] = True
                structured = result['structured_data']
                
                # Felder zählen
                fields_count = 0
                for key, value in structured.items():
                    if value and str(value).strip() and str(value).strip() != 'N/A':
                        fields_count += 1
                        
                validation['fields_found'] = fields_count
                
            # Quellen validieren
            if result and 'sources' in result and result['sources']:
                validation['sources_count'] = len(result['sources'])
                
            # Fehler erfassen
            if result and 'error_message' in result and result['error_message']:
                validation['errors'].append(result['error_message'])
                
        except Exception as e:
            validation['errors'].append(f"Validation Error: {str(e)}")
            
        return validation
        
    def validate_database_write(self, before_snapshot: Dict, after_snapshot: Dict, 
                              expected_writes: Dict) -> Dict[str, Any]:
        """Database-Writes nach Modell-Aufruf validieren"""
        db_validation = {
            'timestamp': datetime.now().isoformat(),
            'writes_detected': {},
            'expected_vs_actual': {},
            'data_integrity_issues': []
        }
        
        try:
            # Änderungen in jeder Tabelle prüfen
            for table in ['search_results', 'model_statistics', 'field_consistency', 
                         'field_statistics', 'model_summary']:
                
                before_count = before_snapshot.get(f"{table}_count", 0)
                after_count = after_snapshot.get(f"{table}_count", 0)
                
                writes_detected = after_count - before_count
                db_validation['writes_detected'][table] = writes_detected
                
                # Erwartete vs tatsächliche Writes
                expected = expected_writes.get(table, 0)
                db_validation['expected_vs_actual'][table] = {
                    'expected': expected,
                    'actual': writes_detected,
                    'match': writes_detected == expected
                }
                
                if writes_detected != expected:
                    db_validation['data_integrity_issues'].append(
                        f"{table}: Expected {expected} writes, got {writes_detected}"
                    )
                    
        except Exception as e:
            db_validation['data_integrity_issues'].append(f"Validation Error: {str(e)}")
            
        return db_validation
        
    async def run_comprehensive_validation(self):
        """Hauptfunktion für umfassende Data-Validation"""
        self.log_validation("=== STARTING COMPREHENSIVE DATA VALIDATION ===", "INFO")
        
        # Initialer Database-Snapshot
        initial_snapshot = self.get_database_snapshot()
        self.log_validation(f"Initial DB Snapshot: {json.dumps(initial_snapshot, indent=2)}")
        
        validation_summary = {
            'session_id': self.session_id,
            'start_time': datetime.now().isoformat(),
            'models_tested': 0,
            'mines_tested': 0,
            'successful_calls': 0,
            'failed_calls': 0,
            'data_extraction_success': 0,
            'database_integrity_issues': 0,
            'detailed_results': []
        }
        
        # Für jede Test-Mine
        for mine_idx, mine_data in enumerate(self.test_mines):
            self.log_validation(f"\\n=== TESTING MINE {mine_idx + 1}/3: {mine_data['mine_name']} ===")
            
            mine_session_id = f"{self.session_id}_mine_{mine_idx + 1}"
            
            # Für jedes Test-Modell
            for model_idx, (provider, model_id) in enumerate(self.test_models):
                self.log_validation(f"\\n--- Testing Model {model_idx + 1}/8: {provider}/{model_id} ---")
                
                # Pre-Call Database-Snapshot
                before_snapshot = self.get_database_snapshot()
                
                try:
                    # LIVE-SUCHE DURCHFÜHREN
                    self.log_validation(f"Calling {provider}/{model_id} for {mine_data['mine_name']}")
                    
                    start_time = time.time()
                    
                    # Einzelner Modell-Aufruf über Enhanced Search Service
                    full_model_id = f"{provider}:{model_id}"
                    result = await self.search_service.search_single_model(
                        model_id=full_model_id,
                        mine_name=mine_data['mine_name'],
                        country=mine_data['country'],
                        commodity=mine_data['commodity'],
                        region=mine_data['region']
                    )
                    
                    end_time = time.time()
                    actual_response_time = (end_time - start_time) * 1000
                    
                    # Post-Call Database-Snapshot
                    after_snapshot = self.get_database_snapshot()
                    
                    # ECHTZEIT-VALIDATION
                    call_validation = self.validate_model_call(provider, model_id, mine_data, result)
                    call_validation['actual_response_time_ms'] = actual_response_time
                    
                    # DATABASE-WRITE VALIDATION
                    expected_writes = {
                        'search_results': 1,
                        'model_statistics': 1,
                        'field_statistics': 10,  # Etwa 10 Felder erwartet
                        'model_summary': 1
                    }
                    
                    db_validation = self.validate_database_write(
                        before_snapshot, after_snapshot, expected_writes
                    )
                    
                    # Ergebnisse sammeln
                    test_result = {
                        'mine': mine_data['mine_name'],
                        'provider': provider,
                        'model_id': model_id,
                        'call_validation': call_validation,
                        'database_validation': db_validation,
                        'raw_result': result
                    }
                    
                    validation_summary['detailed_results'].append(test_result)
                    validation_summary['models_tested'] += 1
                    
                    if call_validation['call_successful']:
                        validation_summary['successful_calls'] += 1
                        self.log_validation(f"✅ SUCCESS: {provider}/{model_id} - Fields: {call_validation['fields_found']}, Sources: {call_validation['sources_count']}")
                    else:
                        validation_summary['failed_calls'] += 1
                        self.log_validation(f"❌ FAILED: {provider}/{model_id} - Errors: {call_validation['errors']}", "ERROR")
                        
                    if call_validation['data_extracted']:
                        validation_summary['data_extraction_success'] += 1
                        
                    if db_validation['data_integrity_issues']:
                        validation_summary['database_integrity_issues'] += len(db_validation['data_integrity_issues'])
                        self.log_validation(f"⚠️  DB Issues: {db_validation['data_integrity_issues']}", "WARNING")
                        
                except Exception as e:
                    self.log_validation(f"❌ EXCEPTION during {provider}/{model_id}: {str(e)}", "ERROR")
                    validation_summary['failed_calls'] += 1
                    
                # Kurze Pause zwischen Aufrufen
                await asyncio.sleep(2)
                
            validation_summary['mines_tested'] += 1
            
            # Längere Pause zwischen Minen
            await asyncio.sleep(5)
            
        # Final Database-Snapshot
        final_snapshot = self.get_database_snapshot()
        
        # Zusammenfassung erstellen
        validation_summary['end_time'] = datetime.now().isoformat()
        validation_summary['final_db_snapshot'] = final_snapshot
        validation_summary['success_rate'] = (validation_summary['successful_calls'] / 
                                            validation_summary['models_tested'] * 100) if validation_summary['models_tested'] > 0 else 0
        validation_summary['data_extraction_rate'] = (validation_summary['data_extraction_success'] / 
                                                     validation_summary['models_tested'] * 100) if validation_summary['models_tested'] > 0 else 0
        
        # Validation-Bericht speichern
        report_filename = f"data_validation_report_{int(time.time())}.json"
        with open(report_filename, 'w') as f:
            json.dump(validation_summary, f, indent=2, default=str)
            
        self.log_validation(f"\\n=== VALIDATION COMPLETED ===")
        self.log_validation(f"Report saved: {report_filename}")
        self.log_validation(f"Models tested: {validation_summary['models_tested']}")
        self.log_validation(f"Success rate: {validation_summary['success_rate']:.1f}%")
        self.log_validation(f"Data extraction rate: {validation_summary['data_extraction_rate']:.1f}%")
        self.log_validation(f"DB integrity issues: {validation_summary['database_integrity_issues']}")
        
        return validation_summary

if __name__ == "__main__":
    async def main():
        validator = DataValidator()
        results = await validator.run_comprehensive_validation()
        print("\\n" + "="*80)
        print("DATA VALIDATION COMPLETED")
        print(f"Check report file for detailed results")
        print("="*80)
        
    asyncio.run(main())