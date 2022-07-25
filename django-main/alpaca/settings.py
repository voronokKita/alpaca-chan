"""
Django settings for Alpaca-chan project.

Generated by 'django-admin startproject' using Django 4.0.4.

For more information on this file, see
https://docs.djangoproject.com/en/4.0/topics/settings/

For the full list of settings and their values, see
https://docs.djangoproject.com/en/4.0/ref/settings/

As a security measure, Django will exclude from debug pages any setting
whose name partial includes any of the following:
'API', 'KEY', 'PASS', 'SECRET', 'SIGNATURE', 'TOKEN'
"""
import sys
import secrets
from pathlib import Path


BASE_DIR = Path(__file__).resolve().parent.parent
PROJECT_ROOT_DIR = BASE_DIR.parent
PROJECT_APPLICATIONS = PROJECT_ROOT_DIR / 'applications'
for app in PROJECT_APPLICATIONS.iterdir():
    if str(app) not in sys.path:
        sys.path.append(str(app))


# <development settings>
# Deployment checklist https://docs.djangoproject.com/en/4.0/howto/deployment/checklist/
DEBUG = True

# If DEBUG is False, you also need to properly set the ALLOWED_HOSTS setting
ALLOWED_HOSTS = ['example.com', 'test.com', 'localhost', '127.0.0.1', '[::1]']

INTERNAL_IPS = ['127.0.0.1']

# SECURITY WARNING: keep the secret key used in production secret!
# https://docs.djangoproject.com/en/4.0/ref/settings/#secret-key
key = BASE_DIR / '.SECRET_KEY'
if key.exists():
    with open(key, 'r') as f: SECRET_KEY = f.read().strip()
else:
    print("WARNING — can't find SECRET_KEY — a random token will be generated.")
    SECRET_KEY = secrets.token_urlsafe(49)
del key
# </development settings>


# <application definition>
# https://docs.djangoproject.com/en/4.0/ref/applications/
ROOT_URLCONF = 'alpaca.urls'

WSGI_APPLICATION = 'alpaca.wsgi.application'

INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'django.contrib.staticfiles',
    'debug_toolbar',
    'polls.apps.PollsConfig',
    'encyclopedia.apps.EncyclopediaConfig',
    'accounts.apps.AccountsConfig',
    'auctions.apps.AuctionsConfig',
]
MIDDLEWARE = [
    'django.middleware.security.SecurityMiddleware',
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
    'debug_toolbar.middleware.DebugToolbarMiddleware'
]
TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [BASE_DIR / 'templates'],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]
# https://docs.djangoproject.com/en/4.0/howto/static-files/
# https://docs.djangoproject.com/en/4.0/ref/settings/#static-files
# https://docs.djangoproject.com/en/4.0/howto/static-files/deployment/
STATIC_URL = 'static/'
STATIC_ROOT = BASE_DIR / 'static_for_deployment'
STATICFILES_DIRS = [
    BASE_DIR / 'static',
]
# File upload
# https://docs.djangoproject.com/en/4.0/topics/files/
MEDIA_URL = 'media/'
MEDIA_ROOT = BASE_DIR / 'media'
# </application definition>


# <database>
# https://docs.djangoproject.com/en/4.0/ref/settings/#databases
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': BASE_DIR / 'django-main.sqlite3',
        'TIME_ZONE': 'Europe/Moscow',
        'TEST': {
            'NAME': None,
            'DEPENDENCIES': [],
        },
    },
    'polls_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': PROJECT_APPLICATIONS / 'django-polls' / 'polls.sqlite3',
        'TIME_ZONE': 'Europe/Moscow',
        'TEST': {
            'NAME': None,
            'DEPENDENCIES': []
        },
    },
    'encyclopedia_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': PROJECT_APPLICATIONS / 'django-cs50web-wiki' / 'encyclopedia.sqlite3',
        'TIME_ZONE': 'Europe/Moscow',
        'TEST': {
            'NAME': None,
            'DEPENDENCIES': []
        },
    },
    'auctions_db': {
        'ENGINE': 'django.db.backends.sqlite3',
        'NAME': PROJECT_APPLICATIONS / 'django-cs50web-commerce' / 'auctions.sqlite3',
        'TIME_ZONE': 'Europe/Moscow',
        'TEST': {
            'NAME': None,
            'DEPENDENCIES': []
        },
    }
}
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# https://docs.djangoproject.com/en/4.0/topics/db/multi-db/#topics-db-multi-db-routing
DATABASE_ROUTERS = [
    'polls.db_router.PollsRouter',
    'encyclopedia.db_router.WikiRouter',
    'auctions.db_router.CommerceRouter',
]
# </database>


