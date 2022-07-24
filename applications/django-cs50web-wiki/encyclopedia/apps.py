from django.apps import AppConfig
from django.db.models.signals import post_save
from django.db.models.signals import post_delete


class EncyclopediaConfig(AppConfig):
    name = 'encyclopedia'

    def ready(self):
        from .logs import log_model_create_or_update, log_model_delete
        post_save.connect(log_model_create_or_update, sender='encyclopedia.Entry')
        post_delete.connect(log_model_delete, sender='encyclopedia.Entry')
