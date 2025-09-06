# MineSearch v3.0.0 Systematischer Test Workflow - ECHTE API-AUFRUFE

**ECHTE API-AUFRUFE:** Verwendet echte HTTP-Requests gegen localhost:8000 API

**Parameter:**
- `mine_name` (Pflicht): Name der zu testenden Mine 
- `country` (optional): Land der Mine
- `region` (optional): Region der Mine

**Verwendung**: 
- `/test_workflow mine_name="Casa Berardi" country="Kanada"`
- `/test_workflow mine_name="Éléonore"`
- `/test_workflow mine_name="Grasberg" country="Indonesia"`

---

!python3 -c "
import sys
import os
import json
import time
import requests
from datetime import datetime

# PARSE ARGUMENTS FROM USER INPUT - v3.0.0 SYSTEM
args_text = '''$ARGS'''
mine_name = 'Éléonore'  # Default
country = 'Canada'      # Default  
region = 'Quebec'       # Default

# Simple argument parsing
if 'mine_name=' in args_text:
    mine_start = args_text.find('mine_name=\"') + 11
    mine_end = args_text.find('\"', mine_start)
    if mine_start > 10 and mine_end > mine_start:
        mine_name = args_text[mine_start:mine_end]

if 'country=' in args_text:
    country_start = args_text.find('country=\"') + 9
    country_end = args_text.find('\"', country_start)
    if country_start > 8 and country_end > country_start:
        country = args_text[country_start:country_end]

if 'region=' in args_text:
    region_start = args_text.find('region=\"') + 8
    region_end = args_text.find('\"', region_start)
    if region_start > 7 and region_end > region_start:
        region = args_text[region_start:region_end]

# MINESEARCH v3.0.0 SYSTEMATISCHER TEST WORKFLOW - ECHTE API-AUFRUFE
print('🚀 MINESEARCH v3.0.0 SYSTEMATISCHER TEST WORKFLOW')
print('   *** ECHTE API-AUFRUFE - KEINE SIMULATION ***')
print('=' * 80)
print(f'Start Time: {datetime.now().strftime(\"%Y-%m-%d %H:%M:%S\")}')
print(f'Test Mine: {mine_name}')
print(f'Country: {country}')
print(f'Region: {region}')
print('=' * 80)

# SYSTEM REQUIREMENTS CHECK
print('\\n🔧 SYSTEM REQUIREMENTS CHECK')
print('-' * 60)

try:
    print('  ✅ Requests verfügbar')
    
    # API CONNECTIVITY CHECK
    response = requests.get('http://localhost:8000/api/provider-status', timeout=10)
    if response.status_code == 200:
        provider_data = response.json()
        total_providers = provider_data['data']['total_providers']
        healthy_providers = provider_data['data']['healthy_providers']
        print(f'  ✅ API erreichbar: {healthy_providers}/{total_providers} Provider gesund')
        api_available = True
    else:
        print(f'  ❌ API nicht erreichbar (Status: {response.status_code})')
        api_available = False
        
except Exception as e:
    print(f'  ❌ System Check Error: {e}')
    api_available = False

if not api_available:
    print('\\n❌ ABBRUCH: API ist nicht erreichbar!')
    print('   Starte das Backend mit: python3 -m minesearch.main')
    print('=' * 80)
    exit(1)

# BROWSER TEST SETUP (v3.0.0)
print('\\n🌐 ECHTE API TESTS - v3.0.0 SYSTEM')
print('-' * 60)

test_results = {
    'start_time': datetime.now().isoformat(),
    'version': 'v3.0.0-real-api',
    'parameters': {
        'mine_name': mine_name,
        'country': country,
        'region': region
    },
    'phase1_results': {},
    'phase2_results': {},
    'summary': {}
}

# v3.0.0 Test Models (NUR die wichtigsten für schnelleren Test)
test_models = [
    'openrouter:deepseek-free',
    'openrouter:deepseek-chat',
    'openrouter:claude-3.5-sonnet',
    'openrouter:claude-3.5-haiku',
    'openrouter:gpt-4o',
    'openrouter:gpt-4o-mini',
    'openrouter:gemini-2.5-pro',
    'openrouter:gemini-2.5-flash',
    'tavily:search',
    'tavily:deep-research'
]

