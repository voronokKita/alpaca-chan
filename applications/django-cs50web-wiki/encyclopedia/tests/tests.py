from django.test import SimpleTestCase
from django.urls import reverse
from django.conf import settings

from encyclopedia.models import Entry

""" TODO
+ entry model tests
+ create/update form tests
+ index page
+ detail page
+ add new entry page
+ edit entry page
+ delete entry page
+ check resources
+ check navbar
"""
DB = settings.PROJECT_MAIN_APPS['encyclopedia']['db']['name']
PASSWORD_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']


def get_url(path_name, slug=None):
    if path_name == 'index' or path_name == 'new_entry':
        return reverse(f'encyclopedia:{path_name}')
    else:
        return reverse(f'encyclopedia:{path_name}', args=[slug])


def get_entry(slug='test-article', entry_name='Test Article', entry_text='Some text.'):
    return Entry.manager.create(slug=slug, entry_name=entry_name, entry_text=entry_text)


def check_default_navbar(object_, path_name, slug=None):
    """ Will make a new article if [slug] is passed. """
    if slug:
        get_entry(slug, 'Domine', 'de morte aeterna')
    response = object_.client.get(get_url(path_name, slug))
    from encyclopedia.views import NavbarMixin
    navbar_list = NavbarMixin._get_default_nav()
    for ell in navbar_list:
        object_.assertContains(response, ell['text'])


class WikiResourcesTests(SimpleTestCase):
    """ Check that I didn't miss anything. """
    app_dir = settings.PROJECT_MAIN_APPS['encyclopedia']['app_dir']
    resources = [
        app_dir / 'readme.md',
        app_dir / 'encyclopedia' / 'db_router.py',
        app_dir / 'encyclopedia' / 'logs.py',
        app_dir / 'encyclopedia' / 'static' / 'encyclopedia' / 'favicon.ico',
        app_dir / 'encyclopedia' / 'static' / 'encyclopedia' / 'logo.jpg',
        app_dir / 'encyclopedia' / 'templates' / 'encyclopedia' / 'base_wiki.html',
    ]

    def test_base_resources_exists(self):
        from encyclopedia.db_router import WikiRouter
        for item in self.resources:
            self.assertTrue(item.exists(), msg=item)
