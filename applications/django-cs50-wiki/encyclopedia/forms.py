from django.forms import ModelForm, TextInput, Textarea

from .models import Entry


class AddNewEntryForm(ModelForm):
    class Meta:
        model = Entry
        fields = ['entry_name', 'entry_text']
        widgets = {
            'entry_name': TextInput(),
            'entry_text': Textarea(),
        }
