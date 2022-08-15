import logging
import markdown2

from django.urls import reverse_lazy
from django.views import generic

from .models import Entry
from .forms import EntryForm, DeleteEntryForm

logger = logging.getLogger(__name__)


class NavbarMixin:
    @staticmethod
    def _get_default_nav():
        return [{'url': reverse_lazy('encyclopedia:index'), 'text': 'Wiki main', 'focus': True}, ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['navbar_list'] = self._get_default_nav()
        return context


class IndexView(generic.ListView):
    template_name = 'encyclopedia/index.html'
    queryset = Entry.objects.all()[:20]
    context_object_name = 'wiki_entries'
    extra_context = {
        'navbar_list': [{'url': reverse_lazy('encyclopedia:new_entry'),
                        'text': 'Write a new article', 'focus': True}]
        }


class DetailView(NavbarMixin, generic.DetailView):
    template_name = 'encyclopedia/detail.html'
    model = Entry
    context_object_name = 'article'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['entry_text_html'] = markdown2.markdown(
            context['article'].entry_text
        )

        slug = context['article'].slug
        url_edit = reverse_lazy('encyclopedia:edit_entry', args=[slug])
        url_delete = reverse_lazy('encyclopedia:delete_entry', args=[slug])
        context['navbar_list'] += [
            {'url': url_edit, 'text': 'Edit this article'},
            {'url': url_delete, 'text': 'Delete this article'},
        ]
        return context


class AddNewEntry(NavbarMixin, generic.CreateView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = EntryForm
    extra_context = {'title': 'Add new article'}


class EditEntry(NavbarMixin, generic.UpdateView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = EntryForm
    model = Entry

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Edit an article :: {context["entry"].entry_name}'
        return context


class DeleteEntry(NavbarMixin, generic.DeleteView):
    template_name = 'encyclopedia/entry_form.html'
    form_class = DeleteEntryForm
    model = Entry
    success_url = reverse_lazy('encyclopedia:index')

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['title'] = f'Delete an article :: {context["entry"].entry_name}'
        context['delete_conformation'] = \
            f'Are you sure you want to delete \"{context["entry"].entry_name}\"?'
        return context
