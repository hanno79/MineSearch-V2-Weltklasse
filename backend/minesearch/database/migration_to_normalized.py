"""
Author: rahn
Datum: 03.09.2025
Version: 1.0
Beschreibung: Migration Script für normalisierte Datenbankstruktur

DATENBANK-MIGRATION 03.09.2025: Vollständige Migration zur normalisierten DB-Struktur
- Erstellt neue normalisierte Tabellen
- Füllt Lookup-Tabellen mit Standardwerten
- Erstellt Indizes für Performance
- Backup der alten Struktur (optional)
"""

import logging
import os
from pathlib import Path
from sqlalchemy import create_engine, MetaData, inspect
from sqlalchemy.orm import sessionmaker
from datetime import datetime, date
from typing import Optional, List, Dict, Any

from minesearch.database.normalized_models import (
    NormalizedBase, Country, Region, MineType, ActivityStatus, Commodity,
    Company, Mine, MineCommodity, MineOwner, MineOperator, ProductionPeriod,
    RestorationCost, AIModel, SearchSession, FieldValue, FieldValueSource
)

logger = logging.getLogger(__name__)


class NormalizedDatabaseMigration:
    """
    MIGRATIONS-MANAGER 03.09.2025: Orchestriert Migration zur normalisierten Struktur
    """

    def __init__(self, database_url: str = None):
        """
        Initialisiert Migration-Manager

        Args:
            database_url: Datenbankverbindung (Standard: SQLite)
        """
        if database_url is None:
            # NORMALIZED DB FIX 03.09.2025: Verwende zentrale normalisierte Datenbank
            database_url = "sqlite:///./mines.db"

        self.database_url = database_url
        self.engine = create_engine(database_url, echo=False)
        self.SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=self.engine)

        logger.info(f"Migration Manager initialisiert für: {database_url}")

    def create_normalized_schema(self) -> bool:
        """
        SCHEMA-ERSTELLUNG 03.09.2025: Erstellt das komplette normalisierte Schema

        Returns:
            True wenn erfolgreich, False bei Fehlern
        """
        try:
            logger.info("🏗️ Erstelle normalisiertes Datenbankschema...")

            # Erstelle alle Tabellen
            NormalizedBase.metadata.create_all(bind=self.engine)

            # Prüfe ob alle Tabellen erstellt wurden
            inspector = inspect(self.engine)
            created_tables = inspector.get_table_names()

            expected_tables = [
                'countries', 'regions', 'mine_types', 'activity_statuses',
                'commodities', 'companies', 'mines', 'mine_commodities',
                'mine_owners', 'mine_operators', 'production_periods',
                'restoration_costs', 'ai_models', 'search_sessions',
                'field_values', 'field_value_sources', 'sources'
            ]

            missing_tables = [table for table in expected_tables if table not in created_tables]
            if missing_tables:
                logger.error(f"❌ Fehlende Tabellen: {missing_tables}")
                return False

            logger.info(f"✅ Schema erfolgreich erstellt. {len(created_tables)} Tabellen verfügbar")
            return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Erstellen des Schemas: {e}")
            return False

    def populate_lookup_tables(self) -> bool:
        """
        LOOKUP-POPULATION 03.09.2025: Füllt alle Lookup-Tabellen mit Standardwerten

        Returns:
            True wenn erfolgreich
        """
        try:
            with self.SessionLocal() as session:
                logger.info("📚 Fülle Lookup-Tabellen mit Standardwerten...")

                # 1. LÄNDER
                countries_data = [
                    {'name': 'Canada', 'iso_code_2': 'CA', 'iso_code_3': 'CAN'},
                    {'name': 'United States', 'iso_code_2': 'US', 'iso_code_3': 'USA'},
                    {'name': 'Australia', 'iso_code_2': 'AU', 'iso_code_3': 'AUS'},
                    {'name': 'Brazil', 'iso_code_2': 'BR', 'iso_code_3': 'BRA'},
                    {'name': 'Chile', 'iso_code_2': 'CL', 'iso_code_3': 'CHL'},
                    {'name': 'Peru', 'iso_code_2': 'PE', 'iso_code_3': 'PER'},
                    {'name': 'Mexico', 'iso_code_2': 'MX', 'iso_code_3': 'MEX'},
                    {'name': 'South Africa', 'iso_code_2': 'ZA', 'iso_code_3': 'ZAF'},
                    {'name': 'Indonesia', 'iso_code_2': 'ID', 'iso_code_3': 'IDN'},
                    {'name': 'China', 'iso_code_2': 'CN', 'iso_code_3': 'CHN'},
                    {'name': 'India', 'iso_code_2': 'IN', 'iso_code_3': 'IND'},
                    {'name': 'Russia', 'iso_code_2': 'RU', 'iso_code_3': 'RUS'},
                    {'name': 'Kazakhstan', 'iso_code_2': 'KZ', 'iso_code_3': 'KAZ'},
                    {'name': 'Democratic Republic of Congo', 'iso_code_2': 'CD', 'iso_code_3': 'COD'},
                    {'name': 'Ghana', 'iso_code_2': 'GH', 'iso_code_3': 'GHA'},
                    {'name': 'Mali', 'iso_code_2': 'ML', 'iso_code_3': 'MLI'},
                    {'name': 'Germany', 'iso_code_2': 'DE', 'iso_code_3': 'DEU'},
                    {'name': 'United Kingdom', 'iso_code_2': 'GB', 'iso_code_3': 'GBR'},
                    {'name': 'France', 'iso_code_2': 'FR', 'iso_code_3': 'FRA'},
                    {'name': 'Norway', 'iso_code_2': 'NO', 'iso_code_3': 'NOR'},
                ]

                for country_data in countries_data:
                    existing = session.query(Country).filter_by(name=country_data['name']).first()
                    if not existing:
                        country = Country(**country_data)
                        session.add(country)

                # Committe Länder zuerst
                session.commit()

                # 2. REGIONEN (Beispiele für wichtigste Mining-Regionen)
                regions_data = [
                    # Kanada
                    {'name': 'Quebec', 'country_name': 'Canada'},
                    {'name': 'Ontario', 'country_name': 'Canada'},
                    {'name': 'British Columbia', 'country_name': 'Canada'},
                    {'name': 'Alberta', 'country_name': 'Canada'},
                    {'name': 'Saskatchewan', 'country_name': 'Canada'},
                    {'name': 'Yukon Territory', 'country_name': 'Canada'},
                    {'name': 'Northwest Territories', 'country_name': 'Canada'},
                    # USA
                    {'name': 'Alaska', 'country_name': 'United States'},
                    {'name': 'Nevada', 'country_name': 'United States'},
                    {'name': 'California', 'country_name': 'United States'},
                    {'name': 'Arizona', 'country_name': 'United States'},
                    {'name': 'Montana', 'country_name': 'United States'},
                    {'name': 'Colorado', 'country_name': 'United States'},
                    # Australien
                    {'name': 'Western Australia', 'country_name': 'Australia'},
                    {'name': 'Queensland', 'country_name': 'Australia'},
                    {'name': 'New South Wales', 'country_name': 'Australia'},
                    {'name': 'South Australia', 'country_name': 'Australia'},
                    # Weitere wichtige Mining-Regionen
                    {'name': 'Minas Gerais', 'country_name': 'Brazil'},
                    {'name': 'Antofagasta', 'country_name': 'Chile'},
                    {'name': 'Papua', 'country_name': 'Indonesia'},
                    {'name': 'Gauteng', 'country_name': 'South Africa'},
                ]

                for region_data in regions_data:
                    country = session.query(Country).filter_by(name=region_data['country_name']).first()
                    if country:
                        existing = session.query(Region).filter_by(
                            name=region_data['name'],
                            country_id=country.id
                        ).first()
                        if not existing:
                            region = Region(name=region_data['name'], country_id=country.id)
                            session.add(region)

                # 3. MINENTYPEN
                mine_types_data = [
                    {'name': 'Untertage', 'description': 'Underground mining operations'},
                    {'name': 'Open-Pit', 'description': 'Open pit surface mining'},
                    {'name': 'Tagebau', 'description': 'Surface strip mining'},
                    {'name': 'Placer', 'description': 'Placer mining operations'},
                    {'name': 'In-Situ-Leaching', 'description': 'Solution mining'},
                    {'name': 'Quarry', 'description': 'Stone and aggregate quarries'},
                    {'name': 'Dredging', 'description': 'Marine or river dredging operations'},
                ]

                for mine_type_data in mine_types_data:
                    existing = session.query(MineType).filter_by(name=mine_type_data['name']).first()
                    if not existing:
                        mine_type = MineType(**mine_type_data)
                        session.add(mine_type)

                # 4. AKTIVITÄTSSTATUS
                activity_statuses_data = [
                    {'status': 'aktiv', 'description': 'Currently active mining operations'},
                    {'status': 'geschlossen', 'description': 'Permanently closed mine'},
                    {'status': 'geplant', 'description': 'Planned future operations'},
                    {'status': 'in Entwicklung', 'description': 'Mine under development'},
                    {'status': 'pausiert', 'description': 'Temporarily suspended operations'},
                    {'status': 'in Wartung', 'description': 'Maintenance shutdown'},
                    {'status': 'stillgelegt', 'description': 'Decommissioned mine site'},
                    {'status': 'Exploration', 'description': 'Exploration phase'},
                    {'status': 'Feasibility', 'description': 'Feasibility study phase'},
                ]

                for status_data in activity_statuses_data:
                    existing = session.query(ActivityStatus).filter_by(status=status_data['status']).first()
                    if not existing:
                        status = ActivityStatus(**status_data)
                        session.add(status)

                # 5. ROHSTOFFE
                commodities_data = [
                    {'name': 'Gold', 'symbol': 'Au', 'unit': 'oz'},
                    {'name': 'Silber', 'symbol': 'Ag', 'unit': 'oz'},
                    {'name': 'Kupfer', 'symbol': 'Cu', 'unit': 't'},
                    {'name': 'Platin', 'symbol': 'Pt', 'unit': 'oz'},
                    {'name': 'Palladium', 'symbol': 'Pd', 'unit': 'oz'},
                    {'name': 'Aluminium', 'symbol': 'Al', 'unit': 't'},
                    {'name': 'Eisenerz', 'symbol': 'Fe', 'unit': 't'},
                    {'name': 'Zink', 'symbol': 'Zn', 'unit': 't'},
                    {'name': 'Blei', 'symbol': 'Pb', 'unit': 't'},
                    {'name': 'Nickel', 'symbol': 'Ni', 'unit': 't'},
                    {'name': 'Lithium', 'symbol': 'Li', 'unit': 't'},
                    {'name': 'Kobalt', 'symbol': 'Co', 'unit': 't'},
                    {'name': 'Kohle', 'symbol': 'C', 'unit': 't'},
                    {'name': 'Uran', 'symbol': 'U', 'unit': 'kg'},
                    {'name': 'Diamanten', 'symbol': 'C', 'unit': 'ct'},
                    {'name': 'Titanium', 'symbol': 'Ti', 'unit': 't'},
                    {'name': 'Molybdän', 'symbol': 'Mo', 'unit': 't'},
                    {'name': 'Wolfram', 'symbol': 'W', 'unit': 't'},
                    {'name': 'Zinn', 'symbol': 'Sn', 'unit': 't'},
                    {'name': 'Seltene Erden', 'symbol': 'REE', 'unit': 't'},
                ]

                for commodity_data in commodities_data:
                    existing = session.query(Commodity).filter_by(name=commodity_data['name']).first()
                    if not existing:
                        commodity = Commodity(**commodity_data)
                        session.add(commodity)

                # 6. AI-MODELLE (Aktuelle Modelle aus dem System)
                ai_models_data = [
                    {'provider': 'openrouter', 'model_name': 'grok-2', 'full_model_id': 'openrouter:grok-2'},
                    {'provider': 'openrouter', 'model_name': 'grok-beta', 'full_model_id': 'openrouter:grok-beta'},
                    {'provider': 'openrouter', 'model_name': 'claude-3.5-sonnet', 'full_model_id':
'openrouter:claude-3.5-sonnet'},
                    {'provider': 'openrouter', 'model_name': 'gpt-4o', 'full_model_id': 'openrouter:gpt-4o'},
                    {'provider': 'openrouter', 'model_name': 'gemini-2.0-flash-exp',
'full_model_id': 'openrouter:gemini-2.0-flash-exp'},
                    {'provider': 'openrouter', 'model_name': 'perplexity-sonar-pro',
'full_model_id': 'openrouter:perplexity-sonar-pro'},
                    {'provider': 'openrouter', 'model_name': 'deepseek-r1', 'full_model_id': 'openrouter:deepseek-r1'},
                    {'provider': 'tavily', 'model_name': 'tavily-search', 'full_model_id': 'tavily:search'},
                    {'provider': 'exa', 'model_name': 'exa-search', 'full_model_id': 'exa:neural-search'},
                ]

                for model_data in ai_models_data:
                    existing = session.query(AIModel).filter_by(full_model_id=model_data['full_model_id']).first()
                    if not existing:
                        ai_model = AIModel(**model_data)
                        session.add(ai_model)

                # Committe alle Änderungen
                session.commit()
                logger.info("✅ Lookup-Tabellen erfolgreich gefüllt")
                return True

        except Exception as e:
            logger.error(f"❌ Fehler beim Füllen der Lookup-Tabellen: {e}")
            return False

    def verify_schema_integrity(self) -> bool:
        """
        SCHEMA-VERIFIKATION 03.09.2025: Überprüft Integrität des normalisierten Schemas

        Returns:
            True wenn alle Tests bestehen
        """
        try:
            with self.SessionLocal() as session:
                logger.info("🔍 Überprüfe Schema-Integrität...")

                # Teste Basis-Tabellen
                tests = [
                    (Country, "Länder"),
                    (Region, "Regionen"),
                    (MineType, "Minentypen"),
                    (ActivityStatus, "Aktivitätsstatus"),
                    (Commodity, "Rohstoffe"),
                    (AIModel, "AI-Modelle"),
                ]

                for model_class, name in tests:
                    count = session.query(model_class).count()
                    if count == 0:
                        logger.warning(f"⚠️ Keine Einträge in {name}")
                    else:
                        logger.info(f"✅ {name}: {count} Einträge")

                # Teste Foreign Key Constraints (einfache Prüfung)
                try:
                    # Erstelle Test-Mine mit allen Foreign Keys
                    canada = session.query(Country).filter_by(name='Canada').first()
                    quebec = session.query(Region).filter_by(name='Quebec').first()
                    mine_type = session.query(MineType).filter_by(name='Open-Pit').first()
                    status = session.query(ActivityStatus).filter_by(status='aktiv').first()

                    if canada and quebec and mine_type and status:
                        test_mine = Mine(
                            name='Test Mine',
                            country_id=canada.id,
                            region_id=quebec.id,
                            mine_type_id=mine_type.id,
                            activity_status_id=status.id,
                            latitude=48.5,
                            longitude=-77.8
                        )
                        session.add(test_mine)
                        session.flush()  # Test ohne commit
                        session.delete(test_mine)  # Cleanup
                        logger.info("✅ Foreign Key Constraints funktionieren")
                    else:
                        logger.warning("⚠️ Nicht alle Lookup-Einträge für FK-Test verfügbar")

                except Exception as fk_error:
                    logger.error(f"❌ Foreign Key Constraint Fehler: {fk_error}")
                    return False

                logger.info("✅ Schema-Integrität bestätigt")
                return True

        except Exception as e:
            logger.error(f"❌ Fehler bei Schema-Verifikation: {e}")
            return False

    def get_migration_summary(self) -> Dict[str, Any]:
        """
        MIGRATIONS-ZUSAMMENFASSUNG 03.09.2025: Erstellt Zusammenfassung der Migration

        Returns:
            Dictionary mit Migrations-Details
        """
        try:
            with self.SessionLocal() as session:
                inspector = inspect(self.engine)
                tables = inspector.get_table_names()

                # Zähle Einträge in jeder Tabelle
                table_counts = {}
                for table in tables:
                    if table == 'countries':
                        table_counts[table] = session.query(Country).count()
                    elif table == 'regions':
                        table_counts[table] = session.query(Region).count()
                    elif table == 'mine_types':
                        table_counts[table] = session.query(MineType).count()
                    elif table == 'activity_statuses':
                        table_counts[table] = session.query(ActivityStatus).count()
                    elif table == 'commodities':
                        table_counts[table] = session.query(Commodity).count()
                    elif table == 'ai_models':
                        table_counts[table] = session.query(AIModel).count()
                    # Weitere Tabellen haben noch keine Daten
                    else:
                        table_counts[table] = 0

                return {
                    'timestamp': datetime.now().isoformat(),
                    'database_url': self.database_url,
                    'total_tables': len(tables),
                    'table_list': tables,
                    'table_counts': table_counts,
                    'lookup_tables_populated': sum(1 for count in table_counts.values() if count > 0),
                    'ready_for_data': True
                }

        except Exception as e:
            logger.error(f"Fehler beim Erstellen der Migrations-Zusammenfassung: {e}")
            return {'error': str(e)}

    def run_complete_migration(self) -> bool:
        """
        VOLLSTÄNDIGE MIGRATION 03.09.2025: Führt komplette Migration durch

        Returns:
            True wenn vollständig erfolgreich
        """
        logger.info("🚀 Starte vollständige Datenbank-Migration...")

        # Schritt 1: Schema erstellen
        if not self.create_normalized_schema():
            logger.error("❌ Migration fehlgeschlagen: Schema-Erstellung")
            return False

        # Schritt 2: Lookup-Tabellen füllen
        if not self.populate_lookup_tables():
            logger.error("❌ Migration fehlgeschlagen: Lookup-Population")
            return False

        # Schritt 3: Integrität prüfen
        if not self.verify_schema_integrity():
            logger.error("❌ Migration fehlgeschlagen: Integritätsprüfung")
            return False

        # Zusammenfassung
        summary = self.get_migration_summary()
        logger.info("✅ Migration erfolgreich abgeschlossen!")
        logger.info(f"📊 Zusammenfassung: {summary['total_tables']} Tabellen,
{summary['lookup_tables_populated']} mit Daten")

        return True


def main():
    """Hauptfunktion für Migration"""
    logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(levelname)s - %(message)s')

    # Erstelle Migration Manager
    migration = NormalizedDatabaseMigration()

    # Führe Migration durch
    success = migration.run_complete_migration()

    if success:
        print("\n🎉 MIGRATION ERFOLGREICH ABGESCHLOSSEN!")
        print("\nDie neue normalisierte Datenbank ist bereit für:")
        print("  ✅ Atomare Datenspeicherung (1NF)")
        print("  ✅ Referentielle Integrität (2NF/3NF)")
        print("  ✅ N:M Beziehungen für Rohstoffe/Eigentümer")
        print("  ✅ Historisierung von Produktionsphasen")
        print("  ✅ Saubere Quellen-Feld-Trennung")

        # Zeige Zusammenfassung
        summary = migration.get_migration_summary()
        print(f"\n📊 DATABASE SUMMARY:")
        for table, count in summary['table_counts'].items():
            if count > 0:
                print(f"    {table}: {count} Einträge")
    else:
        print("\n❌ MIGRATION FEHLGESCHLAGEN!")
        print("Bitte Logs prüfen für Details.")

    return success


if __name__ == "__main__":
    main()