print(f'  📋 Test Models: {len(test_models)} ausgewählt für schnelleren Test')
print(f'  🎯 Target: {mine_name} ({country}, {region})')
print('  🆕 Zwei-Phasen-Test: Einzelsuche + Batch-Suche')

# PHASE 1: EINZELSUCHE TESTS
print('\\n📍 PHASE 1: EINZELSUCHE TESTS (v3.0.0)')
print('-' * 60)

def test_model_real_api(model_name, mine, country, region):
    result = {
        'model': model_name,
        'status': 'UNKNOWN',
        'runtime_seconds': 0,
        'found_fields': {},
        'missing_fields': [],
        'quality_score': 0.0,
        'source_count': 0,
        'errors': [],
        'notes': '',
        'phase': 'single_search'
    }
    
    try:
        start_time = time.time()
        
        print(f'   🔍 ECHTER API-AUFRUF für {model_name}')
        print(f'      Suche: {mine} in {country}, {region}')
        
        # ECHTER API-AUFRUF - KEINE SIMULATION
        api_url = 'http://localhost:8000/api/search'
        payload = {
            'model': model_name,
            'mine_name': mine,
            'country': country,
            'region': region,
            'cache': False  # Cache-freie Version
        }
        
        response = requests.post(api_url, json=payload, timeout=120)
        result['runtime_seconds'] = time.time() - start_time
        
        if response.status_code == 200:
            data = response.json()
            if data.get('success', False):
                # ECHTE Daten aus API - KEINE Dummy-Werte
                mine_data = data.get('data', {})
                result['found_fields'] = {k: v for k, v in mine_data.items() if v and v != 'N/A'}
                result['source_count'] = data.get('source_count', 0)
                result['quality_score'] = data.get('quality_score', 0.0)
                result['status'] = 'SUCCESS'
                result['notes'] = f'Erfolgreiche API-Suche für {mine}'
                
                print(f'   ✅ ERFOLG: {len(result[\"found_fields\"])} echte Felder gefunden')
            else:
                # API-Fehler OHNE Dummy-Daten
                result['status'] = 'FAILED'
                result['errors'].append(data.get('error', 'API returned success=false'))
                result['notes'] = f'API-Fehler für {mine}'
                print(f'   ❌ API-FEHLER: {data.get(\"error\", \"Unknown\")}')
        else:
            # HTTP-Fehler OHNE Dummy-Daten
            result['status'] = 'FAILED'
            result['errors'].append(f'HTTP {response.status_code}: {response.text[:200]}')
            result['notes'] = f'HTTP-Fehler für {mine}'
            print(f'   ❌ HTTP-FEHLER: {response.status_code}')
            
        # Alle möglichen Felder als missing definieren wenn nicht gefunden
        all_fields = ['Name', 'Land', 'Region', 'Eigentümer', 'Betreiber', 'Koordinaten', 
                     'Aktivitätsstatus', 'Rohstoff', 'Minentyp', 'Produktionsstart', 
                     'Produktionsende', 'Fördermenge', 'Restaurationskosten', 'Fläche', 
                     'Quellenangaben', 'Tiefe', 'Reserven', 'Ressourcen']
        result['missing_fields'] = [f for f in all_fields if f not in result['found_fields']]
            
    except Exception as e:
        result['status'] = 'ERROR'
        result['runtime_seconds'] = time.time() - start_time
        result['errors'].append(str(e))
        print(f'   💥 EXCEPTION: {str(e)[:200]}')
    
    return result

# Execute Phase 1 Tests
print('\\n🚀 SEQUENTIELLE API-TESTS: Starte Tests für alle Modelle')
print('-' * 60)

phase1_successful = 0
total_tests = len(test_models)

for i, model in enumerate(test_models, 1):
    print(f'\\n📍 TEST {i}/{total_tests}: {model}')
    model_result = test_model_real_api(model, mine_name, country, region)
    test_results['phase1_results'][model] = model_result
    
    if model_result['status'] == 'SUCCESS':
        phase1_successful += 1

print(f'\\n📊 ERGEBNISSE ALLER {total_tests} MODELLE:')
print('=' * 80)

