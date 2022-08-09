import sys
from django.apps import AppConfig


class AuctionsConfig(AppConfig):
    name = 'auctions'

    def ready(self):
        from django.db.models.signals import post_save, pre_delete, post_delete
        from django.contrib.auth.models import User
        from .signals import new_user_signal, user_deleted_signal
        post_save.connect(new_user_signal, sender=User, dispatch_uid='user-save')
        pre_delete.connect(user_deleted_signal, sender=User, dispatch_uid='user-delete')

        if 'test' not in sys.argv:
            from auctions.models import Profile, ListingCategory, Listing, Bid
            from .logs import (
                log_profile_save, log_profile_deleted,
                log_category_save, log_bid_save, log_listing_save
            )
            post_save.connect(log_profile_save, sender=Profile, dispatch_uid='profile')
            post_delete.connect(log_profile_deleted, sender=Profile, dispatch_uid='profile-delete')
            post_save.connect(log_category_save, sender=ListingCategory, dispatch_uid='category')
            post_save.connect(log_bid_save, sender=Bid, dispatch_uid='bid')
            post_save.connect(log_listing_save, sender=Listing, dispatch_uid='listing')
