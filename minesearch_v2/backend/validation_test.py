#!/usr/bin/env python3
"""
Cross-Field-Validation Tester
Author: rahn
Datum: 30.07.2025
Version: 1.0
Beschreibung: Testet Cross-Field-Validation für Status-Konsistenz in konsolidierten Ergebnissen
"""

import json
import requests
from typing import Dict, List, Any
from dataclasses import dataclass

@dataclass
class ValidationIssue:
    mine_name: str
    issue_type: str
    description: str
    fields_involved: List[str]
    severity: str  # CRITICAL, HIGH, MEDIUM, LOW

class CrossFieldValidator:
    def __init__(self, api_url: str = "http://localhost:8000"):
        self.api_url = api_url
        self.issues: List[ValidationIssue] = []
        
    def fetch_consolidated_results(self) -> Dict[str, Any]:
        """Hole konsolidierte Ergebnisse von der API"""
        try:
            response = requests.get(f"{self.api_url}/api/results/consolidated")
            response.raise_for_status()
            return response.json()
        except Exception as e:
            print(f"FEHLER beim Abrufen der API-Daten: {e}")
            return {}
    
    def validate_status_consistency(self, mine_data: Dict[str, Any]) -> None:
        """Validiere Status-Konsistenz zwischen Feldern"""
        mine_name = mine_data.get("mine_name", "UNBEKANNT")
        best_values = mine_data.get("best_values", {})
        
        # Extrahiere relevante Felder
        aktivitaetsstatus = best_values.get("Aktivitätsstatus", "").lower()
        produktionsende = best_values.get("Produktionsende", "").lower()
        foerdermenge = best_values.get("Fördermenge/Jahr", "").lower()
        
        # REGEL 1: Aktive Minen sollten nicht "Mine geschlossen" in Fördermenge haben
        if "aktiv" in aktivitaetsstatus and "mine geschlossen" in foerdermenge:
            self.issues.append(ValidationIssue(
                mine_name=mine_name,
                issue_type="INKONSISTENTER_STATUS",
                description=f"Mine ist '{aktivitaetsstatus}' aber Fördermenge zeigt '{foerdermenge}'",
                fields_involved=["Aktivitätsstatus", "Fördermenge/Jahr"],
                severity="CRITICAL"
            ))
        
        # REGEL 2: Aktive Minen sollten nicht definitive Produktionsende-Daten haben
        if "aktiv" in aktivitaetsstatus and produktionsende not in ["noch aktiv", "n/a", ""]:
            # Prüfe ob es ein Datum ist (einfache Heuristik)
            if any(char.isdigit() for char in produktionsende) and "noch" not in produktionsende:
                self.issues.append(ValidationIssue(
                    mine_name=mine_name,
                    issue_type="AKTIV_MIT_ENDDATUM",
                    description=f"Aktive Mine hat Produktionsende: '{produktionsende}'",
                    fields_involved=["Aktivitätsstatus", "Produktionsende"],
                    severity="HIGH"
                ))
        
        # REGEL 3: Geschlossene Minen sollten nicht "noch aktiv" in Produktionsende haben
        if ("geschlossen" in aktivitaetsstatus or "inaktiv" in aktivitaetsstatus) and "noch aktiv" in produktionsende:
            self.issues.append(ValidationIssue(
                mine_name=mine_name,
                issue_type="GESCHLOSSEN_NOCH_AKTIV",
                description=f"Geschlossene Mine hat Produktionsende: '{produktionsende}'",
                fields_involved=["Aktivitätsstatus", "Produktionsende"],
                severity="CRITICAL"
            ))
        
        # REGEL 4: Logische Konsistenz zwischen Produktionsende und Fördermenge
        if "noch aktiv" in produktionsende and "mine geschlossen" in foerdermenge:
            self.issues.append(ValidationIssue(
                mine_name=mine_name,
                issue_type="NOCH_AKTIV_ABER_GESCHLOSSEN",
                description=f"Produktionsende '{produktionsende}' aber Fördermenge '{foerdermenge}'",
                fields_involved=["Produktionsende", "Fördermenge/Jahr"],
                severity="CRITICAL"
            ))
    
    def validate_all_mines(self) -> None:
        """Validiere alle Minen"""
        print("🔍 STARTE CROSS-FIELD-VALIDATION...")
        
        data = self.fetch_consolidated_results()
        if not data.get("success", False):
            print("❌ FEHLER: API-Antwort nicht erfolgreich")
            return
        
        consolidated_results = data.get("data", {}).get("consolidated_results", [])
        total_mines = len(consolidated_results)
        
        print(f"📊 Validiere {total_mines} Minen...")
        
        for i, mine_data in enumerate(consolidated_results):
            self.validate_status_consistency(mine_data)
            
            # Progress-Anzeige
            if (i + 1) % 10 == 0 or i == 0:
                print(f"⏳ Verarbeitet: {i + 1}/{total_mines} Minen")
    
    def generate_report(self) -> str:
        """Generiere Validierungsbericht"""
        report = []
        report.append("=" * 80)
        report.append("CROSS-FIELD-VALIDATION TESTBERICHT")
        report.append("=" * 80)
        report.append(f"Datum: 30.07.2025")
        report.append(f"Autor: Data Validation Tester")
        report.append("")
        
        # Zusammenfassung
        critical_count = len([i for i in self.issues if i.severity == "CRITICAL"])
        high_count = len([i for i in self.issues if i.severity == "HIGH"])
        medium_count = len([i for i in self.issues if i.severity == "MEDIUM"])
        low_count = len([i for i in self.issues if i.severity == "LOW"])
        
        report.append("📊 ZUSAMMENFASSUNG:")
        report.append(f"   Gesamt Probleme: {len(self.issues)}")
        report.append(f"   ❌ CRITICAL: {critical_count}")
        report.append(f"   🔥 HIGH: {high_count}")
        report.append(f"   ⚠️  MEDIUM: {medium_count}")
        report.append(f"   💡 LOW: {low_count}")
        report.append("")
        
        if not self.issues:
            report.append("✅ KEINE VALIDIERUNGSFEHLER GEFUNDEN - CROSS-FIELD-VALIDATION FUNKTIONIERT!")
            return "\n".join(report)
        
        # Detaillierte Fehler nach Schweregrad
        for severity in ["CRITICAL", "HIGH", "MEDIUM", "LOW"]:
            severity_issues = [i for i in self.issues if i.severity == severity]
            if not severity_issues:
                continue
                
            report.append(f"\n{severity} PROBLEME ({len(severity_issues)}):")
            report.append("-" * 50)
            
            for issue in severity_issues:
                report.append(f"🏭 Mine: {issue.mine_name}")
                report.append(f"   Typ: {issue.issue_type}")
                report.append(f"   Beschreibung: {issue.description}")
                report.append(f"   Betroffene Felder: {', '.join(issue.fields_involved)}")
                report.append("")
        
        # Empfehlungen
        report.append("🔧 EMPFEHLUNGEN:")
        if critical_count > 0:
            report.append("   ❌ SOFORTIGER HANDLUNGSBEDARF - Cross-Field-Validation ist fehlerhaft!")
            report.append("   - Status Logic Implementer muss die Validierungsregeln überarbeiten")
            report.append("   - Inkonsistente Daten müssen korrigiert werden")
        
        if high_count > 0:
            report.append("   🔥 Hohe Priorität - Logik-Fehler in Statusverarbeitung")
        
        return "\n".join(report)
    
    def save_detailed_issues(self, filename: str = "validation_issues.json") -> None:
        """Speichere detaillierte Probleme als JSON"""
        issues_data = []
        for issue in self.issues:
            issues_data.append({
                "mine_name": issue.mine_name,
                "issue_type": issue.issue_type,
                "description": issue.description,
                "fields_involved": issue.fields_involved,
                "severity": issue.severity
            })
        
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(issues_data, f, indent=2, ensure_ascii=False)
        
        print(f"💾 Detaillierte Probleme gespeichert in: {filename}")

def main():
    validator = CrossFieldValidator()
    validator.validate_all_mines()
    
    # Generiere und zeige Bericht
    report = validator.generate_report()
    print(report)
    
    # Speichere detaillierte Daten
    validator.save_detailed_issues()
    
    # Speichere Bericht
    with open("validation_test_report.txt", 'w', encoding='utf-8') as f:
        f.write(report)
    
    print(f"\n📄 Vollständiger Bericht gespeichert in: validation_test_report.txt")
    
    # Return-Code für Automation
    if any(issue.severity in ["CRITICAL", "HIGH"] for issue in validator.issues):
        exit(1)  # Fehler-Exit-Code
    else:
        exit(0)  # Erfolg-Exit-Code

if __name__ == "__main__":
    main()