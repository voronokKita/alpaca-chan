from django.apps import AppConfig


class AuctionsConfig(AppConfig):
    name = 'auctions'

    def ready(self):
        from django.db.models.signals import post_save, post_delete
        from django.contrib.auth.models import User
        from .signals import new_user_signal, user_deleted_signal
        post_save.connect(new_user_signal, sender=User, dispatch_uid='user-save')
        post_delete.connect(user_deleted_signal, sender=User, dispatch_uid='user-delete')