# <password>
# https://docs.djangoproject.com/en/4.0/topics/auth/passwords/#password-validation
AUTH_PASSWORD_VALIDATORS = [
    {'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator'},
    # {'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator'},
    {'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator'},
]
# </password>


# <sessions>
# https://docs.djangoproject.com/en/4.0/ref/settings/#sessions
# </sessions>


# <internationalization>
# https://docs.djangoproject.com/en/4.0/topics/i18n/
LANGUAGE_COOKIE_SECURE = True

LANGUAGE_CODE = 'en-us'
USE_L10N = False

DEFAULT_CHARSET = 'utf-8'

TIME_ZONE = 'Europe/Moscow'
USE_I18N = True
USE_TZ = True

DATE_FORMAT = 'Y.n.j'
TIME_FORMAT = 'G:i:s'
DATETIME_FORMAT = 'Y.n.j G:i:s'
SHORT_DATE_FORMAT = 'Y.n.j P'
# </internationalization>


# <logging>
# https://docs.djangoproject.com/en/4.0/ref/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'polls': {
            'handlers': ['polls_file', 'console_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'encyclopedia': {
            'handlers': ['encyclopedia_file', 'console_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'accounts': {
            'handlers': ['accounts_file', 'console_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'auctions': {
            'handlers': ['auctions_file', 'console_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'django': {
            'handlers': ['console', 'django_main_file'],
            'level': 'INFO',
        },
        'django.server': {
            'handlers': ['django.server', 'django_main_file'],
            'level': 'INFO',
            'propagate': False,
        },
        '': {
            'handlers': ['detail_errors_file'],
            'level': 'ERROR',
        }
    },
    'handlers': {
        'polls_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': PROJECT_APPLICATIONS / 'django-polls' / 'polls.log',
            'formatter': 'file',
        },
        'encyclopedia_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': PROJECT_APPLICATIONS / 'django-cs50web-wiki' / 'encyclopedia.log',
            'formatter': 'file',
        },
        'accounts_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': PROJECT_APPLICATIONS / 'django-accounts' / 'accounts.log',
            'formatter': 'file',
        },
        'auctions_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': PROJECT_APPLICATIONS / 'django-cs50web-commerce' / 'auctions.log',
            'formatter': 'file',
        },
        'django_main_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'django-main.log',
            'formatter': 'file',
        },
        'detail_errors_file': {
            'level': 'ERROR',
            'class': 'logging.FileHandler',
            'filename': BASE_DIR / 'detail-errors.log',
            'formatter': 'file_errors',
        },
        'console_debug': {
            'level': 'DEBUG',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
            'formatter': 'console_debug',
        },
        'console': {
            'level': 'INFO',
            'filters': ['require_debug_true'],
            'class': 'logging.StreamHandler',
        },
        'django.server': {
            'level': 'INFO',
            'class': 'logging.StreamHandler',
            'formatter': 'django.server',
        },
        'mail_admins': {
            'level': 'ERROR',
            'filters': ['require_debug_false'],
            'class': 'django.utils.log.AdminEmailHandler'
        },
    },
    'formatters': {
        'file': {
            'format': '[{levelname}] {asctime} {message}',
            'style': '{',
        },
        'file_errors': {
            'format': '\n[{levelname}] {asctime} ~/mdl-{module}/func-{funcName}/line-{lineno}\n'
                      '[MESSAGE] {message}\n'
                      '[EXC_INFO] {exc_info}\n'
                      '[STACK_INFO] {stack_info}\n',
            'style': '{',
        },
        'console_debug': {
            'format': '!>> {message} <<!',
            'style': '{',
        },
        'django.server': {
            '()': 'django.utils.log.ServerFormatter',
            'format': '[{server_time}] {message}',
            'style': '{',
        },
    },
    'filters': {
        'require_debug_false': {
            '()': 'django.utils.log.RequireDebugFalse',
        },
        'require_debug_true': {
            '()': 'django.utils.log.RequireDebugTrue',
        },
    },
}
# </logging>


# <misc>
APPEND_SLASH = False
CSRF_COOKIE_SECURE = True
# </misc>
