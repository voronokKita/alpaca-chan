from django.forms import ModelForm, RadioSelect, ModelChoiceField
from django.db.models import F

from .models import Question, Choice


class ChoiceSetForm(ModelForm):
    choices = ModelChoiceField(queryset=Choice.manager.all(), label='', widget=RadioSelect)

    class Meta:
        model = Question
        fields = ['choices']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['choices'].queryset = self.instance.choice_set.all()

    def clean_choices(self):
        choice = self.cleaned_data['choices']
        choice.votes = F('votes') + 1
        choice.save()
        return choice
