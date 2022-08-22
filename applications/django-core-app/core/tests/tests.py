from django.conf import settings
from django.test import SimpleTestCase

""" TODO
+ resources check
+ core index page
+ integrity tests
  + list of applications test
  + project resources check
+ check navbar
"""
PASSWORD_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']
SIGNAL_DB = settings.PROJECT_MAIN_APPS['auctions']['db']['name']


class CoreResourcesTests(SimpleTestCase):
    """ Check that I didn't miss anything. """
    app_dir = settings.ALL_PROJECT_APPS['core']['app_dir']
    resources = [
        app_dir / 'readme.md',
        app_dir / 'core' / 'static' / 'core' / 'favicon.ico',
        app_dir / 'core' / 'templates' / 'core' / 'base_core.html',
        app_dir / 'core' / 'templatetags' / 'active_nav_tag.py',
    ]

    def test_base_resources_exists(self):
        for item in self.resources:
            self.assertTrue(item.exists(), msg=item)


class ProjectResourcesTests(SimpleTestCase):
    """ Check that I didn't miss anything. """
    prjct_dir = settings.PROJECT_ROOT_DIR
    prjct_resources = [
        prjct_dir / 'Pipfile',
        prjct_dir / 'Development History.md',
        prjct_dir / 'Alpaca-chan.jpg',
        prjct_dir / 'requirements.txt',
        prjct_dir / '.gitignore',
    ]
    base_dir = settings.BASE_DIR
    base_resources = [
        base_dir / '.SECRET_KEY',
        base_dir / 'static' / 'favicon.ico',
        base_dir / 'static' / 'base.css',
        base_dir / 'templates' / 'base.html',
        base_dir / 'templates' / '_navbar.html',
        base_dir / 'templates' / '_navbar_light.html',
        base_dir / 'templates' / '_messages.html',
    ]
    main_apps = settings.ALL_PROJECT_APPS

    def test_base_resources_exists(self):
        for item in self.prjct_resources + self.base_resources:
            self.assertTrue(item.exists(), msg=item)
        for app in self.main_apps:
            self.assertTrue(self.main_apps[app]['app_dir'].exists(), msg=app)
