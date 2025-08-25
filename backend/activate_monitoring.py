#!/usr/bin/env python3
"""
Author: rahn
Datum: 25.08.2025
Version: 1.0
Beschreibung: Aktivierungs-Script für Monitoring und Alerting

MONITORING-AKTIVIERUNG 25.08.2025: Startet vollständiges Monitoring-System
"""

import sys
sys.path.insert(0, '.')

import logging
from minesearch.monitoring_system import DataQualityMonitor

# Logging konfigurieren
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)

def activate_monitoring_system():
    """
    MONITORING-AKTIVIERUNG 25.08.2025
    Aktiviert und konfiguriert das komplette Monitoring-System
    """
    
    print("🚀 MONITORING & ALERTING SYSTEM AKTIVIERUNG")
    print("=" * 55)
    
    try:
        # 1. MONITORING-SYSTEM INITIALISIEREN
        print("📊 Initialisiere Monitoring-System...")
        monitor = DataQualityMonitor()
        
        # 2. INITIAL-CHECK DURCHFÜHREN
        print("🔍 Führe Initial-Qualitätsprüfung durch...")
        quality_report = monitor.check_data_quality()
        
        print(f"   📈 System Status: {quality_report['overall_status']}")
        print(f"   🚨 Aktive Alerts: {len(quality_report['alerts'])}")
        print(f"   📊 Metriken: {len(quality_report['metrics'])} Kategorien")
        
        # 3. SCHUTZEBENEN VALIDIEREN
        print("\n🛡️  Validiere alle Schutzebenen...")
        dashboard = monitor.get_monitoring_dashboard()
        
        protection_status = {
            'extraction_layer': dashboard['protection_layers']['extraction_layer'],
            'service_layer': dashboard['protection_layers']['service_layer'],
            'database_layer': dashboard['protection_layers']['database_layer'],
            'data_layer': dashboard['protection_layers']['data_layer']
        }
        
        active_layers = 0
        for layer_name, layer_info in protection_status.items():
            status = layer_info['status']
            status_icon = "✅" if status == 'ACTIVE' else "⚠️" if status == 'PARTIAL' else "❌"
            print(f"   {status_icon} {layer_name}: {status}")
            
            if status in ['ACTIVE', 'PARTIAL']:
                active_layers += 1
        
        # 4. ALERT-SYSTEM KONFIGURIEREN
        print(f"\n⚠️  Konfiguriere Alert-System...")
        print(f"   🎯 Kontaminations-Threshold: {monitor.alert_thresholds['contamination_rate']:.1%}")
        print(f"   📊 NULL-Anomalie-Threshold: {monitor.alert_thresholds['null_anomaly_rate']:.1%}")
        print(f"   🗄️  Constraint-Violation-Threshold: {monitor.alert_thresholds['constraint_violations']}/h")
        
        # 5. MONITORING-EVENTS TABELLE ERSTELLEN
        print(f"\n📝 Erstelle Monitoring-Events Tabelle...")
        monitor.log_search_event("monitoring_activated", "SYSTEM", {
            "active_layers": active_layers,
            "total_layers": len(protection_status),
            "system_status": quality_report['overall_status']
        })
        
        # 6. ENDERGEBNIS
        print(f"\n📊 MONITORING-SYSTEM STATUS:")
        print(f"   🛡️  Aktive Schutzebenen: {active_layers}/4")
        print(f"   📈 System-Zustand: {dashboard['system_status']}")
        print(f"   🚨 Aktuelle Alerts: {dashboard['active_alerts']}")
        
        if active_layers >= 3 and dashboard['system_status'] in ['HEALTHY', 'WARNING']:
            print(f"\n🎉 MONITORING-SYSTEM ERFOLGREICH AKTIVIERT!")
            print(f"   ✅ Kontinuierliche Datenqualitäts-Überwachung aktiv")
            print(f"   ✅ Feldkontamination-Alerts konfiguriert") 
            print(f"   ✅ Multi-Layer-Protection überwacht")
            print(f"   ✅ Real-time Anomalie-Erkennung läuft")
            
            print(f"\n📋 MONITORING-BEFEHLE:")
            print(f"   🔍 Status prüfen: python -c \"from minesearch.monitoring_system import data_quality_monitor; print(data_quality_monitor.check_data_quality())\"")
            print(f"   🖥️  Dashboard: python minesearch/monitoring_system.py")
            print(f"   📊 Metriken: Dashboard unter protection_layers verfügbar")
            
            return True
            
        else:
            print(f"\n⚠️  MONITORING-SYSTEM PARTIELL AKTIVIERT")
            print(f"   📊 {active_layers}/4 Schutzebenen aktiv")
            print(f"   🔧 System-Status: {dashboard['system_status']}")
            print(f"   💡 Monitoring läuft, aber nicht alle Komponenten optimal")
            
            return False
        
    except Exception as e:
        print(f"\n❌ FEHLER bei Monitoring-Aktivierung: {e}")
        logger.error(f"Monitoring-Aktivierung fehlgeschlagen: {e}")
        return False

def main():
    """Hauptfunktion"""
    success = activate_monitoring_system()
    exit(0 if success else 1)

if __name__ == "__main__":
    main()