from django.test import TestCase

from django.contrib.auth.models import User
from accounts.models import ProxyUser


class ProxyUserModelTests(TestCase):
    databases = ['default']

    def test_entry_normal_case(self):
        """ Test that the proxy model is working fine. """
        user = ProxyUser.manager.create(
            username='Rockhopper', first_name='Iwatobi', last_name='the Penguin',
            email='rockhopper@japaripark.int', is_staff=True, password='qwerty'
        )
        self.assertTrue(User.objects.filter(username='Rockhopper').exists())
        self.assertEqual(user.get_full_name(), 'Iwatobi the Penguin')
        self.assertEqual(user.get_short_name(), 'Iwatobi')
        self.assertEqual(user.get_username(), 'Rockhopper')
