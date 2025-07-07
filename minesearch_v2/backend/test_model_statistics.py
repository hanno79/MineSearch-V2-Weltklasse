"""
Author: rahn
Datum: 06.07.2025
Version: 1.0
Beschreibung: Umfassender statistischer Test aller Modelle mit detaillierten Metriken
"""

import sys
import json
import asyncio
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Any, Optional, Tuple
import re
from urllib.parse import urlparse

sys.path.insert(0, str(Path(__file__).parent.parent.parent))

from minesearch_v2.backend.search_service_multi import MultiProviderSearchService
from minesearch_v2.backend.extraction_validators import validate_restoration_cost, is_placeholder_value

# Logging Setup
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(message)s',
    handlers=[
        logging.FileHandler(f'model_statistics_{datetime.now().strftime("%Y%m%d_%H%M%S")}.log'),
        logging.StreamHandler()
    ]
)
logger = logging.getLogger(__name__)


class SourceCredibilityAnalyzer:
    """Bewertet die Glaubwürdigkeit von Quellen"""
    
    # Tier 1: Höchste Glaubwürdigkeit (Score: 90-100)
    TIER_1_DOMAINS = [
        'agnicoeagle.com', 'alamosgold.com', 'yamana.com',  # Unternehmensseiten
        'sedar.com', 'sec.gov', 'asx.com.au', 'tsx.com',   # Börsen/Regulatoren
        'nrcan.gc.ca', 'ontario.ca', 'quebec.ca',          # Regierung
        'mern.gouv.qc.ca'                                   # Mining-Ministerien
    ]
    
    # Tier 2: Hohe Glaubwürdigkeit (Score: 70-89)
    TIER_2_DOMAINS = [
        'mining.com', 'minerweb.com', 'northernminer.com',
        'mining-journal.com', 'miningweekly.com',
        'reuters.com', 'bloomberg.com', 'ft.com',
        'theglobeandmail.com', 'financialpost.com'
    ]
    
    # Tier 3: Mittlere Glaubwürdigkeit (Score: 50-69)
    TIER_3_DOMAINS = [
        'wikipedia.org', 'marketwatch.com', 'yahoo.com',
        'investingnews.com', 'kitco.com', 'mining-technology.com'
    ]
    
    @classmethod
    def calculate_source_credibility(cls, sources: List[Dict]) -> Dict[str, Any]:
        """Berechnet Glaubwürdigkeits-Score für Quellen"""
        if not sources:
            return {
                'score': 0,
                'tier_distribution': {},
                'top_sources': []
            }
        
        tier_counts = {1: 0, 2: 0, 3: 0, 4: 0}
        total_score = 0
        source_details = []
        
        for source in sources:
            url = source.get('url', source.get('value', ''))
            if not url:
                continue
                
            try:
                domain = urlparse(url).netloc.lower()
                tier, score = cls._get_domain_tier(domain)
                tier_counts[tier] += 1
                total_score += score
                
                source_details.append({
                    'url': url,
                    'domain': domain,
                    'tier': tier,
                    'score': score
                })
            except:
                tier_counts[4] += 1
                total_score += 30
        
        # Sortiere nach Score
        source_details.sort(key=lambda x: x['score'], reverse=True)
        
        avg_score = total_score / len(sources) if sources else 0
        
        return {
            'score': round(avg_score, 1),
            'tier_distribution': tier_counts,
            'top_sources': source_details[:5],
            'total_sources': len(sources)
        }
    
    @classmethod
    def _get_domain_tier(cls, domain: str) -> Tuple[int, int]:
        """Bestimmt Tier und Score für eine Domain"""
        # Prüfe Tier 1
        for tier1_domain in cls.TIER_1_DOMAINS:
            if tier1_domain in domain:
                return 1, 95
        
        # Prüfe Tier 2
        for tier2_domain in cls.TIER_2_DOMAINS:
            if tier2_domain in domain:
                return 2, 80
        
        # Prüfe Tier 3
        for tier3_domain in cls.TIER_3_DOMAINS:
            if tier3_domain in domain:
                return 3, 60
        
        # Default: Tier 4
        return 4, 30


