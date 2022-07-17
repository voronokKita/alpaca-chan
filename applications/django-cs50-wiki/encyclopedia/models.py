from django.utils import timezone
from django.urls import reverse
from django.db.models import (
    Model, DateTimeField,
    CharField, TextField
)


class Entry(Model):
    entry_name = CharField('Article Name', max_length=150)
    entry_text = TextField('Article Text')
    pub_date = DateTimeField('Date Published', default=timezone.localtime)
    upd_date = DateTimeField('Last Update', auto_now=True)

    def __repr__(self): return f'<entry-{self.pk}>'

    def get_absolute_url(self):
        return reverse('encyclopedia:detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Wiki Entry'
        verbose_name_plural = 'Wiki Entries'
        ordering = ['entry_name']
