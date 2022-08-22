from django.test import TestCase, override_settings
from django.contrib.auth.hashers import make_password

from django.contrib.auth.models import User
from accounts.models import ProxyUser
from accounts.forms import UserLoginForm, UserRegisterForm
from .tests import PASSWORD_HASHER


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
class UserRegisterFormTests(TestCase):
    databases = ['default']

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


@override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
class UserLoginFormTests(TestCase):
    databases = ['default']

    def test_login_form_normal_case(self):
        user = ProxyUser.manager.create(username='Tsuchinoko',
                                        password=make_password('qwerty'))
        form_data = {'username': 'Tsuchinoko', 'password': 'qwerty'}
        form = UserLoginForm(data=form_data)
        self.assertTrue(form.is_valid())
