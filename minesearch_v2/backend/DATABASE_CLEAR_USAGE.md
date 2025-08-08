# Database Clear Script - Nutzungsanleitung

## Übersicht
Das `database_clear.py` Script ermöglicht sichere und robuste Datenbank-Bereinigung mit automatischem Backup-System.

## Grundlegende Nutzung

### 1. Sofortige komplette Bereinigung (EMPFOHLEN)
```bash
python3 database_clear.py --mode all --vacuum
```
- Löscht ALLE Daten (search_results, model_statistics, model_summary, field_statistics, field_consistency)
- Erstellt automatisch Backup vor Löschung
- Komprimiert Datenbank nach Bereinigung
- Behält sources und mines bei

### 2. Nur Einträge zählen (keine Bereinigung)
```bash
python3 database_clear.py --counts-only
```

### 3. Verfügbare Modi

| Modus | Beschreibung |
|-------|-------------|
| `all` | Alle Haupt-Tabellen (search_results, model_statistics, model_summary, field_statistics, field_consistency) |
| `results` | Nur search_results |
| `statistics` | Alle Statistik-Tabellen (model_statistics, model_summary, field_statistics, field_consistency) |
| `model_stats` | Nur model_statistics |
| `summaries` | Nur model_summary |
| `field_stats` | Nur field_statistics |
| `consistency` | Nur field_consistency |
| `sources` | Nur sources |
| `mines` | Nur mines |

### 4. Erweiterte Optionen

#### Ohne Backup bereinigen (VORSICHT!)
```bash
python3 database_clear.py --mode all --no-backup
```

#### Spezifische Modi
```bash
# Nur Suchergebnisse löschen
python3 database_clear.py --mode results

# Nur Statistiken löschen
python3 database_clear.py --mode statistics

# Mit Komprimierung
python3 database_clear.py --mode field_stats --vacuum
```

## Backup-System

### Backups auflisten
```bash
python3 database_clear.py --list-backups
```

### Backup wiederherstellen
```bash
python3 database_clear.py --restore [backup_name]
```

Beispiel:
```bash
python3 database_clear.py --restore before_clear_all_20250802_211354
```

## Sicherheitsfeatures

1. **Automatisches Backup**: Vor jeder Bereinigung wird automatisch ein Backup erstellt
2. **Verifizierung**: Nach Bereinigung wird geprüft ob Tabellen wirklich leer sind
3. **Metadaten**: Jedes Backup enthält Informationen über den ursprünglichen Datenstand
4. **Sichere Wiederherstellung**: Vor Restore wird automatisch ein Backup der aktuellen DB erstellt

## Aktuelle Datenbank-Größen

Nach kompletter Bereinigung (Stand: 02.08.2025):
- search_results: 0 Einträge
- model_statistics: 0 Einträge  
- model_summary: 0 Einträge
- field_statistics: 0 Einträge
- field_consistency: 0 Einträge
- sources: 19 Einträge (behalten)
- mines: 0 Einträge

**Gesamt: 19 Einträge** (nur sources)

## Backup-Historie

Verfügbare Backups (neueste zuerst):
- `before_clear_all_20250802_211447` (11.7 MB) - Vollständiger Datenbestand vor finaler Bereinigung
- `current_before_restore_20250802_211440` (0.2 MB) - Leere DB vor Restore-Test
- `before_clear_all_20250802_211354` (11.7 MB) - Vollständiger Datenbestand vor erster Bereinigung

## Notfall-Wiederherstellung

Bei Problemen kann der ursprüngliche Datenbestand mit folgendem Befehl wiederhergestellt werden:

```bash
python3 database_clear.py --restore before_clear_all_20250802_211447
```

Dies stellt den Zustand mit allen 3.238 ursprünglichen Einträgen wieder her.