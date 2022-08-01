import sys
from django.apps import AppConfig
from django.db.models.signals import post_save, post_delete


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        if 'test' not in sys.argv:
            from .logs import log_model_create_or_update, log_model_delete
            post_save.connect(log_model_create_or_update, sender='accounts.ProxyUser')
            post_delete.connect(log_model_delete, sender='accounts.ProxyUser')
