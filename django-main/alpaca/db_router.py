from django.conf import settings


class DefaultRouter:
    """ A router that will redirect all requests to the default database,
        except for the main applications. """
    db_name = 'default'
    app_labels = settings.PROJECT_MAIN_APPS.keys()

    def db_for_read(self, model, **hints):
        """ Attempts to read from the MAIN_APPS will go farther. """
        if model._meta.app_label not in self.app_labels:
            return self.db_name
        else:
            return None

    def db_for_write(self, model, **hints):
        """ Attempts to write to the MAIN_APPS will go farther. """
        if model._meta.app_label not in self.app_labels:
            return self.db_name
        else:
            return None
