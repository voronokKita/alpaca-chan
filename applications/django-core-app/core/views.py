import logging

from django.conf import settings
from django.urls import reverse_lazy
from django.views import generic
from django.contrib.messages.views import SuccessMessageMixin
from django.contrib.auth import views, login, authenticate
from django.contrib import messages

logger = logging.getLogger(__name__)


class IndexView(generic.TemplateView):
    template_name = 'core/index.html'
    def get(self, request, *args, **kwargs):
        logger.debug('OK')
        return super().get(request, *args, **kwargs)
