/*
Author: rahn
Datum: 27.07.2025
Version: 1.0
Beschreibung: Intelligente Deduplizierung-Engine für konsolidierte Ergebnisse mit Synonym-Erkennung
*/

/**
 * ============================================
 * DEDUPLIZIERUNG-ARCHITEKTUR
 * ============================================
 * 
 * PROBLEMSTELLUNG:
 * - Statt: "X / Geplant / Geplant / Aktiv / Geplant / Geplant"
 * - Zeige: "X (1) / Geplant (4) / Aktiv (1)"
 * - Häufigster Wert zuerst
 * - Synonym-Erkennung: "Canada" und "Kanada" zusammenfassen
 * 
 * ARCHITEKTUR-KOMPONENTEN:
 * 1. Wert-Sammler und -Zähler
 * 2. Synonym-Normalisierer
 * 3. Häufigkeits-Sortierer
 * 4. Format-Renderer
 */

class DeduplicationEngine {
    constructor() {
        this.synonymMaps = this.initializeSynonymMaps();
        this.cache = new Map();
        this.debugMode = false;
    }

    /**
     * SYNONYM-MAPPING-SYSTEM
     * Definiert Synonyme für verschiedene Feldtypen
     */
    initializeSynonymMaps() {
        return {
            // Länder-Synonyme
            countries: {
                'canada': ['canada', 'kanada', 'ca'],
                'usa': ['usa', 'united states', 'united states of america', 'us'],
                'germany': ['germany', 'deutschland', 'de'],
                'france': ['france', 'frankreich', 'fr'],
                'australia': ['australia', 'australien', 'au'],
                'chile': ['chile', 'cl'],
                'peru': ['peru', 'pe'],
                'brazil': ['brazil', 'brasilien', 'br'],
                'mexico': ['mexico', 'mexiko', 'mx'],
                'south africa': ['south africa', 'südafrika', 'za']
            },

            // Status-Synonyme
            status: {
                'aktiv': ['aktiv', 'active', 'operating', 'in operation', 'betrieb'],
                'geplant': ['geplant', 'planned', 'proposed', 'development', 'in development'],
                'stillgelegt': ['stillgelegt', 'closed', 'abandoned', 'inactive', 'shut down'],
                'exploration': ['exploration', 'erkunden', 'prospecting', 'feasibility'],
                'construction': ['construction', 'bau', 'building', 'under construction'],
                'production': ['production', 'produktion', 'mining', 'extracting']
            },

            // Mineralien-Synonyme
            minerals: {
                'gold': ['gold', 'au', 'aurum'],
                'silver': ['silver', 'silber', 'ag'],
                'copper': ['copper', 'kupfer', 'cu'],
                'iron': ['iron', 'eisen', 'fe', 'iron ore'],
                'zinc': ['zinc', 'zink', 'zn'],
                'lead': ['lead', 'blei', 'pb'],
                'nickel': ['nickel', 'ni'],
                'lithium': ['lithium', 'li'],
                'cobalt': ['cobalt', 'kobalt', 'co'],
                'platinum': ['platinum', 'platin', 'pt']
            },

            // Regionen-Synonyme
            regions: {
                'british columbia': ['british columbia', 'bc', 'b.c.'],
                'ontario': ['ontario', 'on'],
                'quebec': ['quebec', 'québec', 'qc', 'que'],
                'alberta': ['alberta', 'ab'],
                'northern territory': ['northern territory', 'nt'],
                'western australia': ['western australia', 'wa'],
                'new south wales': ['new south wales', 'nsw']
            }
        };
    }

