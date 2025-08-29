import os
from pathlib import Path

import pytest


@pytest.fixture(autouse=True, scope="session")
def configure_mines_db_path_env():
    """Setzt MINES_DB_PATH für Tests, falls nicht bereits gesetzt.

    Ermittelt einen Standardpfad relativ zum Repo-Root, damit CI und lokale
    Entwickler den Pfad bei Bedarf per Umgebungsvariable überschreiben können.
    """
    repo_root = Path(__file__).resolve().parent
    default_db_path = (repo_root / "backend" / "minesearch" / "database" / "mines.db").resolve()

    previous_value = os.environ.get("MINES_DB_PATH")
    if previous_value is None:
        os.environ["MINES_DB_PATH"] = str(default_db_path)

    try:
        yield
    finally:
        # Ursprungszustand wiederherstellen
        if previous_value is None:
            os.environ.pop("MINES_DB_PATH", None)
        else:
            os.environ["MINES_DB_PATH"] = previous_value



