from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import (
    Model, DateTimeField, Index,
    CharField, TextField, SlugField
)


class Entry(Model):
    slug = SlugField('URL Shortcut (slug)', null=True, unique=True)
    entry_name = CharField('Article Name', max_length=150)
    entry_text = TextField('Article Text')
    pub_date = DateTimeField('Date Published', default=timezone.localtime)
    upd_date = DateTimeField('Last Update', auto_now=True)

    def get_absolute_url(self):
        return reverse('encyclopedia:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.entry_name)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'Wiki Entry'
        verbose_name_plural = 'Wiki Entries'
        ordering = ['entry_name']
        indexes = [Index(fields=['slug'])]

    def __str__(self): return self.slug

    def __repr__(self): return f'<entry-{self.slug}>'
