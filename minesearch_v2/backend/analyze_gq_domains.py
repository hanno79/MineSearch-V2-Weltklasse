"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Detaillierte Analyse der gq.mines.gouv.qc.ca Quellen
"""

import sqlite3
from urllib.parse import urlparse
from collections import Counter, defaultdict

# Verbindung zur Datenbank
conn = sqlite3.connect('mines.db')
cursor = conn.cursor()

print("=== DETAILLIERTE ANALYSE DER gq.mines.gouv.qc.ca QUELLEN ===\n")

# Hole alle gq.mines.gouv.qc.ca URLs
cursor.execute("""
    SELECT id, url, country, region, source_type, reliability_score
    FROM sources 
    WHERE domain = 'gq.mines.gouv.qc.ca'
    ORDER BY url
""")

sources = cursor.fetchall()
print(f"Gefundene gq.mines.gouv.qc.ca Quellen: {len(sources)}\n")

# Analysiere URL-Struktur
url_patterns = defaultdict(list)
path_segments = defaultdict(int)

for source in sources:
    url = source[1]
    parsed = urlparse(url)
    path = parsed.path
    
    # Extrahiere Hauptkategorie (erster Pfad-Teil)
    path_parts = path.strip('/').split('/')
    if path_parts:
        main_category = path_parts[0]
        url_patterns[main_category].append(url)
        
    # Zähle Pfad-Segmente
    segment_count = len(path_parts)
    path_segments[segment_count] += 1

print("=== URL-KATEGORIEN ===")
for category, urls in sorted(url_patterns.items(), key=lambda x: -len(x[1])):
    print(f"\n{category}: {len(urls)} URLs")
    # Zeige erste 3 Beispiele
    for i, url in enumerate(urls[:3]):
        print(f"  - {url}")
    if len(urls) > 3:
        print(f"  ... und {len(urls) - 3} weitere")

print("\n\n=== PFAD-TIEFE ANALYSE ===")
for depth, count in sorted(path_segments.items()):
    print(f"URLs mit {depth} Pfad-Segmenten: {count}")

# Prüfe auf sehr ähnliche URLs
print("\n\n=== ÄHNLICHKEITS-ANALYSE ===")

# Gruppiere nach Basis-URL (ohne Dateiname)
base_urls = defaultdict(list)
for source in sources:
    url = source[1]
    if url.endswith('.pdf') or url.endswith('.html'):
        base = '/'.join(url.split('/')[:-1])
        base_urls[base].append(url)

# Zeige Gruppen mit mehreren ähnlichen URLs
similar_groups = 0
for base, urls in base_urls.items():
    if len(urls) > 1:
        similar_groups += 1
        if similar_groups <= 5:  # Zeige nur erste 5 Gruppen
            print(f"\nGruppe {similar_groups}: {base}/")
            for url in urls:
                filename = url.split('/')[-1]
                print(f"  - {filename}")

if similar_groups > 5:
    print(f"\n... und {similar_groups - 5} weitere Gruppen mit ähnlichen URLs")

# Dateiendungen analysieren
print("\n\n=== DATEIENDUNGEN ===")
extensions = Counter()
for source in sources:
    url = source[1]
    if '.' in url.split('/')[-1]:
        ext = url.split('.')[-1].lower()
        extensions[ext] += 1

for ext, count in extensions.most_common():
    print(f"{ext}: {count} Dateien")

# Empfehlungen
print("\n\n=== EMPFEHLUNGEN ===")
print(f"1. Die Domain gq.mines.gouv.qc.ca hat {len(sources)} verschiedene URLs")
print(f"2. Hauptkategorien: {', '.join(list(url_patterns.keys())[:5])}")
print(f"3. {similar_groups} Gruppen von ähnlichen URLs gefunden")
print("\nVorschläge:")
print("- Frontend sollte vollständige URL oder zumindest Pfad anzeigen")
print("- Gruppierung nach Kategorie könnte Übersicht verbessern")
print("- Eventuell Filter für Dateitypen hinzufügen")

conn.close()