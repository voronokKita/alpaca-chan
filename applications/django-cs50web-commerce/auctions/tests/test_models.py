import datetime

from django.conf import settings
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.hashers import make_password

from django.contrib.auth.models import User
from auctions.models import Profile

""" 
ⓘ The application folder must be added to the "sources" 
for PyCharm to stop swearing on the models import.
"""
SECOND_DB = settings.PROJECT_MAIN_APPS['auctions']['db']['name']
PASSWORD_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']


class UserProfileTests(TestCase):
    databases = ['default', SECOND_DB]

    def test_new_user_creates_new_profile_in_correct_db(self):
        User.objects.create(username='user1')
        self.assertQuerysetEqual(
            User.objects.db_manager(SECOND_DB).filter(username='user1'), []
        )
        self.assertTrue(
            len(User.objects.db_manager('default').filter(username='user1')) == 1
        )

        self.assertTrue(
            len(Profile.manager.db_manager(SECOND_DB).filter(username='user1')) == 1
        )
        try: Profile.manager.db_manager('default').get(username='user1')
        except Exception: pass
        else: raise Exception('found profile on defaults db')
