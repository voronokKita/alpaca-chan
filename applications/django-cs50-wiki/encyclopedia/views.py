from django.views import generic

from django.utils import timezone

from .models import Entry
from .forms import AddNewEntryForm


class IndexView(generic.ListView):
    template_name = 'encyclopedia/index.html'
    queryset = Entry.objects.order_by('entry_name')[:20]
    context_object_name = 'wiki_entries'


class DetailView(generic.DetailView):
    template_name = 'encyclopedia/detail.html'
    model = Entry
    context_object_name = 'article'


class AddNewEntry(generic.CreateView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = AddNewEntryForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add New Article'
        return context
