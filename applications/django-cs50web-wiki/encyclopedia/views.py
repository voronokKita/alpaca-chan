import logging
import markdown2

from django.urls import reverse_lazy
from django.views import generic

from .models import Entry
from .forms import EntryForm, DeleteEntryForm

logger = logging.getLogger(__name__)


class IndexView(generic.ListView):
    template_name = 'encyclopedia/index.html'
    queryset = Entry.objects.order_by('entry_name')[:20]
    context_object_name = 'wiki_entries'


class DetailView(generic.DetailView):
    template_name = 'encyclopedia/detail.html'
    model = Entry
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entry_text_html'] = markdown2.markdown(
            context['article'].entry_text
        )
        return context


class AddNewEntry(generic.CreateView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = EntryForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = 'Add new article'
        return context


class EditEntry(generic.UpdateView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = EntryForm
    model = Entry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit an article :: {context["entry"].entry_name}'
        return context


class DeleteEntry(generic.DeleteView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = DeleteEntryForm
    model = Entry
    success_url = reverse_lazy('encyclopedia:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Delete an article :: {context["entry"].entry_name}'
        context['delete_conformation'] = f'Are you sure you want to delete \"{context["entry"].entry_name}\"?'
        return context
