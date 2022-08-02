from django.test import TestCase
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.hashers import make_password

from django.contrib.auth.models import User
from .models import ProxyUser
from .forms import UserLoginForm, UserRegisterForm


# + proxy user model
# + forms
# + index page
# + login & logout
# + register page
#   + register a new user
# + redirections
# + check resources

DB = ['default', settings.PROJECT_MAIN_APPS['polls']['db']['name']]


class ProxyUserModelTests(TestCase):
    def test_entry_normal_case(self):
        """ Test that the proxy model is working fine. """
        user = ProxyUser.objects.create(
            username='Rockhopper', first_name='Iwatobi', last_name='the Penguin',
            email='rockhopper@japaripark.int', is_staff=True, password='qwerty'
        )
        self.assertTrue(User.objects.filter(username='Rockhopper').exists())
        self.assertEqual(user.get_full_name(), 'Iwatobi the Penguin')
        self.assertEqual(user.get_short_name(), 'Iwatobi')
        self.assertEqual(user.get_username(), 'Rockhopper')


class UserRegisterFormTests(TestCase):
    def test_register_form_normal_case(self):
        form_data = {
            'username': 'Hululu',
            'first_name': 'Humboldt',
            'last_name': 'the Penguin',
            'email': 'hululu@japaripark.int',
            'password1': 'qwerty',
            'password2': 'qwerty'
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(User.objects.filter(username='Hululu').exists())

    def test_register_form_optional_parameters(self):
        form_data = {
            'username': 'Princess',
            'password1': 'qwerty',
            'password2': 'qwerty'
        }
        form = UserRegisterForm(data=form_data)
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(User.objects.filter(username='Princess').exists())

    def test_register_form_errors(self):
        errors = [
            {'username': 'Gentoo'},
            {'username': 'Koutei', 'password1': 'qwerty'},
            {'username': 'Margay', 'password2': 'qwerty'},
        ]
        for err in errors:
            form = UserRegisterForm(data=err)
            self.assertFalse(form.is_valid())


class UserLoginFormTests(TestCase):
    def test_login_form_normal_case(self):
        user = ProxyUser.objects.create(username='Tsuchinoko',
                                        password=make_password('qwerty'))
        form_data = {'username': 'Tsuchinoko', 'password': 'qwerty'}
        form = UserLoginForm(data=form_data)
        self.assertTrue(form.is_valid())


class AccountsIndexViewTests(TestCase):
    def test_page_access(self):
        response = self.client.get(reverse('accounts:index'))
        self.assertEqual(response.status_code, 200)


class AccountsLoginViewTests(TestCase):

    def test_login_page_loads(self):
        response = self.client.get(reverse('accounts:login'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response.context['form']), UserLoginForm)

    def test_login_normal(self):
        """ Login process works well? """
        self.user = ProxyUser.objects.create(username='Toki-chan',
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


class AccountsLogoutViewTests(TestCase):
    def test_logout_page_redirects_anonymous(self):
        response = self.client.get(reverse('accounts:logout'))
        self.assertRedirects(response, reverse('core:index'), 302)

    def test_logout_normal(self):
        """ Logout process works well? """
        self.user = ProxyUser.objects.create(username='Tairikuookami',
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


class AccountsLoginLogoutIntegrityTests(TestCase):
    databases = DB

    def test_login_and_logout_redirects_back_to_app(self):
        user = ProxyUser.objects.create(username='Kitakitsune',
                                        password=make_password('qwerty'))
        response_login = self.client.post(
            reverse('accounts:login', args=['polls']),
            data={'username': 'Kitakitsune',
                  'password': 'qwerty'}
        )
        self.assertRedirects(response_login, reverse('polls:index'))
        response_get_login = self.client.get(reverse('core:index'))
        self.assertTrue(response_get_login.context['user'].is_authenticated)

        response_logout = self.client.get(reverse('accounts:logout', args=['polls']))
        self.assertRedirects(response_logout, reverse('polls:index'))
        response_get_logout = self.client.get(reverse('core:index'))
        self.assertFalse(response_get_logout.context['user'].is_authenticated)


class AccountsRegisterViewTests(TestCase):
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


class AccountsRegisterIntegrityTests(TestCase):
    databases = DB

    def test_register_redirects_back_to_app(self):
        response_register = self.client.post(
            reverse('accounts:register', args=['polls']),
            data={'username': 'Fennec-chan',
                  'password1': 'qwerty',
                  'password2': 'qwerty'}
        )
        self.assertRedirects(response_register, reverse('polls:index'))
        self.assertTrue(User.objects.filter(username='Fennec-chan').exists())
        response_get_register = self.client.get(reverse('core:index'))
        self.assertTrue(response_get_register.context['user'].is_authenticated)


class AccountsResourcesTests(TestCase):
    app_dir = settings.ALL_PROJECT_APPS['accounts']['app_dir']
    resources = [
        app_dir / 'readme.md',
        app_dir / 'accounts' / 'logs.py',
        app_dir / 'accounts' / 'static' / 'accounts' / 'favicon.ico',
        app_dir / 'accounts' / 'templates' / 'accounts' / 'base_accounts.html',
    ]
    def test_base_resources_exists(self):
        """ Check that I didn't miss anything. """
        for item in self.resources:
            self.assertTrue(item.exists(), msg=item)
