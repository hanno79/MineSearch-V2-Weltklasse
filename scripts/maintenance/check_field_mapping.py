"""
Author: rahn
Datum: 11.09.2025
Version: 1.0
Beschreibung: Funktionalität für check field mapping
"""

import requests
import json

try:
    response =
requests.get("http://localhost:8000/api/consolidated/results?exclude_exa=true&days_back=30&sort_by=mine_name&order=asc")
    data = response.json()

    if data['success'] and data['data']['consolidated_results']:
        print('=== ANDERE MINEN ÜBERPRÜFUNG ===')
        for i, mine in enumerate(data['data']['consolidated_results']):
            if i >= 3:  # Nur erste 3 Minen
                break
            print(f'\nMine {i+1}: {mine["mine_name"]}')

            # Prüfe auf verdächtige Feldwerte
            suspicious_fields = []
            best_values = mine.get("best_values", {})

            for field, value in best_values.items():
                # Prüfe ob Feldwerte andere Feldnamen enthalten
                field_names = ['Betreiber', 'Eigentümer', 'x-Koordinate', 'y-Koordinate', 'Region',
'Restaurationskosten']
                for fname in field_names:
                    if str(value) == fname and field != fname:
                        suspicious_fields.append(f'{field} = "{value}" (sollte {fname} sein)')

            if suspicious_fields:
                print('  ⚠️  FELDMAPPING-PROBLEME:')
                for s in suspicious_fields[:3]:  # Nur erste 3
                    print(f'    {s}')
            else:
                print('  ✅ Keine offensichtlichen Feldmapping-Probleme')

        # Zeige auch hohe Confidence-Werte
        print(f'\n=== HOHE CONFIDENCE-WERTE ANALYSE ===')
        high_confidence_examples = []

        for mine in data['data']['consolidated_results'][:5]:
            detailed = mine.get("detailed_breakdown", {})
            for field_name, field_data in detailed.items():
                confidence = field_data.get("best_value", {}).get('confidence_score', 0)
                display_value = field_data.get("best_value", {}).get('display_value', '')

                if confidence >= 90 and display_value != mine['mine_name']:  # Nicht Mine-Name
                    high_confidence_examples.append(f'{mine["mine_name"][:20]}... -> {field_name}:
{confidence}% ("{display_value}")')

        print(f'Gefundene hohe Confidence-Werte: {len(high_confidence_examples)}')
        for example in high_confidence_examples[:10]:  # Erste 10
            print(f'  {example}')

    else:
        print('No data or API error')
        print(data)

except Exception as e:
    print(f'Error: {e}')
    import traceback
    traceback.print_exc()
