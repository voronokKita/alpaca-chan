from django.conf import settings
from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.hashers import make_password

from accounts.models import ProxyUser
from .tests import PASSWORD_HASHER


class CoreIndexViewTests(TestCase):
    databases = ['default']

    def test_index_loads(self):
        """ The index page loads and is displaying apps. """
        response = self.client.get(reverse('core:index'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(len(response.context['main_app_list']),
                         len(settings.PROJECT_MAIN_APPS))
        for card in response.context['main_app_list']:
            self.assertIn(card['app_name'], settings.PROJECT_MAIN_APPS, card['app_name'])

    @override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
    def test_core_navbar(self):
        response_anon = self.client.get(reverse('core:index'))
        self.assertContains(response_anon, 'Register')
        self.assertContains(response_anon, 'Login')

        ProxyUser.manager.create(username='Gingitsune', password=make_password('qwerty'))
        login = self.client.login(username='Gingitsune', password='qwerty')
        response_user = self.client.get(reverse('core:index'))
        self.assertContains(response_user, 'Gingitsune')
        self.assertContains(response_user, 'Logout')


class ProjectBaseIntegrityTests(TestCase):
    databases = '__all__'

    def test_index_loads(self):
        """ The index view of all the apps loads well? """
        url_patterns = [f'{app}:index' for app in settings.ALL_PROJECT_APPS]
        url_patterns.append('admin:login')
        for pattern in url_patterns:
            response = self.client.get(reverse(pattern))
            self.assertEqual(response.status_code, 200, msg=pattern)
