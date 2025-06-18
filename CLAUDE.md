PROJEKTREGELN
========================================

Author: rahn
Datum: 15.06.2025
Version: 1.4

========================================
ÜBERSICHT
========================================

Diese Regeln definieren die Standards für die Entwicklung und Wartung 
der GINES Test Automation Codebasis. Alle Teammitglieder und KI-Assistenten 
müssen sich strikt an diese Regeln halten.

========================================
REGEL 1: DATEI-GRÖSSENBESCHRÄNKUNG
========================================

Skriptdateien dürfen MAXIMAL 500 Zeilen Code enthalten.

VORGEHEN:
- Vor jeder neuen Funktionalität prüfen: Bleibt die Datei unter 500 Zeilen?
- Bei Überschreitung: Sofortiges Refactoring erforderlich
- Code in logische Module/Dateien aufteilen
- Gemeinsame Funktionen in separate Utility-Dateien auslagern
- Vor der Umsetzung selbst darauf achten ob ein Refactoring notwendig ist

ZWECK: Wartbarkeit und Lesbarkeit des Codes sicherstellen

========================================
REGEL 2: KEINE DUPLIKATDATEIEN BEI FIXES
========================================

Bei Fehlerbehebungen NIEMALS neue Dateien mit Endungen erstellen wie:
- *_fixed
- *_korrigiert  
- *_new
- *_updated

VORGEHEN:
- Defekte Dateien direkt editieren
- Bestehende Datei überschreiben
- Änderungen mit Kommentaren dokumentieren
- Zu einem Thema nur jeweils eine konkrete Datei erstellen

ZWECK: Vermeidung einer unübersichtlichen Codebasis

========================================
REGEL 3: VERSIONIERUNG NACH BEDARF
========================================

Neue Versionen NUR erstellen wenn:
- Eine funktionierende Version als Backup benötigt wird
- Grundlegende Architekturänderungen anstehen
- Experimentelle Features entwickelt werden
- Tatsächlich eine neue Datei erstellt werden muss

NAMENSKONVENTION:
- Ausschließlich Versionsnummern verwenden: *_v1, *_v2, *_v3
- VERBOTEN: *_final, *_korrigiert, *_latest, *_backup

VORGEHEN:
- Sparsam verwenden - nur bei echter Notwendigkeit
- Bei Minor-Fixes: Direkte Bearbeitung ohne neue Version
- Bei Korrekturen direkt die entsprechende Datei korrigieren ohne neue zu erstellen

========================================
REGEL 4: KOMMUNIKATIONSSPRACHE
========================================

Standardsprache: DEUTSCH

Ausnahmen nur bei expliziter anderslautender Anweisung.
Code-Kommentare, Dokumentation und Kommunikation auf Deutsch.

========================================
REGEL 5: CHAT-ZUSAMMENFASSUNGEN
========================================

Bei Anfrage nach Zusammenfassung:

ANFORDERUNGEN:
- Ausführlich und vollständig
- Chronologisch strukturiert
- Alle wichtigen Entscheidungen dokumentieren
- Aktuelle Problemstellungen erwähnen
- Nächste Schritte definieren
- Sorgfältig und konzentriert arbeiten

SPEICHERORT: 
- Immer in: C:\xampp\htdocs\gines-test-automation\documentation\
- Dateiname: chat_summary_[DATUM].txt

ZWECK: Nahtlose Fortsetzung in neuen Chat-Sessions

========================================
REGEL 6: DATEI-ORGANISATION
========================================

ORDNERSTRUKTUR BEACHTEN:

/frontend/          → Frontend-Tests, UI-Automatisierung
/backend/           → Backend-Tests, API-Tests
/documentation/     → Dokumentation, Zusammenfassungen, Regeln
/to_delete/         → Veraltete/obsolete Dateien
/tests/             → Test-Dateien für alle Module
/config/            → Konfigurationsdateien

VORGEHEN:
- Vor Dateierstellung: Verzeichnisstruktur prüfen
- Logische Zuordnung zu entsprechendem Ordner
- Bei Unsicherheit: Dokumentation in /documentation/
- Immer darauf achten, Dateien am richtigen Ort zu speichern

========================================
REGEL 7: CODEBASIS-BEREINIGUNG
========================================

Bei expliziter Bereinigungsanfrage:

VORGEHEN:
1. Gesamte Codebasis analysieren
2. Veraltete/überflüssige Dateien identifizieren
3. Obsolete Versionen finden
4. Dateien nach /to_delete/ verschieben (NICHT löschen)

KRITERIEN FÜR VERSCHIEBUNG:
- Ältere Versionen bei funktionierender neuer Version
- Test-Dateien ohne aktuellen Bezug
- Backup-Dateien älter als 30 Tage
- Dateien mit veralteten Endungen (*_old, *_backup, etc.)

========================================
REGEL 8: AUTOR-KENNZEICHNUNG
========================================

In JEDER Skriptdatei mandatory:

HEADER-FORMAT:
"""
Author: rahn
Datum: [TT.MM.YYYY]
Version: [X.X]
Beschreibung: [Kurze Funktionsbeschreibung]
"""

