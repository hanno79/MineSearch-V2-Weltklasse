#!/usr/bin/env python3
"""
Author: rahn
Datum: 07.08.2025
Version: 1.0
Beschreibung: Model-ID Parser für Batch → Individual Models
ÄNDERUNG 07.08.2025: Parser für zusammengesetzte Model-IDs
"""

import logging
from typing import List, Dict, Any
from minesearch.database import db_manager, ModelStatisticsComprehensive

logger = logging.getLogger(__name__)

class ModelIdParser:
    """
    Parser für Batch-Model-IDs zu Individual-Model-IDs
    """
    
    def parse_batch_model_id(self, batch_model_id: str) -> List[str]:
        """
        Parst eine Batch-Model-ID in Individual-Model-IDs
        
        Input: "openrouter:deepseek-free_openrouter:deepseek-chat_openrouter:reasoner"
        Output: ["openrouter:deepseek-free", "openrouter:deepseek-chat", "openrouter:reasoner"]
        """
        if not batch_model_id:
            return []
        
        # Split by underscore, dann reconstructe individual IDs
        parts = batch_model_id.split('_')
        individual_models = []
        
        for part in parts:
            if ':' in part and part.startswith(('openrouter:', 'perplexity:', 'anthropic:', 'openai:')):
                # Dies ist eine vollständige Model-ID
                individual_models.append(part)
            elif part and individual_models:
                # Dies könnte ein model name ohne provider sein
                # Nimm den letzten provider
                last_model = individual_models[-1] if individual_models else ""
                if ':' in last_model:
                    provider = last_model.split(':')[0]
                    individual_models.append(f"{provider}:{part}")
        
        # Deduplicate
        return list(set(individual_models))
    
    def create_model_display_name(self, model_id: str) -> str:
        """
        Erstellt benutzerfreundlichen Display-Namen
        
        Input: "openrouter:deepseek-free"
        Output: "OpenRouter - DeepSeek Free"
        """
        if not model_id or ':' not in model_id:
            return model_id
        
        provider, model_name = model_id.split(':', 1)
        
        # Provider cleanup
        provider_map = {
            'openrouter': 'OpenRouter',
            'perplexity': 'Perplexity',
            'anthropic': 'Anthropic',
            'openai': 'OpenAI',
            'gemini': 'Google Gemini',
            'grok': 'xAI Grok'
        }
        
        clean_provider = provider_map.get(provider, provider.title())
        
        # Model name cleanup
        model_parts = model_name.replace('-', ' ').replace('_', ' ').split()
        clean_model = ' '.join(word.title() for word in model_parts)
        
        return f"{clean_provider} - {clean_model}"
    
    def split_comprehensive_stats(self, batch_stat: ModelStatisticsComprehensive) -> List[Dict[str, Any]]:
        """
        Teilt Batch-Statistik in Individual-Model-Statistiken auf
        """
        individual_models = self.parse_batch_model_id(batch_stat.model_id)
        
        if not individual_models:
            logger.warning(f"Konnte keine Individual Models aus {batch_stat.model_id} parsen")
            return []
        
        num_models = len(individual_models)
        logger.info(f"Teile Batch-Statistik für {batch_stat.model_id} in {num_models} Individual-Models auf")
        
        individual_stats = []
        
        for model_id in individual_models:
            # Teile Statistiken gleichmäßig auf alle Modelle auf
            individual_stat = {
                'model_id': model_id,
                'model_display_name': self.create_model_display_name(model_id),
                'provider': model_id.split(':')[0] if ':' in model_id else 'unknown',
                
                # Performance-Metriken (gleichmäßig aufteilen)
                'total_searches': max(1, batch_stat.total_searches // num_models),
                'successful_searches': max(1, batch_stat.successful_searches // num_models),
                'success_rate_percent': batch_stat.success_rate_percent,  # Bleibt gleich
                
                # Scores (bleiben gleich da sie Durchschnittswerte sind)
                'completeness_score': batch_stat.completeness_score,
                'consistency_score': batch_stat.consistency_score,
                'consistency_grade': batch_stat.consistency_grade,
                'overall_score': batch_stat.overall_score,
                'score_category': batch_stat.score_category,
                
                # Weitere Metriken
                'avg_fields_found': batch_stat.avg_fields_found,
                'avg_sources_per_search': batch_stat.avg_sources_per_search,
                'unique_sources_total': max(1, batch_stat.unique_sources_total // num_models),
                'source_diversity_score': batch_stat.source_diversity_score,
                
                # Performance
                'avg_response_time_ms': batch_stat.avg_response_time_ms,
                'avg_search_duration_ms': batch_stat.avg_search_duration_ms,
                'performance_category': batch_stat.performance_category,
                
                # Kosten
                'estimated_cost_per_search': batch_stat.estimated_cost_per_search,
                'cost_efficiency_score': batch_stat.cost_efficiency_score,
                
                # Spezialisierung
                'best_field_categories': batch_stat.best_field_categories,
                'specialization_score': batch_stat.specialization_score,
                
                # Timestamps
                'first_search_at': batch_stat.first_search_at,
                'last_search_at': batch_stat.last_search_at,
                'last_updated': batch_stat.last_updated
            }
            
            individual_stats.append(individual_stat)
        
        return individual_stats

def migrate_batch_to_individual_models():
    """
    Führt Migration von Batch-Models zu Individual-Models durch
    """
    parser = ModelIdParser()
    
    print("=== BATCH → INDIVIDUAL MODEL MIGRATION ===")
    
    with db_manager.get_session() as session:
        # Hole alle bestehenden Batch-Statistics
        batch_stats = session.query(ModelStatisticsComprehensive).all()
        print(f"Gefunden: {len(batch_stats)} Batch-Statistik-Einträge")
        
        all_individual_stats = []
        
        # Parse jede Batch-Statistik
        for batch_stat in batch_stats:
            print(f"\nVerarbeite Batch: {batch_stat.model_id}")
            print(f"  Länge: {len(batch_stat.model_id)} Zeichen")
            
            individual_stats = parser.split_comprehensive_stats(batch_stat)
            print(f"  → Erstellt: {len(individual_stats)} Individual-Models")
            
            for stat in individual_stats:
                print(f"    - {stat['model_display_name']}")
            
            all_individual_stats.extend(individual_stats)
        
        print(f"\nGesamt Individual-Models zu erstellen: {len(all_individual_stats)}")
        
        # Deduplicate basierend auf model_id
        unique_stats = {}
        for stat_data in all_individual_stats:
            model_id = stat_data['model_id']
            if model_id not in unique_stats:
                unique_stats[model_id] = stat_data
            else:
                # Bei Duplikaten nehme die besseren Werte (höhere Scores)
                existing = unique_stats[model_id]
                if stat_data['overall_score'] > existing['overall_score']:
                    unique_stats[model_id] = stat_data
        
        deduplicated_stats = list(unique_stats.values())
        print(f"Nach Deduplizierung: {len(deduplicated_stats)} Individual-Models")
        
        # Lösche alte Batch-Einträge
        print("\nLösche alte Batch-Einträge...")
        session.query(ModelStatisticsComprehensive).delete()
        
        # Erstelle neue Individual-Einträge
        print("Erstelle neue Individual-Einträge...")
        for stat_data in deduplicated_stats:
            stat = ModelStatisticsComprehensive(
                model_id=stat_data['model_id'],
                total_searches=stat_data['total_searches'],
                successful_searches=stat_data['successful_searches'], 
                success_rate_percent=stat_data['success_rate_percent'],
                total_expected_fields=20,  # Default
                avg_fields_found=stat_data['avg_fields_found'],
                completeness_score=stat_data['completeness_score'],
                consistency_score=stat_data['consistency_score'],
                consistency_grade=stat_data['consistency_grade'],
                avg_sources_per_search=stat_data['avg_sources_per_search'],
                unique_sources_total=stat_data['unique_sources_total'],
                source_diversity_score=stat_data['source_diversity_score'],
                avg_response_time_ms=stat_data['avg_response_time_ms'],
                avg_search_duration_ms=stat_data['avg_search_duration_ms'],
                performance_category=stat_data['performance_category'],
                overall_score=stat_data['overall_score'],
                score_category=stat_data['score_category'],
                best_field_categories=stat_data['best_field_categories'],
                specialization_score=stat_data['specialization_score'],
                estimated_cost_per_search=stat_data['estimated_cost_per_search'],
                cost_efficiency_score=stat_data['cost_efficiency_score'],
                first_search_at=stat_data['first_search_at'],
                last_search_at=stat_data['last_search_at'],
                last_updated=stat_data['last_updated']
            )
            session.add(stat)
        
        # Commit
        session.commit()
        
        # Validierung
        new_count = session.query(ModelStatisticsComprehensive).count()
        print(f"\n✅ Migration erfolgreich!")
        print(f"✅ Neue Individual-Models: {new_count}")
        
        # Zeige Beispiele
        print("\n📋 Beispiel Individual-Models:")
        samples = session.query(ModelStatisticsComprehensive).limit(5).all()
        for sample in samples:
            display_name = parser.create_model_display_name(sample.model_id)
            print(f"  - {display_name} (Score: {sample.overall_score})")
        
        return new_count

if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    migrate_batch_to_individual_models()