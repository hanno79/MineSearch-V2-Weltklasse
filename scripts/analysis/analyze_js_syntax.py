#!/usr/bin/env python3
"""
Author: rahn
Datum: 28.07.2025
Version: 1.0
Beschreibung: JavaScript Error Analyzer für Details-Button Syntax-Probleme
"""

import re
import json
from pathlib import Path

def analyze_javascript_syntax_errors(html_file):
    """Analysiere JavaScript-Syntax-Fehler in HTML-Datei"""

    print("🔍 JavaScript Syntax Error Analysis")
    print("=" * 50)

    try:
        with open(html_file, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Fehler beim Lesen der Datei: {e}")
        return {}

    issues = []
    line_number = 0

    # Suche nach problematischen Mustern
    lines = content.split('\n')

    for i, line in enumerate(lines, 1):
        line_number = i

        # Pattern 1: showModelDetails mit ungeschlossener Klammer
        pattern1 = r'showModelDetails\([^)]*$'
        if re.search(pattern1, line) and 'safeJSONStringify' in line:
            issues.append({
                'line': line_number,
                'type': 'MISSING_CLOSING_PARENTHESIS',
                'pattern': pattern1,
                'content': line.strip(),
                'severity': 'CRITICAL',
                'error_message': 'Unexpected end of input - missing closing parenthesis'
            })

        # Pattern 2: onclick Handler mit Syntax-Fehlern
        pattern2 = r'onclick=["\'][^"\']*showModelDetails\([^"\']*[^)]["\']'
        matches2 = re.findall(pattern2, line)
        for match in matches2:
            issues.append({
                'line': line_number,
                'type': 'ONCLICK_SYNTAX_ERROR',
                'pattern': pattern2,
                'content': line.strip(),
                'match': match,
                'severity': 'HIGH',
                'error_message': 'Malformed onclick handler'
            })

        # Pattern 3: Template String mit ungeschlossenen Funktionsaufrufen
        pattern3 = r'\${[^}]*showModelDetails\([^}]*[^)]\}'
        matches3 = re.findall(pattern3, line)
        for match in matches3:
            issues.append({
                'line': line_number,
                'type': 'TEMPLATE_STRING_ERROR',
                'pattern': pattern3,
                'content': line.strip(),
                'match': match,
                'severity': 'HIGH',
                'error_message': 'Unclosed function call in template string'
            })

        # Pattern 4: safeJSONStringify ohne schließende Klammer
        pattern4 = r'safeJSONStringify\([^)]*$'
        if re.search(pattern4, line) and 'showModelDetails' in line:
            issues.append({
                'line': line_number,
                'type': 'SAFEJSONSTRINGIFY_UNCLOSED',
                'pattern': pattern4,
                'content': line.strip(),
                'severity': 'CRITICAL',
                'error_message': 'safeJSONStringify call not properly closed'
            })

    # Suche nach globalen Mustern (mehrzeilig)
    multiline_patterns = [
        (r'showModelDetails\([^\)]*\n[^\)]*[^\)]$', 'MULTILINE_UNCLOSED_CALL'),
        (r'onclick="[^"]*showModelDetails\([^"]*\n[^"]*[^)][^"]*"', 'MULTILINE_ONCLICK_ERROR')
    ]

    for pattern, error_type in multiline_patterns:
        matches = re.findall(pattern, content, re.MULTILINE | re.DOTALL)
        for match in matches:
            # Finde die Zeilennummer für mehrzeilige Matches
            match_line = content[:content.find(match)].count('\n') + 1
            issues.append({
                'line': match_line,
                'type': error_type,
                'pattern': pattern,
                'content': match[:100] + '...' if len(match) > 100 else match,
                'severity': 'HIGH',
                'error_message': 'Multiline syntax error detected'
            })

    # Analysiere spezifische showModelDetails-Aufrufe
    showmodel_calls = re.findall(r'showModelDetails\([^)]*\)', content)
    onclick_calls = re.findall(r'onclick=["\'][^"\']*showModelDetails[^"\']*["\']', content)

    analysis_result = {
        'file': str(html_file),
        'total_issues': len(issues),
        'critical_issues': len([i for i in issues if i['severity'] == 'CRITICAL']),
        'high_issues': len([i for i in issues if i['severity'] == 'HIGH']),
        'issues': issues,
        'showmodel_calls_found': len(showmodel_calls),
        'onclick_calls_found': len(onclick_calls),
        'sample_calls': showmodel_calls[:5],  # Ersten 5 Aufrufe als Sample
        'sample_onclick': onclick_calls[:5]   # Ersten 5 onclick Handler als Sample
    }

    # Ausgabe der Ergebnisse
    print(f"📁 Datei: {html_file}")
    print(f"🚨 Gefundene Issues: {len(issues)}")
    print(f"   - CRITICAL: {analysis_result['critical_issues']}")
    print(f"   - HIGH: {analysis_result['high_issues']}")
    print(f"📊 showModelDetails Aufrufe: {analysis_result['showmodel_calls_found']}")
    print(f"🖱️  onclick Handler: {analysis_result['onclick_calls_found']}")

    if issues:
        print("\n🔍 GEFUNDENE PROBLEME:")
        for issue in issues:
            print(f"   Zeile {issue['line']}: {issue['type']} ({issue['severity']})")
            print(f"      Error: {issue['error_message']}")
            print(f"      Code: {issue['content'][:80]}...")
            print()

    return analysis_result

def main():
    """Hauptfunktion für die Analyse"""

    html_file = Path('/app/minesearch_v2/frontend/index.html')

    if not html_file.exists():
        print(f"❌ HTML-Datei nicht gefunden: {html_file}")
        return

    # Analysiere die Hauptdatei
    result = analyze_javascript_syntax_errors(html_file)

    # Speichere Ergebnisse
    output_file = Path('/app/JAVASCRIPT_SYNTAX_ANALYSIS_REPORT.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(result, f, indent=2, ensure_ascii=False)

    print(f"💾 Analysebericht gespeichert: {output_file}")

    # Zusammenfassung
    print("\n" + "=" * 50)
    print("📋 ZUSAMMENFASSUNG")
    print("=" * 50)

    if result['total_issues'] == 0:
        print("✅ Keine kritischen JavaScript-Syntax-Fehler gefunden!")
    else:
        print(f"⚠️  {result['total_issues']} potentielle Syntax-Probleme identifiziert")
        print(f"   - {result['critical_issues']} CRITICAL (führen zu Runtime-Fehlern)")
        print(f"   - {result['high_issues']} HIGH (potentielle Probleme)")

        print("\n🛠️  NÄCHSTE SCHRITTE:")
        if result['critical_issues'] > 0:
            print("   1. CRITICAL Issues sofort beheben")
            print("   2. Browser-Konsole auf 'Unexpected end of input' prüfen")
            print("   3. Details-Buttons testen")

        print("   4. HTML-Validierung durchführen")
        print("   5. JavaScript-Linting aktivieren")

if __name__ == "__main__":
    main()
