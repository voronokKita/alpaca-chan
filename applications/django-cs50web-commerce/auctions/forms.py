import logging

from django.utils import timezone
from django.forms import (
    ModelForm, Textarea,
    FloatField, NumberInput,
    CharField, TextInput,
    ImageField, ClearableFileInput,
    ModelChoiceField, Select, HiddenInput,
    BooleanField, DateTimeField,
    ValidationError
)
from .models import (
    SLUG_MAX_LEN, LOT_TITLE_MAX_LEN, DEFAULT_STARTING_PRICE,
    Profile, Listing, ListingCategory
)

logger = logging.getLogger(__name__)


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

    # TODO def is_valid(self):


class PublishListingForm(ModelForm):  # TODO test
    foo = BooleanField(required=False, disabled=True, widget=HiddenInput())

    class Meta:
        model = Listing
        fields = ['foo']

    def clean(self):
        if self.instance.can_be_published() is False:
            raise ValidationError('ERROR: this lot already published!')
        return super().clean()

    def is_valid(self):
        if super().is_valid():
            return self.instance.publish_the_lot()
        else:
            return False


class AuctionLotForm(ModelForm):  # TODO test
    pass


class EditListingForm(ModelForm):  # TODO test
    title = CharField(
        label='Listing title',
        help_text=f'{LOT_TITLE_MAX_LEN} characters max',
        widget=TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )
    category = ModelChoiceField(
        label='Category',
        queryset=ListingCategory.manager.all(),  # TODO filter ghost
        widget=Select(attrs={'class': 'form-control'})
    )
    starting_price = FloatField(
        label='Starting 🪙 price',
        min_value=0.01,
        widget=NumberInput(attrs={'class': 'form-control'})
    )
    description = CharField(
        label='Description',
        min_length=10,
        widget=Textarea(attrs={'class': 'form-control'})
    )
    image = ImageField(
        label='Item image',
        widget=ClearableFileInput(attrs={'class': 'form-control'})
    )
    class Meta:
        model = Listing
        fields = ['title', 'category', 'starting_price', 'description', 'image']

    def clean(self):
        if 'button_publish' in self.data and self.instance.can_be_published() is False:
            raise ValidationError('ERROR: this lot already published!')
        return super().clean()

    def is_valid(self):
        if super().is_valid() is False:
            return False
        elif 'button_publish' in self.data:
            return self.instance.publish_the_lot()
        else:
            return True


class CreateListingForm(ModelForm):  # TODO test
    slug = CharField(
        label='SLUG (optional)',
        required=False,
        widget=TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off',
                   'placeholder': f'{SLUG_MAX_LEN} characters max'}
        )
    )
    title = CharField(
        label='Listing title',
        widget=TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off',
                   'placeholder': f'{LOT_TITLE_MAX_LEN} characters max'}
        )
    )
    category = ModelChoiceField(
        label='Category',
        queryset=ListingCategory.manager.all(),  # TODO filter ghost
        widget=Select(attrs={'class': 'form-control'})
    )
    starting_price = FloatField(
        label='Starting 🪙 price',
        min_value=0.01,
        initial=DEFAULT_STARTING_PRICE,
        widget=NumberInput(attrs={'class': 'form-control'})
    )
    description = CharField(
        label='Description',
        min_length=10,
        widget=Textarea(attrs={'class': 'form-control'})
    )
    image = ImageField(
        label='Item image',
        widget=ClearableFileInput(attrs={'class': 'form-control'})
    )
    owner = ModelChoiceField(
        disabled=True,
        queryset=None,
        widget=HiddenInput()
    )
    class Meta:
        model = Listing
        fields = ['slug', 'title', 'category', 'starting_price',
                  'description', 'image', 'owner']
