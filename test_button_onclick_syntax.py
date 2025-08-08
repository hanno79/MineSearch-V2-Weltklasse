#!/usr/bin/env python3
"""
Author: rahn
Datum: 28.07.2025
Version: 1.0
Beschreibung: Button OnClick Syntax Validator für Details-Buttons
"""

import re
import json
from pathlib import Path

def test_onclick_syntax(html_content):
    """Teste alle onclick-Handler auf Syntax-Korrektheit"""
    
    print("🔍 Testing OnClick Handler Syntax")
    print("=" * 50)
    
    results = {
        'tested_handlers': [],
        'syntax_errors': [],
        'warnings': [],
        'valid_handlers': []
    }
    
    # Finde alle onclick-Handler
    onclick_pattern = r'onclick=["\']([^"\']*)["\']'
    onclick_matches = re.findall(onclick_pattern, html_content)
    
    print(f"📊 Found {len(onclick_matches)} onclick handlers")
    
    for i, onclick_code in enumerate(onclick_matches):
        handler_info = {
            'index': i + 1,
            'code': onclick_code,
            'valid': True,
            'issues': []
        }
        
        # Test 1: Ungeschlossene Klammern
        open_parens = onclick_code.count('(')
        close_parens = onclick_code.count(')')
        
        if open_parens != close_parens:
            handler_info['valid'] = False
            handler_info['issues'].append(f"Unmatched parentheses: {open_parens} open, {close_parens} close")
            results['syntax_errors'].append(handler_info.copy())
        
        # Test 2: showModelDetails-spezifische Tests
        if 'showModelDetails' in onclick_code:
            # Teste ob showModelDetails korrekt aufgerufen wird
            showmodel_pattern = r'showModelDetails\([^)]*\)'
            showmodel_matches = re.findall(showmodel_pattern, onclick_code)
            
            if not showmodel_matches and 'showModelDetails(' in onclick_code:
                handler_info['valid'] = False
                handler_info['issues'].append("showModelDetails call appears incomplete")
                results['syntax_errors'].append(handler_info.copy())
            
            # Teste Parameter-Escaping
            if '${' in onclick_code and '}' not in onclick_code:
                handler_info['valid'] = False
                handler_info['issues'].append("Template string syntax error - unclosed ${}")
                results['syntax_errors'].append(handler_info.copy())
        
        # Test 3: JavaScript-Syntax-Simulation (vereinfacht)
        try:
            # Simuliere JavaScript-Parsing durch Python eval (sehr vereinfacht)
            # Dies ist nur ein grobes Test-Werkzeug
            if onclick_code.strip():
                # Ersetze JavaScript-spezifische Elemente für den Test
                test_code = onclick_code.replace('${', '').replace('}', '').replace('`', '"')
                
                # Suche nach offensichtlichen Syntax-Fehlern
                if test_code.count('"') % 2 != 0:
                    handler_info['issues'].append("Unmatched quotes detected")
                    results['warnings'].append(handler_info.copy())
                
                if test_code.count("'") % 2 != 0:
                    handler_info['issues'].append("Unmatched single quotes detected")
                    results['warnings'].append(handler_info.copy())
        
        except Exception as e:
            handler_info['issues'].append(f"Syntax validation error: {str(e)}")
            results['warnings'].append(handler_info.copy())
        
        if handler_info['valid'] and not handler_info['issues']:
            results['valid_handlers'].append(handler_info)
        
        results['tested_handlers'].append(handler_info)
    
    return results

