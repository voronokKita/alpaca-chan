from django.test import SimpleTestCase
from django.conf import settings

""" TODO
+ proxy user model
+ forms
+ index page
+ login & logout
+ register page
  + register a new user
+ redirections
+ check resources
+ check navbar
"""
SECOND_DB = settings.PROJECT_MAIN_APPS['polls']['db']['name']
PASSWORD_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']


class AccountsResourcesTests(SimpleTestCase):
    """ Check that I didn't miss anything. """
    app_dir = settings.ALL_PROJECT_APPS['accounts']['app_dir']
    resources = [
        app_dir / 'readme.md',
        app_dir / 'accounts' / 'logs.py',
        app_dir / 'accounts' / 'static' / 'accounts' / 'favicon.ico',
        app_dir / 'accounts' / 'templates' / 'accounts' / 'base_accounts.html',
    ]
    def test_base_resources_exists(self):
        for item in self.resources:
            self.assertTrue(item.exists(), msg=item)
