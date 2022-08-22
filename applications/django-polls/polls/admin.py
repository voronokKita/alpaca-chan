from django.contrib import admin

from .models import Question, Choice


class ChoiceInline(admin.TabularInline):
    model = Choice
    extra = 0


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ['pk', 'question_text', 'pub_date', 'published_recently']
    list_display_links = ['pk', 'question_text']
    list_filter = ['pub_date']

    fields = ['question_text', 'pub_date']
    search_fields = ['question_text']

    inlines = [ChoiceInline]
