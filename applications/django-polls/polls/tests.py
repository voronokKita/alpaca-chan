import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question


def create_question(question_text, days=0):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    localtime = timezone.localtime()
    pub_date = localtime + datetime.timedelta(days=days) if days else localtime
    return Question.objects.create(question_text=question_text, pub_date=pub_date)


class QuestionIndexViewTests(TestCase):
    databases = ['polls_db']

    def test_no_questions(self):
        """ If no questions exist, an appropriate message is displayed. """
        response = self.client.get(reverse('polls:index'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'No polls are available.')
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_question(self):
        """ The questions index page may display questions. """
        question = create_question(question_text='Question.')
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [question]
        )

    def test_past_question(self):
        """ Questions with a pub_date in the past are displayed on the index page. """
        question1 = create_question(question_text='Past question 1.', days=-10)
        question2 = create_question(question_text='Past question 2.', days=-30)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [question1, question2]
        )

    def test_future_question(self):
        """ Questions with a pub_date in the future aren't displayed on the index page. """
        create_question(question_text='Future question 1.', days=1)
        create_question(question_text='Future question 2.', days=30)
        response = self.client.get(reverse('polls:index'))
        self.assertContains(response, 'No polls are available.')
        self.assertQuerysetEqual(response.context['latest_question_list'], [])

    def test_future_question_and_past_question(self):
        """ Even if both past and future questions exist, only past questions are displayed. """
        question = create_question(question_text='Past question.', days=-1)
        create_question(question_text='Future question.', days=1)
        response = self.client.get(reverse('polls:index'))
        self.assertQuerysetEqual(
            response.context['latest_question_list'], [question]
        )


class QuestionDetailViewTests(TestCase):
    databases = ['polls_db']

    def test_future_question(self):
        """ The detail view of a question with a pub_date in the future returns a 404 not found. """
        future_question = create_question(question_text='Future question.', days=1)
        url = reverse('polls:detail', args=(future_question.id,))
        response = self.client.get(url)
        self.assertEqual(response.status_code, 404)

    def test_past_question(self):
        """ The detail view of a question with a pub_date in the past displays the question's text. """
        past_question = create_question(question_text='Past Question.', days=-1)
        url = reverse('polls:detail', args=(past_question.id,))
        response = self.client.get(url)
        self.assertContains(response, past_question.question_text)


class QuestionModelTests(TestCase):
    def test_was_published_recently_with_future_question(self):
        pub_date = timezone.localtime() + datetime.timedelta(days=1)
        future_question = Question(pub_date=pub_date)
        self.assertIs(future_question.published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        pub_date = timezone.localtime() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(pub_date=pub_date)
        self.assertIs(old_question.published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        pub_date = timezone.localtime() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(pub_date=pub_date)
        self.assertIs(recent_question.published_recently(), True)
