import re
import markdown2
import logging

from django.conf import settings
from django.views import generic

logger = logging.getLogger(__name__)


def get_context():
    """ It will make a context from the readme file,
        from the folder of each main project. """
    main_app_list = []
    for app in settings.PROJECT_MAIN_APPS:
        try:
            readme = settings.PROJECT_MAIN_APPS[app] / 'readme.md'
            readme_html = markdown2.markdown(readme.read_text())
            result = re.findall(r".*<h5>(.+)</h5>.*<p>(.+)</p>.*",
                                readme_html, re.I | re.DOTALL)[0]
            context_card = {
                'app_name': app,
                'title': result[0],
                'description': result[1],
            }
            main_app_list.append(context_card)
        except Exception as err:
            logger.debug(f'core: {err}')
    return {'main_app_list': main_app_list}


class IndexView(generic.TemplateView):
    template_name = 'core/index.html'
    extra_context = get_context()
