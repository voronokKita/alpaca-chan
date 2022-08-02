import markdown2

from django.test import TestCase
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify

from .models import Entry
from .forms import EntryForm, DeleteEntryForm


DB = 'encyclopedia_db'


def get_url(path_name, slug=None):
    if path_name == 'index' or path_name == 'new_entry':
        return reverse(f'encyclopedia:{path_name}')
    else:
        return reverse(f'encyclopedia:{path_name}', args=[slug])


def get_entry(slug='test-article', entry_name='Test Article', entry_text='Some text.'):
    return Entry.objects.create(slug=slug, entry_name=entry_name, entry_text=entry_text)


class EntryModelTests(TestCase):
    databases = [DB]

    def test_entry_normal_case(self):
        """ Test that model is working. """
        slug = 'test-slug'
        article = get_entry(slug)
        self.assertTrue(Entry.objects.filter(slug=slug).exists())
        self.assertIsNotNone(article.pub_date)
        self.assertIsNotNone(article.upd_date)
        self.assertIn(slug, article.get_absolute_url())

    def test_entry_auto_slug(self):
        """ Test that model makes a slug automatically. """
        test_name = 'Slugify Me'
        article = Entry(entry_name=test_name, entry_text='Some text.')
        article.save()
        article.refresh_from_db()
        self.assertEqual(article.slug, slugify(test_name))


class EntryFormTests(TestCase):
    databases = [DB]

    def test_entry_form_normal_case(self):
        form_data = {'slug': 'test', 'entry_name': 'Test', 'entry_text': 'text'}
        form = EntryForm(data=form_data)
        self.assertTrue(form.is_valid())

    def test_entry_form_errors(self):
        attempts = [
            {'slug': 'correct', 'entry_name': 'Correct', 'entry_text': ''},
            {'slug': 'correct', 'entry_name': '', 'entry_text': 'Correct.'},
            {'slug': '', 'entry_name': 'Correct', 'entry_text': 'Correct.'},
            {'slug': 'wro^%# $*&+ng', 'entry_name': 'Correct', 'entry_text': 'Correct.'},
            {'slug': 'correct', 'entry_name': 'w'*200, 'entry_text': 'Correct.'},
            {'slug': 'w'*100, 'entry_name': 'Correct', 'entry_text': 'Correct.'},
        ]
        for form_data in attempts:
            form = EntryForm(data=form_data)
            self.assertFalse(form.is_valid())


class IndexViewTests(TestCase):
    databases = [DB]

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


class DetailViewTests(TestCase):
    databases = [DB]

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


class NewEntryTests(TestCase):
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
        self.assertEqual(expected_name, Entry.objects.get(slug=slug).entry_name)

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
        self.assertFalse(Entry.objects.filter(slug=slug).exists())


class EditEntryTests(TestCase):
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


class DeleteEntryTests(TestCase):
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
        self.assertTrue(Entry.objects.filter(slug=slug).exists())

    def test_delete_normal(self):
        """ Test normal case. """
        slug = 'test-delete'
        article = get_entry(slug)

        response = self.client.post(
            get_url('delete_entry', slug),
            data={'conform': True}
        )
        self.assertRedirects(response, get_url('index'))
        self.assertFalse(Entry.objects.filter(slug=slug).exists())
