"""
Author: rahn
Datum: 17.08.2025
Version: 1.0
Beschreibung: Debug Script für Source Discovery Analysis
"""

import asyncio
import sys
import os
sys.path.append('/app/backend')

from minesearch.enhanced_source_discovery import EnhancedSourceDiscovery
from minesearch.database import db_manager

class SourceDiscoveryDebugger:
    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.test_mine_name = "Lac Expanse"
        self.test_country = "Canada"
        self.test_region = "Quebec"

    async def test_source_discovery(self):
        """Test Enhanced Source Discovery für Quebec Mining"""
        print("=" * 60)

        print(f"Testing: {self.test_mine_name}")
        print(f"Country: {self.test_country}")
        print(f"Region: {self.test_region}")

        try:
            # Test enhanced source discovery
            print(f"\n📊 [STEP 1] Enhanced Source Discovery...")
            discovery = EnhancedSourceDiscovery()
            sources = discovery.discover_sources_for_mine(
                mine_name=self.test_mine_name,
                country=self.test_country,
                region=self.test_region
            )

            print(f"✅ Sources found: {len(sources)}")

            # Analyze source types
            source_types = {}
            quebec_sources = []
            canada_sources = []
            global_sources = []

            for source in sources:
                url = source.get("url", '')
                title = source.get("title", '')
                source_type = source.get("type", 'unknown')

                # Count by type
                source_types[source_type] = source_types.get(source_type, 0) + 1

                # Categorize by region
                if 'quebec' in url.lower() or 'quebec' in title.lower():
                    quebec_sources.append((url, title))
                elif 'canada' in url.lower() or '.ca' in url:
                    canada_sources.append((url, title))
                else:
                    global_sources.append((url, title))

            print(f"\n📋 SOURCE ANALYSIS:")
            print(f"By Type: {source_types}")
            print(f"Quebec-specific: {len(quebec_sources)}")
            print(f"Canada-wide: {len(canada_sources)}")
            print(f"Global: {len(global_sources)}")

            # Show Quebec-specific sources
            print(f"\n🇨🇦 QUEBEC-SPECIFIC SOURCES:")
            for i, (url, title) in enumerate(quebec_sources[:5], 1):
                print(f"  {i}. {url}")
                print(f"     Title: {title[:80]}...")

            # Show Canada-wide sources
            print(f"\n🍁 CANADA-WIDE SOURCES:")
            for i, (url, title) in enumerate(canada_sources[:5], 1):
                print(f"  {i}. {url}")
                print(f"     Title: {title[:80]}...")

            # Check database sources
            print(f"\n📊 [STEP 2] Database Sources Check...")
            with db_manager.get_session() as session:
                from minesearch.database.models import Source

                # Count total sources in database
                total_sources = session.query(Source).count()
                canada_db_sources = session.query(Source).filter_by(country='Canada').count()
                quebec_db_sources = session.query(Source).filter_by(country='Canada', region='Quebec').count()

                print(f"Total DB sources: {total_sources}")
                print(f"Canada DB sources: {canada_db_sources}")
                print(f"Quebec DB sources: {quebec_db_sources}")

                # Get some Quebec-specific sources from DB
                quebec_sources_db = session.query(Source).filter_by(
                    country='Canada', region='Quebec'
                ).limit(5).all()

                print(f"\n🗄️ QUEBEC SOURCES IN DATABASE:")
                for i, source in enumerate(quebec_sources_db, 1):
                    print(f"  {i}. {source.url}")
                    print(f"     Type: {source.source_type}, Reliability: {source.reliability_score}")

            return {
                'total_sources': len(sources),
                'source_types': source_types,
                'quebec_sources': len(quebec_sources),
                'canada_sources': len(canada_sources),
                'global_sources': len(global_sources),
                'sources_detail': sources[:10]  # First 10 for analysis
            }

        except Exception as e:
            print(f"❌ Source Discovery Error: {e}")
            import traceback
            traceback.print_exc()
            return None

# Main execution
if __name__ == "__main__":
    async def main():
        debugger = SourceDiscoveryDebugger()
        result = await debugger.test_source_discovery()

        if result:
            print(f"\n🎯 SOURCE DISCOVERY TEST RESULTS:")
            print(f"=" * 60)
            print(f"✅ Total Sources Found: {result['total_sources']}")
            print(f"📊 Quebec-specific: {result['quebec_sources']}")
            print(f"🍁 Canada-wide: {result['canada_sources']}")
            print(f"🌍 Global: {result['global_sources']}")

            if result['total_sources'] > 0:
                print(f"\n✅ SOURCE DISCOVERY WORKING")
                print(f"Next: Test API Response Analysis")
            else:
                print(f"\n❌ SOURCE DISCOVERY PROBLEM IDENTIFIED")
                print(f"Issue: No sources found for Quebec mining")

    asyncio.run(main())
