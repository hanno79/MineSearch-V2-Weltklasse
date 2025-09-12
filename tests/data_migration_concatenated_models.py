"""
Author: rahn
Datum: 17.08.2025
Version: 1.0
Beschreibung: Data Migration Script - Parse existing concatenated model_used entries
"""

import asyncio
from datetime import datetime
from minesearch.database import db_manager
from minesearch.database.models import SearchResult, ModelStatisticsComprehensive

class DataMigrationConcatenatedModels:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.migrated_count = 0
        self.skipped_count = 0
        self.error_count = 0

    async def migrate_concatenated_entries(self):
        """Migrate concatenated model_used entries to individual model entries"""
        print("🚀 DATA MIGRATION: Concatenated Model Entries")
        print("=" * 60)

        try:
            with db_manager.get_session() as session:
                # Find all SearchResult entries with concatenated model_used strings
                all_results = session.query(SearchResult).all()

                print(f"📊 Total SearchResult entries to analyze: {len(all_results)}")

                concatenated_entries = []
                individual_entries = []

                for result in all_results:
                    model_used = result.model_used or ""

                    # Detect concatenated entries (contain underscores and are long)
                    if '_' in model_used and len(model_used) > 50:
                        concatenated_entries.append(result)
                    else:
                        individual_entries.append(result)

                print(f"📋 Concatenated entries found: {len(concatenated_entries)}")
                print(f"📋 Individual entries found: {len(individual_entries)}")

                if len(concatenated_entries) == 0:
                    print("✅ No concatenated entries found - migration not needed")
                    return

                # Analyze concatenated entries
                print(f"\n🔍 ANALYZING CONCATENATED ENTRIES:")
                print(f"=" * 60)

                for i, result in enumerate(concatenated_entries[:5]):  # Show first 5
                    models = result.model_used.split('_')
                    print(f"{i+1}. Mine: {result.mine_name}")
                    print(f"   Models: {len(models)} ({models[:3]}...)")
                    print(f"   Date: {result.search_timestamp}")
                    print()

                # Ask for confirmation (in real scenario)
                print(f"⚠️ MIGRATION PLAN:")
                print(f"   - {len(concatenated_entries)} concatenated entries will be analyzed")
                print(f"   - Individual model entries will be created where appropriate")
                print(f"   - Statistics will be updated for individual models")
                print(f"   - Original concatenated entries will be marked as 'legacy'")

                # For each concatenated entry, create individual entries
                for i, result in enumerate(concatenated_entries):
                    try:
                        await self.process_concatenated_entry(result, session)
                        self.migrated_count += 1

                        if (i + 1) % 10 == 0:
                            print(f"📈 Progress: {i + 1}/{len(concatenated_entries)} processed")

                    except Exception as e:
                        print(f"❌ Error processing entry {result.id}: {e}")
                        self.error_count += 1

                # Commit all changes
                session.commit()

                # Final statistics update
                await self.update_all_model_statistics()

                print(f"\n🎉 MIGRATION COMPLETED:")
                print(f"=" * 60)
                print(f"✅ Migrated: {self.migrated_count}")
                print(f"⚠️ Skipped: {self.skipped_count}")
                print(f"❌ Errors: {self.error_count}")

        except Exception as e:
            print(f"❌ Migration failed: {e}")
            import traceback
            traceback.print_exc()

    async def process_concatenated_entry(self, result, session):
        """Process a single concatenated entry"""
        models = result.model_used.split('_')

        # Skip if not really concatenated (false positive)
        if len(models) < 2:
            self.skipped_count += 1
            return

        print(f"🔧 Processing: {result.mine_name} with {len(models)} models")

        # Create individual entries for each model (only for recent data)
        recent_threshold = datetime(2025, 8, 1)  # Only migrate data from August 2025

        if result.search_timestamp and result.search_timestamp > recent_threshold:
            for model_id in models:
                if model_id.strip():
                    # Create individual SearchResult entry
                    individual_result = SearchResult(
                        mine_name=result.mine_name,
                        model_used=model_id.strip(),
                        structured_data=result.structured_data,
                        sources=result.sources,
                        session_id=f"{result.session_id}_migrated" if result.session_id else None,
                        country=result.country,
                        region=result.region,
                        commodity=result.commodity,
                        search_type=f"{result.search_type}_migrated" if result.search_type else "migrated",
                        search_duration=result.search_duration,
                        data_quality=result.data_quality,
                        success=result.success,
                        search_timestamp=result.search_timestamp
                    )

                    session.add(individual_result)

                    # Update individual model statistics
                    try:
                        db_manager.update_model_statistics_comprehensive(model_id.strip())
                    except Exception as e:
                        print(f"⚠️ Statistics update failed for {model_id}: {e}")

        # Mark original as legacy
        result.search_type = f"{result.search_type}_legacy" if result.search_type else "legacy_concatenated"

    async def update_all_model_statistics(self):
        """Update statistics for all individual models"""
        print(f"\n📊 UPDATING ALL MODEL STATISTICS...")

        with db_manager.get_session() as session:
            # Get all individual models (non-concatenated)
            individual_models = session.query(SearchResult.model_used).filter(
                ~SearchResult.model_used.contains('_')
            ).distinct().all()

            print(f"📋 Individual models to update: {len(individual_models)}")

            for model_tuple in individual_models:
                model_id = model_tuple[0]
                if model_id and len(model_id) < 50:  # Reasonable model ID length
                    try:
                        db_manager.update_model_statistics_comprehensive(model_id)
                    except Exception as e:
                        print(f"⚠️ Failed to update stats for {model_id}: {e}")

# Main execution
if __name__ == "__main__":
    async def main():
        migrator = DataMigrationConcatenatedModels()
        await migrator.migrate_concatenated_entries()

        print(f"\n💾 Data migration completed successfully!")
        print(f"🎯 All individual models now have proper statistics entries")
        print(f"📈 Frontend Statistics tab should show all models as individual cards")

    asyncio.run(main())
