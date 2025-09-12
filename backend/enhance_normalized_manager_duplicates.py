#!/usr/bin/env python3
"""
Author: rahn
Datum: 06.09.2025
Version: 1.0
Beschreibung: Phase 3 - Stärkt NormalizedDatabaseManager mit Duplikate-Prävention
Fügt robuste Duplikate-Erkennung und -Vermeidung hinzu
"""

from minesearch.database.normalized_manager import read_file

def create_enhanced_normalized_manager():
    """Erstellt verbesserte Version des NormalizedDatabaseManager mit Duplikate-Prävention"""

    print("🔧 PHASE 3: ENHANCED NORMALIZED DATABASE MANAGER")
    print("=" * 70)

    # Lese aktuelle Datei
    current_code = read_file("/home/hanno/projects/MineSearch/backend/minesearch/database/normalized_manager.py")

    print("1. Analysiere aktuelle normalized_manager.py...")
    print(f"   📊 Aktuelle Dateigröße: {len(current_code)} Zeichen")

    # Finde Insertionspunkt für neue Methoden
    class_start = current_code.find("class NormalizedDatabaseManager:")
    if class_start == -1:
        print("   ❌ NormalizedDatabaseManager Klasse nicht gefunden!")
        return False

    # Neue Methoden für Duplikate-Prävention
    duplicate_prevention_methods = """
    # ===== DUPLIKATE-PRÄVENTION (Phase 3 Enhancement) =====

    def _check_company_duplicates(self, session: Session, name: str, role: str) -> Optional[int]:
    """_check_company_duplicates - TODO: Dokumentation hinzufügen"""
        \"\"\"
        Prüft auf Company-Duplikate durch intelligente Namensvergleiche
        Returns: company_id wenn Duplikat gefunden, None sonst
        \"\"\"
        if not name or not name.strip():
            return None

        clean_name = name.strip().lower()

        # Definiere bekannte Varianten-Muster
        variant_patterns = {
            # Basis -> Varianten die konsolidiert werden sollen
            'goldcorp': ['goldcorp inc', 'goldcorp inc.', 'goldcorp corporation'],
            'barrick': ['barrick gold', 'barrick gold corp', 'barrick gold corporation'],
            'newmont': ['newmont corp', 'newmont corporation', 'newmont mining'],
            'rio tinto': ['rio tinto group', 'rio tinto plc'],
            'vale': ['vale s.a.', 'vale sa'],
            'bhp': ['bhp billiton', 'bhp group']
        }

        # Prüfe exakte Duplikate
        existing_company = session.query(Company).filter(
            Company.name.ilike(name.strip())
        ).first()

        if existing_company:
            logger.debug(f"Exaktes Company-Duplikat gefunden: {name} -> ID:{existing_company.id}")
            return existing_company.id

        # Prüfe Varianten-basierte Duplikate
        for base_name, variants in variant_patterns.items():
            if clean_name == base_name:
                # Suche nach einer der Varianten
                for variant in variants:
                    variant_company = session.query(Company).filter(
                        Company.name.ilike(variant)
                    ).first()
                    if variant_company:
                        logger.debug(f"Varianten-Duplikat gefunden: {name} -> {variant_company.name}
(ID:{variant_company.id})")
                        return variant_company.id

            elif clean_name in [v.lower() for v in variants]:
                # Suche nach Basis-Name
                base_company = session.query(Company).filter(
                    Company.name.ilike(base_name)
                ).first()
                if base_company:
                    logger.debug(f"Basis-Company gefunden: {name} -> {base_company.name} (ID:{base_company.id})")
                    return base_company.id

                # Suche nach anderen Varianten
                for variant in variants:
                    if variant.lower() != clean_name:
                        variant_company = session.query(Company).filter(
                            Company.name.ilike(variant)
                        ).first()
                        if variant_company:
                            logger.debug(f"Andere Variante gefunden: {name} ->
{variant_company.name} (ID:{variant_company.id})")
                            return variant_company.id

        # Fuzzy-Matching für ähnliche Namen (optional)
        # Suche nach Namen mit ähnlichen Wörtern (z.B. "Inc" vs "Corporation")
        name_words = clean_name.replace('.', '').replace(',', '').split()
        if len(name_words) >= 2:
            base_words = name_words[:-1]  # Ohne letztes Wort (oft Inc/Corp/etc)
            base_search = ' '.join(base_words)

            similar_companies = session.query(Company).filter(
                Company.name.ilike(f"{base_search}%")
            ).all()

            for similar in similar_companies:
                similar_words = similar.name.lower().replace('.', '').replace(',', '').split()
                if len(similar_words) >= 2 and similar_words[:-1] == base_words:
                    logger.debug(f"Ähnliches Company-Duplikat gefunden: {name} -> {similar.name} (ID:{similar.id})")
                    return similar.id

        return None

    def _check_region_duplicates(self, session: Session, name: str, country_id: int) -> Optional[int]:
    """_check_region_duplicates - TODO: Dokumentation hinzufügen"""
        \"\"\"
        Prüft auf Region-Duplikate (besonders Quebec-Varianten)
        \"\"\"
        if not name or not name.strip():
            return None

        clean_name = name.strip().lower()

        # Quebec-spezifische Varianten
        quebec_variants = [
            'quebec', 'québec', 'quebec/québec', 'québec/côte-nord'
        ]

        if any(quebec_var in clean_name for quebec_var in quebec_variants):
            # Suche nach irgendeiner Quebec-Variante
            for variant in quebec_variants:
                existing_region = session.query(Region).filter(
                    Region.name.ilike(f"%{variant}%"),
                    Region.country_id == country_id
                ).first()

                if existing_region:
                    logger.debug(f"Quebec-Variante gefunden: {name} -> {existing_region.name}
(ID:{existing_region.id})")
                    return existing_region.id

        # Exakter Match
        existing_region = session.query(Region).filter(
            Region.name.ilike(name.strip()),
            Region.country_id == country_id
        ).first()

        if existing_region:
            logger.debug(f"Exaktes Region-Duplikat gefunden: {name} -> ID:{existing_region.id}")
            return existing_region.id

        return None

    def _check_commodity_duplicates(self, session: Session, name: str) -> Optional[int]:
    """_check_commodity_duplicates - TODO: Dokumentation hinzufügen"""
        \"\"\"
        Prüft auf Commodity-Duplikate (deutsch/englisch)
        \"\"\"
        if not name or not name.strip():
            return None

        clean_name = name.strip().lower()

        # Deutsch-Englisch Mapping
        translation_map = {
            'gold': 'gold',
            'kupfer': 'copper',
            'copper': 'kupfer',
            'silber': 'silver',
            'silver': 'silber',
            'eisenerz': 'iron ore',
            'iron ore': 'eisenerz',
            'kohle': 'coal',
            'coal': 'kohle'
        }

        # Exakter Match
        existing_commodity = session.query(Commodity).filter(
            Commodity.name.ilike(name.strip())
        ).first()

        if existing_commodity:
            logger.debug(f"Exaktes Commodity-Duplikat gefunden: {name} -> ID:{existing_commodity.id}")
            return existing_commodity.id

        # Translation-basierter Match
        if clean_name in translation_map:
            translated_name = translation_map[clean_name]
            translated_commodity = session.query(Commodity).filter(
                Commodity.name.ilike(translated_name)
            ).first()

            if translated_commodity:
                logger.debug(f"Übersetzungs-Duplikat gefunden: {name} -> {translated_commodity.name}
(ID:{translated_commodity.id})")
                return translated_commodity.id

        return None

    def _check_mine_type_duplicates(self, session: Session, name: str) -> Optional[int]:
    """_check_mine_type_duplicates - TODO: Dokumentation hinzufügen"""
        \"\"\"
        Prüft auf Mine-Type-Duplikate (deutsch/englisch)
        \"\"\"
        if not name or not name.strip():
            return None

        clean_name = name.strip().lower()

        # Deutsch-Englisch Type-Mapping
        type_translation_map = {
            'open-pit': 'tagebau',
            'open pit': 'tagebau',
            'surface': 'tagebau',
            'underground': 'untertage',
            'quarry': 'steinbruch',
            'dredging': 'schwimmbagger',
            'in-situ-leaching': 'lösungsbergbau',
            'placer': 'seifenlagerstätte'
        }

        # Exakter Match
        existing_type = session.query(MineType).filter(
            MineType.name.ilike(name.strip())
        ).first()

        if existing_type:
            logger.debug(f"Exaktes MineType-Duplikat gefunden: {name} -> ID:{existing_type.id}")
            return existing_type.id

        # Translation-basierter Match
        if clean_name in type_translation_map:
            translated_name = type_translation_map[clean_name]
            translated_type = session.query(MineType).filter(
                MineType.name.ilike(translated_name)
            ).first()

            if translated_type:
                logger.debug(f"Übersetzungs-Duplikat gefunden: {name} -> {translated_type.name}
(ID:{translated_type.id})")
                return translated_type.id

        return None

    def _validate_normalized_data_integrity(self, session: Session, field_data: Dict[str, Any]) -> bool:
    """_validate_normalized_data_integrity - TODO: Dokumentation hinzufügen"""
        \"\"\"
        Validiert Datenintegrität vor Insert (3NF-Compliance)
        \"\"\"
        field_type = field_data.get('field_type')

        if field_type == 'normalized':
            # Normalized Fields müssen mindestens eine FK-ID haben
            fk_fields = [
                'commodity_id', 'company_id', 'activity_status_id',
                'mine_type_id', 'country_id', 'region_id'
            ]

            has_fk = any(field_data.get(fk) is not None for fk in fk_fields)
            has_primitive = field_data.get('primitive_value') is not None

            if not has_fk:
                logger.error(f"3NF-Violation: Normalized field '{field_data.get('field_name')}' hat keine FK-ID")
                return False

            if has_primitive:
                logger.error(f"3NF-Violation: Normalized field '{field_data.get('field_name')}' hat primitive_value")
                return False

        elif field_type == 'primitive':
            # Primitive Fields dürfen keine FK-IDs haben
            fk_fields = [
                'commodity_id', 'company_id', 'activity_status_id',
                'mine_type_id', 'country_id', 'region_id'
            ]

            has_fk = any(field_data.get(fk) is not None for fk in fk_fields)
            has_primitive = field_data.get('primitive_value') is not None

            if has_fk:
                logger.error(f"3NF-Violation: Primitive field '{field_data.get('field_name')}' hat FK-IDs")
                return False

            if not has_primitive and not field_data.get('numeric_value'):
                logger.error(f"3NF-Violation: Primitive field '{field_data.get('field_name')}' hat
weder primitive_value noch numeric_value")
                return False

        return True

    def get_or_create_company(self, session: Session, name: str, role: str = None) -> Company:
    """get_or_create_company - TODO: Dokumentation hinzufügen"""
        \"\"\"
        ENHANCED: Holt oder erstellt Company mit Duplikate-Prävention
        \"\"\"
        if not name:
            raise ValueError("Company name cannot be empty")

        # Prüfe auf Duplikate BEVOR neue Company erstellt wird
        duplicate_id = self._check_company_duplicates(session, name, role)
        if duplicate_id:
            existing_company = session.query(Company).get(duplicate_id)
            logger.info(f"Company-Duplikat verhindert: '{name}' -> existierende
'{existing_company.name}' (ID:{duplicate_id})")
            return existing_company

        # Keine Duplikate -> erstelle neue Company
        logger.info(f"Erstelle neue Company: '{name}' (Role: {role})")
        new_company = Company(name=name.strip(), role=role)
        session.add(new_company)
        session.flush()

        return new_company

    def get_or_create_region(self, session: Session, name: str, country_id: int) -> Region:
    """get_or_create_region - TODO: Dokumentation hinzufügen"""
        \"\"\"
        ENHANCED: Holt oder erstellt Region mit Duplikate-Prävention
        \"\"\"
        if not name:
            raise ValueError("Region name cannot be empty")

        # Prüfe auf Duplikate
        duplicate_id = self._check_region_duplicates(session, name, country_id)
        if duplicate_id:
            existing_region = session.query(Region).get(duplicate_id)
            logger.info(f"Region-Duplikat verhindert: '{name}' -> existierende
'{existing_region.name}' (ID:{duplicate_id})")
            return existing_region

        # Keine Duplikate -> erstelle neue Region
        logger.info(f"Erstelle neue Region: '{name}' (Country: {country_id})")
        new_region = Region(name=name.strip(), country_id=country_id)
        session.add(new_region)
        session.flush()

        return new_region

    def get_or_create_commodity(self, session: Session, name: str, symbol: str = None, unit: str = None) -> Commodity:
    """get_or_create_commodity - TODO: Dokumentation hinzufügen"""
        \"\"\"
        ENHANCED: Holt oder erstellt Commodity mit Duplikate-Prävention
        \"\"\"
        if not name:
            raise ValueError("Commodity name cannot be empty")

        # Prüfe auf Duplikate
        duplicate_id = self._check_commodity_duplicates(session, name)
        if duplicate_id:
            existing_commodity = session.query(Commodity).get(duplicate_id)
            logger.info(f"Commodity-Duplikat verhindert: '{name}' -> existierende
'{existing_commodity.name}' (ID:{duplicate_id})")
            return existing_commodity

        # Keine Duplikate -> erstelle neue Commodity
        logger.info(f"Erstelle neue Commodity: '{name}' (Symbol: {symbol}, Unit: {unit})")
        new_commodity = Commodity(name=name.strip(), symbol=symbol, unit=unit)
        session.add(new_commodity)
        session.flush()

        return new_commodity

    def get_or_create_mine_type(self, session: Session, name: str, description: str = None) -> MineType:
    """get_or_create_mine_type - TODO: Dokumentation hinzufügen"""
        \"\"\"
        ENHANCED: Holt oder erstellt MineType mit Duplikate-Prävention
        \"\"\"
        if not name:
            raise ValueError("MineType name cannot be empty")

        # Prüfe auf Duplikate
        duplicate_id = self._check_mine_type_duplicates(session, name)
        if duplicate_id:
            existing_type = session.query(MineType).get(duplicate_id)
            logger.info(f"MineType-Duplikat verhindert: '{name}' -> existierende
'{existing_type.name}' (ID:{duplicate_id})")
            return existing_type

        # Keine Duplikate -> erstelle neuen MineType
        logger.info(f"Erstelle neuen MineType: '{name}' (Description: {description})")
        new_type = MineType(name=name.strip(), description=description)
        session.add(new_type)
        session.flush()

        return new_type

    def _insert_mine_data_field_3nf(self, session: Session, data: Dict[str, Any]) -> bool:
    """_insert_mine_data_field_3nf - TODO: Dokumentation hinzufügen"""
        \"\"\"
        ENHANCED: Fügt mine_data_field mit 3NF-Validierung und Duplikate-Prävention ein
        \"\"\"
        try:
            # Pre-Validierung der Datenintegrität
            if not self._validate_normalized_data_integrity(session, data):
                logger.error("3NF-Validierung fehlgeschlagen - Insert abgebrochen")
                return False

            # Bestehende Insert-Logik...
            mine_data_field = MineDataField(**data)
            session.add(mine_data_field)
            session.flush()

            logger.debug(f"MineDataField erfolgreich eingefügt: {data.get('field_name')} (Type:
{data.get('field_type')})")
            return True

        except Exception as e:
            logger.error(f"Fehler beim Einfügen von MineDataField: {e}")
            session.rollback()
            return False

    # ===== ENDE DUPLIKATE-PRÄVENTION =====
"""

    print("2. Berechne Einfügepunkte für Enhanced Methods...")

    # Finde Ende der Klasse (vor letzter Methode)
    last_method_start = current_code.rfind("    def ", class_start)
    if last_method_start == -1:
        print("   ❌ Keine Methoden in Klasse gefunden!")
        return False

    # Finde Ende der letzten Methode
    insertion_point = current_code.rfind("\n", last_method_start)

    # Füge neue Methoden ein
    enhanced_code = (
        current_code[:insertion_point] +
        duplicate_prevention_methods +
        current_code[insertion_point:]
    )

    print("3. Schreibe Enhanced Version...")

    try:
        with
