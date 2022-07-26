import logging
import markdown2

from django.urls import reverse_lazy, reverse
from django.views import generic

from .models import Entry
from .forms import EntryForm, DeleteEntryForm

logger = logging.getLogger(__name__)


def get_default_nav():
    return [{'url': reverse_lazy('encyclopedia:index'), 'text': 'Goto home', 'focus': True}, ]


class IndexView(generic.ListView):
    template_name = 'encyclopedia/index.html'
    queryset = Entry.objects.order_by('entry_name')[:20]
    context_object_name = 'wiki_entries'
    extra_context = {
        'navbar_list': [{'url': reverse_lazy('encyclopedia:new_entry'),
                        'text': 'Write a new article', 'focus': True}]
        }


class DetailView(generic.DetailView):
    template_name = 'encyclopedia/detail.html'
    model = Entry
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entry_text_html'] = markdown2.markdown(
            context['article'].entry_text
        )
        slug = context['article'].slug
        context['navbar_list'] = [
            {'url': reverse('encyclopedia:index'), 'text': 'Go back', 'focus': True},
            {'url': reverse('encyclopedia:edit_entry', kwargs={'slug': slug}),
             'text': 'Edit this article'},
            {'url': reverse('encyclopedia:delete_entry', kwargs={'slug': slug}),
             'text': 'Delete this article'},
        ]
        return context


class AddNewEntry(generic.CreateView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = EntryForm
    extra_context = {'title': 'Add new article', 'navbar_list': get_default_nav()}


class EditEntry(generic.UpdateView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = EntryForm
    model = Entry
    extra_context = {'navbar_list': get_default_nav()}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit an article :: {context["entry"].entry_name}'
        return context


class DeleteEntry(generic.DeleteView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = DeleteEntryForm
    model = Entry
    success_url = reverse_lazy('encyclopedia:index')
    extra_context = {'navbar_list': get_default_nav()}

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Delete an article :: {context["entry"].entry_name}'
        context['delete_conformation'] = f'Are you sure you want to delete \"{context["entry"].entry_name}\"?'
        return context
