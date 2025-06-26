# UI Update Problem - Analyse und Lösungen
**Author:** rahn  
**Datum:** 27.06.2025  
**Version:** 1.0

## Problem-Beschreibung

Die UI wird während der Suche nicht aktualisiert. Der Benutzer sieht:
- "Unknown" statt des Mine-Namens
- 0 gefundene Daten obwohl in den Logs Funde stehen  
- Keine Live-Updates der Fortschrittsanzeige
- "missing ScriptRunContext" Fehler in den Logs

## Ursachen-Analyse

### 1. Falscher Dictionary-Key für Mine-Name
**Problem:** In `search_form.py` Zeile 184 wurde der falsche Key verwendet:
```python
current_mine=mine_data.get('name', 'Unknown')  # FALSCH
```

**Lösung:** Korrektur auf den richtigen Key:
```python
current_mine=mine_data.get('mine_name', 'Unknown')  # RICHTIG
```

**Status:** ✅ BEHOBEN

### 2. Threading-Problem mit Streamlit
**Problem:** Die `status_callback` Funktion wird aus einem async Thread (`Thread-26 (_run_loop)`) heraus aufgerufen. Streamlit UI-Updates können nicht aus separaten Threads erfolgen.

**Symptom:** 
```
Thread 'Thread-26 (_run_loop)': missing ScriptRunContext
```

**Lösung:** Status-Updates nur in Session State schreiben, keine direkten UI-Manipulationen aus Callbacks.

**Status:** ✅ BEHOBEN - Callback schreibt jetzt nur in Session State

### 3. Fehlende Live-Updates der UI
**Problem:** Daten werden in Session State geschrieben, aber die UI wird nicht automatisch aktualisiert.

**Lösungsansätze:**

#### Option A: Polling-basierte Updates (IMPLEMENTIERT)
- Session State wird regelmäßig gelesen
- UI wird periodisch neu gerendert
- Verwendung von `st.empty()` Containern

#### Option B: Thread-sichere Queue (VORBEREITET)
- `ThreadSafeSearchFormComponent` mit Update-Queue
- Separater Thread für Suche
- Main Thread pollt Queue und updated UI

#### Option C: Live Update Mixin (VORBEREITET)
- `LiveUpdateMixin` für wiederverwendbare Live-Updates
- Decorator-basierter Ansatz
- Automatisches Polling während Operation läuft

## Implementierte Fixes

### 1. search_form.py - Korrektur Mine-Name Key
```python
# Alt:
current_mine=mine_data.get('name', 'Unknown')
# Neu:
current_mine=mine_data.get('mine_name', 'Unknown')
```

### 2. search_form.py - Thread-sichere Status Updates
```python
def status_callback(message, phase=None, agent=None, partial_results=None):
    # Nur in Session State schreiben
    st.session_state.live_progress.update({
        'current_mine': mine_data['mine_name'],
        'mine_index': getattr(self, 'current_mine_index', 0),
        'total_mines': getattr(self, 'total_mines', 1),
        'phase': phase,
        'agent': agent,
        'status_message': message,
        'partial_results': partial_results
    })
```

### 3. search_progress.py - Session State Integration
```python
def render_progress(self, ...):
    # Daten aus Session State lesen wenn nicht übergeben
    if 'live_progress' in st.session_state:
        live_data = st.session_state.live_progress
        current_mine = current_mine or live_data.get('current_mine', 'Unknown')
        # ... weitere Felder
```

## Neue Komponenten

### 1. search_form_threadsafe.py
- Vollständig thread-sichere Implementation
- Update-Queue für UI-Updates
- Separater Search-Thread

### 2. live_update_mixin.py
- Wiederverwendbarer Mixin für Live-Updates
- Decorator-basiert
- Automatisches Polling

## Empfehlungen

### Kurzfristig (sofort umsetzbar)
1. ✅ Mine-Name Key korrigiert
2. ✅ Status-Callback thread-sicher gemacht
3. ⏳ Polling-Loop in _perform_search einbauen

### Mittelfristig
1. ThreadSafeSearchFormComponent testen und einsetzen
2. LiveUpdateMixin in andere Komponenten integrieren
3. Streamlit's experimentelle Features evaluieren (st.rerun mit Timer)

### Langfristig
1. Vollständige Überarbeitung des async/UI Update Mechanismus
2. WebSocket-basierte Updates evaluieren
3. Server-Sent Events für echte Live-Updates

## Testing

### Test-Szenario 1: Mine-Name Anzeige
1. CSV mit Minen laden
2. Suche starten
3. **Erwartung:** Korrekter Mine-Name statt "Unknown"

### Test-Szenario 2: Live-Updates
1. Suche mit mehreren Minen starten
2. Progress beobachten
3. **Erwartung:** 
   - Fortschrittsbalken aktualisiert sich
   - Gefundene Daten zählen hoch
   - Phase/Agent werden angezeigt

### Test-Szenario 3: Thread-Sicherheit
1. Logs während Suche beobachten
2. **Erwartung:** Keine "missing ScriptRunContext" Fehler mehr

## Offene Punkte

1. **Polling-Intervall optimieren**
   - Aktuell: Manuelles time.sleep()
   - Besser: Dynamisches Intervall basierend auf Update-Frequenz

2. **Performance-Impact**
   - Häufige Session State Updates
   - Polling overhead
   - Monitoring erforderlich

3. **Browser-Kompatibilität**
   - Auto-Refresh in verschiedenen Browsern testen
   - Mobile Geräte berücksichtigen