from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.hashers import make_password

from django.contrib.auth.models import User
from accounts.models import ProxyUser
from accounts.forms import UserLoginForm, UserRegisterForm
from .tests import SECOND_DB, PASSWORD_HASHER


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
class AccountsIndexViewTests(TestCase):
    databases = ['default']

    def test_page_access(self):
        response = self.client.get(reverse('accounts:index'))
        self.assertEqual(response.status_code, 200)

    def test_accounts_navbar(self):
        response_anon = self.client.get(reverse('accounts:index'))
        self.assertContains(response_anon, 'Alpaca’s Cafe')
        self.assertContains(response_anon, 'Register')
        self.assertContains(response_anon, 'Login')

        ProxyUser.manager.create(username='Hashibirokou', password=make_password('qwerty'))
        self.client.login(username='Hashibirokou', password='qwerty')
        response_user = self.client.get(reverse('accounts:index'))
        self.assertContains(response_user, 'Hashibirokou')
        self.assertContains(response_user, 'Logout')


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
class AccountsLoginViewTests(TestCase):
    databases = ['default']

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response.context['form']), UserLoginForm)

    def test_login_normal(self):
        """ Login process works well? """
        self.user = ProxyUser.manager.create(username='Toki-chan',
                                             password=make_password('qwerty'))
        response_post = self.client.post(
            reverse('accounts:login'),
            data={'username': 'Toki-chan',
                  'password': 'qwerty'}
        )
        self.assertRedirects(response_post, reverse('core:index'))
        response_get = self.client.get(reverse('core:index'))
        self.assertTrue(response_get.context['user'].is_authenticated)
        self.assertEqual(response_get.context['user'].username, 'Toki-chan')

    def test_login_error(self):
        """ You shall not pass. """
        response = self.client.post(
            reverse('accounts:login'),
            data={'username': 'Araiguma-chan', 'password': 'qwerty'}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Please enter a correct username and password.')

        response = self.client.post(reverse('accounts:login'),
                                    data={'username': 'Araiguma-chan'})
        self.assertContains(response, 'This field is required.')


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
class AccountsLogoutViewTests(TestCase):
    databases = ['default']

    def test_logout_page_redirects_anonymous(self):
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('core:index'), 302)

    def test_logout_normal(self):
        """ Logout process works well? """
        self.user = ProxyUser.manager.create(username='Tairikuookami',
                                             password=make_password('qwerty'))
        response_login = self.client.post(
            reverse('accounts:login'),
            data={'username': 'Tairikuookami',
                  'password': 'qwerty'}
        )
        self.assertRedirects(response_login, reverse('core:index'))
        response_get_login = self.client.get(reverse('core:index'))
        self.assertTrue(response_get_login.context['user'].is_authenticated)

        response_logout = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response_logout, reverse('core:index'))
        response_get_logout = self.client.get(reverse('core:index'))
        self.assertFalse(response_get_logout.context['user'].is_authenticated)


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
class AccountsLoginLogoutIntegrityTests(TestCase):
    databases = ['default', SECOND_DB]

    def test_login_and_logout_redirects_back_to_app(self):
        user = ProxyUser.manager.create(username='Kitakitsune',
                                        password=make_password('qwerty'))
        response_login = self.client.post(
            reverse('accounts:login_and_next', args=['polls']),
            data={'username': 'Kitakitsune',
                  'password': 'qwerty'}
        )
        self.assertRedirects(response_login, reverse('polls:index'))
        response_get_login = self.client.get(reverse('core:index'))
        self.assertTrue(response_get_login.context['user'].is_authenticated)

        response_logout = self.client.get(reverse('accounts:logout_and_next', args=['polls']))
        self.assertRedirects(response_logout, reverse('polls:index'))
        response_get_logout = self.client.get(reverse('core:index'))
        self.assertFalse(response_get_logout.context['user'].is_authenticated)


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
class AccountsRegisterViewTests(TestCase):
    databases = ['default']

    def test_register_page_loads(self):
        response = self.client.get(reverse('accounts:register'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response.context['form']), UserRegisterForm)

    def test_register_normal(self):
        """ Register process works well? """
        response_post = self.client.post(
            reverse('accounts:register'),
            data={'username': 'Kaban-chan',
                  'first_name': 'Kaban',
                  'last_name': 'Chan',
                  'email': 'kabanchan@japaripark.int',
                  'password1': 'qwerty',
                  'password2': 'qwerty'}
        )
        self.assertRedirects(response_post, reverse('core:index'))
        self.assertTrue(User.objects.filter(username='Kaban-chan').exists())
        response_get = self.client.get(reverse('core:index'))
        self.assertTrue(response_get.context['user'].is_authenticated)
        self.assertEqual(response_get.context['user'].username, 'Kaban-chan')

        self.client.get(reverse('accounts:logout'))
        self.client.post(
            reverse('accounts:register'),
            data={'username': 'Serval-chan',
                  'password1': 'qwerty',
                  'password2': 'qwerty'}
        )
        self.assertTrue(User.objects.filter(username='Serval-chan').exists())

    def test_register_errors(self):
        """ You shall not pass. """
        errors = [
            {'username': 'Araiguma-chan'},
            {'username': 'Araiguma-chan', 'password1': 'qwerty'},
            {'username': 'Araiguma-chan', 'password2': 'qwerty'},
        ]
        for err in errors:
            response = self.client.post(reverse('accounts:register'), data=err)
            self.assertEqual(response.status_code, 200)
            self.assertContains(response, 'This field is required.')


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
class AccountsRegisterIntegrityTests(TestCase):
    databases = ['default', SECOND_DB]

    def test_register_redirects_back_to_app(self):
        response_register = self.client.post(
            reverse('accounts:register_and_next', args=['polls']),
            data={'username': 'Fennec-chan',
                  'password1': 'qwerty',
                  'password2': 'qwerty'}
        )
        self.assertRedirects(response_register, reverse('polls:index'))
        self.assertTrue(User.objects.filter(username='Fennec-chan').exists())
        response_get_register = self.client.get(reverse('core:index'))
        self.assertTrue(response_get_register.context['user'].is_authenticated)
