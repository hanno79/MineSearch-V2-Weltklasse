#!/usr/bin/env python3
"""
Author: rahn
Datum: 24.06.2025
Version: 1.0
Beschreibung: Sicherer Starter für MineSearch
"""

import os
import sys
import subprocess
import time

def kill_existing_processes():
    """Beendet existierende Streamlit/Python Prozesse"""
    print("Beende existierende Prozesse...")
    subprocess.run(["pkill", "-f", "streamlit"], capture_output=True)
    subprocess.run(["pkill", "-f", "main.py"], capture_output=True)
    time.sleep(2)

def start_minesearch():
    """Startet MineSearch sicher"""
    print("Starte MineSearch...")
    
    # Environment Setup
    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"
    env["STREAMLIT_SERVER_HEADLESS"] = "true"
    env["STREAMLIT_SERVER_PORT"] = "8501"
    env["STREAMLIT_SERVER_ADDRESS"] = "0.0.0.0"
    
    # Clear logs
    log_file = "logs/minesearch.log"
    if os.path.exists(log_file):
        # Keep last 100 lines
        with open(log_file, 'r') as f:
            lines = f.readlines()
        with open(log_file, 'w') as f:
            f.writelines(lines[-100:])
    
    # Start Streamlit
    cmd = [
        sys.executable,
        "-m", "streamlit", "run",
        "src/ui/main.py",
        "--server.port=8501",
        "--server.address=0.0.0.0",
        "--server.headless=true",
        "--browser.gatherUsageStats=false",
        "--theme.base=dark"
    ]
    
    print("Führe aus:", " ".join(cmd))
    print("\nMineSearch wird gestartet...")
    print("Öffnen Sie: http://localhost:8501")
    print("\nDrücken Sie Ctrl+C zum Beenden\n")
    
    try:
        process = subprocess.Popen(cmd, env=env)
        process.wait()
    except KeyboardInterrupt:
        print("\nBeende MineSearch...")
        process.terminate()
        process.wait()
        print("MineSearch beendet.")
    except Exception as e:
        print(f"Fehler: {e}")
        if process:
            process.terminate()

if __name__ == "__main__":
    kill_existing_processes()
    start_minesearch()