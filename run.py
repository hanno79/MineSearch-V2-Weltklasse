#!/usr/bin/env python
"""
Starter für Multi-Agent Mining Research System
"""
import subprocess
import sys
import os
from pathlib import Path
import importlib
import shutil

def clear_python_cache():
    """Löscht Python-Cache vor dem Start"""
    print("🧹 Bereinige Python-Cache vor Start...")
    cache_cleared = 0
    
    # Lösche __pycache__ im src Verzeichnis
    src_dir = Path(__file__).parent / "src"
    for cache_dir in src_dir.rglob("__pycache__"):
        try:
            shutil.rmtree(cache_dir)
            cache_cleared += 1
        except:
            pass
    
    if cache_cleared > 0:
        print(f"✅ {cache_cleared} Cache-Verzeichnisse gelöscht")

def main():
    """Startet die Streamlit-Anwendung"""
    # Optional: Cache bereinigen bei jedem Start
    if "--clean" in sys.argv or os.environ.get("CLEAN_START", "").lower() == "true":
        clear_python_cache()
    
    streamlit_file = Path(__file__).parent / "src" / "ui" / "main.py"
    
    print("🚀 Starte Multi-Agent Mining Research System...")
    print("=" * 50)
    print("Öffne Browser unter: http://localhost:8501")
    print("=" * 50)
    
    # Umgebungsvariable für Module-Reload
    env = os.environ.copy()
    env["PYTHONDONTWRITEBYTECODE"] = "1"  # Verhindere .pyc Erstellung
    
    # Starte Streamlit mit erweiterten Optionen
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(streamlit_file),
        "--server.port", "8501",
        "--server.address", "localhost",
        "--server.runOnSave", "true",  # Auto-Reload bei Dateiänderungen
        "--server.fileWatcherType", "auto"  # Besseres File-Watching
    ], env=env)

if __name__ == "__main__":
    main()