def find_model_detail_buttons(html_content):
    """Finde alle Model-Detail-Buttons und analysiere sie"""
    
    print("\n🔍 Analyzing Model Detail Buttons")
    print("=" * 50)
    
    # Suche nach verschiedenen Button-Patterns
    patterns = [
        r'<button[^>]*onclick[^>]*showModelDetails[^>]*>',
        r'<button[^>]*data-model-id[^>]*>',
        r'<.*onclick[^>]*showModelDetails[^>]*>'
    ]
    
    button_analysis = {
        'total_model_buttons': 0,
        'buttons_with_issues': [],
        'buttons_valid': []
    }
    
    for pattern in patterns:
        matches = re.findall(pattern, html_content, re.IGNORECASE | re.DOTALL)
        button_analysis['total_model_buttons'] += len(matches)
        
        for match in matches:
            # Analysiere jeden Button
            button_info = {
                'html': match[:200] + '...' if len(match) > 200 else match,
                'has_onclick': 'onclick' in match.lower(),
                'has_data_model_id': 'data-model-id' in match.lower(),
                'has_showmodeldetails': 'showmodeldetails' in match.lower()
            }
            
            # Extrahiere onclick-Code
            onclick_match = re.search(r'onclick=["\']([^"\']*)["\']', match, re.IGNORECASE)
            if onclick_match:
                onclick_code = onclick_match.group(1)
                button_info['onclick_code'] = onclick_code
                
                # Teste Syntax
                if onclick_code.count('(') != onclick_code.count(')'):
                    button_info['syntax_issue'] = 'Unmatched parentheses'
                    button_analysis['buttons_with_issues'].append(button_info)
                else:
                    button_analysis['buttons_valid'].append(button_info)
            
            print(f"📊 Button: {button_info['has_onclick']=}, {button_info['has_data_model_id']=}, {button_info['has_showmodeldetails']=}")
    
    return button_analysis

def main():
    """Hauptfunktion für Button-Syntax-Tests"""
    
    html_file = Path('/app/minesearch_v2/frontend/index.html')
    
    if not html_file.exists():
        print(f"❌ HTML-Datei nicht gefunden: {html_file}")
        return
    
    with open(html_file, 'r', encoding='utf-8') as f:
        html_content = f.read()
    
    print(f"📁 Analyzing: {html_file}")
    print(f"📏 File size: {len(html_content):,} characters")
    
    # Teste onclick-Handler
    onclick_results = test_onclick_syntax(html_content)
    
    # Analysiere Model-Detail-Buttons
    button_results = find_model_detail_buttons(html_content)
    
    # Kombiniere Ergebnisse
    final_results = {
        'file': str(html_file),
        'file_size': len(html_content),
        'onclick_analysis': onclick_results,
        'button_analysis': button_results,
        'summary': {
            'total_onclick_handlers': len(onclick_results['tested_handlers']),
            'syntax_errors': len(onclick_results['syntax_errors']),
            'warnings': len(onclick_results['warnings']),
            'valid_handlers': len(onclick_results['valid_handlers']),
            'model_buttons_found': button_results['total_model_buttons'],
            'model_buttons_with_issues': len(button_results['buttons_with_issues'])
        }
    }
    
    # Speichere Ergebnisse
    output_file = Path('/app/BUTTON_ONCLICK_SYNTAX_REPORT.json')
    with open(output_file, 'w', encoding='utf-8') as f:
        json.dump(final_results, f, indent=2, ensure_ascii=False)
    
    # Ausgabe der Zusammenfassung
    print("\n" + "=" * 50)
    print("📋 ONCLICK SYNTAX TEST SUMMARY")
    print("=" * 50)
    
    summary = final_results['summary']
    
    print(f"📊 Total onClick handlers: {summary['total_onclick_handlers']}")
    print(f"❌ Syntax errors: {summary['syntax_errors']}")
    print(f"⚠️  Warnings: {summary['warnings']}")
    print(f"✅ Valid handlers: {summary['valid_handlers']}")
    print(f"🔘 Model buttons found: {summary['model_buttons_found']}")
    print(f"🚨 Model buttons with issues: {summary['model_buttons_with_issues']}")
    
    if onclick_results['syntax_errors']:
        print("\n🚨 CRITICAL SYNTAX ERRORS:")
        for error in onclick_results['syntax_errors']:
            print(f"   Handler #{error['index']}: {', '.join(error['issues'])}")
            print(f"      Code: {error['code'][:80]}...")
    
    if button_results['buttons_with_issues']:
        print("\n⚠️  BUTTON ISSUES:")
        for button in button_results['buttons_with_issues']:
            print(f"   Issue: {button.get('syntax_issue', 'Unknown')}")
            print(f"   HTML: {button['html'][:60]}...")
    
    print(f"\n💾 Detailed report saved: {output_file}")
    
    # Empfehlungen
    if summary['syntax_errors'] > 0 or summary['model_buttons_with_issues'] > 0:
        print("\n🛠️  RECOMMENDATIONS:")
        print("   1. Fix syntax errors immediately")
        print("   2. Test all model detail buttons")
        print("   3. Validate JavaScript in browser console")
        print("   4. Consider using a JavaScript linter")
    else:
        print("\n✅ All onClick handlers appear syntactically correct!")

if __name__ == "__main__":
    main()