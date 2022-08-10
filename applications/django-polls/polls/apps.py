from django.apps import AppConfig


class PollsConfig(AppConfig):
    name = 'polls'

    def ready(self):
        import sys
        if 'test' not in sys.argv:
            from django.db.models.signals import post_save
            from .logs import log_choice_save
            from .models import Choice
            post_save.connect(log_choice_save, sender=Choice, dispatch_uid='choice-save')
