from django.conf import settings


class PollsRouter:
    """ A router to control all database operations on models in an [app]. """
    app_label = 'polls'
    db_name = settings.PROJECT_MAIN_APPS['polls']['db']['name']

    def db_for_read(self, model, **hints):
        """ Attempts to read from the [app] models go to the [app_db]. """
        if model._meta.app_label == self.app_label:
            return self.db_name
        else:
            return None

    def db_for_write(self, model, **hints):
        """ Attempts to write to the [app] models go to the [app_db]. """
        if model._meta.app_label == self.app_label:
            return self.db_name
        else:
            return None

    def allow_relation(self, obj1, obj2, **hints):
        """ Allow any relation if a model in the [app] is involved. """
        if obj1._meta.app_label == self.app_label or \
                obj2._meta.app_label == self.app_label:
            return True
        else:
            return None

    def allow_migrate(self, db, app_label, model_name=None, **hints):
        """ Make sure the [app] only appear in the [app_db]. """
        if app_label == self.app_label:
            return db == self.db_name
        else:
            return None
