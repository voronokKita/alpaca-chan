from django.test import TestCase, override_settings
from django.urls import reverse
from django.contrib.auth.hashers import make_password

from accounts.models import ProxyUser
from polls.models import Choice
from polls.forms import ChoiceSetForm
from .tests import DB, PASSWORD_HASHER, create_question, check_default_navbar


class PollsIndexViewTests(TestCase):
    databases = ['default', DB]

    def test_no_questions(self):
        """ If no questions exist, an appropriate message is displayed. """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No polls are available.')
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_question(self):
        """ The questions index page may display questions. """
        question = create_question(question_text='Index Question?')
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [question]
        )

    def test_past_question(self):
        """ Questions with a pub_date in the past are displayed on the index page. """
        question1 = create_question(question_text='Past question 1?', days=-10)
        question2 = create_question(question_text='Past question 2?', days=-30)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [question1, question2]
        )

    def test_future_question(self):
        """ Questions with a pub_date in the future aren't displayed on the index page. """
        create_question(question_text='Future question 1?', days=1)
        create_question(question_text='Future question 2?', days=30)

        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, 'No polls are available.')
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """ Even if both past and future questions exist, only past questions are displayed. """
        question = create_question(question_text='Past question?', days=-1)
        create_question(question_text='Future question?', days=1)

        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [question]
        )

    @override_settings(PASSWORD_HASHERS=PASSWORD_HASHER)
    def test_polls_navbar(self):
        response_anon = self.client.get(reverse('polls:index'))
        self.assertContains(response_anon, 'Alpaca’s Cafe')
        self.assertContains(response_anon, 'Register')
        self.assertContains(response_anon, 'Login')

        ProxyUser.manager.create(username='Sunaneko', password=make_password('qwerty'))
        self.client.login(username='Sunaneko', password='qwerty')
        response_user = self.client.get(reverse('polls:index'))
        self.assertContains(response_user, 'Sunaneko')
        self.assertContains(response_user, 'Logout')


class PollsDetailViewTests(TestCase):
    databases = [DB]

    def test_future_question(self):
        """ The detail view of a question with a pub_date in the future returns a 404 not found. """
        future_question = create_question(question_text='Future question?', days=1)
        url = reverse('polls:detail', args=(future_question.pk,))

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """ The detail view of a question with a pub_date in the past displays the question's text. """
        past_question = create_question(question_text='Detail Past Question?', days=-1)
        url = reverse('polls:detail', args=(past_question.pk,))

        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)
        self.assertEqual(type(response.context['form']), ChoiceSetForm)

    def test_choice_set(self):
        """ The detail view of a question displays the question's choices. """
        question = create_question(question_text='Question Choices?')
        choice1 = Choice.manager.create(question=question, choice_text='Choice #1')
        choice2 = Choice.manager.create(question=question, choice_text='Choice #2')
        url = reverse('polls:detail', args=[question.pk])

        response = self.client.get(url)
        self.assertContains(response, choice1.choice_text)
        self.assertContains(response, choice2.choice_text)

    def test_detail_navbar(self):
        check_default_navbar(self, 'detail')


class PollsResultsTests(TestCase):
    databases = [DB]

    def test_future_question(self):
        """ The results view of a question with a pub_date in the future returns a 404 not found. """
        future_question = create_question(question_text='Future question?', days=1)
        url = reverse('polls:results', args=[future_question.pk])

        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_normal_case(self):
        """ The results view may display questions. """
        question = create_question(question_text='Question?')
        choice1 = Choice.manager.create(question=question, choice_text='Choice #1')
        choice2 = Choice.manager.create(question=question, choice_text='Choice #2')
        url = reverse('polls:results', args=[question.pk])

        response = self.client.get(url)
        self.assertContains(response, question.question_text)
        self.assertContains(response, choice1.choice_text)
        self.assertContains(response, choice2.choice_text)

    def test_results_navbar(self):
        check_default_navbar(self, 'results')
