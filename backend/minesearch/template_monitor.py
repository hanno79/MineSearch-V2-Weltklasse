"""
Author: rahn
Datum: 26.08.2025
Version: 1.0
Beschreibung: Template-Monitoring-System für REGEL 10 Compliance
ZWECK: Erkennung von wiederkehrenden Template-/Dummy-Datenmustern über Zeit
"""

import logging
import json
import re
from datetime import datetime, timedelta
from typing import Dict, List, Any, Optional, Set
from collections import defaultdict, Counter
from dataclasses import dataclass
from pathlib import Path
import sqlite3
from minesearch.config import config

logger = logging.getLogger(__name__)

@dataclass
class TemplateAlert:
    """Alert für verdächtige Template-Pattern"""
    pattern: str
    field: str
    occurrences: int
    mines: List[str]
    first_seen: datetime
    last_seen: datetime
    severity: str  # 'low', 'medium', 'high', 'critical'

    def to_dict(self) -> Dict[str, Any]:
    """to_dict - TODO: Dokumentation hinzufügen"""
        return {
            'pattern': self.pattern,
            'field': self.field,
            'occurrences': self.occurrences,
            'mines': self.mines,
            'first_seen': self.first_seen.isoformat(),
            'last_seen': self.last_seen.isoformat(),
            'severity': self.severity
        }

