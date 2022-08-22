import os
import sys
from django.apps import AppConfig


class AccountsConfig(AppConfig):
    name = 'accounts'

    def ready(self):
        if os.environ.get('RUN_MAIN') != 'true' and 'test' not in sys.argv:
            from django.db.models.signals import post_save, post_delete
            from .logs import log_proxy_user_save, log_proxy_user_delete
            from .models import ProxyUser
            post_save.connect(log_proxy_user_save, sender=ProxyUser, dispatch_uid='proxy-save')
            post_delete.connect(log_proxy_user_delete, sender=ProxyUser, dispatch_uid='proxy-delete')