class ModelStatisticsTester:
    """Führt umfassende statistische Tests aller Modelle durch"""
    
    def __init__(self):
        self.service = MultiProviderSearchService()
        self.credibility_analyzer = SourceCredibilityAnalyzer()
        self.start_time = datetime.now()
        self.results = {
            'test_info': {
                'timestamp': self.start_time.isoformat(),
                'test_type': 'comprehensive_model_statistics',
                'mine_tested': None
            },
            'model_statistics': {},
            'aggregated_stats': {},
            'rankings': {}
        }
        
        # Definiere alle erwarteten Felder
        self.all_fields = {
            'critical_financial': [
                'Restaurationskosten', 'Marktkapitalisierung', 'Investitionssumme',
                'Jahresumsatz', 'EBITDA', 'Cashflow'
            ],
            'important': [
                'Eigentümer', 'Betreiber', 'Status', 'Vorräte/Reserven',
                'Fördermenge', 'Produktionsstart', 'Produktionsende'
            ],
            'supplementary': [
                'Minentyp', 'Fläche', 'Mitarbeiterzahl', 'Region', 'Rohstoffabbau'
            ],
            'low_priority': [
                'x-Koordinate', 'y-Koordinate', 'GPS-Koordinaten'
            ]
        }
        self.total_fields = sum(len(fields) for fields in self.all_fields.values())
    
    async def test_all_models(self, mine_name: str, country: str, region: str, commodity: str):
        """Testet alle verfügbaren Modelle mit detaillierten Statistiken"""
        
        self.results['test_info']['mine_tested'] = {
            'name': mine_name,
            'country': country,
            'region': region,
            'commodity': commodity
        }
        
        # Hole alle verfügbaren Modelle
        all_models = list(self.service.registry.get_all_models().keys())
        logger.info(f"\n{'='*80}")
        logger.info(f"STATISTISCHER TEST ALLER {len(all_models)} MODELLE")
        logger.info(f"{'='*80}")
        logger.info(f"Mine: {mine_name} ({country})")
        logger.info(f"{'='*80}\n")
        
        # Teste jedes Modell
        for i, model_id in enumerate(all_models, 1):
            logger.info(f"\n[{i}/{len(all_models)}] Testing {model_id}...")
            
            stats = await self._test_single_model(
                model_id, mine_name, country, region, commodity
            )
            
            self.results['model_statistics'][model_id] = stats
            
            # Zeige Kurzübersicht
            if stats['success']:
                logger.info(f"  ✓ Zeit: {stats['response_time']:.1f}s | "
                          f"Felder: {stats['fields_coverage']['total_filled']}/{self.total_fields} | "
                          f"Quellen: {stats['sources_found']['total']} | "
                          f"Glaubwürdigkeit: {stats['sources_found']['credibility_score']:.0f}%")
                
                if stats['financial_data_quality']['has_restoration_costs']:
                    logger.info(f"  💰 Restaurationskosten: {stats['financial_data_quality']['restoration_cost_value']}")
            else:
                logger.info(f"  ✗ Fehler: {stats.get('error', 'Unbekannt')}")
            
            # Kurze Pause zwischen Tests
            if i < len(all_models):
                await asyncio.sleep(1)
        
        # Aggregiere Statistiken
        self._aggregate_statistics()
        
        # Erstelle Rankings
        self._create_rankings()
        
        # Generiere Reports
        self._generate_markdown_report()
        self._save_json_results()
        
        # Zeige Zusammenfassung
        self._print_summary()
    
    async def _test_single_model(self, model_id: str, mine_name: str, 
                                 country: str, region: str, commodity: str) -> Dict[str, Any]:
        """Testet ein einzelnes Modell und sammelt Statistiken"""
        
        start_time = datetime.now()
        
        try:
            # Führe Suche durch
            result = await self.service.search_with_model(
                model_id=model_id,
                mine_name=mine_name,
                country=country,
                region=region,
                commodity=commodity
            )
            
            response_time = (datetime.now() - start_time).total_seconds()
            
            if result.get('success'):
                data = result.get('data', {})
                sources = result.get('sources', [])
                
                # Analysiere Quellen
                source_analysis = self.credibility_analyzer.calculate_source_credibility(sources)
                
                # Analysiere Felder
                fields_analysis = self._analyze_field_coverage(data)
                
                # Analysiere Finanzdaten
                financial_analysis = self._analyze_financial_data(data)
                
                # Berechne Gesamt-Score
                reliability_score = self._calculate_reliability_score(
                    fields_analysis, financial_analysis, source_analysis
                )
                
                return {
                    'success': True,
                    'response_time': response_time,
                    'sources_found': {
                        'urls': len([s for s in sources if s.get('type') == 'url']),
                        'documents': len([s for s in sources if s.get('type') == 'document']),
                        'organizations': len([s for s in sources if s.get('type') == 'organization']),
                        'total': len(sources),
                        'credibility_score': source_analysis['score'],
                        'tier_distribution': source_analysis['tier_distribution'],
                        'top_sources': source_analysis['top_sources'][:3]
                    },
                    'fields_coverage': fields_analysis,
                    'financial_data_quality': financial_analysis,
                    'reliability_score': reliability_score,
                    'raw_data': data  # Für detaillierte Analyse
                }
            else:
                return {
                    'success': False,
                    'response_time': response_time,
                    'error': result.get('error', 'Unbekannt'),
                    'reliability_score': 0
                }
                
        except Exception as e:
            return {
                'success': False,
                'response_time': (datetime.now() - start_time).total_seconds(),
                'error': str(e),
                'reliability_score': 0
            }
    
    def _analyze_field_coverage(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiert die Feldabdeckung"""
        filled_fields = {k: v for k, v in data.items() if v and str(v).strip()}
        
        # Zähle nach Kategorie
        critical_filled = sum(1 for field in self.all_fields['critical_financial'] if field in filled_fields)
        important_filled = sum(1 for field in self.all_fields['important'] if field in filled_fields)
        supplementary_filled = sum(1 for field in self.all_fields['supplementary'] if field in filled_fields)
        low_priority_filled = sum(1 for field in self.all_fields['low_priority'] if field in filled_fields)
        
        return {
            'total_filled': len(filled_fields),
            'coverage_percentage': (len(filled_fields) / self.total_fields * 100),
            'critical_fields': critical_filled,
            'important_fields': important_filled,
            'supplementary_fields': supplementary_filled,
            'low_priority_fields': low_priority_filled,
            'by_category': {
                'critical_financial': f"{critical_filled}/{len(self.all_fields['critical_financial'])}",
                'important': f"{important_filled}/{len(self.all_fields['important'])}",
                'supplementary': f"{supplementary_filled}/{len(self.all_fields['supplementary'])}",
                'low_priority': f"{low_priority_filled}/{len(self.all_fields['low_priority'])}"
            }
        }
    
    def _analyze_financial_data(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Analysiert die Qualität der Finanzdaten"""
        resto_cost = data.get('Restaurationskosten')
        has_resto = bool(resto_cost and str(resto_cost).strip())
        
        # Validiere Restaurationskosten
        validated = False
        if has_resto:
            validated = bool(validate_restoration_cost(str(resto_cost)))
        
        # Zähle andere Finanzfelder
        other_financial = sum(1 for field in self.all_fields['critical_financial'][1:] 
                            if data.get(field) and str(data.get(field)).strip())
        
        return {
            'has_restoration_costs': has_resto,
            'restoration_cost_value': resto_cost if has_resto else None,
            'is_validated': validated,
            'other_financial_fields': other_financial,
            'financial_completeness': (other_financial + (1 if has_resto else 0)) / len(self.all_fields['critical_financial']) * 100
        }
    
    def _calculate_reliability_score(self, fields: Dict, financial: Dict, sources: Dict) -> float:
        """Berechnet einen Gesamt-Zuverlässigkeits-Score (0-100)"""
        # Gewichtung der Faktoren
        weights = {
            'field_coverage': 0.3,
            'financial_quality': 0.4,
            'source_credibility': 0.3
        }
        
        # Berechne Teil-Scores
        field_score = fields['coverage_percentage']
        
        # Finanzscore mit Bonus für Restaurationskosten
        financial_score = financial['financial_completeness']
        if financial['has_restoration_costs']:
            financial_score += 20  # Bonus
            if financial['is_validated']:
                financial_score += 10  # Extra Bonus für validierte Werte
        financial_score = min(financial_score, 100)
        
        source_score = sources.get('score', 0)
        
        # Gewichteter Durchschnitt
        total_score = (
            field_score * weights['field_coverage'] +
            financial_score * weights['financial_quality'] +
            source_score * weights['source_credibility']
        )
        
        return round(total_score, 1)
    
    def _aggregate_statistics(self):
        """Aggregiert Statistiken über alle Modelle"""
        successful_models = [
            (model_id, stats) for model_id, stats in self.results['model_statistics'].items()
            if stats['success']
        ]
        
        if not successful_models:
            return
        
        # Durchschnittswerte
        avg_response_time = sum(s[1]['response_time'] for s in successful_models) / len(successful_models)
        avg_fields = sum(s[1]['fields_coverage']['total_filled'] for s in successful_models) / len(successful_models)
        avg_sources = sum(s[1]['sources_found']['total'] for s in successful_models) / len(successful_models)
        avg_credibility = sum(s[1]['sources_found']['credibility_score'] for s in successful_models) / len(successful_models)
        
        # Modelle mit Restaurationskosten
        with_resto = [s for s in successful_models if s[1]['financial_data_quality']['has_restoration_costs']]
        
        self.results['aggregated_stats'] = {
            'total_models_tested': len(self.results['model_statistics']),
            'successful_tests': len(successful_models),
            'failed_tests': len(self.results['model_statistics']) - len(successful_models),
            'average_response_time': round(avg_response_time, 1),
            'average_fields_filled': round(avg_fields, 1),
            'average_sources_found': round(avg_sources, 1),
            'average_credibility_score': round(avg_credibility, 1),
            'models_with_restoration_costs': len(with_resto),
            'restoration_cost_percentage': round(len(with_resto) / len(successful_models) * 100, 1)
        }
    
    def _create_rankings(self):
        """Erstellt verschiedene Rankings der Modelle"""
        successful = [
            (model_id, stats) for model_id, stats in self.results['model_statistics'].items()
            if stats['success']
        ]
        
        # Sortiere nach verschiedenen Kriterien
        self.results['rankings'] = {
            'by_reliability_score': sorted(successful, key=lambda x: x[1]['reliability_score'], reverse=True)[:10],
            'by_response_time': sorted(successful, key=lambda x: x[1]['response_time'])[:10],
            'by_field_coverage': sorted(successful, key=lambda x: x[1]['fields_coverage']['total_filled'], reverse=True)[:10],
            'by_source_credibility': sorted(successful, key=lambda x: x[1]['sources_found']['credibility_score'], reverse=True)[:10],
            'with_restoration_costs': [s for s in successful if s[1]['financial_data_quality']['has_restoration_costs']]
        }
    
    def _generate_markdown_report(self):
        """Generiert einen detaillierten Markdown-Report"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        report_file = f'model_statistics_report_{timestamp}.md'
        
        with open(report_file, 'w', encoding='utf-8') as f:
            # Header
            f.write("# Model Statistics Report\n\n")
            f.write(f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}\n")
            f.write(f"**Mine Tested:** {self.results['test_info']['mine_tested']['name']} ")
            f.write(f"({self.results['test_info']['mine_tested']['country']})\n")
            f.write(f"**Total Models Tested:** {self.results['aggregated_stats']['total_models_tested']}\n\n")
            
            # Übersichtstabelle
            f.write("## Übersicht aller Modelle\n\n")
            f.write("| Modell | Zeit (s) | Quellen | Felder | Restaurationskosten | Glaubwürdigkeit | Score |\n")
            f.write("|--------|----------|---------|--------|---------------------|-----------------|-------|\n")
            
            # Sortiere nach Reliability Score
            sorted_models = sorted(
                self.results['model_statistics'].items(),
                key=lambda x: x[1].get('reliability_score', 0),
                reverse=True
            )
            
            for model_id, stats in sorted_models:
                if stats['success']:
                    resto = "✓ " + str(stats['financial_data_quality']['restoration_cost_value']) if stats['financial_data_quality']['has_restoration_costs'] else "✗"
                    f.write(f"| {model_id} | {stats['response_time']:.1f} | ")
                    f.write(f"{stats['sources_found']['total']} | ")
                    f.write(f"{stats['fields_coverage']['total_filled']}/{self.total_fields} | ")
                    f.write(f"{resto} | ")
                    f.write(f"{stats['sources_found']['credibility_score']:.0f}% | ")
                    f.write(f"{stats['reliability_score']:.1f} |\n")
                else:
                    f.write(f"| {model_id} | FEHLER | - | - | - | - | 0 |\n")
            
            # Aggregierte Statistiken
            f.write("\n## Aggregierte Statistiken\n\n")
            agg = self.results['aggregated_stats']
            f.write(f"- **Erfolgreiche Tests:** {agg['successful_tests']}/{agg['total_models_tested']}\n")
            f.write(f"- **Durchschnittliche Antwortzeit:** {agg['average_response_time']}s\n")
            f.write(f"- **Durchschnittliche Feldabdeckung:** {agg['average_fields_filled']:.0f} Felder\n")
            f.write(f"- **Durchschnittliche Quellenanzahl:** {agg['average_sources_found']:.0f}\n")
            f.write(f"- **Durchschnittliche Glaubwürdigkeit:** {agg['average_credibility_score']:.0f}%\n")
            f.write(f"- **Modelle mit Restaurationskosten:** {agg['models_with_restoration_costs']} ({agg['restoration_cost_percentage']:.1f}%)\n")
            
            # Top Rankings
            f.write("\n## Top 10 Rankings\n\n")
            
            # Nach Zuverlässigkeit
            f.write("### Nach Gesamt-Zuverlässigkeit\n\n")
            f.write("| Rang | Modell | Score | Zeit | Felder | Quellen |\n")
            f.write("|------|--------|-------|------|--------|----------|\n")
            for i, (model_id, stats) in enumerate(self.results['rankings']['by_reliability_score'][:10], 1):
                f.write(f"| {i} | {model_id} | {stats['reliability_score']:.1f} | ")
                f.write(f"{stats['response_time']:.1f}s | ")
                f.write(f"{stats['fields_coverage']['total_filled']} | ")
                f.write(f"{stats['sources_found']['total']} |\n")
            
            # Nach Geschwindigkeit
            f.write("\n### Schnellste Modelle\n\n")
            f.write("| Rang | Modell | Zeit | Score |\n")
            f.write("|------|--------|------|-------|\n")
            for i, (model_id, stats) in enumerate(self.results['rankings']['by_response_time'][:10], 1):
                f.write(f"| {i} | {model_id} | {stats['response_time']:.1f}s | {stats['reliability_score']:.1f} |\n")
            
            # Mit Restaurationskosten
            f.write("\n### Modelle mit Restaurationskosten\n\n")
            f.write("| Modell | Wert | Validiert | Score |\n")
            f.write("|--------|------|-----------|-------|\n")
            for model_id, stats in self.results['rankings']['with_restoration_costs']:
                validated = "✓" if stats['financial_data_quality']['is_validated'] else "✗"
                f.write(f"| {model_id} | {stats['financial_data_quality']['restoration_cost_value']} | ")
                f.write(f"{validated} | {stats['reliability_score']:.1f} |\n")
            
            # Empfehlungen
            f.write("\n## Empfehlungen\n\n")
            
            # Beste Balance
            f.write("### Beste Balance (Qualität/Geschwindigkeit)\n")
            balanced = [m for m in self.results['rankings']['by_reliability_score'][:10] 
                       if m[1]['response_time'] < 60]
            if balanced:
                f.write(f"**Empfohlen:** {balanced[0][0]} (Score: {balanced[0][1]['reliability_score']:.1f}, ")
                f.write(f"Zeit: {balanced[0][1]['response_time']:.1f}s)\n\n")
            
            # Für Finanzdaten
            f.write("### Für Finanzdaten (Restaurationskosten)\n")
            if self.results['rankings']['with_restoration_costs']:
                best_financial = self.results['rankings']['with_restoration_costs'][0]
                f.write(f"**Empfohlen:** {best_financial[0]} ")
                f.write(f"({best_financial[1]['financial_data_quality']['restoration_cost_value']})\n\n")
            
            # Für schnelle Suchen
            f.write("### Für schnelle Suchen\n")
            fast_reliable = [m for m in self.results['rankings']['by_response_time'][:5] 
                           if m[1]['reliability_score'] > 50]
            if fast_reliable:
                f.write(f"**Empfohlen:** {fast_reliable[0][0]} (Zeit: {fast_reliable[0][1]['response_time']:.1f}s, ")
                f.write(f"Score: {fast_reliable[0][1]['reliability_score']:.1f})\n")
        
        logger.info(f"\n✅ Markdown-Report gespeichert: {report_file}")
    
    def _save_json_results(self):
        """Speichert die Rohdaten als JSON"""
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        json_file = f'model_statistics_raw_{timestamp}.json'
        
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(self.results, f, ensure_ascii=False, indent=2)
        
        logger.info(f"✅ JSON-Rohdaten gespeichert: {json_file}")
    
    def _print_summary(self):
        """Zeigt eine Zusammenfassung in der Konsole"""
        logger.info(f"\n{'='*80}")
        logger.info("ZUSAMMENFASSUNG")
        logger.info(f"{'='*80}")
        
        # Top 5 Modelle
        logger.info("\n🏆 TOP 5 MODELLE (nach Zuverlässigkeit):")
        for i, (model_id, stats) in enumerate(self.results['rankings']['by_reliability_score'][:5], 1):
            logger.info(f"{i}. {model_id}: Score {stats['reliability_score']:.1f} "
                       f"({stats['fields_coverage']['total_filled']} Felder, "
                       f"{stats['response_time']:.1f}s)")
        
        # Modelle mit Restaurationskosten
        logger.info(f"\n💰 MODELLE MIT RESTAURATIONSKOSTEN ({len(self.results['rankings']['with_restoration_costs'])}):")
        for model_id, stats in self.results['rankings']['with_restoration_costs'][:5]:
            logger.info(f"- {model_id}: {stats['financial_data_quality']['restoration_cost_value']}")
        
        # Gesamtdauer
        total_duration = (datetime.now() - self.start_time).total_seconds()
        logger.info(f"\n⏱️  Gesamtdauer: {total_duration:.1f}s ({total_duration/60:.1f} Minuten)")
        logger.info(f"\n✅ Test abgeschlossen!")


async def main():
    """Hauptfunktion"""
    tester = ModelStatisticsTester()
    
    # Test mit Canadian Malartic Mine
    await tester.test_all_models(
        mine_name='Canadian Malartic Mine',
        country='Canada',
        region='Quebec',
        commodity='Gold'
    )


if __name__ == "__main__":
    asyncio.run(main())