    /**
     * HAUPT-DEDUPLIZIERUNGS-FUNKTION
     * Verarbeitet einen Werte-String und gibt deduplizierte Darstellung zurück
     */
    deduplicateValues(valuesString, fieldType = 'general') {
        if (!valuesString || typeof valuesString !== 'string') {
            return valuesString;
        }

        // Cache-Check für Performance
        const cacheKey = `${valuesString}_${fieldType}`;
        if (this.cache.has(cacheKey)) {
            return this.cache.get(cacheKey);
        }

        try {
            // 1. Spezielle X-Behandlung: Zähle X-Werte separat
            const allRawValues = valuesString
                .split(' / ')
                .map(value => value.trim())
                .filter(value => value && value !== '' && value !== 'N/A' && value !== 'null');
                
            const xCount = allRawValues.filter(value => value === 'X').length;
            
            // 2. Werte extrahieren (ohne X-Werte für normale Verarbeitung)
            const rawValues = this.extractValues(valuesString);
            
            // 3. Werte normalisieren und Synonyme zusammenfassen
            const normalizedValues = this.normalizeValues(rawValues, fieldType);
            
            // 4. Häufigkeiten zählen
            const frequencies = this.countFrequencies(normalizedValues);
            
            // 5. X-Werte zu Häufigkeiten hinzufügen wenn vorhanden
            if (xCount > 0) {
                frequencies.set('X', xCount);
            }
            
            // 4. Nach Häufigkeit sortieren und formatieren
            const result = this.formatDeduplicatedResult(frequencies);
            
            // Cache speichern
            this.cache.set(cacheKey, result);
            
            if (this.debugMode) {
                console.log('Deduplication Debug:', {
                    original: valuesString,
                    fieldType,
                    rawValues,
                    normalizedValues,
                    frequencies,
                    result
                });
            }
            
            return result;
            
        } catch (error) {
            console.error('Deduplication Error:', error);
            return valuesString; // Fallback zum Original
        }
    }

    /**
     * WERT-EXTRAKTION
     * Extrahiert einzelne Werte aus einem zusammengesetzten String
     */
    extractValues(valuesString) {
        const allValues = valuesString
            .split(' / ')
            .map(value => value.trim())
            .filter(value => value && value !== '' && value !== 'N/A' && value !== 'null');
        
        // Spezielle Behandlung für X-Werte: Wenn alle Werte "X" sind, einen behalten
        const nonXValues = allValues.filter(value => value !== 'X');
        const xCount = allValues.length - nonXValues.length;
        
        // Wenn nur X-Werte vorhanden sind, einen X-Wert beibehalten für Häufigkeitszählung
        if (nonXValues.length === 0 && xCount > 0) {
            return ['X'];
        }
        
        // Wenn gemischte Werte vorhanden sind, X-Werte ignorieren
        return nonXValues.length > 0 ? nonXValues : allValues;
    }

    /**
     * WERT-NORMALISIERUNG MIT SYNONYM-ERKENNUNG
     * Konvertiert Synonyme zu Standardformen
     */
    normalizeValues(values, fieldType) {
        const synonymMap = this.getSynonymMapForFieldType(fieldType);
        
        return values.map(value => {
            const cleanValue = this.cleanValue(value);
            return this.findCanonicalForm(cleanValue, synonymMap) || cleanValue;
        });
    }

    /**
     * WERT-BEREINIGUNG
     * Entfernt Quellen-Referenzen und bereinigt den Wert
     */
    cleanValue(value) {
        // Entferne Quellen-Referenzen wie [gpt-4, claude-3]
        let cleaned = value.replace(/\s*\[([^\]]+)\]\s*$/, '');
        
        // Bereinige Whitespace und konvertiere zu Lowercase
        cleaned = cleaned.trim().toLowerCase();
        
