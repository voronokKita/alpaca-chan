from django.forms import ModelForm, FloatField, NumberInput

from .models import Profile


class TransferMoneyForm(ModelForm):  # TODO test
    transfer_money = FloatField(
        label='', min_value=0.01, max_value=9999.99,
        widget=NumberInput(attrs={'placeholder': '0.01',
                                  'class': 'form-control',
                                  'autocomplete': 'off'})
    )
    class Meta:
        model = Profile
        fields = ['transfer_money']

    def clean_transfer_money(self):
        money = self.cleaned_data['transfer_money']
        self.instance.add_money(money)
        return money
