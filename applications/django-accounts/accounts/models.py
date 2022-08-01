from django.contrib.auth.models import User


class ProxyUser(User):
    """ Used as a simple hook. """
    def __str__(self): return self.username

    class Meta:
        proxy = True
        ordering = ['first_name', 'username']
