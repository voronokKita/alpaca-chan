import sys
from pathlib import Path


DEBUG = True

BASE_DIR = Path(__file__).resolve().parent.parent

PROJECT_ROOT_DIR = BASE_DIR.parent

PROJECT_APPS_DIR = PROJECT_ROOT_DIR / 'applications'

for item in PROJECT_APPS_DIR.iterdir():
    if item.is_dir() and str(item) not in sys.path:
        sys.path.append(str(item))

PROJECT_MAIN_APPS = {
    'polls': {
        'app_dir': PROJECT_APPS_DIR / 'django-polls',
        'db': {'name': 'polls_db', 'dependencies': [], 'router_class': 'PollsRouter'}
    },
    'encyclopedia': {
        'app_dir': PROJECT_APPS_DIR / 'django-cs50web-wiki',
        'db': {'name': 'encyclopedia_db', 'dependencies': [], 'router_class': 'WikiRouter'}
    },
    'auctions': {
        'app_dir': PROJECT_APPS_DIR / 'django-cs50web-commerce',
        'db': {'name': 'auctions_db', 'dependencies': ['default'], 'router_class': 'CommerceRouter'}
    },
}
ALL_PROJECT_APPS = {
    'core': {'app_dir': PROJECT_APPS_DIR / 'django-core-app', 'db': False},
    'accounts': {'app_dir': PROJECT_APPS_DIR / 'django-accounts', 'db': False},
}
ALL_PROJECT_APPS.update(PROJECT_MAIN_APPS)
