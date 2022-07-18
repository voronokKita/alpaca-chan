from django.forms import Form, ModelForm, TextInput, Textarea, BooleanField, CheckboxInput, SlugField

from .models import Entry


class EntryForm(ModelForm):
    class Meta:
        model = Entry
        fields = ['slug', 'entry_name', 'entry_text']
        widgets = {
            'slug': TextInput,
            'entry_name': TextInput,
            'entry_text': Textarea,
        }

    def __init__(self, *args, **kwargs):
        super(EntryForm, self).__init__(*args, **kwargs)
        if self.instance and self.instance.slug:
            self.fields['slug'].disabled = True


class DeleteEntryForm(Form):
    conform = BooleanField(label='Yes.', widget=CheckboxInput)
