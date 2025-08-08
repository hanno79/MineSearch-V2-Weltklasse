# Transitional import shim to support legacy absolute imports inside package
import sys
from pathlib import Path
_pkg_dir = Path(__file__).parent
if str(_pkg_dir) not in sys.path:
    sys.path.insert(0, str(_pkg_dir))
