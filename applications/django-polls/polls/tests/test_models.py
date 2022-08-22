import datetime

from django.test import TestCase
from django.utils import timezone

from polls.models import Question, Choice
from .tests import DB, create_question


class QuestionAndChoiceModelTests(TestCase):
    databases = [DB]

    def test_was_published_recently_with_future_question(self):
        future_question = create_question('Future Question?', days=1)
        self.assertIs(future_question.published_recently(), False)

    def test_was_published_recently_with_old_question(self):
        pub_date = timezone.localtime() - datetime.timedelta(days=1, seconds=1)
        old_question = Question(question_text='Old Question?', pub_date=pub_date)
        self.assertIs(old_question.published_recently(), False)

    def test_was_published_recently_with_recent_question(self):
        pub_date = timezone.localtime() - datetime.timedelta(hours=23, minutes=59, seconds=59)
        recent_question = Question(question_text='Recent Question?', pub_date=pub_date)
        self.assertIs(recent_question.published_recently(), True)

    def test_models_integrity(self):
        question = create_question('Integrity Question?')
        choice1 = Choice.manager.create(question=question, choice_text='Choice #1')
        choice2 = Choice.manager.create(question=question, choice_text='Choice #2')
        question.refresh_from_db()
        queryset = question.choice_set.all()
        self.assertIn(choice1, queryset)
        self.assertIn(choice2, queryset)
