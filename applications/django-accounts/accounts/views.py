import logging

from django.urls import reverse, reverse_lazy
from django.views import generic


logger = logging.getLogger(__name__)


class IndexView(generic.TemplateView):
    template_name = 'accounts/index.html'


class RegisterView(generic.CreateView):
    template_name = 'accounts/index.html'


class LoginView(generic.FormView):
    template_name = 'accounts/index.html'
