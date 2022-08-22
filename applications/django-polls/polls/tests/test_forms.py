from django.test import TestCase
from django.urls import reverse

from polls.models import Choice
from polls.forms import ChoiceSetForm
from .tests import DB, create_question


class ChoiceSetFormTests(TestCase):
    databases = [DB]

    def test_form_normal_case(self):
        question = create_question(question_text='Form Test Question?')
        choice1 = Choice.manager.create(question=question, choice_text='Choice to', votes=0)
        form_data = {'choices': choice1.pk}

        form = ChoiceSetForm(data=form_data, instance=question)
        self.assertIn('choices', form.fields)
        self.assertTrue(form.is_valid())
        choice1.refresh_from_db()
        self.assertEqual(choice1.votes, 1)


class PollsDetailViewFormTests(TestCase):
    databases = [DB]

    def test_choice_normal(self):
        """ The detail view post method works. """
        question = create_question(question_text='Choice Form Test?')
        choice1 = Choice.manager.create(question=question, choice_text='Choice #1', votes=0)
        choice2 = Choice.manager.create(question=question, choice_text='Choice #2')

        response = self.client.post(
            reverse('polls:detail', args=[question.pk]),
            data={'choices': choice1.pk}
        )
        self.assertRedirects(response, reverse('polls:results', args=[question.pk]))
        choice1.refresh_from_db()
        self.assertEqual(choice1.votes, 1)
