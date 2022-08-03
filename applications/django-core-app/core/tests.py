from django.conf import settings
from django.test import TestCase
from django.urls import reverse
from django.contrib.auth.hashers import make_password
from django.contrib.auth.models import User


# + resources check
# + core index page
# + integrity tests
#   + list of applications test
#   + project resources check
# + check navbar

DB = ['default']
for appname in settings.PROJECT_MAIN_APPS:
    DB.append(settings.PROJECT_MAIN_APPS[appname]['db']['name'])


class CoreResourcesTests(TestCase):
    app_dir = settings.ALL_PROJECT_APPS['core']['app_dir']
    resources = [
        app_dir / 'readme.md',
        app_dir / 'core' / 'static' / 'core' / 'favicon.ico',
        app_dir / 'core' / 'templates' / 'core' / 'base_core.html',
        app_dir / 'core' / 'templatetags' / 'active_nav_tag.py',
    ]

    def test_base_resources_exists(self):
        """ Check that I didn't miss anything. """
        for item in self.resources:
            self.assertTrue(item.exists(), msg=item)


class ProjectResourcesTests(TestCase):
    prjct_dir = settings.PROJECT_ROOT_DIR
    prjct_resources = [
        prjct_dir / 'Pipfile',
        prjct_dir / 'Development History.md',
        prjct_dir / 'Alpaca-chan.jpg',
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
        """ Check that I didn't miss anything. """
        for item in self.prjct_resources + self.base_resources:
            self.assertTrue(item.exists(), msg=item)
        for app in self.main_apps:
            self.assertTrue(self.main_apps[app]['app_dir'].exists(), msg=app)


class CoreIndexViewTests(TestCase):
    def test_index_loads(self):
        """ The index page loads and is displaying apps. """
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['main_app_list']),
                         len(settings.PROJECT_MAIN_APPS))
        for card in response.context['main_app_list']:
            self.assertIn(card['app_name'], settings.PROJECT_MAIN_APPS, card['app_name'])

    def test_core_navbar(self):
        response_anon = self.client.get(reverse('core:index'))
        self.assertContains(response_anon, 'Register')
        self.assertContains(response_anon, 'Login')

        User.objects.create(username='Gingitsune', password=make_password('qwerty'))
        login = self.client.login(username='Gingitsune', password='qwerty')
        response_user = self.client.get(reverse('core:index'))
        self.assertContains(response_user, 'Gingitsune')
        self.assertContains(response_user, 'Logout')


class ProjectBaseIntegrityTests(TestCase):
    databases = DB
    def test_index_loads(self):
        """ The index view of all the apps loads well? """
        url_patterns = [f'{app}:index' for app in settings.ALL_PROJECT_APPS]
        url_patterns.append('admin:login')
        for pattern in url_patterns:
            response = self.client.get(reverse(pattern))
            self.assertEqual(response.status_code, 200, msg=pattern)
