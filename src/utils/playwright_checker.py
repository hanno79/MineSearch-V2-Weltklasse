"""
Author: rahn
Datum: 24.06.2025
Version: 1.0
Beschreibung: Playwright Installation Checker
"""

import subprocess
import sys
import os
from pathlib import Path
from src.core.logger import get_logger


class PlaywrightChecker:
    """Prüft und installiert Playwright bei Bedarf"""
    
    def __init__(self):
        self.logger = get_logger("playwright_checker")
        
    def check_and_install(self) -> bool:
        """Prüft Playwright und installiert bei Bedarf"""
        try:
            # Prüfe ob Playwright importierbar ist
            try:
                import playwright
                self.logger.info(f"Playwright {playwright.__version__} ist installiert")
            except ImportError:
                self.logger.warning("Playwright nicht gefunden - installiere...")
                if not self._install_playwright():
                    return False
            
            # Prüfe ob Browser installiert sind
            if not self._check_browsers():
                self.logger.warning("Browser nicht gefunden - installiere...")
                if not self._install_browsers():
                    return False
            
            self.logger.info("✓ Playwright ist bereit")
            return True
            
        except Exception as e:
            self.logger.error(f"Fehler bei Playwright-Prüfung: {e}")
            return False
    
    def _install_playwright(self) -> bool:
        """Installiert Playwright"""
        try:
            self.logger.info("Installiere Playwright...")
            result = subprocess.run(
                [sys.executable, '-m', 'pip', 'install', '--upgrade', 'playwright'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                self.logger.error(f"Pip install fehlgeschlagen: {result.stderr}")
                return False
                
            self.logger.info("Playwright erfolgreich installiert")
            return True
            
        except Exception as e:
            self.logger.error(f"Installation fehlgeschlagen: {e}")
            return False
    
    def _check_browsers(self) -> bool:
        """Prüft ob Browser installiert sind"""
        # Prüfe typische Browser-Pfade
        browser_paths = [
            Path.home() / '.cache' / 'ms-playwright' / 'chromium-1091' / 'chrome-linux' / 'chrome',
            Path('/root/.cache/ms-playwright/chromium-1091/chrome-linux/chrome'),
        ]
        
        for path in browser_paths:
            if path.exists() and os.access(str(path), os.X_OK):
                self.logger.debug(f"Browser gefunden: {path}")
                return True
        
        return False
    
    def _install_browsers(self) -> bool:
        """Installiert Playwright Browser"""
        try:
            # Verwende das install_playwright.sh Script wenn vorhanden
            script_path = Path('/app/install_playwright.sh')
            if script_path.exists():
                self.logger.info("Nutze install_playwright.sh...")
                
                # Mache Script ausführbar
                os.chmod(str(script_path), 0o755)
                
                # Führe Script aus
                result = subprocess.run(
                    ['/bin/bash', str(script_path)],
                    capture_output=True,
                    text=True
                )
                
                if result.returncode == 0:
                    self.logger.info("Browser erfolgreich installiert")
                    return True
                else:
                    self.logger.error(f"Script fehlgeschlagen: {result.stderr}")
            
            # Fallback: Direkte Installation
            self.logger.info("Installiere Browser direkt...")
            result = subprocess.run(
                ['playwright', 'install', 'chromium', '--with-deps'],
                capture_output=True,
                text=True
            )
            
            if result.returncode != 0:
                # Versuche ohne System-Dependencies
                result = subprocess.run(
                    ['playwright', 'install', 'chromium'],
                    capture_output=True,
                    text=True
                )
            
            return result.returncode == 0
            
        except Exception as e:
            self.logger.error(f"Browser-Installation fehlgeschlagen: {e}")
            return False
    
    @staticmethod
    def ensure_playwright_ready():
        """Statische Methode für einfache Nutzung"""
        checker = PlaywrightChecker()
        if not checker.check_and_install():
            checker.logger.warning(
                "Playwright konnte nicht installiert werden. "
                "Browser Agent wird im Fallback-Modus laufen."
            )
            return False
        return True