ZWECK: Nachvollziehbarkeit und Verantwortlichkeit

========================================
REGEL 9: ÄNDERUNGSDOKUMENTATION
========================================

JEDE Änderung dokumentieren mit:

FORMAT:
# ÄNDERUNG [TT.MM.YYYY]: [Begründung]
# [Beschreibung der Änderung]

BEISPIEL:
# ÄNDERUNG 11.06.2025: Bugfix für Login-Timeout
# Timeout von 5s auf 10s erhöht wegen langsamer Serverantwort

SPEICHERORT: 
- Im Code als Kommentar
- Bei größeren Änderungen zusätzlich in CHANGELOG.txt

========================================
REGEL 10: KEINE DUMMY- UND FALLBACK-WERTE
========================================

STRIKT VERBOTEN:
- Hardcodierte Dummy-Werte ohne Kennzeichnung
- Versteckte Fallback-Werte bei Fehlern
- Ausgedachte Testwerte die echte Daten vortäuschen
- "Irgendein Wert" bei Problemen oder Fehlern

FALLS ABSOLUT NOTWENDIG:
- Dummy-Werte: Eindeutig kennzeichnen mit Kommentaren
  // DUMMY-WERT: Nur für Tests - NICHT produktiv verwenden!
  const testUser = "DUMMY_USER_FOR_TESTING_ONLY";

- Fallback-Werte: Explizit ausweisen und loggen
  // FALLBACK: Verwendet wenn API nicht erreichbar
  const fallbackValue = "FALLBACK_API_UNAVAILABLE";
  console.log("WARNUNG: Fallback-Wert verwendet - API Problem!");

KENNZEICHNUNG:
- Frontend: Deutlich sichtbare Markierung in UI
- Backend: Logging mit WARNUNG/ERROR Level
- Beide: Kommentare im Code mit "DUMMY" oder "FALLBACK"

VERMEIDUNG:
- Proper Error Handling statt Fallbacks
- Validierung statt Dummy-Werte
- Explizite Fehlermeldungen statt versteckte Ersatzwerte
- Fail-Fast Prinzip: Bei Problemen sofort stoppen

ZWECK: Transparenz und Nachvollziehbarkeit aller Datenwerte

========================================
REGEL 11: MCP SERVER NUTZUNG
========================================

Model Context Protocol (MCP) Server sollen aktiv genutzt werden:

VORGEHEN:
- Bei Fragen oder Aufgaben: Verfügbare MCP Server prüfen
- Eigenständige Entscheidung welcher Server sinnvoll hilft
- MCP Tools bevorzugt nutzen wenn verfügbar und passend
- Effizienz durch spezialisierte Tools steigern

EINSATZBEREICHE:
- File-Management und Code-Organisation
- Dokumentation und Analyse
- Spezifische Entwicklungsaufgaben
- Automatisierung von Routineaufgaben

ZWECK: Maximale Effizienz durch spezialisierte Tools

========================================
REGEL 12: GITHUB VERSIONIERUNG
========================================

PROJEKTSTART:
- Bei jedem neuen Projekt: GitHub Repository anlegen
- Saubere Grundstruktur etablieren
- Ordnerstruktur entsprechend Regel 6 einrichten

BRANCH-MANAGEMENT:
- Neue Funktionen/Änderungen: Neuen Branch erstellen
- Branch-Naming: v0.1, v0.2, v0.3, etc. (fortlaufend)
- Master/Main Branch: Nur stabile, getestete Versionen

COMMIT-REGELN:
- NUR bei funktionierenden Änderungen committen
- NUR auf explizite Anweisung hin committen
- NIEMALS automatisch committen
- Vor Commit immer nachfragen: "Soll ich die aktuelle Version auf GitHub committen?"

COMMIT-NACHRICHTEN:
- Deutsch verfasst
- Beschreibend und konkret
- Format: "[Version] - [Kurze Beschreibung der Änderung]"

ZWECK: Professionelle Versionskontrolle und Nachvollziehbarkeit

========================================
REGEL 13: CODE-QUALITÄTSSTANDARDS
========================================

NAMING CONVENTIONS:
- Variablen: aussagekräftige deutsche Namen (userLoginData, testErgebnis)
- Funktionen: Verben verwenden (pruefeLogin, sendeFormular)
- Konstanten: GROSSBUCHSTABEN (MAX_RETRY_COUNT, DEFAULT_TIMEOUT)
- Dateien: lowercase mit underscores (login_test.py, user_utils.js)

ERROR HANDLING:
- Jede Funktion mit try-catch ausstatten
- Aussagekräftige Fehlermeldungen auf Deutsch
- Logging bei kritischen Fehlern mandatory
- Graceful Degradation bei nicht-kritischen Fehlern

CODE-KOMMENTARE:
- Komplexe Logik immer kommentieren
- Deutsch verfasste Kommentare
- Zweck der Funktion am Anfang erklären
- TODO-Kommentare mit Datum versehen

ZWECK: Einheitliche und wartbare Codequalität

========================================
REGEL 14: TESTING-STANDARDS
========================================