for i, model in enumerate(test_models, 1):
    model_result = test_results['phase1_results'][model]
    
    # Display results with detailed field values
    status_icon = '✅' if model_result['status'] == 'SUCCESS' else '❌'
    runtime = model_result['runtime_seconds']
    found_fields = len(model_result['found_fields'])
    total_fields = found_fields + len(model_result['missing_fields'])
    completeness = (found_fields / total_fields * 100) if total_fields > 0 else 0
    
    print(f'  {status_icon} {model}')
    print(f'     Status: {model_result[\"status\"]}')
    print(f'     Runtime: {runtime:.2f}s')
    print(f'     Quality: {model_result[\"quality_score\"]:.2f}')
    print(f'     Sources: {model_result[\"source_count\"]}')
    
    if model_result['status'] == 'SUCCESS' and model_result['found_fields']:
        print(f'     ✅ ERFOLG: {found_fields}/{total_fields} echte Felder gefunden ({completeness:.1f}%)')
        for field_name, field_value in model_result['found_fields'].items():
            print(f'       - {field_name}: {field_value}')
        
        if model_result['missing_fields']:
            missing_names = ', '.join(model_result['missing_fields'])
            print(f'     Fehlende Felder: {missing_names} ({len(model_result[\"missing_fields\"])}/{total_fields})')
    else:
        print(f'     ❌ FEHLER: Keine Daten gefunden ({found_fields}/{total_fields})')
        if model_result['errors']:
            print(f'     Errors: {\", \".join(model_result[\"errors\"])}')

print(f'\\n📊 PHASE 1 SUMMARY: {phase1_successful}/{total_tests} models successful')

# PHASE 2: BATCH-SUCHE TEST
print('\\n📦 PHASE 2: BATCH-SUCHE TEST (v3.0.0)')
print('-' * 60)

# Create test CSV with 3 mines
test_csv_content = f'''Mine,Land,Region
{mine_name},{country},{region}
Lac Bloom,Canada,Quebec
Olympic Dam,Australia,South Australia'''

csv_path = '/tmp/test_batch_mines.csv'
with open(csv_path, 'w') as f:
    f.write(test_csv_content)

print(f'  📄 Test CSV erstellt: {csv_path}')
print('  📝 Inhalt: 3 Test-Minen für Batch-Verarbeitung')

# ECHTE BATCH PROCESSING - KEINE SIMULATION
print('  🔄 ECHTE Batch-Verarbeitung mit API-Aufrufen')
print('     Nutze echte CSV und API für alle Minen')

batch_results = {'error': 'Batch API not implemented yet', 'mines_count': 3, 'processing_time': 0, 'successful_mines': 0}

# Für jetzt: Einfacher Fallback ohne Batch-API
print('  ⚠️  Batch-API noch nicht implementiert - überspringe Phase 2')

test_results['phase2_results'] = batch_results

# GENERATE COMPREHENSIVE REPORT
success_rate = (phase1_successful / total_tests * 100) if total_tests > 0 else 0
batch_success_rate = 0  # Da Batch nicht implementiert

# Berechne echte Testdauer
total_test_time = sum([r['runtime_seconds'] for r in test_results['phase1_results'].values()])
test_duration_minutes = total_test_time / 60

test_results['summary'] = {
    'total_models_tested': total_tests,
    'successful_models': phase1_successful,
    'single_search_success_rate': success_rate,
    'batch_success_rate': batch_success_rate,
    'overall_success_rate': success_rate,  # Nur Phase 1 da Batch nicht implementiert
    'test_duration_minutes': test_duration_minutes,
    'version': 'v3.0.0-real-api'
}

# Create detailed markdown report
timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
safe_mine_name = mine_name.replace(' ', '_').replace('é', 'e').replace('É', 'E')
report_filename = f'REAL_API_TEST_WORKFLOW_{timestamp}_{safe_mine_name}.md'
report_path = f'/home/hanno/projects/MineSearch/documentation/{report_filename}'

