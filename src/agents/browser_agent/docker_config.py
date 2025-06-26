"""
Author: rahn
Datum: 24.06.2025
Version: 1.0
Beschreibung: Docker-spezifische Browser-Konfiguration
"""

import os
import platform
from typing import List, Dict, Any


class DockerBrowserConfig:
    """Docker-optimierte Browser-Konfiguration"""
    
    @staticmethod
    def get_browser_args() -> List[str]:
        """Gibt Browser-Argumente für Docker-Umgebung zurück"""
        args = [
            '--no-sandbox',
            '--disable-setuid-sandbox',
            '--disable-dev-shm-usage',
            '--disable-accelerated-2d-canvas',
            '--no-first-run',
            '--no-zygote',
            '--disable-gpu',
            '--disable-features=VizDisplayCompositor'
        ]
        
        # Zusätzliche Args für headless
        if DockerBrowserConfig.is_docker():
            args.extend([
                '--single-process',  # Wichtig für Docker
                '--disable-web-security',
                '--disable-features=IsolateOrigins',
                '--disable-site-isolation-trials'
            ])
        
        return args
    
    @staticmethod
    def is_docker() -> bool:
        """Prüft ob in Docker-Container"""
        # Methode 1: /.dockerenv existiert
        if os.path.exists('/.dockerenv'):
            return True
        
        # Methode 2: Container in cgroup
        try:
            with open('/proc/self/cgroup', 'r') as f:
                return 'docker' in f.read() or 'containerd' in f.read()
        except:
            pass
        
        # Methode 3: Kubernetes Pod
        return os.path.exists('/var/run/secrets/kubernetes.io')
    
    @staticmethod
    def get_browser_config() -> Dict[str, Any]:
        """Gibt optimale Browser-Konfiguration zurück"""
        config = {
            'headless': True,
            'args': DockerBrowserConfig.get_browser_args(),
            'ignore_default_args': ['--enable-automation'],
            'handle_sigint': False,
            'handle_sigterm': False,
            'handle_sighup': False
        }
        
        # Docker-spezifische Anpassungen
        if DockerBrowserConfig.is_docker():
            config.update({
                'executable_path': DockerBrowserConfig.find_chrome_executable(),
                'slow_mo': 100  # Langsamer in Docker für Stabilität
            })
        
        return config
    
    @staticmethod
    def find_chrome_executable() -> str:
        """Findet Chrome-Executable in verschiedenen Locations"""
        possible_paths = [
            # Playwright Standard-Pfade
            '/root/.cache/ms-playwright/chromium-1091/chrome-linux/chrome',
            '/ms-playwright/chromium-1091/chrome-linux/chrome',
            # System-Installationen
            '/usr/bin/chromium',
            '/usr/bin/chromium-browser',
            '/usr/bin/google-chrome',
            '/usr/bin/google-chrome-stable',
            # Snap
            '/snap/bin/chromium'
        ]
        
        for path in possible_paths:
            if os.path.exists(path) and os.access(path, os.X_OK):
                return path
        
        # Fallback: Playwright soll selbst suchen
        return None
    
    @staticmethod
    def get_viewport_config() -> Dict[str, int]:
        """Gibt Viewport-Konfiguration zurück"""
        # Kleinere Viewport in Docker für Performance
        if DockerBrowserConfig.is_docker():
            return {'width': 1280, 'height': 720}
        else:
            return {'width': 1920, 'height': 1080}
    
    @staticmethod
    def diagnose() -> Dict[str, Any]:
        """Diagnose-Informationen für Debugging"""
        import subprocess
        
        info = {
            'is_docker': DockerBrowserConfig.is_docker(),
            'platform': platform.platform(),
            'python_version': platform.python_version(),
            'chrome_found': False,
            'chrome_path': None,
            'system_deps': []
        }
        
        # Chrome-Pfad suchen
        chrome_path = DockerBrowserConfig.find_chrome_executable()
        if chrome_path:
            info['chrome_found'] = True
            info['chrome_path'] = chrome_path
        
        # System-Dependencies prüfen
        deps_to_check = ['libnss3', 'libxss1', 'libasound2', 'libgtk-3-0']
        for dep in deps_to_check:
            try:
                result = subprocess.run(['dpkg', '-l', dep], 
                                      capture_output=True, text=True)
                if result.returncode == 0:
                    info['system_deps'].append(dep)
            except:
                pass
        
        return info