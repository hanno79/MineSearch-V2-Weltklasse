"""
Author: rahn
Datum: 15.07.2025
Version: 1.0
Beschreibung: Sources Seeding Script für MineSearch v2.1 - befüllt leere Quellen-Datenbank
"""

import logging
from typing import List, Dict, Any
from database.manager import DatabaseManager
from database.models import Source

logger = logging.getLogger(__name__)

class SourceSeeder:
    """Seeding-Klasse für Standard-Mining-Quellen"""
    
    def __init__(self):
        self.db_manager = DatabaseManager()
    
    def get_global_mining_sources(self) -> List[Dict[str, Any]]:
        """Definiert weltweite Standard-Mining-Quellen"""
        return [
            # US Government Sources
            {
                "url": "https://www.usgs.gov/centers/national-minerals-information-center",
                "domain": "usgs.gov",
                "country": "US",
                "region": "North America",
                "source_type": "government",
                "reliability_score": 95.0,
                "metadata": {
                    "description": "US Geological Survey - National Minerals Information Center",
                    "data_types": ["production", "reserves", "consumption", "trade"],
                    "coverage": "global",
                    "update_frequency": "annual"
                }
            },
            {
                "url": "https://mrdata.usgs.gov/mrds/",
                "domain": "usgs.gov", 
                "country": "US",
                "region": "North America",
                "source_type": "database",
                "reliability_score": 95.0,
                "metadata": {
                    "description": "USGS Mineral Resources Data System",
                    "data_types": ["deposits", "prospects", "mines"],
                    "coverage": "global"
                }
            },
            
            # Canadian Government Sources
            {
                "url": "https://www.nrcan.gc.ca/our-natural-resources/minerals-mining",
                "domain": "nrcan.gc.ca",
                "country": "CA", 
                "region": "North America",
                "source_type": "government",
                "reliability_score": 90.0,
                "metadata": {
                    "description": "Natural Resources Canada - Minerals and Mining",
                    "data_types": ["production", "exploration", "policy"],
                    "coverage": "canada_focused"
                }
            },
            
            # Australian Government Sources
            {
                "url": "https://www.ga.gov.au/scientific-topics/minerals",
                "domain": "ga.gov.au",
                "country": "AU",
                "region": "Oceania", 
                "source_type": "government",
                "reliability_score": 90.0,
                "metadata": {
                    "description": "Geoscience Australia - Minerals",
                    "data_types": ["geology", "resources", "exploration"],
                    "coverage": "australia_focused"
                }
            },
            {
                "url": "https://www.industry.gov.au/data-and-publications/resources-and-energy-quarterly",
                "domain": "industry.gov.au",
                "country": "AU",
                "region": "Oceania",
                "source_type": "government",
                "reliability_score": 85.0,
                "metadata": {
                    "description": "Australian Government Resources and Energy Quarterly",
                    "data_types": ["production", "trade", "forecasts"],
                    "coverage": "australia_global"
                }
            },
            
            # European Sources
            {
                "url": "https://rmis.jrc.ec.europa.eu/",
                "domain": "jrc.ec.europa.eu",
                "country": "EU",
                "region": "Europe",
                "source_type": "government",
                "reliability_score": 85.0,
                "metadata": {
                    "description": "EU Raw Materials Information System",
                    "data_types": ["critical_materials", "supply_chains", "policy"],
                    "coverage": "europe_global"
                }
            },
            {
                "url": "https://www.bgs.ac.uk/geology-projects/world-mineral-statistics/",
                "domain": "bgs.ac.uk",
                "country": "GB",
                "region": "Europe",
                "source_type": "government",
                "reliability_score": 90.0,
                "metadata": {
                    "description": "British Geological Survey - World Mineral Statistics",
                    "data_types": ["production", "trade", "reserves"],
                    "coverage": "global"
                }
            },
            
            # Commercial/Industry Sources
            {
                "url": "https://www.mining.com/",
                "domain": "mining.com",
                "country": None,
                "region": "Global", 
                "source_type": "commercial",
                "reliability_score": 75.0,
                "metadata": {
                    "description": "Mining.com - Mining Industry News and Analysis",
                    "data_types": ["news", "market_analysis", "company_data"],
                    "coverage": "global"
                }
            },
            {
                "url": "https://www.infomine.com/",
                "domain": "infomine.com",
                "country": "US",
                "region": "North America",
                "source_type": "commercial",
                "reliability_score": 70.0,
                "metadata": {
                    "description": "InfoMine - Mining Information Database",
                    "data_types": ["companies", "projects", "market_data"],
                    "coverage": "global"
                }
            },
            {
                "url": "https://www.miningnews.net/", 
                "domain": "miningnews.net",
                "country": "AU",
                "region": "Oceania",
                "source_type": "commercial",
                "reliability_score": 70.0,
                "metadata": {
                    "description": "Mining News - Industry Publication",
                    "data_types": ["news", "exploration", "production"],
                    "coverage": "australia_focused"
                }
            },
            
            # International Organizations
            {
                "url": "https://www.iea.org/topics/critical-minerals",
                "domain": "iea.org",
                "country": None,
                "region": "Global",
                "source_type": "international",
                "reliability_score": 90.0,
                "metadata": {
                    "description": "International Energy Agency - Critical Minerals",
                    "data_types": ["critical_minerals", "supply_security", "policy"],
                    "coverage": "global"
                }
            },
            {
                "url": "https://www.worldbank.org/en/topic/extractiveindustries",
                "domain": "worldbank.org", 
                "country": None,
                "region": "Global",
                "source_type": "international",
                "reliability_score": 85.0,
                "metadata": {
                    "description": "World Bank - Extractive Industries",
                    "data_types": ["development", "governance", "sustainability"],
                    "coverage": "global"
                }
            },
            
            # Regional Geological Surveys
            {
                "url": "https://www.bgr.bund.de/EN/Themen/Min_rohstoffe/min_rohstoffe_node_en.html",
                "domain": "bgr.bund.de",
                "country": "DE",
                "region": "Europe", 
                "source_type": "government",
                "reliability_score": 85.0,
                "metadata": {
                    "description": "BGR Germany - Mineral Resources",
                    "data_types": ["geology", "resources", "sustainability"],
                    "coverage": "germany_global"
                }
            },
            {
                "url": "https://www.brgm.fr/en/activities/mineral-resources",
                "domain": "brgm.fr",
                "country": "FR",
                "region": "Europe",
                "source_type": "government", 
                "reliability_score": 85.0,
                "metadata": {
                    "description": "BRGM France - Mineral Resources",
                    "data_types": ["exploration", "resources", "environmental"],
                    "coverage": "france_global"
                }
            },
            
            # African Sources
            {
                "url": "https://www.amdc.gov.et/",
                "domain": "amdc.gov.et",
                "country": "ET",
                "region": "Africa",
                "source_type": "government",
                "reliability_score": 75.0,
                "metadata": {
                    "description": "African Minerals Development Centre",
                    "data_types": ["policy", "development", "capacity_building"],
                    "coverage": "africa"
                }
            },
            
            # South American Sources
            {
                "url": "https://www.cprm.gov.br/en/",
                "domain": "cprm.gov.br",
                "country": "BR",
                "region": "South America",
                "source_type": "government",
                "reliability_score": 80.0,
                "metadata": {
                    "description": "CPRM Brazil - Geological Survey",
                    "data_types": ["geology", "mineral_potential", "exploration"],
                    "coverage": "brazil_focused"
                }
            },
            
            # Asian Sources
            {
                "url": "https://www.jogmec.go.jp/english/",
                "domain": "jogmec.go.jp",
                "country": "JP",
                "region": "Asia",
                "source_type": "government",
                "reliability_score": 85.0,
                "metadata": {
                    "description": "JOGMEC Japan - Oil, Gas and Metals Corporation",
                    "data_types": ["exploration", "development", "security"],
                    "coverage": "japan_global"
                }
            },
            
            # Stock Exchanges (for mining companies)
            {
                "url": "https://www.tsx.com/",
                "domain": "tsx.com", 
                "country": "CA",
                "region": "North America",
                "source_type": "exchange",
                "reliability_score": 80.0,
                "metadata": {
                    "description": "Toronto Stock Exchange - Mining Companies",
                    "data_types": ["financial", "company_reports", "listings"],
                    "coverage": "global_mining_companies"
                }
            },
            {
                "url": "https://www.asx.com.au/",
                "domain": "asx.com.au",
                "country": "AU", 
                "region": "Oceania",
                "source_type": "exchange",
                "reliability_score": 80.0,
                "metadata": {
                    "description": "Australian Securities Exchange - Mining Sector",
                    "data_types": ["financial", "announcements", "company_data"],
                    "coverage": "australia_global"
                }
            }
        ]
    
    def seed_sources(self, force: bool = False) -> Dict[str, Any]:
        """Befüllt die Quellen-Datenbank mit Standard-Quellen"""
        logger.info("🌱 Starting sources seeding process...")
        
        # Prüfe ob bereits Quellen vorhanden sind
        with self.db_manager.get_session() as session:
            existing_count = session.query(Source).count()
            
            if existing_count > 0 and not force:
                logger.info(f"⚠️ Database already contains {existing_count} sources. Use force=True to override.")
                return {
                    "success": False,
                    "message": f"Database already contains {existing_count} sources",
                    "existing_count": existing_count,
                    "action": "skipped"
                }
        
        # Hole Standard-Quellen
        standard_sources = self.get_global_mining_sources()
        
        added_count = 0
        updated_count = 0
        error_count = 0
        
        for source_data in standard_sources:
            try:
                # Füge Quelle hinzu oder aktualisiere sie
                source = self.db_manager.add_or_update_source(
                    url=source_data["url"],
                    domain=source_data["domain"],
                    country=source_data.get("country"),
                    region=source_data.get("region"),
                    source_type=source_data["source_type"],
                    metadata=source_data.get("metadata", {})
                )
                
                # Setze reliability_score wenn angegeben
                if "reliability_score" in source_data:
                    with self.db_manager.get_session() as session:
                        existing = session.query(Source).filter_by(url=source_data["url"]).first()
                        if existing:
                            existing.reliability_score = source_data["reliability_score"]
                            session.commit()
                            updated_count += 1
                        else:
                            added_count += 1
                
                logger.debug(f"✅ Added/Updated: {source_data['domain']}")
                
            except Exception as e:
                logger.error(f"❌ Error adding source {source_data['url']}: {e}")
                error_count += 1
        
        # Final statistics
        with self.db_manager.get_session() as session:
            final_count = session.query(Source).count()
        
        result = {
            "success": True,
            "message": f"Sources seeding completed",
            "statistics": {
                "total_processed": len(standard_sources),
                "added_count": added_count,
                "updated_count": updated_count, 
                "error_count": error_count,
                "final_database_count": final_count
            }
        }
        
        logger.info(f"🎉 Seeding completed: {final_count} total sources in database")
        logger.info(f"📊 Processed: {len(standard_sources)}, Added: {added_count}, Updated: {updated_count}, Errors: {error_count}")
        
        return result

def seed_database_sources(force: bool = False) -> Dict[str, Any]:
    """Convenience function für direktes Seeding"""
    seeder = SourceSeeder()
    return seeder.seed_sources(force=force)

if __name__ == "__main__":
    # Direct execution for testing
    import sys
    force = "--force" in sys.argv
    
    print("🌱 MineSearch v2.1 - Sources Database Seeding")
    print("=" * 50)
    
    result = seed_database_sources(force=force)
    
    if result["success"]:
        stats = result["statistics"]
        print(f"✅ SUCCESS: {stats['final_database_count']} sources in database")
        print(f"📈 Added: {stats['added_count']}, Updated: {stats['updated_count']}")
        if stats['error_count'] > 0:
            print(f"⚠️ Errors: {stats['error_count']}")
    else:
        print(f"❌ FAILED: {result['message']}")
        print("💡 Use --force flag to override existing sources")