TEST-STRUKTUR:
- Für jede Hauptfunktion: Mindestens einen Test
- Test-Dateien: *_test.py / *_test.js
- Test-Ordner: /tests/ unterhalb der jeweiligen Module
- Test-Coverage: Mindestens 70% anstreben

ASSERT-NACHRICHTEN:
- Immer deutsche Fehlermeldungen bei fehlgeschlagenen Tests
- Format: "Erwartet: X, Erhalten: Y bei Funktion Z"
- Aussagekräftige Test-Namen auf Deutsch

TEST-KATEGORIEN:
- Unit Tests: Einzelne Funktionen
- Integration Tests: Zusammenspiel von Komponenten
- End-to-End Tests: Komplette User-Journeys

ZWECK: Zuverlässige und getestete Software

========================================
REGEL 15: KONFIGURATION & UMGEBUNG
========================================

CONFIG-MANAGEMENT:
- Alle Umgebungsvariablen in .env Dateien
- Niemals Passwörter oder API-Keys im Code
- config.py/config.js für zentrale Konfiguration
- Separate Config-Dateien für verschiedene Umgebungen

UMGEBUNGEN:
- Separate Configs für dev/test/prod
- Environment-spezifische Branches wenn nötig
- Klare Trennung zwischen lokaler und produktiver Konfiguration

SICHERHEIT:
- .env Dateien immer in .gitignore
- API-Keys über Umgebungsvariablen
- Sensible Daten niemals committen

ZWECK: Sichere und flexible Konfigurationsverwaltung

========================================
REGEL 16: PERFORMANCE & MONITORING
========================================

PERFORMANCE:
- Funktionen über 5 Sekunden Laufzeit dokumentieren
- Bei Schleifen: Performance-Comments hinzufügen
- Speicher-intensive Operationen kennzeichnen
- Timeouts für alle externen Aufrufe definieren

LOGGING:
- Log-Level: INFO für wichtige Aktionen, DEBUG für Details
- Log-Format: [TIMESTAMP] [LEVEL] [FUNKTION] - Nachricht
- Log-Rotation bei größeren Anwendungen
- Deutschsprachige Log-Nachrichten

MONITORING:
- Kritische Funktionen mit Monitoring ausstatten
- Metriken für wichtige Business-Prozesse
- Alerting bei Fehlern oder Performance-Problemen

ZWECK: Performante und überwachbare Anwendungen

========================================
REGEL 17: DEPENDENCY MANAGEMENT
========================================

BIBLIOTHEKEN:
- requirements.txt / package.json aktuell halten
- Nur notwendige Dependencies installieren
- Versionsnummern fixieren für Stabilität
- Regelmäßige Security-Updates prüfen

LIZENZ-COMPLIANCE:
- Lizenz aller verwendeten Bibliotheken prüfen
- Kompatibilität mit Projektlizenz sicherstellen
- Dokumentation der verwendeten Third-Party-Komponenten

UPDATE-STRATEGIE:
- Monatliche Überprüfung auf Updates
- Testlauf vor Update in Produktionsumgebung
- Breaking Changes dokumentieren

ZWECK: Stabile und rechtskonforme Dependency-Verwaltung

========================================
REGEL 18: STANDARD-WORKFLOW (CLAUDE.MD-REGELN)
========================================

OBLIGATORISCHER ARBEITSABLAUF:

1. PROBLEMANALYSE:
   - Problem durchdenken
   - Relevante Dateien im Code suchen
   - MCP Server auf Nützlichkeit prüfen
   - Plan in projectplan.md schreiben

2. AUFGABENPLANUNG:
   - Liste mit konkreten Aufgaben erstellen
   - Aufgaben nach Erledigung abhakbar machen
   - Plan vor Arbeitsbeginn zur Überprüfung melden

3. UMSETZUNG:
   - Aufgaben nacheinander bearbeiten
   - Jede Aufgabe nach Erledigung als erledigt markieren
   - Bei jedem Schritt detailliert erläutern welche Änderungen vorgenommen wurden

4. EINFACHHEITSPRINZIP:
   - Alle Aufgaben und Codeänderungen so einfach wie möglich gestalten
   - Massive oder komplexe Änderungen vermeiden
   - Jede Änderung soll minimale Auswirkungen auf den Code haben
   - EINFACHHEIT IST ALLES

5. ABSCHLUSS:
   - Überprüfungsbereich in projectplan.md einfügen
   - Zusammenfassung der vorgenommenen Änderungen
   - Alle relevanten Informationen dokumentieren
   - Bei funktionierenden Änderungen: GitHub Commit anbieten

ZWECK: Strukturierte und nachvollziehbare Projektarbeit

========================================
COMPLIANCE-HINWEIS
========================================

Diese Regeln sind VERBINDLICH für alle Projektbeteiligten.
Bei Regelverstößen ist sofortige Korrektur erforderlich.

Anwendungsbereich: 
- Claude AI-Assistant Projekte
- Andere Programmierumgebungen
- Allgemeine Softwareentwicklungsprojekte

Letzte Aktualisierung: 15.06.2025
Nächste Review: Nach Projektabschluss Phase 1