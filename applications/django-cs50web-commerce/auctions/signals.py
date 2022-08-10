from django.contrib.auth.models import User

from .models import Profile


def user_saved_signal(instance, created, **kwargs):
    if created is True:
        p = Profile(username=instance.username)
        p.save(date_joined=instance.date_joined)


def user_pre_saved_signal(instance, **kwargs):
    if not instance.pk:
        return
    else:
        old_user_entry = User.objects.get(pk=instance.pk)

    if old_user_entry.username == instance.username:
        return
    elif not Profile.manager.filter(username=old_user_entry.username).exists():
        return
    else:
        profile = Profile.manager.get(username=old_user_entry.username)
        profile.username = instance.username
        profile.save(update_fields=['username'])


def user_pre_delete_signal(instance, **kwargs):
    p = Profile.manager.get(username=instance.username)
    p.delete()
