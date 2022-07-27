import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_ROOT_DIR = BASE_DIR.parent

PROJECT_APPS_DIR = PROJECT_ROOT_DIR / 'applications'

for item in PROJECT_APPS_DIR.iterdir():
    if item.is_dir() and str(item) not in sys.path:
        sys.path.append(str(item))

DEBUG = True
