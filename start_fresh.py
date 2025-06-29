#!/usr/bin/env python
"""
Author: rahn
Datum: 27.06.2025
Version: 1.0
Beschreibung: Start-Skript mit explizitem Module-Reload für MineSearch
"""

import sys
import os
import subprocess
import time

def clear_python_cache():
    """Löscht Python Cache"""
    print("🧹 Lösche Python Cache...")
    os.system('find /app -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null || true')
    os.system('find /app -name "*.pyc" -type f -delete 2>/dev/null || true')
    print("✅ Cache gelöscht")

def reload_modules():
    """Entfernt Module aus sys.modules um Neuladung zu erzwingen"""
    print("🔄 Erzwinge Module-Neuladung...")
    modules_to_remove = []
    for module_name in list(sys.modules.keys()):
        if module_name.startswith(('src.', 'streamlit')):
            modules_to_remove.append(module_name)
    
    for module in modules_to_remove:
        if module in sys.modules:
            del sys.modules[module]
    
    print(f"✅ {len(modules_to_remove)} Module aus Cache entfernt")

def kill_existing_processes():
    """Beendet existierende Streamlit Prozesse"""
    print("🛑 Beende existierende Prozesse...")
    os.system('pkill -9 -f streamlit 2>/dev/null || true')
    os.system('pkill -9 -f "python.*main.py" 2>/dev/null || true')
    time.sleep(2)  # Warte kurz
    print("✅ Prozesse beendet")

def start_streamlit():
    """Startet Streamlit mit frischem Python Interpreter"""
    print("\n🚀 Starte MineSearch mit frischem Python Interpreter...")
    print("📌 Session Manager Version wird in den Logs angezeigt")
    print("📌 Suche nach: [SESSION MANAGER v2.1-TIMEOUT-FIX-27062025]")
    print("\n" + "="*60 + "\n")
    
    # Verwende subprocess für sauberen Start
    env = os.environ.copy()
    env['PYTHONDONTWRITEBYTECODE'] = '1'  # Verhindere .pyc Erstellung
    
    cmd = [
        sys.executable, '-u',  # Unbuffered output
        '-m', 'streamlit', 'run',
        'src/ui/main.py',
        '--server.port', '8501',
        '--server.headless', 'true',
        '--logger.level', 'info'
    ]
    
    subprocess.run(cmd, env=env)

if __name__ == "__main__":
    print("=== MineSearch Fresh Start ===\n")
    
    # 1. Beende alte Prozesse
    kill_existing_processes()
    
    # 2. Lösche Cache
    clear_python_cache()
    
    # 3. Module-Reload
    reload_modules()
    
    # 4. Starte neu
    start_streamlit()