import sys
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_ROOT_DIR = BASE_DIR.parent

PROJECT_APPLICATIONS = PROJECT_ROOT_DIR / 'applications'

for app in PROJECT_APPLICATIONS.iterdir():
    if str(app) not in sys.path:
        sys.path.append(str(app))

DEBUG = True
