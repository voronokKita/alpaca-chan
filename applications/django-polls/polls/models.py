import datetime

from django.utils import timezone
from django.urls import reverse
from django.contrib import admin
from django.db import models
from django.db.models import (
    Model, IntegerField, CharField,
    DateTimeField, ForeignKey
)


class Question(Model):
    question_text = CharField('text', max_length=200)
    pub_date = DateTimeField('date published', default=timezone.localtime)

    def __str__(self): return self.question_text

    def __repr__(self): return f'<question-{self.pk}>'

    @admin.display(
        boolean=True,
        description='Published recently?',
    )
    def published_recently(self):
        now = timezone.localtime()
        yesterday = now - datetime.timedelta(days=1)
        return yesterday <= self.pub_date <= now

    def get_absolute_url(self):
        return reverse('polls:detail', kwargs={'pk': self.pk})

    class Meta:
        verbose_name = 'Question'
        verbose_name_plural = 'Questions'
        ordering = ['-pub_date']


class Choice(Model):
    question = ForeignKey(Question, on_delete=models.PROTECT, db_index=True)
    choice_text = CharField('text', max_length=200)
    votes = IntegerField(default=0)

    class Meta:
        ordering = ['-votes']

    def __str__(self): return self.choice_text

    def __repr__(self): return f'<choice-{self.pk}>'
