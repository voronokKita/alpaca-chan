from django.apps import AppConfig
from django.db.models.signals import post_save


class PollsConfig(AppConfig):
    name = 'polls'

    def ready(self):
        from .logs import log_model_updated
        post_save.connect(log_model_updated, sender='polls.Choice')
