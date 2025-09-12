#!/usr/bin/env python3
"""
Author: rahn
Datum: 12.07.2025
Version: 1.0
Beschreibung: Intelligentes Service-Management für MineSearch v2 System
"""

import os
import sys
import time
import signal
import psutil
import asyncio
import logging
import subprocess
from pathlib import Path
from typing import List, Dict, Optional, Tuple
import requests
from datetime import datetime

# Setup Logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ServiceManager:
    """Intelligenter Service-Manager für MineSearch v2"""

    def __init__(self):
    """__init__ - TODO: Dokumentation hinzufügen"""
        self.backend_port = 8000
        self.frontend_port = 8080
        self.backend_process = None
        self.frontend_process = None

        # Service-Konfiguration
        self.backend_path = Path("/app/minesearch_v2/backend")
        self.frontend_path = Path("/app/minesearch_v2/frontend")
        self.logs_path = Path("/app/minesearch_v2/backend/logs")

        # Erstelle Log-Verzeichnis
        self.logs_path.mkdir(exist_ok=True)

    def detect_running_services(self) -> Dict[str, Optional[int]]:
        """
        Erkennt laufende Services automatisch

        Returns:
            Dict mit Service-Namen und Process-IDs
        """
        services = {
            "backend": None,
            "frontend": None
        }

        try:
            # Portable Methode mit ss für Port-Prüfung
            import subprocess

            # Prüfe Backend-Port mit ss
            try:
                result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{self.backend_port}' in line and 'LISTEN' in line:
                            # Extrahiere PID aus ss-Output: users:(("python",pid=12345,fd=3))
                            import re
                            pid_match = re.search(r'pid=(\d+)', line)
                            if pid_match:
                                pid = int(pid_match.group(1))
                                services["backend"] = pid
                                logger.info(f"[SERVICE-DETECT] Backend gefunden: PID {pid}")
                                break
            except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
                pass

            # Prüfe Frontend-Port mit ss
            try:
                result = subprocess.run(['ss', '-tlnp'], capture_output=True, text=True, timeout=5)
                if result.returncode == 0:
                    for line in result.stdout.split('\n'):
                        if f':{self.frontend_port}' in line and 'LISTEN' in line:
                            import re
                            pid_match = re.search(r'pid=(\d+)', line)
                            if pid_match:
                                pid = int(pid_match.group(1))
                                services["frontend"] = pid
                                logger.info(f"[SERVICE-DETECT] Frontend gefunden: PID {pid}")
                                break
            except (subprocess.TimeoutExpired, ValueError, FileNotFoundError):
                pass

        except ValueError as e:
            logger.error(f"[SERVICE-DETECT] Fehler bei Service-Erkennung: {e}")

        return services

    def check_port_availability(self, port: int) -> bool:
        """
        Prüft ob ein Port verfügbar ist

        Args:
            port: Port-Nummer

        Returns:
            True wenn verfügbar, False wenn belegt
        """
        import socket
        try:
            with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
                sock.settimeout(1)
                result = sock.connect_ex(('localhost', port))
                return result != 0  # 0 = Verbindung erfolgreich (Port belegt)
        except OSError as e:
            logger.debug(f"[SERVICE_MANAGER] Socket-Fehler beim Port-Check {port}: {e}")
            return True  # Bei Fehler als verfügbar annehmen
        except Exception as e:
            logger.warning(f"[SERVICE_MANAGER] Unerwarteter Fehler bei Port-Check {port}: {e}")
            return True  # Bei Fehler als verfügbar annehmen

    def stop_service_by_pid(self, pid: int, service_name: str) -> bool:
        """
        Stoppt Service anhand der Process-ID

        Args:
            pid: Process-ID
            service_name: Service-Name für Logging

        Returns:
            True wenn erfolgreich gestoppt
        """
        try:
            proc = psutil.Process(pid)
            logger.info(f"[SERVICE-STOP] Stoppe {service_name} (PID {pid})")

            # Graceful shutdown versuchen
            proc.terminate()

            # Warte bis zu 10 Sekunden
            for _ in range(10):
                if not proc.is_running():
                    logger.info(f"[SERVICE-STOP] {service_name} erfolgreich gestoppt")
                    return True
                time.sleep(1)

            # Force kill falls nötig
            if proc.is_running():
                logger.warning(f"[SERVICE-STOP] Force kill für {service_name}")
                proc.kill()
                time.sleep(2)

            return not proc.is_running()

        except (psutil.NoSuchProcess, psutil.AccessDenied) as e:
            logger.info(f"[SERVICE-STOP] {service_name} bereits gestoppt oder nicht zugänglich")
            return True
        except Exception as e:
            logger.error(f"[SERVICE-STOP] Fehler beim Stoppen von {service_name}: {e}")
            return False

    def start_backend(self) -> bool:
        """
        Startet Backend-Service

        Returns:
            True wenn erfolgreich gestartet
        """
        try:
            # Prüfe ob Port verfügbar
            if not self.check_port_availability(self.backend_port):
                logger.error(f"[BACKEND-START] Port {self.backend_port} bereits belegt")
                return False

            # Wechsle ins Backend-Verzeichnis
            os.chdir(self.backend_path)

            # Log-Datei für Backend
            backend_log = self.logs_path / f"backend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            # Starte Backend mit uvicorn
            cmd = [
                sys.executable, "-m", "uvicorn",
                "main:app",
                "--host", "0.0.0.0",
                "--port", str(self.backend_port),
                "--reload",
                "--log-level", "info"
            ]

            logger.info(f"[BACKEND-START] Starte Backend: {' '.join(cmd)}")

            with open(backend_log, 'w') as log_file:
                self.backend_process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT,
                    cwd=self.backend_path
                )

            # Warte auf Start
            for attempt in range(30):  # 30 Sekunden timeout
                try:
                    response = requests.get(f"http://localhost:{self.backend_port}/health", timeout=2)
                    if response.status_code == 200:
                        logger.info(f"[BACKEND-START] ✅ Backend erfolgreich gestartet auf Port {self.backend_port}")
                        logger.info(f"[BACKEND-START] Logs: {backend_log}")
                        return True
                except requests.RequestException:
                    pass

                time.sleep(1)

            logger.error(f"[BACKEND-START] ❌ Backend-Start fehlgeschlagen - Timeout")
            return False

        except Exception as e:
            logger.error(f"[BACKEND-START] ❌ Fehler beim Backend-Start: {e}")
            return False

    def start_frontend(self) -> bool:
        """
        Startet Frontend-Service

        Returns:
            True wenn erfolgreich gestartet
        """
        try:
            # Prüfe ob Port verfügbar
            if not self.check_port_availability(self.frontend_port):
                logger.error(f"[FRONTEND-START] Port {self.frontend_port} bereits belegt")
                return False

            # Prüfe ob Frontend-Verzeichnis existiert
            if not self.frontend_path.exists():
                logger.warning(f"[FRONTEND-START] Frontend-Verzeichnis nicht gefunden: {self.frontend_path}")
                return False

            # Log-Datei für Frontend
            frontend_log = self.logs_path / f"frontend_{datetime.now().strftime('%Y%m%d_%H%M%S')}.log"

            # Starte Frontend mit Python HTTP-Server
            cmd = [
                sys.executable, "-m", "http.server",
                str(self.frontend_port),
                "--directory", str(self.frontend_path)
            ]

            logger.info(f"[FRONTEND-START] Starte Frontend: {' '.join(cmd)}")

            with open(frontend_log, 'w') as log_file:
                self.frontend_process = subprocess.Popen(
                    cmd,
                    stdout=log_file,
                    stderr=subprocess.STDOUT
                )

            # Warte auf Start
            for attempt in range(10):  # 10 Sekunden timeout
                try:
                    response = requests.get(f"http://localhost:{self.frontend_port}", timeout=2)
                    if response.status_code == 200:
                        logger.info(f"[FRONTEND-START] ✅ Frontend erfolgreich gestartet auf Port {self.frontend_port}")
                        logger.info(f"[FRONTEND-START] Logs: {frontend_log}")
                        return True
                except requests.RequestException:
                    pass

                time.sleep(1)

            logger.warning(f"[FRONTEND-START] ⚠️ Frontend gestartet aber Health-Check fehlgeschlagen")
            return True  # Frontend läuft wahrscheinlich trotzdem

        except Exception as e:
            logger.error(f"[FRONTEND-START] ❌ Fehler beim Frontend-Start: {e}")
            return False

    def health_check(self) -> Dict[str, bool]:
        """
        Führt Health-Check für alle Services durch

        Returns:
            Dict mit Service-Status
        """
        status = {
            "backend": False,
            "frontend": False
        }

        # Backend Health-Check
        try:
            response = requests.get(f"http://localhost:{self.backend_port}/health", timeout=5)
            status["backend"] = response.status_code == 200
        except requests.RequestException:
            status["backend"] = False

        # Frontend Health-Check
        try:
            response = requests.get(f"http://localhost:{self.frontend_port}", timeout=5)
            status["frontend"] = response.status_code == 200
        except requests.RequestException:
            status["frontend"] = False

        return status

    def start_all_services(self, force_restart: bool = False, backend_only: bool = False,
    """start_all_services - TODO: Dokumentation hinzufügen"""
                          frontend_only: bool = False) -> Dict[str, bool]:
        """
        Startet alle Services mit intelligenter Erkennung

        Args:
            force_restart: Erzwingt kompletten Neustart
            backend_only: Nur Backend starten
            frontend_only: Nur Frontend starten

        Returns:
            Dict mit Start-Status der Services
        """
        logger.info("🚀 [SERVICE-MANAGER] Starte MineSearch v2 Service-Management")

        # Erkenne laufende Services
        running_services = self.detect_running_services()

        results = {
            "backend": False,
            "frontend": False,
            "action_taken": "none"
        }

        # Force Restart - Stoppe alle Services
        if force_restart:
            logger.info("🔄 [SERVICE-MANAGER] Force Restart angefordert")
            for service_name, pid in running_services.items():
                if pid:
                    self.stop_service_by_pid(pid, service_name)
            running_services = {"backend": None, "frontend": None}
            results["action_taken"] = "force_restart"

        # Backend Management
        if not frontend_only:
            if running_services["backend"]:
                if not force_restart:
                    logger.info("🔄 [SERVICE-MANAGER] Backend läuft bereits - führe Restart durch")
                    self.stop_service_by_pid(running_services["backend"], "backend")
                    results["action_taken"] = "restart"

            logger.info("▶️ [SERVICE-MANAGER] Starte Backend...")
            results["backend"] = self.start_backend()

        # Frontend Management
        if not backend_only:
            if running_services["frontend"]:
                if not force_restart:
                    logger.info("🔄 [SERVICE-MANAGER] Frontend läuft bereits - führe Restart durch")
                    self.stop_service_by_pid(running_services["frontend"], "frontend")
                    if results["action_taken"] == "none":
                        results["action_taken"] = "restart"

            logger.info("▶️ [SERVICE-MANAGER] Starte Frontend...")
            results["frontend"] = self.start_frontend()

        # Final Health-Check
        time.sleep(3)  # Kurz warten für Service-Stabilisierung
        health_status = self.health_check()

        # Ausgabe der Ergebnisse
        print("\n" + "="*60)
        print("🎯 MINESEARCH V2 SERVICE STATUS")
        print("="*60)

        if not frontend_only:
            status_icon = "✅" if health_status["backend"] else "❌"
            print(f"{status_icon} Backend (Port {self.backend_port}): {'Läuft' if
health_status['backend'] else 'Fehler'}")
            if health_status["backend"]:
                print(f"   🌐 API: http://localhost:{self.backend_port}")
                print(f"   📊 Health: http://localhost:{self.backend_port}/health")

        if not backend_only:
            status_icon = "✅" if health_status["frontend"] else "❌"
            print(f"{status_icon} Frontend (Port {self.frontend_port}): {'Läuft' if
health_status['frontend'] else 'Fehler'}")
            if health_status["frontend"]:
                print(f"   🌐 Web-App: http://localhost:{self.frontend_port}")

        print(f"\n🔧 Aktion: {results['action_taken']}")
        print(f"📂 Logs: {self.logs_path}")
        print("="*60)

        # Update results mit Health-Check
        results["backend"] = health_status["backend"] if not frontend_only else True
        results["frontend"] = health_status["frontend"] if not backend_only else True

        return results


def main():
    """Hauptfunktion für direkten Aufruf"""
    import argparse

    parser = argparse.ArgumentParser(description='MineSearch v2 Service Manager')
    parser.add_argument('--force-restart', action='store_true', help='Erzwingt kompletten Neustart')
    parser.add_argument('--backend-only', action='store_true', help='Nur Backend starten')
    parser.add_argument('--frontend-only', action='store_true', help='Nur Frontend starten')

    args = parser.parse_args()

    manager = ServiceManager()
    results = manager.start_all_services(
        force_restart=args.force_restart,
        backend_only=args.backend_only,
        frontend_only=args.frontend_only
    )

    # Exit Code basierend auf Erfolg
    success = results["backend"] and results["frontend"]
    sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()