class TemplateMonitor:
    """
    REGEL 10 COMPLIANCE MONITOR

    Überwacht Datenbankeinträge auf verdächtige Muster die auf AI-Templates hindeuten:
    - Identische Werte über viele Minen hinweg
    - Verdächtige Quellen wie "Fachwissen"
    - Runde Zahlen in unnatürlichen Häufigkeiten
    - Template-Phrasen und -Strukturen
    """

    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.db_path = self._get_monitor_db_path()
        self.alerts: List[TemplateAlert] = []
        self._setup_monitor_db()

    def _get_monitor_db_path(self) -> Path:
        """Bestimme Pfad für Monitor-Datenbank"""
        try:
            # Versuche Config-Datenbankpfad zu verwenden
            main_db = config.DATABASE_URL
            if main_db.startswith('sqlite:///'):
                db_dir = Path(main_db.replace('sqlite:///', '')).parent
                return db_dir / 'template_monitor.db'
        except:
            pass

        # Fallback: Backend-Verzeichnis
        return Path(__file__).parent / 'database' / 'template_monitor.db'

    def _setup_monitor_db(self):
        """Erstelle Monitor-Datenbank falls nicht vorhanden"""
        try:
            self.db_path.parent.mkdir(parents=True, exist_ok=True)

            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    CREATE TABLE IF NOT EXISTS template_patterns (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern TEXT NOT NULL,
                        field TEXT NOT NULL,
                        mine_name TEXT NOT NULL,
                        value TEXT NOT NULL,
                        source_info TEXT,
                        detected_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
                        severity TEXT DEFAULT 'medium'
                    )
                ''')

                conn.execute('''
                    CREATE TABLE IF NOT EXISTS pattern_alerts (
                        id INTEGER PRIMARY KEY AUTOINCREMENT,
                        pattern TEXT NOT NULL,
                        field TEXT NOT NULL,
                        occurrences INTEGER NOT NULL,
                        mines TEXT NOT NULL,  -- JSON array
                        first_seen TIMESTAMP,
                        last_seen TIMESTAMP,
                        severity TEXT,
                        status TEXT DEFAULT 'active',  -- active, resolved, false_positive
                        created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
                    )
                ''')

                # Erstelle Indizes für Performance
                conn.execute('''CREATE INDEX IF NOT EXISTS idx_pattern_field
                               ON template_patterns(pattern, field)''')
                conn.execute('''CREATE INDEX IF NOT EXISTS idx_detected_at
                               ON template_patterns(detected_at)''')
                conn.execute('''CREATE INDEX IF NOT EXISTS idx_mine_name
                               ON template_patterns(mine_name)''')

        except Exception as e:
            logger.error(f"[TEMPLATE_MONITOR] Fehler beim Setup der Monitor-DB: {e}")

    def record_pattern(self, pattern_type: str, field: str, mine_name: str,
    """record_pattern - TODO: Dokumentation hinzufügen"""
                      value: str, source_info: Optional[str] = None,
                      severity: str = 'medium'):
        """
        Erfasse verdächtiges Pattern

        Args:
            pattern_type: Art des Pattern (z.B. 'duplicate_value', 'fake_source', 'round_number')
            field: Betroffenes Datenfeld
            mine_name: Name der Mine
            value: Der verdächtige Wert
            source_info: Information über Quelle (falls verfügbar)
            severity: Schweregrad ('low', 'medium', 'high', 'critical')
        """
        try:
            with sqlite3.connect(self.db_path) as conn:
                conn.execute('''
                    INSERT INTO template_patterns
                    (pattern, field, mine_name, value, source_info, severity)
                    VALUES (?, ?, ?, ?, ?, ?)
                ''', (pattern_type, field, mine_name, value, source_info, severity))

            logger.info(f"[TEMPLATE_MONITOR] Pattern erfasst: {pattern_type} in {field} für {mine_name}")

        except Exception as e:
            logger.error(f"[TEMPLATE_MONITOR] Fehler beim Erfassen des Patterns: {e}")

    def analyze_patterns(self, days_back: int = 7, min_occurrences: int = 3) -> List[TemplateAlert]:
        """
        Analysiere Pattern der letzten Tage auf verdächtige Häufungen

        Args:
            days_back: Anzahl Tage zurück zu analysieren
            min_occurrences: Minimum Vorkommen für Alert

        Returns:
            Liste von TemplateAlert Objekten
        """
        alerts = []
        cutoff_date = datetime.now() - timedelta(days=days_back)

        try:
            with sqlite3.connect(self.db_path) as conn:
                # Gruppiere Pattern nach Typ und Feld
                query = '''
                    SELECT pattern, field, value, COUNT(*) as occurrences,
                           GROUP_CONCAT(DISTINCT mine_name) as mines,
                           MIN(detected_at) as first_seen,
                           MAX(detected_at) as last_seen,
                           severity
                    FROM template_patterns
                    WHERE detected_at >= ?
                    GROUP BY pattern, field, value
                    HAVING COUNT(*) >= ?
                    ORDER BY occurrences DESC, last_seen DESC
                '''

                cursor = conn.execute(query, (cutoff_date.isoformat(), min_occurrences))

                for row in cursor.fetchall():
                    pattern, field, value, occurrences, mines_str, first_seen_str, last_seen_str, severity = row

                    mines = mines_str.split(',') if mines_str else []
                    first_seen = datetime.fromisoformat(first_seen_str)
                    last_seen = datetime.fromisoformat(last_seen_str)

                    # Bestimme Schweregrad basierend auf Häufigkeit
                    if occurrences >= 50:
                        alert_severity = 'critical'
                    elif occurrences >= 20:
                        alert_severity = 'high'
                    elif occurrences >= 10:
                        alert_severity = 'medium'
                    else:
                        alert_severity = 'low'

                    alert = TemplateAlert(
                        pattern=f"{pattern}: '{value}'",
                        field=field,
                        occurrences=occurrences,
                        mines=mines[:20],  # Limitiere auf 20 Minen für Übersichtlichkeit
                        first_seen=first_seen,
                        last_seen=last_seen,
                        severity=alert_severity
                    )

                    alerts.append(alert)

        except Exception as e:
            logger.error(f"[TEMPLATE_MONITOR] Fehler bei Pattern-Analyse: {e}")

        self.alerts = alerts
        return alerts

    def check_for_rule10_violations(self) -> Dict[str, Any]:
        """
        Spezielle Prüfung auf REGEL 10 Verstöße

        Returns:
            Dictionary mit Analyseergebnissen
        """
        violations = {
            'duplicate_values': {},
            'fake_sources': [],
            'round_number_clusters': {},
            'template_phrases': [],
            'total_violations': 0
        }

        try:
            with sqlite3.connect(self.db_path) as conn:

                # 1. Prüfe auf identische Werte in kritischen Feldern
                critical_fields = ['Restaurationskosten', 'Fläche der Mine in qkm',
                                 'x-Koordinate', 'y-Koordinate']

                for field in critical_fields:
                    query = '''
                        SELECT value, COUNT(DISTINCT mine_name) as mine_count,
                               GROUP_CONCAT(DISTINCT mine_name) as mines
                        FROM template_patterns
                        WHERE field = ? AND pattern = 'duplicate_value'
                        GROUP BY value
                        HAVING COUNT(DISTINCT mine_name) >= 5
                        ORDER BY mine_count DESC
                    '''

                    cursor = conn.execute(query, (field,))
                    field_violations = [{
                            'value': value,
                            'mine_count': mine_count,
                            'mines': mines_str.split(',' for value, mine_count, mines_str in cursor.fetchall()][:10]  # Ersten 10 Minen zeigen
                        })

                    if field_violations:
                        violations['duplicate_values'][field] = field_violations
                        violations['total_violations'] += len(field_violations)

                # 2. Prüfe auf fake Quellen
                fake_source_query = '''
                    SELECT DISTINCT value, COUNT(*) as occurrences,
                           GROUP_CONCAT(DISTINCT mine_name) as mines
                    FROM template_patterns
                    WHERE pattern = 'fake_source'
                    GROUP BY value
                    ORDER BY occurrences DESC
                '''

                for value, occurrences, mines_str in conn.execute(fake_source_query).fetchall():
                    violations['fake_sources'].append({
                        'source': value,
                        'occurrences': occurrences,
                        'mines': mines_str.split(',')[:5]
                    })
                    violations['total_violations'] += 1

                # 3. Prüfe auf verdächtige Runde Zahlen
                round_number_query = '''
                    SELECT field, value, COUNT(*) as occurrences
                    FROM template_patterns
                    WHERE pattern = 'round_number'
                    GROUP BY field, value
                    HAVING COUNT(*) >= 3
                    ORDER BY occurrences DESC
                '''

                for field, value, occurrences in conn.execute(round_number_query).fetchall():
                    if field not in violations['round_number_clusters']:
                        violations['round_number_clusters'][field] = []

                    violations['round_number_clusters'][field].append({
                        'value': value,
                        'occurrences': occurrences
                    })
                    violations['total_violations'] += 1

        except Exception as e:
            logger.error(f"[TEMPLATE_MONITOR] Fehler bei REGEL 10 Prüfung: {e}")

        return violations

    def generate_report(self) -> str:
        """
        Generiere detaillierten Report über Template-Monitoring

        Returns:
            Formatierter Report als String
        """
        alerts = self.analyze_patterns()
        violations = self.check_for_rule10_violations()

        report_lines = [
            "═══════════════════════════════════════════════════════════════════════════════",
            "                     TEMPLATE MONITOR REPORT",
            f"                    {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            "═══════════════════════════════════════════════════════════════════════════════",
            "",
            f"📊 GESAMTSTATISTIK:",
            f"   • Template-Alerts: {len(alerts)}",
            f"   • REGEL 10 Verstöße: {violations['total_violations']}",
            ""
        ]

        # Kritische Alerts
        critical_alerts = [a for a in alerts if a.severity == 'critical']
        if critical_alerts:
            report_lines.extend([
                "🚨 KRITISCHE ALERTS:",
                "   (Sofortiger Handlungsbedarf!)",
                ""
            ])

            for alert in critical_alerts[:5]:  # Zeige nur die ersten 5
                report_lines.extend([
                    f"   ❌ {alert.pattern}",
                    f"      Feld: {alert.field}",
                    f"      Vorkommen: {alert.occurrences}",
                    f"      Minen: {', '.join(alert.mines[:3])}{'...' if len(alert.mines) > 3 else ''}",
                    ""
                ])

        # Duplicate Values
        if violations['duplicate_values']:
            report_lines.extend([
                "📋 IDENTISCHE WERTE (Verdacht auf AI-Templates):",
                ""
            ])

            for field, field_violations in violations['duplicate_values'].items():
                report_lines.append(f"   🔴 {field}:")
                for violation in field_violations[:3]:  # Ersten 3 zeigen
                    report_lines.append(f"      • '{violation['value']}' in {violation['mine_count']} Minen")
                    report_lines.append(f"        Beispiele: {', '.join(violation['mines'][:3])}")
                report_lines.append("")

        # Fake Sources
        if violations['fake_sources']:
            report_lines.extend([
                "🔍 VERDÄCHTIGE QUELLEN:",
                ""
            ])

            for source in violations['fake_sources'][:5]:  # Ersten 5 zeigen
                report_lines.extend([
                    f"   ⚠️  '{source['source']}'",
                    f"       Vorkommen: {source['occurrences']}",
                    f"       Minen: {', '.join(source['mines'])}",
                    ""
                ])

        # Round Numbers
        if violations['round_number_clusters']:
            report_lines.extend([
                "🔢 VERDÄCHTIGE RUNDE ZAHLEN:",
                ""
            ])

            for field, clusters in violations['round_number_clusters'].items():
                report_lines.append(f"   📊 {field}:")
                for cluster in clusters[:3]:  # Ersten 3 zeigen
                    report_lines.append(f"      • '{cluster['value']}': {cluster['occurrences']}x")
                report_lines.append("")

        # Empfehlungen
        report_lines.extend([
            "💡 EMPFEHLUNGEN:",
            ""
        ])

        if violations['total_violations'] > 10:
            report_lines.append("   🚨 KRITISCH: Massive Template-Kontamination erkannt!")
            report_lines.append("      → Sofortige Datenbankbereinigung erforderlich")
            report_lines.append("      → Provider-Prompts verschärfen")
            report_lines.append("      → Validierungsregeln erweitern")
        elif violations['total_violations'] > 0:
            report_lines.append("   ⚠️  Template-Muster erkannt - Überwachung intensivieren")
            report_lines.append("      → Betroffene Provider überprüfen")
            report_lines.append("      → Validierung für betroffene Felder verschärfen")
        else:
            report_lines.append("   ✅ Keine kritischen Template-Muster erkannt")
            report_lines.append("      → System arbeitet REGEL 10 konform")

        report_lines.extend([
            "",
            "═══════════════════════════════════════════════════════════════════════════════",
            "                          ENDE REPORT",
            "═══════════════════════════════════════════════════════════════════════════════"
        ])

        return "\n".join(report_lines)

    def save_alerts_to_db(self):
        """Speichere aktuelle Alerts in die Datenbank"""
        try:
            with sqlite3.connect(self.db_path) as conn:
                for alert in self.alerts:
                    conn.execute('''
                        INSERT OR REPLACE INTO pattern_alerts
                        (pattern, field, occurrences, mines, first_seen, last_seen, severity)
                        VALUES (?, ?, ?, ?, ?, ?, ?)
                    ''', (
                        alert.pattern,
                        alert.field,
                        alert.occurrences,
                        json.dumps(alert.mines),
                        alert.first_seen.isoformat(),
                        alert.last_seen.isoformat(),
                        alert.severity
                    ))

        except Exception as e:
            logger.error(f"[TEMPLATE_MONITOR] Fehler beim Speichern der Alerts: {e}")

# Globale Monitor-Instanz
template_monitor = TemplateMonitor()

def monitor_extraction_result(field: str, value: str, mine_name: str,
    """monitor_extraction_result - TODO: Dokumentation hinzufügen"""
                            sources: List[str] = None):
    """
    Überwache Extraktionsergebnis auf Template-Muster

    Diese Funktion wird von data_extraction.py aufgerufen um jeden extrahierten
    Wert zu überwachen.
    """
    if not value or not str(value).strip():
        return

    value_str = str(value).strip()
    value_lower = value_str.lower()

    # 1. Prüfe auf verdächtige Quellen
    if sources:
        for source in sources:
            source_lower = source.lower()
            if any(pattern in source_lower for pattern in [
                'fachwissen', 'expert knowledge', 'schätzung', 'estimated',
                'typical', 'üblich', 'based on similar', 'allgemeines'
            ]):
                template_monitor.record_pattern(
                    'fake_source', field, mine_name, value_str,
                    source_info=source, severity='high'
                )

    # 2. Prüfe auf runde Zahlen (verdächtig bei Kosten/Flächen)
    if field in ['Restaurationskosten', 'Fläche der Mine in qkm']:
        # Pattern für runde Zahlen wie "50.0", "100.0", etc.
        if re.match(r'^\d{1,3}\.0+\s*(million|mio|millionen)?\s*(USD|CAD|EUR)?$', value_lower):
            template_monitor.record_pattern(
                'round_number', field, mine_name, value_str, severity='medium'
            )

    # 3. Prüfe auf Template-Phrasen
    template_phrases = [
        'gold/ kupfer/ kohle/ usw', 'untertage/ open-pit/ usw',
        'aktiv/ inaktiv/ sonstiges', 'typical for', 'generally ranges'
    ]

    if any(phrase in value_lower for phrase in template_phrases):
        template_monitor.record_pattern(
            'template_phrase', field, mine_name, value_str, severity='high'
        )

    # 4. Prüfe auf Duplikate (wird über separate Datenbankanalyse gemacht)
    # Hier nur die Erfassung für spätere Analyse
    template_monitor.record_pattern(
        'duplicate_value', field, mine_name, value_str, severity='low'
    )
