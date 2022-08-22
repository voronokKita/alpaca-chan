import logging

from django.urls import reverse_lazy
from django.views import generic
from django.utils import timezone

from .models import Question
from .forms import ChoiceSetForm

logger = logging.getLogger(__name__)


class NavbarMixin:
    @staticmethod
    def _get_default_nav():
        return [{'url': reverse_lazy('polls:index'), 'text': 'Polls main', 'focus': True}, ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['navbar_list'] = self._get_default_nav()
        return context


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        return Question.manager.filter(pub_date__lte=timezone.localtime())


class DetailView(NavbarMixin, generic.UpdateView):
    template_name = 'polls/detail.html'
    model = Question
    form_class = ChoiceSetForm
    success_url = reverse_lazy('polls:index')

    def get_queryset(self):
        return Question.manager.filter(pub_date__lte=timezone.localtime())

    def form_valid(self, form):
        self.success_url = reverse_lazy('polls:results', args=[form.instance.pk])
        return super().form_valid(form)


class ResultsView(NavbarMixin, generic.DetailView):
    template_name = 'polls/results.html'
    model = Question

    def get_queryset(self):
        return Question.manager.filter(pub_date__lte=timezone.localtime())
