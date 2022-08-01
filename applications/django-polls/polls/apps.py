import sys
from django.apps import AppConfig
from django.db.models.signals import post_save


class PollsConfig(AppConfig):
    name = 'polls'

    def ready(self):
        if 'test' not in sys.argv:
            from .logs import log_model_updated
            post_save.connect(log_model_updated, sender='polls.Choice')
