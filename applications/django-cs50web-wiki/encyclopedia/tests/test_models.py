from django.test import TestCase
from django.utils.text import slugify

from encyclopedia.models import Entry
from .tests import DB, get_entry


class EntryModelTests(TestCase):
    databases = [DB]

    def test_entry_normal_case(self):
        """ Test that model is working. """
        slug = 'test-slug'
        article = get_entry(slug)
        self.assertTrue(Entry.manager.filter(slug=slug).exists())
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