open("/home/hanno/projects/MineSearch/backend/minesearch/database/normalized_manager_enhanced.py",
'w') as f:
            f.write(enhanced_code)

        print(f"   ✅ Enhanced Version erstellt: normalized_manager_enhanced.py")
        print(f"   📊 Neue Dateigröße: {len(enhanced_code)} Zeichen")
        print(f"   🔧 Hinzugefügte Features:")
        print(f"     - Company-Duplikate-Erkennung mit Varianten-Matching")
        print(f"     - Region-Duplikate-Erkennung (Quebec-Varianten)")
        print(f"     - Commodity-Duplikate-Erkennung (Deutsch/Englisch)")
        print(f"     - MineType-Duplikate-Erkennung (Deutsch/Englisch)")
        print(f"     - 3NF-Datenintegrität-Validierung")
        print(f"     - Enhanced get_or_create_* Methoden")

        return True

    except Exception as e:
        print(f"   ❌ Fehler beim Schreiben: {e}")
        return False

if __name__ == "__main__":
    success = create_enhanced_normalized_manager()

    if success:
        print(f"\n🎉 PHASE 3 ERFOLGREICH ABGESCHLOSSEN!")
        print("✅ Enhanced NormalizedDatabaseManager erstellt")
        print("✅ Duplikate-Prävention implementiert")
        print("✅ 3NF-Validierung verstärkt")
        print()
        print("📋 NÄCHSTER SCHRITT:")
        print("   1. Teste Enhanced Version")
        print("   2. Bei Erfolg: Ersetze Original-Datei")
        print("   3. Validierung mit echten Daten")
    else:
        print(f"\n❌ PHASE 3 FEHLGESCHLAGEN!")
        print("🔧 Manuelle Überprüfung erforderlich")
