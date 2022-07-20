import logging

from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse
from django.views import generic

from django.utils import timezone
from django.db.models import F

from .models import Question, Choice


logger = logging.getLogger(__name__)
logger.debug('Logging is going')


class IndexView(generic.ListView):
    template_name = 'polls/index.html'
    context_object_name = 'latest_question_list'

    def get_queryset(self):
        return Question.objects.filter(
            pub_date__lte=timezone.localtime()
        ).order_by('-pub_date')


class DetailView(generic.DetailView):
    template_name = 'polls/detail.html'
    model = Question

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.localtime())


class ResultsView(generic.DetailView):
    template_name = 'polls/results.html'
    model = Question

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.localtime())


def vote(request, question_pk):
    q = get_object_or_404(Question, pk=question_pk)
    try:
        selected = Choice.objects.filter(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(   # TODO ERROR
            request, 'polls/detail.html',
            {'q': q, 'error_message': "You didn't select a choice."}
        )
    else:
        selected.update(votes=F('votes')+1)
        # selected.refresh_from_db()
        return HttpResponseRedirect(reverse('polls:results', args=(q.id,)))
