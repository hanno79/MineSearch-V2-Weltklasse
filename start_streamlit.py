#!/usr/bin/env python3
"""
Streamlit Starter mit besserer Fehlerbehandlung
Author: rahn
Datum: 25.06.2025
"""
import subprocess
import sys
import time
import os

def start_streamlit():
    """Startet Streamlit mit Fehlerbehandlung"""
    
    # Setze Umgebungsvariablen
    env = os.environ.copy()
    env['STREAMLIT_SERVER_HEADLESS'] = 'true'
    env['STREAMLIT_BROWSER_GATHER_USAGE_STATS'] = 'false'
    
    # Streamlit Kommando
    cmd = [
        sys.executable, 
        '-m', 
        'streamlit', 
        'run',
        'src/ui/main.py',
        '--server.port', '8501',
        '--server.address', '0.0.0.0',
        '--server.headless', 'true',
        '--browser.gatherUsageStats', 'false'
    ]
    
    print("Starting Streamlit...")
    print(f"Command: {' '.join(cmd)}")
    
    try:
        # Starte Prozess
        process = subprocess.Popen(
            cmd,
            env=env,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            text=True,
            bufsize=1
        )
        
        # Warte kurz
        time.sleep(2)
        
        # Prüfe ob Prozess läuft
        if process.poll() is None:
            print("\n✅ Streamlit started successfully!")
            print("URL: http://localhost:8501")
            
            # Zeige Output
            while True:
                line = process.stdout.readline()
                if line:
                    print(line.strip())
                
                # Check for errors
                err_line = process.stderr.readline()
                if err_line:
                    print(f"ERROR: {err_line.strip()}")
                
                # Check if process is still running
                if process.poll() is not None:
                    print("\n❌ Streamlit process terminated!")
                    break
                    
        else:
            print("\n❌ Failed to start Streamlit!")
            stdout, stderr = process.communicate()
            if stdout:
                print("STDOUT:", stdout)
            if stderr:
                print("STDERR:", stderr)
            
    except KeyboardInterrupt:
        print("\n\nShutting down Streamlit...")
        process.terminate()
        process.wait()
        print("✅ Streamlit stopped")
    except Exception as e:
        print(f"❌ Error: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    start_streamlit()