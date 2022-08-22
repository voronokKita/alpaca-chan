import os
import sys
from django.apps import AppConfig


class EncyclopediaConfig(AppConfig):
    name = 'encyclopedia'

    def ready(self):
        if os.environ.get('RUN_MAIN') != 'true' and 'test' not in sys.argv:
            from django.db.models.signals import post_save, post_delete
            from .logs import log_entry_save, log_entry_delete
            from .models import Entry
            post_save.connect(log_entry_save, sender=Entry, dispatch_uid='entry-save')
            post_delete.connect(log_entry_delete, sender=Entry, dispatch_uid='entry-update')
