import logging

from django.urls import reverse, reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin

from .forms import UserRegisterForm


logger = logging.getLogger(__name__)


class IndexView(generic.TemplateView):
    template_name = 'accounts/index.html'


class RegisterView(SuccessMessageMixin, generic.CreateView):
    template_name = 'accounts/register_user.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('accounts:index')
    success_message = "Hello, %(username)s!"

    def form_valid(self, form):
        logger.info(f"A new user created ({form.cleaned_data['username']}).")
        return super().form_valid(form)


class LoginView(SuccessMessageMixin, generic.FormView):
    template_name = 'accounts/authentication.html'
