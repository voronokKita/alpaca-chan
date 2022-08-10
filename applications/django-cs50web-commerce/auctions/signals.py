from auctions.models import Profile


def new_user_saved_signal(instance, created, **kwargs):
    if created is True:
        p = Profile(username=instance.username)
        p.save(date_joined=instance.date_joined)


def user_pre_delete_signal(instance, **kwargs):
    p = Profile.manager.get(username=instance.username)
    p.delete()
