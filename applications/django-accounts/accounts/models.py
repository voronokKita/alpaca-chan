from django.db import models
from django.contrib.auth.models import User


class ProxyUser(User):
    """ Interface to the main User model. """
    manager = models.Manager()

    class Meta:
        proxy = True
        db_table = 'proxy_user'
        verbose_name = 'persona'
        verbose_name_plural = 'persons'
        ordering = ['username']

    def __str__(self): return self.username
