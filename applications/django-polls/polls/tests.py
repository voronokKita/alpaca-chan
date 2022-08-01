import datetime

from django.test import TestCase
from django.utils import timezone
from django.urls import reverse

from .models import Question, Choice
from .forms import ChoiceSetForm


DB = 'polls_db'


def create_question(question_text, days=0):
    """
    Create a question with the given `question_text` and published the
    given number of `days` offset to now (negative for questions published
    in the past, positive for questions that have yet to be published).
    """
    localtime = timezone.localtime()
    pub_date = localtime + datetime.timedelta(days=days) if days else localtime
    return Question.objects.create(question_text=question_text, pub_date=pub_date)


class ChoiceSetFormTests(TestCase):
    databases = [DB]

    def test_form_normal_case(self):
        question = create_question(question_text='Form Test Question?')
        choice1 = Choice.objects.create(question=question, choice_text='Choice to', votes=0)
        form_data = {'choices': choice1.pk}

        form = ChoiceSetForm(data=form_data, instance=question)
        self.assertIn('choices', form.fields)
        self.assertTrue(form.is_valid())
        choice1.refresh_from_db()
        self.assertEqual(choice1.votes, 1)


class QuestionModelTests(TestCase):
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
        choice1 = Choice.objects.create(question=question, choice_text='Choice #1')
        choice2 = Choice.objects.create(question=question, choice_text='Choice #2')
        question.refresh_from_db()
        queryset = question.choice_set.all()
        self.assertIn(choice1, queryset)
        self.assertIn(choice2, queryset)


class QuestionIndexViewTests(TestCase):
    databases = [DB]

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


class QuestionDetailViewTests(TestCase):
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
        choice1 = Choice.objects.create(question=question, choice_text='Choice #1')
        choice2 = Choice.objects.create(question=question, choice_text='Choice #2')
        url = reverse('polls:detail', args=[question.pk])

        response = self.client.get(url)
        self.assertContains(response, choice1.choice_text)
        self.assertContains(response, choice2.choice_text)


class ChoiceFormTests(TestCase):
    databases = [DB]

    def test_choice_normal(self):
        """ The detail view post method works. """
        question = create_question(question_text='Choice Form Test?')
        choice1 = Choice.objects.create(question=question, choice_text='Choice #1', votes=0)
        choice2 = Choice.objects.create(question=question, choice_text='Choice #2')

        response = self.client.post(
            reverse('polls:detail', args=[question.pk]),
            data={'choices': choice1.pk}
        )
        self.assertRedirects(response, reverse('polls:results', args=[question.pk]))
        choice1.refresh_from_db()
        self.assertEqual(choice1.votes, 1)


class QuestionResultsTests(TestCase):
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
        choice1 = Choice.objects.create(question=question, choice_text='Choice #1')
        choice2 = Choice.objects.create(question=question, choice_text='Choice #2')
        url = reverse('polls:results', args=[question.pk])

        response = self.client.get(url)
        self.assertContains(response, question.question_text)
        self.assertContains(response, choice1.choice_text)
        self.assertContains(response, choice2.choice_text)
