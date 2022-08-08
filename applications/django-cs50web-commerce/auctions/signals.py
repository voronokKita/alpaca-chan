from auctions.models import Profile


def new_user_signal(sender, instance, created, **kwargs):
    if created is True:
        p = Profile(username=instance.username)
        p.save(date_joined=instance.date_joined)


def user_deleted_signal(sender, instance, **kwargs):
    pass