        // Entferne führende/trailing Anführungszeichen
        cleaned = cleaned.replace(/^["']|["']$/g, '');
        
        return cleaned;
    }

    /**
     * SYNONYM-MAP-SELEKTOR
     * Wählt die passende Synonym-Map basierend auf Feldtyp
     */
    getSynonymMapForFieldType(fieldType) {
        const typeMapping = {
            'country': this.synonymMaps.countries,
            'land': this.synonymMaps.countries,
            'status': this.synonymMaps.status,
            'mine_status': this.synonymMaps.status,
            'operation_status': this.synonymMaps.status,
            'mineral': this.synonymMaps.minerals,
            'commodity': this.synonymMaps.minerals,
            'region': this.synonymMaps.regions,
            'province': this.synonymMaps.regions,
            'state': this.synonymMaps.regions
        };

        return typeMapping[fieldType.toLowerCase()] || {};
    }

    /**
     * KANONISCHE FORM FINDEN
     * Findet die Standardform für einen Wert basierend auf Synonymen
     */
    findCanonicalForm(value, synonymMap) {
        for (const [canonical, synonyms] of Object.entries(synonymMap)) {
            if (synonyms.includes(value)) {
                return canonical;
            }
        }
        return null;
    }

    /**
     * HÄUFIGKEITS-ZÄHLUNG
     * Zählt wie oft jeder normalisierte Wert vorkommt
     */
    countFrequencies(normalizedValues) {
        const frequencies = new Map();
        
        normalizedValues.forEach(value => {
            frequencies.set(value, (frequencies.get(value) || 0) + 1);
        });
        
        return frequencies;
    }

    /**
     * ERGEBNIS-FORMATIERUNG
     * Erstellt die finale deduplizierte Darstellung
     */
    formatDeduplicatedResult(frequencies) {
        if (frequencies.size === 0) {
            return '';
        }

        // Sortiere nach Häufigkeit (absteigend), dann alphabetisch
        const sortedEntries = Array.from(frequencies.entries())
            .sort((a, b) => {
                // Erst nach Häufigkeit
                if (b[1] !== a[1]) {
                    return b[1] - a[1];
                }
                // Dann alphabetisch
                return a[0].localeCompare(b[0]);
            });

        // Formatiere als "Wert (Anzahl)"
        return sortedEntries
            .map(([value, count]) => {
                // Kapitalisiere ersten Buchstaben für bessere Darstellung
                const displayValue = this.capitalizeFirst(value);
                return count > 1 ? `${displayValue} (${count})` : displayValue;
            })
            .join(' / ');
    }

    /**
     * KAPITALISIERUNG
     * Kapitalisiert den ersten Buchstaben eines Strings
     */
    capitalizeFirst(str) {
        if (!str) return str;
        return str.charAt(0).toUpperCase() + str.slice(1);
    }

    /**
     * BATCH-VERARBEITUNG FÜR TABELLEN
     * Verarbeitet alle Werte in einer Tabellen-Zeile
     */
    processTableRow(rowData, fieldTypeMapping = {}) {
        const processedRow = {};
        
        for (const [fieldName, value] of Object.entries(rowData)) {
            if (typeof value === 'string' && value.includes(' / ')) {
                const fieldType = fieldTypeMapping[fieldName] || 'general';
                processedRow[fieldName] = this.deduplicateValues(value, fieldType);
            } else {
                processedRow[fieldName] = value;
            }
        }
        
        return processedRow;
    }

    /**
     * ERWEITERTE SYNONYM-ERKENNUNG
     * Fügt neue Synonyme zur Laufzeit hinzu
     */
    addSynonym(fieldType, canonical, synonym) {
        if (!this.synonymMaps[fieldType]) {
            this.synonymMaps[fieldType] = {};
        }
        
        if (!this.synonymMaps[fieldType][canonical]) {
            this.synonymMaps[fieldType][canonical] = [canonical];
        }
        
        if (!this.synonymMaps[fieldType][canonical].includes(synonym.toLowerCase())) {
            this.synonymMaps[fieldType][canonical].push(synonym.toLowerCase());
        }
        
        // Cache leeren da sich Synonyme geändert haben
        this.cache.clear();
    }

    /**
     * PERFORMANCE-OPTIMIERUNG
     * Cache-Management und Statistiken
     */
    getCacheStats() {
        return {
            size: this.cache.size,
            maxSize: 1000, // Limit für Memory-Management
            hitRate: this.cacheHits / (this.cacheHits + this.cacheMisses) || 0
        };
    }

    clearCache() {
        this.cache.clear();
        this.cacheHits = 0;
        this.cacheMisses = 0;
    }

    /**
     * DEBUG-MODUS
     */
    enableDebug() {
        this.debugMode = true;
    }

    disableDebug() {
        this.debugMode = false;
    }
}

/**
 * ============================================
 * INTEGRATION MIT BESTEHENDER FRONTEND
 * ============================================
 */

// Globale Instanz erstellen
window.deduplicationEngine = new DeduplicationEngine();

/**
 * HELPER-FUNKTIONEN FÜR FRONTEND-INTEGRATION
 */

/**
 * Verarbeitet konsolidierte Feldwerte für bessere Darstellung
 */
function processConsolidatedFields(consolidatedFields) {
    const fieldTypeMapping = {
        'country': 'country',
        'land': 'country',
        'region': 'region',
        'province': 'region',
        'mine_status': 'status',
        'operation_status': 'status',
        'status': 'status',
        'mineral': 'mineral',
        'commodity': 'mineral',
        'primary_mineral': 'mineral'
    };

    const processedFields = {};
    
    for (const [fieldName, value] of Object.entries(consolidatedFields)) {
        if (typeof value === 'string' && value.includes(' / ')) {
            const fieldType = fieldTypeMapping[fieldName.toLowerCase()] || 'general';
            processedFields[fieldName] = window.deduplicationEngine.deduplicateValues(value, fieldType);
        } else {
            processedFields[fieldName] = value;
        }
    }
    
    return processedFields;
}

/**
 * Erweitert bestehende displayResultsTable Funktion
 */
function enhanceResultsTableWithDeduplication() {
    // Hook in die bestehende displayResultsTable Funktion
    const originalDisplayResultsTable = window.displayResultsTable;
    
    if (originalDisplayResultsTable) {
        window.displayResultsTable = function(results, sortBy, order) {
            // Verarbeite Ergebnisse mit Deduplizierung
            const enhancedResults = results.map(result => {
                if (result.consolidated_fields) {
                    result.consolidated_fields = processConsolidatedFields(result.consolidated_fields);
                }
                return result;
            });
            
            // Rufe ursprüngliche Funktion mit verbesserten Daten auf
            return originalDisplayResultsTable.call(this, enhancedResults, sortBy, order);
        };
    }
}

/**
 * HOVER-DETAILS FÜR VOLLSTÄNDIGE LISTEN
 * Zeigt alle ursprünglichen Werte bei Hover an
 */
function createHoverDetailElement(originalValue, deduplicatedValue) {
    const element = document.createElement('span');
    element.textContent = deduplicatedValue;
    element.style.cursor = 'help';
    element.title = `Alle Werte: ${originalValue}`;
    
    // Erweiterte Tooltip-Funktionalität
    element.addEventListener('mouseenter', function(e) {
        showDetailedTooltip(e, originalValue, deduplicatedValue);
    });
    
    return element;
}

function showDetailedTooltip(event, originalValue, deduplicatedValue) {
    // Implementierung eines erweiterten Tooltips
    // mit detaillierter Aufschlüsselung der Werte
    console.log('Detailed tooltip for:', { originalValue, deduplicatedValue });
}

/**
 * ============================================
 * INITIALISIERUNG UND EXPORT
 * ============================================
 */

// Automatische Initialisierung wenn DOM geladen ist
document.addEventListener('DOMContentLoaded', function() {
    enhanceResultsTableWithDeduplication();
    console.log('Deduplication Engine initialized and integrated');
});

// Export für modulare Verwendung
if (typeof module !== 'undefined' && module.exports) {
    module.exports = { DeduplicationEngine, processConsolidatedFields };
}

// Global verfügbar machen
window.MineSearchDeduplication = {
    DeduplicationEngine,
    processConsolidatedFields,
    enhanceResultsTableWithDeduplication
};