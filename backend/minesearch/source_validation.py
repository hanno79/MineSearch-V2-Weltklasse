"""
Author: rahn
Datum: 27.08.2025
Version: 1.0
Beschreibung: Source Validation - Assertions für korrekte Quellenverwendung
"""

import logging
from typing import Dict, List, Any, Optional
from dataclasses import dataclass

logger = logging.getLogger(__name__)


@dataclass
class SourceValidationResult:
    """Ergebnis der Quellenvalidierung"""
    valid: bool
    provider: str
    model_id: str
    issues: List[str]
    discovered_sources_count: int
    result_sources_count: int
    missing_sources: List[str]


class SourceValidator:
    """Validiert dass Provider discovered_sources korrekt verwenden"""
    
    def validate_search_result(self, search_result, provider_name: str, model_id: str, 
                              discovered_sources: List[Dict], options: Dict[str, Any]) -> SourceValidationResult:
        """
        Validiert ein SearchResult auf korrekte Quellenverwendung
        
        Args:
            search_result: Das SearchResult vom Provider
            provider_name: Name des Providers
            model_id: Model ID
            discovered_sources: Die übergebenen discovered_sources
            options: Search options
            
        Returns:
            SourceValidationResult mit Validierungsergebnissen
        """
        issues = []
        
        # ASSERTION 1: SearchResult muss sources haben
        if not hasattr(search_result, 'sources') or not search_result.sources:
            if discovered_sources:  # Nur wenn discovered_sources vorhanden waren
                issues.append("SearchResult.sources ist leer obwohl discovered_sources übergeben wurden")
        
        # ASSERTION 2: Alle discovered_sources sollten im SearchResult sein
        missing_sources = []
        if discovered_sources and search_result.sources:
            discovered_urls = {s.get('url') for s in discovered_sources if s.get('url')}
            result_urls = {s.get('url') for s in search_result.sources if s.get('url')}
            
            missing_urls = discovered_urls - result_urls
            if missing_urls:
                missing_sources = list(missing_urls)
                issues.append(f"Fehlende discovered_sources im SearchResult: {len(missing_urls)} URLs")
        
        # ASSERTION 3: Alle Basis-Quellen sollten als 'searched': True markiert sein
        if search_result.sources:
            unsearched_count = 0
            for source in search_result.sources:
                if source.get('type') == 'discovered' and not source.get('searched'):
                    unsearched_count += 1
            
            if unsearched_count > 0:
                issues.append(f"{unsearched_count} discovered sources nicht als 'searched' markiert")
        
        # ASSERTION 4: Keine 0.5 Fallback-Reliability Werte (REGEL 10)
        if search_result.sources:
            fallback_count = 0
            for source in search_result.sources:
                if source.get('reliability') == 0.5:
                    fallback_count += 1
            
            if fallback_count > 0:
                issues.append(f"REGEL 10 VERLETZUNG: {fallback_count} sources mit 0.5 fallback reliability")
        
        # ASSERTION 5: Provider sollte discovered_sources_count in metadata haben
        if hasattr(search_result, 'metadata') and search_result.metadata:
            reported_count = search_result.metadata.get('discovered_sources_count')
            actual_count = len(discovered_sources) if discovered_sources else 0
            
            if reported_count != actual_count:
                issues.append(f"Metadata discovered_sources_count ({reported_count}) != actual count ({actual_count})")
        
        valid = len(issues) == 0
        
        if not valid:
            logger.warning(f"[SOURCE_VALIDATION] {provider_name}:{model_id} - {len(issues)} Issues: {issues}")
        else:
            logger.info(f"[SOURCE_VALIDATION] {provider_name}:{model_id} - ✅ Alle Assertions erfüllt")
        
        return SourceValidationResult(
            valid=valid,
            provider=provider_name,
            model_id=model_id,
            issues=issues,
            discovered_sources_count=len(discovered_sources) if discovered_sources else 0,
            result_sources_count=len(search_result.sources) if search_result.sources else 0,
            missing_sources=missing_sources
        )
    
    def validate_orchestration_result(self, orchestration_result, expected_discovered_sources: List[Dict]) -> List[SourceValidationResult]:
        """
        Validiert ein gesamtes Orchestration-Ergebnis
        
        Args:
            orchestration_result: OrchestrationResult mit allen Model-Ergebnissen
            expected_discovered_sources: Die erwarteten discovered_sources
            
        Returns:
            Liste von SourceValidationResult für jeden Provider
        """
        results = []
        
        # Validiere jeden erfolgreichen Model-Result
        for model_result in orchestration_result.successful_models:
            # Simuliere SearchResult-ähnliche Struktur
            fake_search_result = type('SearchResult', (), {
                'sources': model_result.sources,
                'metadata': {'discovered_sources_count': len(expected_discovered_sources)}
            })()
            
            validation_result = self.validate_search_result(
                search_result=fake_search_result,
                provider_name="orchestrator",
                model_id=model_result.model_id,
                discovered_sources=expected_discovered_sources,
                options={}
            )
            
            results.append(validation_result)
        
        return results
    
    def create_validation_report(self, validation_results: List[SourceValidationResult]) -> Dict[str, Any]:
        """
        Erstellt einen zusammenfassenden Validierungsbericht
        
        Args:
            validation_results: Liste von SourceValidationResult
            
        Returns:
            Dict mit Zusammenfassung und Details
        """
        total_count = len(validation_results)
        valid_count = sum(1 for r in validation_results if r.valid)
        invalid_count = total_count - valid_count
        
        # Sammle alle Issues
        all_issues = []
        for result in validation_results:
            if result.issues:
                all_issues.extend([f"{result.provider}:{result.model_id} - {issue}" for issue in result.issues])
        
        # Sammle Statistiken
        avg_discovered_count = sum(r.discovered_sources_count for r in validation_results) / max(total_count, 1)
        avg_result_count = sum(r.result_sources_count for r in validation_results) / max(total_count, 1)
        
        report = {
            'summary': {
                'total_providers': total_count,
                'valid_providers': valid_count,
                'invalid_providers': invalid_count,
                'success_rate': f"{valid_count/max(total_count, 1)*100:.1f}%"
            },
            'statistics': {
                'avg_discovered_sources': round(avg_discovered_count, 1),
                'avg_result_sources': round(avg_result_count, 1),
                'total_issues': len(all_issues)
            },
            'issues': all_issues,
            'details': [
                {
                    'provider': r.provider,
                    'model_id': r.model_id,
                    'valid': r.valid,
                    'discovered_count': r.discovered_sources_count,
                    'result_count': r.result_sources_count,
                    'issues': r.issues,
                    'missing_sources_count': len(r.missing_sources)
                }
                for r in validation_results
            ]
        }
        
        return report


# Global validator instance
source_validator = SourceValidator()