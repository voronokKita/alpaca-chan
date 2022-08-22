import datetime

from django.test import SimpleTestCase
from django.utils import timezone
from django.urls import reverse
from django.conf import settings

from polls.models import Question

""" TODO
+ form test
+ model tests
+ index page
+ detail page
  + detail form
+ results page
+ check resources
+ check navbar
"""
DB = settings.PROJECT_MAIN_APPS['polls']['db']['name']
PASSWORD_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']


def create_question(question_text, days=0):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    localtime = timezone.localtime()
    pub_date = localtime + datetime.timedelta(days=days) if days else localtime
    return Question.manager.create(question_text=question_text, pub_date=pub_date)


def check_default_navbar(object_, path_name):
    """ Will make a new article if [slug] is passed. """
    q = create_question('What is love?')
    response = object_.client.get(reverse(f'polls:{path_name}', args=[q.pk]))
    from polls.views import NavbarMixin
    navbar_list = NavbarMixin._get_default_nav()
    for ell in navbar_list:
        object_.assertContains(response, ell['text'])


class PollsResourcesTests(SimpleTestCase):
    """ Check that I didn't miss anything. """
    app_dir = settings.PROJECT_MAIN_APPS['polls']['app_dir']
    resources = [
        app_dir / 'readme.md',
        app_dir / 'polls' / 'db_router.py',
        app_dir / 'polls' / 'logs.py',
        app_dir / 'polls' / 'static' / 'polls' / 'favicon.ico',
        app_dir / 'polls' / 'static' / 'polls' / 'logo.jpg',
        app_dir / 'polls' / 'templates' / 'polls' / 'base_polls.html',
    ]

    def test_base_resources_exists(self):
        from polls.db_router import PollsRouter
        for item in self.resources:
            self.assertTrue(item.exists(), msg=item)
