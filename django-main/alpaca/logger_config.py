from .presets import DEBUG, BASE_DIR, ALL_PROJECT_APPS


# https://docs.djangoproject.com/en/4.0/ref/logging/
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'loggers': {
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
for app in ALL_PROJECT_APPS:
    app_handler_name = f'{app}_app_file'
    logger = {
        app: {
            'handlers': [app_handler_name, 'console_debug'],
            'level': 'DEBUG' if DEBUG else 'INFO',
        }
    }
    handler = {
        app_handler_name: {
            'level': 'INFO',
            'class': 'logging.FileHandler',
            'filename': ALL_PROJECT_APPS[app]['app_dir'] / f'{app}.log',
            'formatter': 'file',
        }
    }
    LOGGING['loggers'].update(logger)
    LOGGING['handlers'].update(handler)
