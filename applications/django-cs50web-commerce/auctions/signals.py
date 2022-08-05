from auctions.models import Profile


def new_user_signal(sender, instance, created, **kwargs):
    if created is True:
        Profile.manager.create(username=instance.username)


def user_deleted_signal(sender, instance, **kwargs):
    pass
