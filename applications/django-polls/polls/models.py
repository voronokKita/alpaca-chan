import datetime

from django.db.models import Model, IntegerField, CharField, DateTimeField, ForeignKey
from django.db import models
from django.utils import timezone
from django.contrib import admin


class Question(Model):
    question_text = CharField(max_length=200)
    pub_date = DateTimeField('date published', default=timezone.localtime)

    def __repr__(self): return f'<q{self.id}: {self.question_text}>'

    @admin.display(
        boolean=True,
        ordering='pub_date',
        description='Published recently?',
    )
    def published_recently(self):
        now = timezone.localtime()
        yesterday = now - datetime.timedelta(days=1)
        return yesterday <= self.pub_date <= now


class Choice(Model):
    question = ForeignKey(Question, on_delete=models.CASCADE)
    choice_text = CharField(max_length=200)
    votes = IntegerField(default=0)

    def __repr__(self): return f'<q{self.question.id}-a{self.id}: {self.choice_text}>'
