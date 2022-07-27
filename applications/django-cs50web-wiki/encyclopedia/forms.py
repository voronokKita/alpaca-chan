from django.forms import (
    Form, ModelForm, TextInput,
    Textarea, BooleanField, CheckboxInput
)
from .models import Entry

class EntryForm(ModelForm):
    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.slug:
            self.fields['slug'].disabled = True

    class Meta:
        model = Entry
        fields = ['slug', 'entry_name', 'entry_text']
        widgets = {
            'slug': TextInput(attrs={'class': 'form-control'}),
            'entry_name': TextInput(attrs={'class': 'form-control'}),
            'entry_text': Textarea(attrs={'class': 'form-control', 'rows': 10}),
        }


class DeleteEntryForm(Form):
    conform = BooleanField(label='Yes.', widget=CheckboxInput)
