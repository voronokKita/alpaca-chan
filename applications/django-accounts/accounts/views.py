import logging

from django.conf import settings
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import views, login, authenticate
from django.contrib import messages

from .forms import UserRegisterForm, UserLoginForm

logger = logging.getLogger(__name__)


def redirect_on_success(source_app: str):
    """ Make sure that the redirect happens to the index of installed apps.
        :source_app: app to redirect, like example.com/[source_app]/login """
    if source_app is not None and source_app in settings.PROJECT_MAIN_APPS:
        return reverse_lazy(f'{source_app}:index')
    else:
        return None


class IndexView(generic.TemplateView):
    template_name = 'accounts/index.html'


class RegisterView(SuccessMessageMixin, generic.CreateView):
    template_name = 'accounts/register_user.html'
    form_class = UserRegisterForm
    success_url = reverse_lazy('core:index')
    success_message = "Hello, %(username)s!"

    def form_valid(self, form):
        next_ = redirect_on_success(self.kwargs.get('next'))
        if next_: self.success_url = next_

        valid = super().form_valid(form)
        new_user = authenticate(
            username=form.cleaned_data.get('username'),
            password=form.cleaned_data.get('password1')
        )
        login(self.request, new_user)
        return valid


class LoginView(SuccessMessageMixin, views.LoginView):
    template_name = 'accounts/authentication.html'
    authentication_form = UserLoginForm
    next_page = reverse_lazy('core:index')
    success_message = "Welcome, %(username)s!"

    def get_success_url(self):
        next_ = redirect_on_success(self.kwargs.get('next'))
        if next_: self.next_page = next_
        return super().get_success_url()


class LogoutView(views.LogoutView):
    next_page = reverse_lazy('core:index')

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated:
            username = self.request.user.username
            messages.add_message(self.request, messages.INFO, f'Farewell, {username}!')
        return super().dispatch(request, *args, **kwargs)

    def get_success_url(self):
        next_ = redirect_on_success(self.kwargs.get('next'))
        if next_: self.next_page = next_
        return super().get_success_url()
