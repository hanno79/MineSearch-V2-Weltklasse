# Port-Standard für MineSearch v2.11

**Author:** rahn  
**Datum:** 19.07.2025  
**Status:** VERBINDLICH

## 🎯 STANDARD-PORT: 8000

**Alle MineSearch Backend-Services laufen auf Port 8000**

### Gründe für Port 8000:
1. ✅ Ursprünglicher Standard-Port
2. ✅ User hat explizit Port 8000 gestartet
3. ✅ Logischer Default (8000 = erster Port)
4. ✅ Keine Konflikte mit anderen Services

### Verbindliche Konfiguration:
- **Backend Server:** `uvicorn main:app --port 8000`
- **Frontend API_BASE_URL:** `http://localhost:8000`
- **Alle API-Endpoints:** `http://localhost:8000/api/*`
- **Health-Check:** `http://localhost:8000/health`

### REGEL: Port-Änderungen VERBOTEN
❌ **NIEMALS** eigenmächtig Port ändern ohne Absprache
❌ **NIEMALS** parallele Instanzen auf verschiedenen Ports
❌ **NIEMALS** Frontend auf anderen Port konfigurieren

### Bei Port-Konflikten:
1. Andere Services beenden, die Port 8000 blockieren
2. Port 8000 freimachen mit `pkill -f uvicorn`
3. Nur eine Instanz auf Port 8000 starten

### Compliance-Check:
```bash
# Nur eine Instanz sollte laufen
ss -tulpn | grep :8000

# Alle anderen Backend-Instanzen beenden
pkill -f "uvicorn.*main:app"

# Neu starten auf korrektem Port
cd /app/minesearch_v2/backend && python -m uvicorn main:app --port 8000
```

## 🚨 NACHHALTIGKEITS-REGEL

**Port 8000 ist der EINZIGE erlaubte Backend-Port für MineSearch**

Jede Abweichung führt zu Instabilität und muss sofort korrigiert werden.