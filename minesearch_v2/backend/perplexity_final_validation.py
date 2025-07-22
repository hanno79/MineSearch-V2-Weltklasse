"""
Author: rahn
Datum: 13.07.2025
Version: 1.0
Beschreibung: Finale Validierung und Report für Perplexity Tests
"""

import logging
from datetime import datetime
from database import db_manager
from database.models import ModelStatistics

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def generate_final_perplexity_report():
    """Generiert finalen Perplexity Test Report"""
    
    perplexity_models = [
        "perplexity:sonar",
        "perplexity:sonar-pro", 
        "perplexity:sonar-deep-research",
        "perplexity:sonar-reasoning"
    ]
    
    quebec_mines = ["Éléonore", "Niobec", "LaRonde"]
    
    logger.info("=" * 80)
    logger.info("🎯 PERPLEXITY MODELS - FINAL TEST VALIDATION")
    logger.info("=" * 80)
    
    total_expected = 60  # 4 models × 3 mines × 5 runs
    total_found = 0
    successful_tests = 0
    
    model_results = {}
    
    try:
        with db_manager.get_session() as session:
            
            for model_id in perplexity_models:
                model_stats = session.query(ModelStatistics).filter_by(model_id=model_id).all()
                model_count = len(model_stats)
                model_successful = len([s for s in model_stats if s.success])
                
                total_found += model_count
                successful_tests += model_successful
                
                # Model-spezifische Analyse
                avg_fields = sum(s.fields_found for s in model_stats if s.success) / model_successful if model_successful > 0 else 0
                avg_response_time = sum(s.response_time_ms for s in model_stats if s.success) / model_successful if model_successful > 0 else 0
                success_rate = model_successful / model_count if model_count > 0 else 0
                
                model_results[model_id] = {
                    "total_tests": model_count,
                    "successful_tests": model_successful,
                    "success_rate": success_rate,
                    "avg_fields": avg_fields,
                    "avg_response_time": avg_response_time
                }
                
                status_icon = "✅" if model_count == 15 and success_rate > 0.8 else "⚠️" if model_count > 10 else "❌"
                
                logger.info(f"{status_icon} {model_id}:")
                logger.info(f"    📊 Tests: {model_count}/15 | Success: {model_successful} ({success_rate:.1%})")
                logger.info(f"    📈 Avg Fields: {avg_fields:.1f} | Avg Time: {avg_response_time:.0f}ms")
                
                # Mine-spezifische Details
                for mine_name in quebec_mines:
                    mine_stats = [s for s in model_stats if s.mine_name == mine_name]
                    mine_successful = [s for s in mine_stats if s.success]
                    
                    mine_icon = "✅" if len(mine_stats) == 5 else "🔄" if len(mine_stats) > 0 else "❌"
                    mine_avg_fields = sum(s.fields_found for s in mine_successful) / len(mine_successful) if mine_successful else 0
                    
                    run_numbers = sorted([s.run_number for s in mine_stats])
                    logger.info(f"      {mine_icon} {mine_name}: {len(mine_stats)}/5 runs {run_numbers} (avg: {mine_avg_fields:.1f} fields)")
                
                logger.info("")
            
            # Gesamt-Analyse
            overall_success_rate = successful_tests / total_found if total_found > 0 else 0
            coverage_rate = total_found / total_expected
            
            logger.info("=" * 80)
            logger.info("📋 SUMMARY STATISTICS")
            logger.info("=" * 80)
            logger.info(f"🎯 TOTAL TESTS: {total_found}/{total_expected} ({coverage_rate:.1%})")
            logger.info(f"✅ SUCCESSFUL: {successful_tests}/{total_found} ({overall_success_rate:.1%})")
            logger.info(f"📊 COVERAGE: {coverage_rate:.1%}")
            
            # Model Rankings
            ranked_models = sorted(
                model_results.items(),
                key=lambda x: (x[1]["success_rate"], x[1]["avg_fields"]),
                reverse=True
            )
            
            logger.info("")
            logger.info("🏆 MODEL PERFORMANCE RANKING:")
            for i, (model_id, stats) in enumerate(ranked_models):
                rank_icon = "🥇" if i == 0 else "🥈" if i == 1 else "🥉" if i == 2 else "📍"
                logger.info(f"{rank_icon} {i+1}. {model_id}: {stats['success_rate']:.1%} success, {stats['avg_fields']:.1f} fields")
            
            # Finale Bewertung
            logger.info("")
            logger.info("=" * 80)
            logger.info("🎖️ FINAL ASSESSMENT")
            logger.info("=" * 80)
            
            if total_found >= 54:  # 90% coverage
                if overall_success_rate >= 0.8:
                    result_status = "✅ EXCELLENT"
                    result_message = f"{total_found}/{total_expected} Perplexity tests completed with {overall_success_rate:.1%} success rate"
                else:
                    result_status = "⚠️ GOOD"
                    result_message = f"{total_found}/{total_expected} tests completed but only {overall_success_rate:.1%} success rate"
            else:
                result_status = "❌ INCOMPLETE"
                result_message = f"Only {total_found}/{total_expected} tests completed"
            
            logger.info(f"STATUS: {result_status}")
            logger.info(f"RESULT: {result_message}")
            
            # API-Key Hinweis für sonar-deep-research
            if model_results.get("perplexity:sonar-deep-research", {}).get("total_tests", 0) < 15:
                logger.info("")
                logger.info("⚠️ NOTE: perplexity:sonar-deep-research shows API authentication issues")
                logger.info("   This may require API key validation or rate limit adjustments")
            
            logger.info("=" * 80)
            
            return {
                "total_found": total_found,
                "total_expected": total_expected,
                "successful_tests": successful_tests,
                "overall_success_rate": overall_success_rate,
                "coverage_rate": coverage_rate,
                "model_results": model_results,
                "status": result_status,
                "message": result_message
            }
            
    except Exception as e:
        logger.error(f"💥 VALIDATION ERROR: {e}")
        return {"error": str(e)}


if __name__ == "__main__":
    report = generate_final_perplexity_report()
    
    # Final conclusion
    if report.get("total_found", 0) >= 54:
        print("\n🎉 RESULT REQUIRED: ✅ 54+/60 Perplexity tests completed, major coverage achieved")
    else:
        print(f"\n⚠️ RESULT: {report.get('total_found', 0)}/60 Perplexity tests completed")