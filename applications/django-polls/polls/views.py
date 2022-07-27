from django.shortcuts import render, get_object_or_404
from django.http import HttpResponseRedirect
from django.urls import reverse, reverse_lazy
from django.views import generic

from django.utils import timezone
from django.db.models import F

from .models import Question, Choice


def get_default_nav():
    return [{'url': reverse_lazy('polls:index'), 'text': 'Polls main', 'focus': True}, ]


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
    extra_context = {'navbar_list': get_default_nav()}

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.localtime())


class ResultsView(generic.DetailView):
    template_name = 'polls/results.html'
    model = Question
    extra_context = {'navbar_list': get_default_nav()}

    def get_queryset(self):
        return Question.objects.filter(pub_date__lte=timezone.localtime())


def vote(request, question_pk):
    q = get_object_or_404(Question, pk=question_pk)
    try:
        selected = q.choice_set.get(pk=request.POST['choice'])
    except (KeyError, Choice.DoesNotExist):
        return render(
            request, 'polls/detail.html',
            {'question': q, 'error_message': "You didn't select a choice.", 'navbar_list': get_default_nav()}
        )
    else:
        selected.votes = F('votes') + 1
        selected.save()
        return HttpResponseRedirect(reverse('polls:results', args=(q.pk,)))
