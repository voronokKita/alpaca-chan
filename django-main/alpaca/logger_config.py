from .presets import DEBUG, BASE_DIR, PROJECT_APPLICATIONS


# https://docs.djangoproject.com/en/4.0/ref/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
        'core': {
            'handlers': ['core_app_file', 'console_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'accounts': {
            'handlers': ['accounts_file', 'console_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'polls': {
            'handlers': ['polls_file', 'console_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        },
        'encyclopedia': {
            'handlers': ['encyclopedia_file', 'console_debug'],
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
        'core_app_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': PROJECT_APPLICATIONS / 'django-core-app' / 'core-app.log',
            'formatter': 'file',
        },
        'accounts_file': {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': PROJECT_APPLICATIONS / 'django-accounts' / 'accounts.log',
            'formatter': 'file',
        },
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
            'format': '[DEBUG] {message} [/DEBUG]',
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
