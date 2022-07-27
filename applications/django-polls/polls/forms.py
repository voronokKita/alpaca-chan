from django.forms import ModelForm, RadioSelect, ModelChoiceField

from .models import Question, Choice


class ChoiceSetForm(ModelForm):
    """ I'm sure that it could be done better,
        but I can't understand or find an adequate answer on the net. """
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        if self.instance:
            self.fields['choices'].queryset = self.instance.choice_set.all()

    choices = ModelChoiceField(queryset=Choice.objects.all(), label='', widget=RadioSelect)

    class Meta:
        model = Question
        fields = ['choices']
