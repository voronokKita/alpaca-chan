import markdown2

from django.test import TestCase, override_settings
from django.utils import timezone
from django.contrib.auth.hashers import make_password

from accounts.models import ProxyUser
from encyclopedia.models import Entry
from encyclopedia.forms import EntryForm, DeleteEntryForm
from .tests import DB, PASSWORD_HASHER, get_url, get_entry, check_default_navbar


class WikiIndexViewTests(TestCase):
    databases = ['default', DB]

    def test_index_no_entries(self):
        """ If no articles exist, an appropriate message is displayed. """
        expected_msg = 'No entries in wiki.'
        response = self.client.get(get_url('index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_msg)
        self.assertQuerysetEqual(response.context['wiki_entries'], [])

    def test_index_has_entries(self):
        """ The index page is displaying articles. """
        article1 = get_entry('a1', 'Article 1')
        article2 = get_entry('a2', 'Article 2')

        response = self.client.get(get_url('index'))
        self.assertQuerysetEqual(
            response.context['wiki_entries'], [article1, article2]
        )

    @override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
    def test_wiki_navbar(self):
        response_anon = self.client.get(get_url('index'))
        self.assertContains(response_anon, 'Alpaca’s Cafe')
        self.assertContains(response_anon, 'Register')
        self.assertContains(response_anon, 'Login')

        from encyclopedia.views import IndexView
        navbar_list = IndexView.extra_context['navbar_list']
        for ell in navbar_list:
            self.assertContains(response_anon, ell['text'])

        ProxyUser.manager.create(username='Mirai', password=make_password('qwerty'))
        self.client.login(username='Mirai', password='qwerty')
        response_user = self.client.get(get_url('index'))
        self.assertContains(response_user, 'Mirai')
        self.assertContains(response_user, 'Logout')


class WikiDetailViewTests(TestCase):
    databases = ['default', DB]

    def test_detail_no_entry(self):
        """ Empty page case. """
        response = self.client.get(get_url('detail', 'void-url'))
        self.assertEqual(response.status_code, 404)

    def test_detail_entry_normal(self):
        """ The detail view is displaying articles. """
        slug = 'test-detail'
        localtime = timezone.localtime()
        article = get_entry(slug, 'Libera me',
                            'Libera me, Domine, de morte aeterna, in die illa tremenda.')

        response = self.client.get(get_url('detail', slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.context['article'], article)
        self.assertIn(article.entry_text, response.context['entry_text_html'])

    def test_detail_markdown_converter(self):
        """ The detail view is converting article md-text to html-text. """
        slug = 'libera-me'
        md_text = '''## Libera me from hell
            ### first verse
            Do the impossible <br>
            See the invisible <br>
            Raw! raw! <br>
            Fight the power! <br>
            ### chorus
            * Libera me, Domine, de morte aeterna,
            * In die illa tremenda. In die illa
            * Quando coeli movendi sunt terra,
            * Dum veneris judicare saeculum per ignem.
            * Tremens factus sum ego et timeo,
            * Dum discussio venerit atque ventura ira. '''
        article = get_entry(slug, 'Libera me', md_text)

        response = self.client.get(get_url('detail', slug))
        self.assertEqual(response.context['entry_text_html'],
                         markdown2.markdown(md_text))

    def test_detail_navbar(self):
        ProxyUser.manager.create(username='Gingitsune', password=make_password('qwerty'))
        login = self.client.login(username='Gingitsune', password='qwerty')
        article = get_entry('domine', 'Domine', 'de morte aeterna')

        response = self.client.get(get_url('detail', 'domine'))

        self.assertContains(response, 'Gingitsune')
        self.assertContains(response, 'Logout')
        self.assertContains(response, article)
        self.assertContains(response, 'Domine')
        self.assertContains(response, 'Edit this article')
        self.assertContains(response, 'Delete this article')


class WikiAddNewEntryViewTests(TestCase):
    databases = [DB]

    def test_create_page_loads(self):
        """ Add-new-entry-page loads well. """
        response = self.client.get(get_url('new_entry'))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response.context['form']), EntryForm)

    def test_create_normal(self):
        """ Creating a new article works well. """
        slug = 'test-insert'
        expected_name = 'New Article'

        response = self.client.post(
            get_url('new_entry'),
            data={'slug': slug,
                  'entry_name': expected_name,
                  'entry_text': 'text'}
        )
        self.assertRedirects(response, get_url('detail', slug))
        self.assertEqual(expected_name, Entry.manager.get(slug=slug).entry_name)

    def test_create_error(self):
        """ Fake input shall not pass. """
        expected_msg = 'This field is required.'
        slug = 'insert %^+@ error'

        response = self.client.post(
            get_url('new_entry'),
            data={'slug': slug, 'entry_name': '', 'entry_text': ''}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_msg)
        self.assertFalse(Entry.manager.filter(slug=slug).exists())

    def test_new_entry_navbar(self):
        check_default_navbar(self, 'new_entry')


class WikiEditEntryViewTests(TestCase):
    databases = [DB]

    def test_update_no_entry(self):
        """ Check if no article exist. """
        response = self.client.get(get_url('edit_entry', 'void-article'))
        self.assertEqual(response.status_code, 404)

    def test_update_page_loads(self):
        """ Check that page loads well. """
        slug = 'edit-loads'
        name = 'Article'
        text = 'Some Text'
        article = get_entry(slug, name, text)

        response = self.client.get(get_url('edit_entry', slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response.context['form']), EntryForm)
        self.assertEqual(response.context['form'].initial['entry_name'], name)
        self.assertEqual(response.context['form'].initial['entry_text'], text)

    def test_update_error(self):
        """ Fake input shall not pass. """
        expected_msg = 'This field is required.'
        slug = 'edit-error'
        article = get_entry(slug)

        response = self.client.post(
            get_url('edit_entry', slug),
            data={'entry_name': '', 'entry_text': ''}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_msg)

    def test_update_normal(self):
        """ Check normal case. """
        expected_text = 'text to test'
        slug = 'article'
        article = get_entry(slug)

        response = self.client.post(
            get_url('edit_entry', slug),
            data={'entry_name': 'Article to test',
                  'entry_text': expected_text}
        )
        self.assertRedirects(response, get_url('detail', slug))
        article.refresh_from_db()
        self.assertEqual(expected_text, article.entry_text)

    def test_edit_entry_navbar(self):
        check_default_navbar(self, 'edit_entry', 'domine')


class WikiDeleteEntryViewTests(TestCase):
    databases = [DB]

    def test_delete_no_entry(self):
        """ Check if no article exist. """
        response = self.client.get(get_url('delete_entry', 'void-uri'))
        self.assertEqual(response.status_code, 404)

    def test_delete_page_loads(self):
        """ Check that page loads well. """
        slug = 'delete-loads'
        article = get_entry(slug)

        response = self.client.get(get_url('delete_entry', slug))
        self.assertEqual(response.status_code, 200)
        self.assertEqual(type(response.context['form']), DeleteEntryForm)

    def test_delete_error(self):
        """ Fake input shall not pass. """
        expected_msg = 'This field is required.'
        slug = 'delete-error'
        article = get_entry(slug)

        response = self.client.post(
            get_url('delete_entry', slug),
            data={'conform': False}
        )
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, expected_msg)
        self.assertTrue(Entry.manager.filter(slug=slug).exists())

    def test_delete_normal(self):
        """ Test normal case. """
        slug = 'test-delete'
        article = get_entry(slug)

        response = self.client.post(
            get_url('delete_entry', slug),
            data={'conform': True}
        )
        self.assertRedirects(response, get_url('index'))
        self.assertFalse(Entry.manager.filter(slug=slug).exists())

    def test_delete_entry_navbar(self):
        check_default_navbar(self, 'delete_entry', 'domine')
