import os
import sys
import logging

from django.apps import AppConfig
from django.db.models.signals import pre_save, post_save, pre_delete, post_delete

logger = logging.getLogger(__name__)


class AuctionsConfig(AppConfig):
    name = 'auctions'

    def ready(self):
        if os.environ.get('RUN_MAIN') != 'true':
            from django.contrib.auth.models import User
            self._user_model_signals(User)

            if 'test' not in sys.argv:
                from .models import Profile
                users = User.objects.all()
                profiles = Profile.manager.all()

                self._logger_signals(Profile)
                self._clean_watchlist(profiles)
                self._clean_bids(profiles)
                self._user_and_profile_models_sync(User, Profile, users, profiles)

    @staticmethod
    def _user_model_signals(user_model):
        """
        The price for a separate application database is
        the need to keep User model in sync with Profile model.
        Surely there are better ways to do this... I wonder...
        I need a knowledge about large systems building.
        """
        from .signals import user_saved_signal, user_pre_saved_signal, user_pre_delete_signal
        post_save.connect(user_saved_signal, sender=user_model, dispatch_uid='user-saved')
        pre_save.connect(user_pre_saved_signal, sender=user_model, dispatch_uid='user-pre-save')
        pre_delete.connect(user_pre_delete_signal, sender=user_model, dispatch_uid='user-delete')

    @staticmethod
    def _logger_signals(profile_model):
        """ Technical logs in files about some key operations with the models. """
        from .models import ListingCategory, Listing, Bid
        from .logs import (
            log_profile_save, log_profile_deleted,
            log_category_save, log_bid_save, log_listing_save
        )
        post_save.connect(log_profile_save, sender=profile_model, dispatch_uid='profile')
        post_delete.connect(log_profile_deleted, sender=profile_model, dispatch_uid='profile-delete')
        post_save.connect(log_category_save, sender=ListingCategory, dispatch_uid='category')
        post_save.connect(log_bid_save, sender=Bid, dispatch_uid='bid')
        post_save.connect(log_listing_save, sender=Listing, dispatch_uid='listing')

    @staticmethod
    def _clean_watchlist(profiles):
        """ Ensures that profiles watching only their own listings or the auction lots. """
        for profile in profiles:
            result = profile.watchlist_set\
                .exclude(listing__owner=profile)\
                .filter(listing__is_active=False)
            if result:
                result.delete()
                logger.info(f'the profile [{profile}] had a subscription to '
                            f'unpublished items that did not belong to him')

    @staticmethod
    def _clean_bids(profiles):
        """ Ensures that profiles do not have bids placed on the unpublished items. """
        for profile in profiles:
            result = profile.bid_set.filter(lot__is_active=False)
            if result:
                for bid in result:
                    bid.delete(refund=True)
                logger.info(f'the profile [{profile}] had bids on unpublished items')

    def _user_and_profile_models_sync(self, user_model, profile_model, users, profiles):
        """ The debug mechanism for the User-Profile synchronisation. """
        users_usernames_set = set([q.username for q in users])
        profiles_usernames_set = set([q.username for q in profiles])

        if users_usernames_set != profiles_usernames_set:
            logger.critical(f'usernames do not match. '
                            f'User{users_usernames_set} Profile{profiles_usernames_set}')
            self._fix_usernames(users, profile_model)

        users_pk_set = set([q.pk for q in users])
        profiles_external_pk_set = set([q.user_model_pk for q in profiles])

        if users_pk_set != profiles_external_pk_set:
            logger.critical(f'users pks do not match. '
                            f'User{users_pk_set} Profile{profiles_external_pk_set}')
            self._fix_pks(users, profile_model)

    @staticmethod
    def _fix_usernames(users, profile_model):
        logger.critical('try to fix usernames...')
        for user in users:
            if not profile_model.manager.filter(username=user.username).exists():
                profile = profile_model.manager.filter(user_model_pk=user.pk).first()
                if profile:
                    logger.critical(f'found instance {user}-{user.pk} with profile {profile}')
                    profile.username = user.username
                    profile.save(update_fields=['username'])
                    logger.critical(f'renamed the profile to {profile}')
                else:
                    logger.critical(f'found instance {user}-{user.pk} without a profile!')

    @staticmethod
    def _fix_pks(users, profile_model):
        logger.critical('try to fix the pk problem...')
        for user in users:
            if not profile_model.manager.filter(user_model_pk=user.pk).exists():
                profile = profile_model.manager.filter(username=user.username).first()
                if profile:
                    logger.critical(f'found instance {user}-{user.pk} with profile {profile}')
                    profile.user_model_pk = user.pk
                    profile.save()
                    logger.critical(f'user.pk saved to the [{profile}]')
                else:
                    logger.critical(f'found instance {user}-{user.pk} without a profile!')
