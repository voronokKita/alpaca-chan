import logging

from django.urls import reverse, reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import views, login, authenticate
from django.contrib import messages

from .forms import UserRegisterForm, UserLoginForm

logger = logging.getLogger(__name__)


class IndexView(generic.TemplateView):
    template_name = 'accounts/index.html'


class RegisterView(SuccessMessageMixin, generic.CreateView):
    template_name = 'accounts/register_user.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('accounts:index')
    success_message = "Hello, %(username)s!"

    def form_valid(self, form):
        url_source = self.request.GET.get('next')
        if url_source: self.success_url = url_source

        valid = super(RegisterView, self).form_valid(form)

        username, password = form.cleaned_data.get('username'), form.cleaned_data.get('password1')
        new_user = authenticate(username=username, password=password)
        login(self.request, new_user)

        logger.info(f"A new user created ({form.cleaned_data['username']}).")
        return valid


class LoginView(SuccessMessageMixin, views.LoginView):
    template_name = 'accounts/authentication.html'
    authentication_form = UserLoginForm
    next_page = reverse_lazy('accounts:index')
    success_message = "Welcome, %(username)s!"


class LogoutView(views.LogoutView):
    next_page = reverse_lazy('accounts:index')

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            username = self.request.user.username
            messages.add_message(self.request, messages.INFO, f'Farewell, {username}!')
        return super().dispatch(request, *args, **kwargs)

    def get_next_page(self):
        url_source = self.request.META.get('HTTP_REFERER')
        if url_source: self.next_page = url_source
        return super().get_next_page()
