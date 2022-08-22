from django.test import TestCase

from encyclopedia.forms import EntryForm
from .tests import DB


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