markdown_content = f'''# MineSearch v3.0.0 - ECHTER API TEST REPORT

**Test Datum:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}  
**Test Parameter:**
- **Mine:** {mine_name}
- **Land:** {country}
- **Region:** {region}
- **System Version:** v3.0.0 (Echte API-Aufrufe)
- **Modus:** ECHTER TEST mit echten HTTP-Requests

---

## 📊 Zusammenfassung

- **Getestete Modelle:** {total_tests}
- **Einzelsuche Erfolgsrate:** {success_rate:.1f}%
- **Gesamterfolgsrate:** {success_rate:.1f}%
- **Testdauer:** {test_duration_minutes:.1f} Minuten

---

## 🔍 Phase 1: Einzelsuche Ergebnisse

'''

# Add individual Phase 1 results
for model_name, result in test_results['phase1_results'].items():
    status_icon = '✅ ERFOLGREICH' if result['status'] == 'SUCCESS' else '❌ FEHLGESCHLAGEN'
    found_count = len(result['found_fields'])
    total_count = found_count + len(result['missing_fields'])
    completeness = (found_count / total_count * 100) if total_count > 0 else 0
    
    markdown_content += f'''### {model_name}
**Status:** {status_icon}
- **API-Aufruf erfolgreich:** {'JA' if result['status'] == 'SUCCESS' else 'NEIN'}
- **Laufzeit:** {result['runtime_seconds']:.2f} Sekunden'''
    
    if result['found_fields']:
        markdown_content += f'''
- **Gefundene Felder:** {found_count}/{total_count} ({completeness:.1f}%)'''
        for field_name, field_value in result['found_fields'].items():
            markdown_content += f'''
  - {field_name}: {field_value}'''
    
    if result['missing_fields']:
        missing_list = ', '.join(result['missing_fields'])
        markdown_content += f'''
- **Fehlende Felder:** {missing_list} ({len(result['missing_fields'])}/{total_count})'''
    
    markdown_content += f'''
- **Qualitätsscore:** {result['quality_score']:.2f}
- **Quellen gefunden:** {result['source_count']} URLs
- **Fehler:** {'KEINE' if not result['errors'] else ', '.join(result['errors'])}
- **Notizen:** {result['notes']}

'''

# Add assessment
overall_rate = success_rate
if overall_rate >= 85:
    assessment = '🎯 EXZELLENT - System ist produktionsreif!'
elif overall_rate >= 75:
    assessment = '✅ GUT - System funktional mit kleineren Problemen'
elif overall_rate >= 60:
    assessment = '🟡 VERBESSERUNGSBEDARF - System braucht Optimierungen'
else:
    assessment = '❌ KRITISCH - System braucht dringende Fixes'

markdown_content += f'''---

## 🏆 Gesamtbewertung

**{assessment}**

### {mine_name} Spezifische Erkenntnisse:
- ✅ Mine erfolgreich in {phase1_successful}/{total_tests} Modellen gefunden  
- ✅ Location: {country}, {region}
- ✅ Durchschnittliche Datenqualität: {sum([r['quality_score'] for r in test_results['phase1_results'].values()]) / len(test_results['phase1_results']):.2f}
- ✅ System Version: v3.0.0 (Echte API-Aufrufe)

### Technische Validierung:
- 🌐 Echte HTTP-Requests gegen localhost:8000 API
- 📊 Detaillierte Qualitäts-Metriken: Quality Score pro Modell
- 📄 Automatische Dokumentation: Strukturierte Markdown Reports
- ⚡ Performance-Messung: Echte Laufzeiten für jeden API-Call

---

*Generiert durch MineSearch v3.0.0 Echter API Test Workflow am {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}*
'''

# Save report
try:
    with open(report_path, 'w', encoding='utf-8') as f:
        f.write(markdown_content)
    print(f'\\n📄 COMPREHENSIVE REPORT GESPEICHERT: {report_path}')
except Exception as e:
    print(f'\\n❌ Report Error: {e}')

# FINAL SUMMARY
print('\\n' + '=' * 80)
print(f'🎯 {mine_name.upper()} ECHTER API TEST WORKFLOW ABGESCHLOSSEN')
print('=' * 80)

print(f'Test Mine: {mine_name} ({country}, {region})')
print(f'Phase 1 - Einzelsuche: {phase1_successful}/{total_tests} ({success_rate:.1f}%)')
print(f'Gesamterfolgsrate: {overall_rate:.1f}%')
print(f'Report: {report_path}')

print(f'\\n{assessment}')
print(f'Version: v3.0.0 (Echte API-Aufrufe)')
print('=' * 80)
"