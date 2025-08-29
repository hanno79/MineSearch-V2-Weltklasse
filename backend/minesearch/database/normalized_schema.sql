-- =====================================================
-- Author: rahn
-- Datum: 27.08.2025
-- Version: 1.0
-- Beschreibung: Normalisiertes Datenbankschema für MineSearch
-- =====================================================
--
-- ZIEL: Ersetze JSON-Chaos durch saubere, atomare Datenstruktur
-- Problem: Dateninkonsistenz, fehlende Validierung, Performance-Issues
--

-- =====================================================
-- 1. COMPANIES (Unternehmen Stammdaten)
-- =====================================================
CREATE TABLE IF NOT EXISTS companies (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE,
    normalized_name VARCHAR(255) NOT NULL, -- Für Deduplizierung
    company_type VARCHAR(20) DEFAULT 'owner' CHECK(company_type IN ('owner', 'operator', 'contractor', 'consultant')),
    country VARCHAR(100),
    website VARCHAR(500),
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Index für schnelle Name-Suche
CREATE INDEX IF NOT EXISTS idx_companies_normalized_name ON companies(normalized_name);

-- =====================================================
-- 2. MINES (Mine Stammdaten - normalisiert!)
-- =====================================================
CREATE TABLE IF NOT EXISTS mines_normalized (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    name VARCHAR(255) NOT NULL UNIQUE, -- EINDEUTIG!
    normalized_name VARCHAR(255) NOT NULL UNIQUE, -- Für Suche (eleonore, éléonore → eleonore)
    country VARCHAR(100) NOT NULL,
    region VARCHAR(100),
    
    -- Geografische Koordinaten (atomare Werte!)
    latitude DECIMAL(10,6),
    longitude DECIMAL(10,6),
    
    -- Status als kontrollierte Werte statt String-Chaos
    status VARCHAR(20) DEFAULT 'active' CHECK(status IN ('active', 'inactive', 'development', 'closed', 'suspended')),
    
    -- Unternehmens-Referenzen (Foreign Keys!)
    owner_company_id INTEGER,
    operator_company_id INTEGER,
    
    -- Mine-Typ als kontrollierte Werte
    mine_type VARCHAR(20) DEFAULT 'open_pit' CHECK(mine_type IN ('open_pit', 'underground', 'placer', 'solution', 'combined')),
    
    -- Primärer Rohstoff
    primary_commodity VARCHAR(20) DEFAULT 'gold' CHECK(primary_commodity IN ('gold', 'copper', 'silver', 'iron', 'coal', 'lithium', 'other')),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Foreign Key Constraints
    FOREIGN KEY (owner_company_id) REFERENCES companies(id) ON DELETE SET NULL,
    FOREIGN KEY (operator_company_id) REFERENCES companies(id) ON DELETE SET NULL
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_mines_normalized_name ON mines_normalized(normalized_name);
CREATE INDEX IF NOT EXISTS idx_mines_country ON mines_normalized(country);
CREATE INDEX IF NOT EXISTS idx_mines_status ON mines_normalized(status);
CREATE INDEX IF NOT EXISTS idx_mines_commodity ON mines_normalized(primary_commodity);

-- =====================================================
-- 3. FIELD_DEFINITIONS (Schema für alle Datenfelder)
-- =====================================================
CREATE TABLE IF NOT EXISTS field_definitions (
    field_name VARCHAR(100) PRIMARY KEY,
    display_name VARCHAR(200) NOT NULL,
    field_category VARCHAR(20) DEFAULT 'technical' CHECK(field_category IN ('technical', 'financial', 'operational', 'geographical', 'administrative')),
    data_type VARCHAR(20) DEFAULT 'text' CHECK(data_type IN ('number', 'text', 'currency', 'percentage', 'date', 'boolean', 'enum')),
    unit_type VARCHAR(50), -- 'currency', 'weight', 'area', 'volume', 'time'
    
    -- Validierung
    is_required BOOLEAN DEFAULT FALSE,
    validation_regex TEXT,
    min_value DECIMAL(20,2),
    max_value DECIMAL(20,2),
    allowed_values JSON, -- Nur für ENUM-Felder
    
    -- Template-Erkennung Patterns
    template_patterns JSON, -- Patterns die als Template erkannt werden
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP
);

-- Standard-Felder definieren
INSERT INTO field_definitions 
(field_name, display_name, field_category, data_type, unit_type, is_required) VALUES
('name', 'Mine Name', 'administrative', 'text', NULL, TRUE),
('country', 'Land', 'geographical', 'text', NULL, TRUE),
('region', 'Region', 'geographical', 'text', NULL, FALSE),
('latitude', 'Breitengrad', 'geographical', 'number', 'coordinate', FALSE),
('longitude', 'Längengrad', 'geographical', 'number', 'coordinate', FALSE),
('restoration_costs', 'Restaurationskosten', 'financial', 'currency', 'currency', FALSE),
('production_year', 'Fördermenge/Jahr', 'operational', 'number', 'weight', FALSE),
('area_sqkm', 'Fläche in qkm', 'technical', 'number', 'area', FALSE),
('depth_meters', 'Tiefe in Metern', 'technical', 'number', 'length', FALSE)
ON CONFLICT(field_name) DO NOTHING;

-- =====================================================
-- 4. MINE_DATA_FIELDS (Atomare Feldwerte!)
-- =====================================================
CREATE TABLE IF NOT EXISTS mine_data_fields (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    search_result_id INTEGER NOT NULL, -- Referenz zu original search_results
    mine_id INTEGER NOT NULL, -- Referenz zu normalisierte Mine
    
    -- Feldwert (atomare Speicherung!)
    field_name VARCHAR(100) NOT NULL,
    raw_value TEXT, -- Original-Wert aus AI-Response
    normalized_value TEXT, -- Normalisierter Wert
    
    -- Numerische Werte für Berechnungen
    numeric_value DECIMAL(20,2),
    unit VARCHAR(50),
    
    -- Qualität und Vertrauenswürdigkeit
    confidence_score DECIMAL(3,2), -- 0.00 bis 1.00
    is_template_value BOOLEAN DEFAULT FALSE, -- REGEL 10 Compliance!
    validation_status VARCHAR(20) DEFAULT 'valid' CHECK(validation_status IN ('valid', 'invalid', 'template', 'uncertain')),
    
    -- Quelle
    source_id INTEGER,
    source_name VARCHAR(500),
    
    -- Modell-Info
    model_used VARCHAR(100) NOT NULL,
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    updated_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (mine_id) REFERENCES mines_normalized(id) ON DELETE CASCADE,
    FOREIGN KEY (field_name) REFERENCES field_definitions(field_name) ON DELETE CASCADE,
    FOREIGN KEY (source_id) REFERENCES sources(id) ON DELETE SET NULL ON UPDATE CASCADE
);

-- Indizes für Performance
CREATE INDEX IF NOT EXISTS idx_mine_fields_mine_id ON mine_data_fields(mine_id);
CREATE INDEX IF NOT EXISTS idx_mine_fields_field_name ON mine_data_fields(field_name);
CREATE INDEX IF NOT EXISTS idx_mine_fields_search_result ON mine_data_fields(search_result_id);
CREATE INDEX IF NOT EXISTS idx_mine_fields_model ON mine_data_fields(model_used);
CREATE INDEX IF NOT EXISTS idx_mine_fields_validation ON mine_data_fields(validation_status);

-- Verhindert Duplikate: Eine Mine kann pro Feld nur einen Wert pro Search Result haben
CREATE UNIQUE INDEX IF NOT EXISTS idx_unique_mine_field_search 
ON mine_data_fields(mine_id, field_name, search_result_id);

-- =====================================================
-- 5. SEARCH_RESULTS_NORMALIZED (Saubere Suchergebnisse)
-- =====================================================
CREATE TABLE IF NOT EXISTS search_results_normalized (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    original_search_result_id INTEGER, -- Referenz zu alter Tabelle
    session_id VARCHAR(255),
    mine_id INTEGER NOT NULL, -- Referenz zu normalisierte Mine
    
    -- Search Metadata
    search_timestamp DATETIME NOT NULL,
    model_used VARCHAR(100) NOT NULL,
    search_type VARCHAR(20) DEFAULT 'single' CHECK(search_type IN ('single', 'batch', 'consolidated')),
    search_duration DECIMAL(8,3),
    
    -- Qualität
    success BOOLEAN DEFAULT TRUE,
    error_message TEXT,
    fields_found INTEGER DEFAULT 0,
    template_fields_rejected INTEGER DEFAULT 0,
    data_quality_score DECIMAL(3,2),
    
    created_at DATETIME DEFAULT CURRENT_TIMESTAMP,
    
    -- Constraints
    FOREIGN KEY (mine_id) REFERENCES mines_normalized(id) ON DELETE CASCADE
);

-- Indizes
CREATE INDEX IF NOT EXISTS idx_search_norm_mine_id ON search_results_normalized(mine_id);
CREATE INDEX IF NOT EXISTS idx_search_norm_model ON search_results_normalized(model_used);
CREATE INDEX IF NOT EXISTS idx_search_norm_timestamp ON search_results_normalized(search_timestamp);

-- =====================================================
-- 6. TRIGGER für automatische Updates
-- =====================================================

-- Auto-Update timestamp auf mines_normalized
CREATE TRIGGER IF NOT EXISTS update_mines_timestamp 
    AFTER UPDATE ON mines_normalized
    WHEN NEW.updated_at IS OLD.updated_at
BEGIN
    UPDATE mines_normalized 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- Auto-Update timestamp auf mine_data_fields
CREATE TRIGGER IF NOT EXISTS update_mine_data_fields_timestamp 
    AFTER UPDATE ON mine_data_fields
    WHEN NEW.updated_at IS OLD.updated_at
BEGIN
    UPDATE mine_data_fields 
    SET updated_at = CURRENT_TIMESTAMP 
    WHERE id = NEW.id;
END;

-- =====================================================
-- 7. VIEWS für einfache Abfragen
-- =====================================================

-- View: Vollständige Mine-Information
CREATE VIEW IF NOT EXISTS mines_complete AS
SELECT 
    m.id,
    m.name,
    m.normalized_name,
    m.country,
    m.region,
    m.latitude,
    m.longitude,
    m.status,
    m.mine_type,
    m.primary_commodity,
    owner.name AS owner_company,
    operator.name AS operator_company,
    m.created_at,
    m.updated_at
FROM mines_normalized m
LEFT JOIN companies owner ON m.owner_company_id = owner.id
LEFT JOIN companies operator ON m.operator_company_id = operator.id;

-- View: Mine mit aktuellsten Felddaten
CREATE VIEW IF NOT EXISTS mines_with_latest_data AS
SELECT 
    m.*,
    COUNT(DISTINCT mdf.field_name) as total_fields,
    COUNT(DISTINCT CASE WHEN mdf.validation_status = 'valid' THEN mdf.field_name END) as valid_fields,
    COUNT(DISTINCT CASE WHEN mdf.is_template_value = TRUE THEN mdf.field_name END) as template_fields,
    MAX(mdf.created_at) as last_updated
FROM mines_normalized m
LEFT JOIN mine_data_fields mdf ON m.id = mdf.mine_id
GROUP BY m.id;

-- =====================================================
-- MIGRATION QUERIES (für späteren Import)
-- =====================================================

-- Diese werden vom Python Migration Script verwendet
-- INSERT INTO mines_normalized (name, normalized_name, country, ...) SELECT ...;
-- INSERT INTO mine_data_fields (mine_id, field_name, raw_value, ...) SELECT ...;