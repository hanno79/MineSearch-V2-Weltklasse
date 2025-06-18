#!/usr/bin/env python
"""
Starter für Multi-Agent Mining Research System
"""
import subprocess
import sys
from pathlib import Path

def main():
    """Startet die Streamlit-Anwendung"""
    streamlit_file = Path(__file__).parent / "ui" / "streamlit_app.py"
    
    print("🚀 Starte Multi-Agent Mining Research System...")
    print("=" * 50)
    print("Öffne Browser unter: http://localhost:8501")
    print("=" * 50)
    
    # Starte Streamlit
    subprocess.run([
        sys.executable, "-m", "streamlit", "run",
        str(streamlit_file),
        "--server.port", "8501",
        "--server.address", "localhost"
    ])

if __name__ == "__main__":
    main()