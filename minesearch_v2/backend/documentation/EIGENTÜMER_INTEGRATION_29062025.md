# Eigentümer-Feld Integration in MineSearch V2
Datum: 29.06.2025
Author: Claude

## Übersicht
Ein neues Feld "Eigentümer" wurde zwischen "Region" und "Betreiber" in MineSearch V2 integriert, um zwischen dem Eigentümer einer Mine (Owner) und dem Betreiber (Operator) unterscheiden zu können.

## Durchgeführte Änderungen

### 1. Backend - main.py

#### CSV_COLUMNS Definition (Zeile 37-46)
```python
CSV_COLUMNS = [
    'ID', 'Name', 'Country', 'Region', 'Eigentümer', 'Betreiber', 'x-Koordinate', 
    'y-Koordinate', 'Aktivitätsstatus',
    'Restaurationskosten', 'Jahr der Aufnahme der Kosten',
    'Jahr der Erstellung des Dokumentes', 
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
    'Minentyp (Untertage/ Open-Pit/ usw.)', 'Produktionsstart',
    'Produktionsende', 'Fördermenge/Jahr', 'Fläche der Mine in qkm',
    'Quellenangaben'
]
```

#### FIELDS_WITHOUT_SOURCES (Zeile 49-56)
```python
FIELDS_WITHOUT_SOURCES = [
    'ID',
    'Name',
    'Country', 
    'Region',
    'Eigentümer',  # ÄNDERUNG 29.06.2025: Eigentümer hinzugefügt
    'Quellenangaben'
]
```

#### Datenextraktion Pattern (Zeile 459-471)
```python
'Eigentümer': [
    r'Eigentümer:\s*([^\n]+)',
    r'Owner:\s*([^\n]+)',
    r'Propriétaire:\s*([^\n]+)',
    r'Propietario:\s*([^\n]+)',
    r'Pemilik:\s*([^\n]+)',
    r'gehört\s+(?:zu|der|dem)\s+([^\n]+)',
    r'owned\s+by\s+([^\n]+)',
    r'property\s+of\s+([^\n]+)',
    r'belongs\s+to\s+([^\n]+)',
    r'possession\s+of\s+([^\n]+)',
    r'Eigentum\s+(?:von|der)\s+([^\n]+)'
],
```

#### Perplexity Prompt Template (Zeile 1089)
```
- Eigentümer: [Eigentümer der Mine] [Quelle: URL/Dokument]
- Betreiber: [Betreiber/Operator] [Quelle: URL/Dokument]
```

#### CSV Upload Handler (Zeile 1344-1351)
```python
# Mögliche Namen für Eigentümer
owner_column = None
owner_possibilities = ['owner', 'eigentümer', 'propriétaire', 'propietario', 
                      'pemilik', 'dueño', 'belongs to', 'property of', 'gehört']
for possible in owner_possibilities:
    if possible.lower() in columns:
        owner_column = columns[possible.lower()]
        break
```

### 2. Backend - config.py

Für alle Länder-Konfigurationen wurde ein neues 'owner' Dictionary in 'mining_terms' hinzugefügt:

#### Kanada/Canada (Französisch & Englisch)
```python
'owner': ['owner', 'propriétaire', 'eigentümer', 'propietario', 'belongs to', 'gehört', 'property of'],
```

#### Australien/Australia
```python
'owner': ['owner', 'owns', 'ownership', 'property of', 'belongs to', 'held by'],
```

#### Indonesien/Indonesia
```python
'owner': ['pemilik', 'owner', 'dimiliki oleh', 'milik', 'kepemilikan'],
```

#### Peru
```python
'owner': ['propietario', 'dueño', 'owner', 'propiedad de', 'pertenece a'],
```

#### Chile
```python
'owner': ['propietario', 'dueño', 'owner', 'propiedad de', 'pertenece a', 'de propiedad de'],
```

### 3. Frontend - index.html

#### csvColumns Array (Zeile 430-439)
```javascript
const csvColumns = [
    'ID', 'Name', 'Country', 'Region', 'Eigentümer', 'Betreiber', 'x-Koordinate', 
    'y-Koordinate', 'Aktivitätsstatus',
    'Restaurationskosten', 'Jahr der Aufnahme der Kosten',
    'Jahr der Erstellung des Dokumentes', 
    'Rohstoffabbau (Gold/ Kupfer/ Kohle/ usw.)',
    'Minentyp (Untertage/ Open-Pit/ usw.)', 'Produktionsstart',
    'Produktionsende', 'Fördermenge/Jahr', 'Fläche der Mine in qkm',
    'Quellenangaben'
];
```

#### fieldsWithoutSources (Zeile 520)
```javascript
const fieldsWithoutSources = ['ID', 'Name', 'Country', 'Region', 'Eigentümer', 'Quellenangaben'];
```

## Funktionalität

### Datenextraktion
Das System sucht nun automatisch nach Eigentümer-Informationen mit verschiedenen Mustern:
- Direkte Kennzeichnung: "Eigentümer:", "Owner:", etc.
- Besitzangaben: "gehört zu", "owned by", "property of"
- Mehrsprachige Unterstützung in 5+ Sprachen

### CSV Import
- Erkennt automatisch Eigentümer-Spalten in CSV-Dateien
- Unterstützt verschiedene Spaltennamen in mehreren Sprachen
- Speichert die Information für die Batch-Verarbeitung

### Anzeige
- Eigentümer wird als separates Feld zwischen Region und Betreiber angezeigt
- In Tabellen und Exporten konsistent positioniert
- Keine Quellenreferenzen für das Eigentümer-Feld (wie bei Name, Country, Region)

### Unterscheidung Eigentümer vs. Betreiber
- **Eigentümer**: Die juristische/wirtschaftliche Einheit, die die Mine besitzt
- **Betreiber**: Das Unternehmen, das die täglichen Operationen durchführt
- Können identisch sein, müssen aber nicht

## Testing

Die Implementierung kann getestet werden durch:
1. Einzelsuche einer Mine mit bekanntem Eigentümer
2. CSV-Upload mit Eigentümer-Spalte
3. Batch-Suche und Überprüfung der Ergebnisse
4. Export der Ergebnisse (CSV-Download)

## Erwartete Suchergebnisse

Bei der Suche wird Perplexity explizit angewiesen, nach dem Eigentümer UND dem Betreiber zu suchen und diese als separate Felder zurückzugeben.

Beispiel-Ausgabe:
```
- Eigentümer: Barrick Gold Corporation [Quelle: Annual Report 2023]
- Betreiber: Nevada Gold Mines LLC (Joint Venture) [Quelle: Company Website]
```