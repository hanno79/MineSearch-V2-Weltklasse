"""
Import Helper für Provider
Löst Import-Probleme zwischen relativen und absoluten Imports
"""

import sys
import os

# Füge backend zum Python-Pfad hinzu
backend_path = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
if backend_path not in sys.path:
    sys.path.insert(0, backend_path)

# Jetzt können alle Provider absolute Imports verwenden