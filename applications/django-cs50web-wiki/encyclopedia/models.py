from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse
from django.db.models import (
    Model, DateTimeField, Index,
    CharField, TextField, SlugField,
    Manager
)


class Entry(Model):
    manager = Manager()

    slug = SlugField('slug', null=True, unique=True)
    entry_name = CharField('article name', max_length=150)
    entry_text = TextField('article text')
    pub_date = DateTimeField('date published', default=timezone.localtime)
    upd_date = DateTimeField('last update', auto_now=True)

    def get_absolute_url(self):
        return reverse('encyclopedia:detail', kwargs={'slug': self.slug})

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.entry_name)
        return super().save(*args, **kwargs)

    class Meta:
        verbose_name = 'wiki entry'
        verbose_name_plural = 'wiki entries'
        ordering = ['entry_name']
        indexes = [Index(fields=['slug'])]

    def __str__(self): return self.slug if self.slug else slugify(self.entry_name)
