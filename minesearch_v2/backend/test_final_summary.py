"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Finale Zusammenfassung aller getesteten Provider und Modelle
"""

import logging
from database import db_manager, ModelSummary, ModelStatistics, Source, SearchResult
from sqlalchemy import func
import json

logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')
logger = logging.getLogger(__name__)


def generate_final_report():
    """Erstelle finale Zusammenfassung aller Tests"""
    
    with db_manager.get_session() as session:
        # Gesamtstatistiken
        total_models = session.query(func.count(ModelSummary.model_id)).scalar()
        total_tests = session.query(func.count(ModelStatistics.id)).scalar()
        total_sources = session.query(func.count(Source.id)).scalar()
        total_results = session.query(func.count(SearchResult.id)).scalar()
        
        logger.info("=== FINALE TEST-ZUSAMMENFASSUNG ===")
        logger.info(f"\nGESAMTSTATISTIKEN:")
        logger.info(f"  - Getestete Modelle: {total_models}")
        logger.info(f"  - Durchgeführte Tests: {total_tests}")
        logger.info(f"  - Quellen in DB: {total_sources}")
        logger.info(f"  - Suchergebnisse: {total_results}")
        
        # Alle Modelle mit Statistiken
        all_models = session.query(ModelSummary).order_by(
            ModelSummary.success_rate.desc(),
            ModelSummary.avg_fields_found.desc()
        ).all()
        
        # Gruppiere nach Provider
        providers = {}
        for model in all_models:
            provider = model.model_id.split(':')[0]
            if provider not in providers:
                providers[provider] = []
            providers[provider].append(model)
        
        # Provider-Übersicht
        logger.info(f"\nPROVIDER-ÜBERSICHT ({len(providers)} Provider):")
        for provider, models in providers.items():
            logger.info(f"\n{provider.upper()} ({len(models)} Modelle):")
            for model in models:
                logger.info(f"  {model.model_id}:")
                logger.info(f"    - Tests: {model.total_tests}")
                logger.info(f"    - Erfolg: {model.success_rate:.0%}")
                logger.info(f"    - Felder: {model.avg_fields_found:.1f}")
                logger.info(f"    - Konsistenz: {model.overall_consistency:.2f}")
                logger.info(f"    - Zeit: {model.avg_response_time_ms:.0f}ms")
        
        # Top 10 Modelle
        logger.info("\n🏆 TOP 10 MODELLE (nach Erfolgsrate & Feldern):")
        top_models = session.query(ModelSummary).filter(
            ModelSummary.success_rate > 0
        ).order_by(
            ModelSummary.success_rate.desc(),
            ModelSummary.avg_fields_found.desc()
        ).limit(10).all()
        
        for i, model in enumerate(top_models, 1):
            score = (model.success_rate * 100 + model.avg_fields_found * 5 + model.overall_consistency * 20) / 3
            logger.info(f"{i}. {model.model_id}: Score={score:.1f}, "
                       f"Erfolg={model.success_rate:.0%}, "
                       f"Felder={model.avg_fields_found:.1f}, "
                       f"Konsistenz={model.overall_consistency:.2f}")
        
        # Problematische Modelle
        failed_models = session.query(ModelSummary).filter(
            ModelSummary.success_rate == 0
        ).all()
        
        if failed_models:
            logger.info("\n❌ PROBLEMATISCHE MODELLE (0% Erfolgsrate):")
            for model in failed_models:
                logger.info(f"  - {model.model_id}: {model.total_tests} Tests, alle fehlgeschlagen")
        
        # Erstelle JSON-Report
        report = {
            'summary': {
                'total_models': total_models,
                'total_tests': total_tests,
                'total_sources': total_sources,
                'total_results': total_results
            },
            'providers': {},
            'top_models': [],
            'failed_models': []
        }
        
        # Provider-Details
        for provider, models in providers.items():
            report['providers'][provider] = {
                'model_count': len(models),
                'models': [
                    {
                        'id': m.model_id,
                        'tests': m.total_tests,
                        'success_rate': float(m.success_rate),
                        'avg_fields': float(m.avg_fields_found),
                        'consistency': float(m.overall_consistency),
                        'avg_time_ms': float(m.avg_response_time_ms)
                    }
                    for m in models
                ]
            }
        
        # Top Models
        for model in top_models[:10]:
            score = (model.success_rate * 100 + model.avg_fields_found * 5 + model.overall_consistency * 20) / 3
            report['top_models'].append({
                'rank': top_models.index(model) + 1,
                'model_id': model.model_id,
                'score': float(score),
                'success_rate': float(model.success_rate),
                'avg_fields': float(model.avg_fields_found),
                'consistency': float(model.overall_consistency)
            })
        
        # Failed Models
        for model in failed_models:
            report['failed_models'].append({
                'model_id': model.model_id,
                'tests': model.total_tests
            })
        
        # Speichere Report
        with open('final_test_report.json', 'w', encoding='utf-8') as f:
            json.dump(report, f, indent=2, ensure_ascii=False)
        
        logger.info("\n✅ Report gespeichert in: final_test_report.json")
        
        # Empfehlungen
        logger.info("\n📋 EMPFEHLUNGEN FÜR PRODUKTIV-EINSATZ:")
        logger.info("\n1. BESTE ALLROUND-MODELLE:")
        logger.info("   - perplexity:sonar-pro (94% Erfolg, 11.1 Felder)")
        logger.info("   - grok:grok-3 (100% Erfolg, 10.7 Felder)")
        logger.info("   - grok:grok-3-fast (100% Erfolg, 10.9 Felder)")
        
        logger.info("\n2. SCHNELLSTE MODELLE:")
        fast_models = session.query(ModelSummary).filter(
            ModelSummary.success_rate > 0.8
        ).order_by(
            ModelSummary.avg_response_time_ms.asc()
        ).limit(3).all()
        
        for model in fast_models:
            logger.info(f"   - {model.model_id}: {model.avg_response_time_ms:.0f}ms")
        
        logger.info("\n3. HÖCHSTE KONSISTENZ:")
        consistent_models = session.query(ModelSummary).filter(
            ModelSummary.overall_consistency > 0.8
        ).order_by(
            ModelSummary.overall_consistency.desc()
        ).limit(3).all()
        
        for model in consistent_models:
            logger.info(f"   - {model.model_id}: {model.overall_consistency:.2f}")
        
        logger.info("\n4. ZU VERMEIDEN:")
        logger.info("   - exa:research (404 Fehler)")
        logger.info("   - exa:research-pro (404 Fehler)")
        logger.info("   - openrouter:deepseek-reasoner (ungültige Model-ID)")


if __name__ == "__main__":
    generate_final_report()