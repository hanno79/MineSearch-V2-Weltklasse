"""
Author: rahn
Datum: 09.07.2025
Version: 1.0
Beschreibung: Analyse von doppelten Quellen in der Datenbank
"""

import sqlite3
from collections import Counter

# Verbindung zur Datenbank
conn = sqlite3.connect('/app/minesearch_v2/backend/mines.db')
cursor = conn.cursor()

print("=== ANALYSE DER QUELLEN-DUPLIKATE ===\n")

# 1. Gesamtanzahl der Quellen
cursor.execute("SELECT COUNT(*) FROM sources")
total_sources = cursor.fetchone()[0]
print(f"Gesamtanzahl Quellen: {total_sources}")

# 2. Eindeutige URLs
cursor.execute("SELECT COUNT(DISTINCT url) FROM sources")
unique_urls = cursor.fetchone()[0]
print(f"Eindeutige URLs: {unique_urls}")
print(f"Duplikate: {total_sources - unique_urls}\n")

# 3. Top 10 doppelte URLs
print("Top 10 doppelte URLs:")
cursor.execute("""
    SELECT url, COUNT(*) as count 
    FROM sources 
    GROUP BY url 
    HAVING count > 1 
    ORDER BY count DESC 
    LIMIT 10
""")
duplicates = cursor.fetchall()
for url, count in duplicates:
    print(f"  {count}x: {url}")

# 4. Detaillierte Analyse der Duplikate
print("\n=== DETAILANALYSE DER DUPLIKATE ===")
cursor.execute("""
    SELECT id, url, name, country, region, source_type, reliability_score
    FROM sources
    WHERE url IN (
        SELECT url FROM sources GROUP BY url HAVING COUNT(*) > 1
    )
    ORDER BY url, id
    LIMIT 20
""")
duplicate_details = cursor.fetchall()

current_url = None
for row in duplicate_details:
    if current_url != row[1]:
        current_url = row[1]
        print(f"\nURL: {current_url}")
    print(f"  ID: {row[0]}, Name: {row[2]}, Country: {row[3]}, Region: {row[4]}, Type: {row[5]}, Score: {row[6]}")

# 5. Prüfe ob es unterschiedliche Daten bei gleicher URL gibt
print("\n=== UNTERSCHIEDE BEI GLEICHER URL ===")
cursor.execute("""
    SELECT url, 
           COUNT(DISTINCT name) as name_variants,
           COUNT(DISTINCT country) as country_variants,
           COUNT(DISTINCT region) as region_variants,
           COUNT(DISTINCT source_type) as type_variants
    FROM sources
    GROUP BY url
    HAVING COUNT(*) > 1 AND (
        name_variants > 1 OR 
        country_variants > 1 OR 
        region_variants > 1 OR 
        type_variants > 1
    )
    LIMIT 10
""")
variations = cursor.fetchall()
for row in variations:
    print(f"URL: {row[0]}")
    print(f"  Verschiedene Namen: {row[1]}")
    print(f"  Verschiedene Länder: {row[2]}")
    print(f"  Verschiedene Regionen: {row[3]}")
    print(f"  Verschiedene Typen: {row[4]}")

conn.close()