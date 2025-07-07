"""
Author: rahn
Datum: 07.07.2025
Version: 1.0
Beschreibung: Test des erweiterten MineSearch v2 Systems
"""

import sys
import asyncio
import json
import logging
from datetime import datetime
from pathlib import Path

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from minesearch_v2.backend.search_service_multi_enhanced import EnhancedMultiProviderSearchService
from minesearch_v2.backend.model_tier_strategy import ModelTierStrategy

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s',
    handlers=[
        logging.FileHandler(f'enhanced_test_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class EnhancedSystemTester:
    """Testet das erweiterte MineSearch System"""
    
    def __init__(self):
        self.service = EnhancedMultiProviderSearchService()
        self.tier_strategy = ModelTierStrategy()
        self.test_results = {
            'timestamp': datetime.now().isoformat(),
            'test_type': 'enhanced_comprehensive',
            'mines_tested': [],
            'phase_results': {},
            'model_performance': {},
            'overall_improvements': {}
        }
    
    async def test_comprehensive_search(self, mine_name: str, country: str, 
                                      region: str = None, commodity: str = None):
        """Führt umfassenden Test einer Mine durch"""
        logger.info(f"\n{'='*80}")
        logger.info(f"TESTE MINE: {mine_name} ({country})")
        logger.info(f"{'='*80}\n")
        
        start_time = datetime.now()
        
        # Test mit dem neuen zweistufigen System
        result = await self.service.search_comprehensive(
            mine_name=mine_name,
            country=country,
            region=region,
            commodity=commodity
        )
        
        duration = (datetime.now() - start_time).total_seconds()
        
        # Analysiere Ergebnisse
        mine_result = {
            'mine_name': mine_name,
            'country': country,
            'region': region,
            'commodity': commodity,
            'duration': duration,
            'success': result.get('success', False),
            'fields_found': len([v for v in result.get('data', {}).values() if v]),
            'sources_collected': result.get('metadata', {}).get('sources_collected', 0),
            'confidence_scores': result.get('confidence_scores', {}),
            'overall_confidence': result.get('overall_confidence', 0),
            'high_confidence_fields': result.get('high_confidence_fields', 0),
            'data': result.get('data', {})
        }
        
        # Spezielle Prüfung für Restaurationskosten
        resto_cost = result.get('data', {}).get('Restaurationskosten')
        if resto_cost:
            mine_result['restoration_cost_found'] = True
            mine_result['restoration_cost_value'] = resto_cost
            mine_result['restoration_cost_confidence'] = (
                result.get('confidence_scores', {})
                .get('Restaurationskosten', {})
                .get('confidence', 0)
            )
        else:
            mine_result['restoration_cost_found'] = False
        
        self.test_results['mines_tested'].append(mine_result)
        
        # Zeige Ergebnisse
        self._print_mine_results(mine_result)
        
        return mine_result
    
    async def test_multi_mine_batch(self):
        """Testet mehrere Minen für Vergleich"""
        test_mines = [
            {
                'mine_name': 'Canadian Malartic Mine',
                'country': 'Canada',
                'region': 'Quebec',
                'commodity': 'Gold'
            },
            {
                'mine_name': 'Éléonore Mine',  # Mit Akzent
                'country': 'Canada',
                'region': 'Québec',  # Mit Akzent
                'commodity': 'Gold'
            },
            {
                'mine_name': 'Antamina Mine',
                'country': 'Peru',
                'region': 'Ancash',
                'commodity': 'Copper'
            },
            {
                'mine_name': 'Olympic Dam',
                'country': 'Australia',
                'region': 'South Australia',
                'commodity': 'Copper'
            }
        ]
        
        for mine_config in test_mines:
            await self.test_comprehensive_search(**mine_config)
            # Kurze Pause zwischen Tests
            await asyncio.sleep(2)
        
        # Berechne Verbesserungen
        self._calculate_improvements()
        
        # Speichere Ergebnisse
        self._save_results()
        
        # Zeige Zusammenfassung
        self._print_summary()
    
    def _print_mine_results(self, result: dict):
        """Zeigt Ergebnisse für eine Mine"""
        logger.info(f"\n🏭 {result['mine_name']} - ERGEBNISSE:")
        logger.info(f"   ⏱️  Dauer: {result['duration']:.1f}s")
        logger.info(f"   📊 Felder gefüllt: {result['fields_found']}")
        logger.info(f"   📚 Quellen gesammelt: {result['sources_collected']}")
        logger.info(f"   🎯 Gesamt-Konfidenz: {result['overall_confidence']:.2%}")
        logger.info(f"   ✅ High-Confidence Felder: {result['high_confidence_fields']}")
        
        if result['restoration_cost_found']:
            logger.info(f"   💰 Restaurationskosten: {result['restoration_cost_value']} "
                       f"(Konfidenz: {result['restoration_cost_confidence']:.2%})")
        else:
            logger.info(f"   ❌ Restaurationskosten: Nicht gefunden")
        
        # Top 5 Felder mit höchster Konfidenz
        if result['confidence_scores']:
            sorted_fields = sorted(
                result['confidence_scores'].items(),
                key=lambda x: x[1].get('confidence', 0),
                reverse=True
            )[:5]
            
            logger.info("\n   Top-Felder nach Konfidenz:")
            for field, score_info in sorted_fields:
                logger.info(f"   - {field}: {score_info['confidence']:.2%} "
                           f"({score_info.get('agreement', 'N/A')})")
    
    def _calculate_improvements(self):
        """Berechnet Verbesserungen gegenüber altem System"""
        if not self.test_results['mines_tested']:
            return
        
        # Durchschnittswerte
        avg_fields = sum(m['fields_found'] for m in self.test_results['mines_tested']) / len(self.test_results['mines_tested'])
        avg_sources = sum(m['sources_collected'] for m in self.test_results['mines_tested']) / len(self.test_results['mines_tested'])
        avg_confidence = sum(m['overall_confidence'] for m in self.test_results['mines_tested']) / len(self.test_results['mines_tested'])
        
        # Restaurationskosten-Erfolgsrate
        resto_success = sum(1 for m in self.test_results['mines_tested'] if m['restoration_cost_found'])
        resto_rate = resto_success / len(self.test_results['mines_tested'])
        
        self.test_results['overall_improvements'] = {
            'avg_fields_per_mine': avg_fields,
            'avg_sources_per_mine': avg_sources,
            'avg_confidence': avg_confidence,
            'restoration_cost_success_rate': resto_rate,
            'estimated_coverage': (avg_fields / 21) * 100  # Von 21 möglichen Feldern
        }
    
    def _save_results(self):
        """Speichert Testergebnisse"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        filename = f'enhanced_test_results_{timestamp}.json'
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(self.test_results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"\n📁 Ergebnisse gespeichert: {filename}")
    
    def _print_summary(self):
        """Zeigt Gesamtzusammenfassung"""
        improvements = self.test_results['overall_improvements']
        
        logger.info(f"\n{'='*80}")
        logger.info("ZUSAMMENFASSUNG - ENHANCED SYSTEM")
        logger.info(f"{'='*80}")
        
        logger.info(f"\n📊 DURCHSCHNITTSWERTE:")
        logger.info(f"   - Felder pro Mine: {improvements['avg_fields_per_mine']:.1f}")
        logger.info(f"   - Quellen pro Mine: {improvements['avg_sources_per_mine']:.1f}")
        logger.info(f"   - Gesamt-Konfidenz: {improvements['avg_confidence']:.2%}")
        logger.info(f"   - Geschätzte Abdeckung: {improvements['estimated_coverage']:.1f}%")
        
        logger.info(f"\n💰 RESTAURATIONSKOSTEN:")
        logger.info(f"   - Erfolgsrate: {improvements['restoration_cost_success_rate']:.1%}")
        
        logger.info(f"\n🎯 ERWARTETE VERBESSERUNGEN:")
        logger.info(f"   - Feldabdeckung: 65% → {improvements['estimated_coverage']:.1f}%")
        logger.info(f"   - Quellenzahl: 3-5 → {improvements['avg_sources_per_mine']:.0f}")
        logger.info(f"   - Restaurationskosten: 65% → {improvements['restoration_cost_success_rate']:.0%}")
    
    async def test_accent_handling(self):
        """Testet spezifisch die Akzent-Behandlung"""
        logger.info(f"\n{'='*80}")
        logger.info("TESTE AKZENT-BEHANDLUNG")
        logger.info(f"{'='*80}\n")
        
        # Test mit und ohne Akzente
        test_cases = [
            ('Quebec', 'Québec'),
            ('Eleonore', 'Éléonore'),
            ('Montreal', 'Montréal')
        ]
        
        for without_accent, with_accent in test_cases:
            logger.info(f"\nTeste: {without_accent} vs {with_accent}")
            
            # Generiere Varianten
            from minesearch_v2.backend.utils import generate_name_variants
            
            variants_without = generate_name_variants(without_accent)
            variants_with = generate_name_variants(with_accent)
            
            # Prüfe ob beide Versionen generiert werden
            logger.info(f"Varianten für '{without_accent}': {len(variants_without)}")
            logger.info(f"Varianten für '{with_accent}': {len(variants_with)}")
            
            # Prüfe ob Akzent-Version in Varianten enthalten
            if with_accent in variants_without or with_accent.lower() in [v.lower() for v in variants_without]:
                logger.info(f"✅ Akzent-Version '{with_accent}' wurde generiert")
            else:
                logger.info(f"❌ Akzent-Version '{with_accent}' fehlt")


async def main():
    """Hauptfunktion"""
    tester = EnhancedSystemTester()
    
    # Teste Akzent-Behandlung
    await tester.test_accent_handling()
    
    # Führe Haupt-Tests durch
    await tester.test_multi_mine_batch()


if __name__ == "__main__":
    asyncio.run(main())