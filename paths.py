"""Project paths shared across scrape, build, and dashboard scripts."""
import os

PROJECT_ROOT = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(PROJECT_ROOT, "data")


def data_path(filename: str) -> str:
    """Return an absolute path inside the project data directory."""
    os.makedirs(DATA_DIR, exist_ok=True)
    return os.path.join(DATA_DIR, filename)
