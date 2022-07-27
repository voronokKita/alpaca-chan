import logging

from django.urls import reverse_lazy
from django.views import generic

from django.utils import timezone
from django.db.models import F

from .models import Question
from .forms import ChoiceSetForm

logger = logging.getLogger(__name__)


def get_default_nav():
    return [{'url': reverse_lazy('polls:index'), 'text': 'Polls main', 'focus': True}, ]


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        return Question.objects.filter(
            pub_date__lte=timezone.localtime()
        ).order_by('-pub_date')


class DetailView(generic.UpdateView):
    template_name = 'polls/detail.html'
    form_class = ChoiceSetForm
    model = Question
    success_url = reverse_lazy('polls:index')
    extra_context = {'navbar_list': get_default_nav()}

    def get_queryset(self):
        return Question.objects.filter(
            pub_date__lte=timezone.localtime()
        ).order_by('-pub_date')

    def form_valid(self, form):
        """ I'm sure that it could be done better,
            but I can't understand or find an adequate answer on the net. """
        choice = form.cleaned_data['choices']
        choice.votes = F('votes') + 1
        choice.save()
        self.success_url = reverse_lazy('polls:results', kwargs={'pk': choice.question.pk})
        return super().form_valid(form)


class ResultsView(generic.DetailView):
    template_name = 'polls/results.html'
    model = Question
    extra_context = {'navbar_list': get_default_nav()}

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.localtime())
