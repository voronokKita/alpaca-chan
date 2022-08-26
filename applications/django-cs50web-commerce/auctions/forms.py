import logging

from django.forms import (
    ModelForm, Textarea,
    FloatField, NumberInput,
    CharField, TextInput,
    ImageField, ClearableFileInput,
    ModelChoiceField, Select, HiddenInput,
    BooleanField, ValidationError,
)
from .models import (
    SLUG_MAX_LEN, LOT_TITLE_MAX_LEN, DEFAULT_STARTING_PRICE,
    USERNAME_MAX_LEN, Profile, Listing, ListingCategory
)

logger = logging.getLogger(__name__)

MONEY_MIN_VALUE = 0.01
MONEY_MAX_VALUE = 9999.99


class TransferMoneyForm(ModelForm):
    transfer_money = FloatField(
        label='', required=True,
        min_value=MONEY_MIN_VALUE, max_value=MONEY_MAX_VALUE,
        widget=NumberInput(attrs={'placeholder': '0.01',
                                  'class': 'form-control',
                                  'autocomplete': 'off'})
    )
    class Meta:
        model = Profile
        fields = ['transfer_money']

    def save(self, commit=True):
        money = self.cleaned_data['transfer_money']
        self.instance.add_money(money)
        self.instance.refresh_from_db()
        return self.instance


class PublishListingForm(ModelForm):
    ghost_field = BooleanField(required=False, disabled=True, widget=HiddenInput())

    class Meta:
        model = Listing
        fields = ['ghost_field']

    def clean(self):
        if self.instance.can_be_published() is False:
            raise ValidationError('ERROR: this lot already published!')
        return super().clean()

    def save(self, commit=True):
        self.instance.publish_the_lot()
        self.instance.refresh_from_db()
        return self.instance


class AuctionLotForm(ModelForm):
    ghost_field = BooleanField(required=False, disabled=True, widget=HiddenInput())
    auctioneer = CharField(required=False, disabled=True,
                           max_length=USERNAME_MAX_LEN, widget=HiddenInput())
    bid_value = FloatField(
        label='',
        min_value=MONEY_MIN_VALUE,
        initial=MONEY_MIN_VALUE,
        required=False,
        widget=NumberInput(attrs={'class': 'form-control d-inline', 'style': 'width: 100px;'})
    )
    class Meta:
        model = Listing
        fields = ['ghost_field', 'bid_value']

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        initial = kwargs['instance'].get_highest_price(percent=True)
        self.fields['bid_value'].initial = initial
        self.fields['bid_value'].min_value = initial
        self.fields['bid_value'].widget.attrs['min'] = initial

    def clean(self):
        username = self.fields['auctioneer'].initial
        if 'btn_owner_closed_auction' in self.data and \
                self.instance.owner.username != username:
            raise ValidationError('ERROR: you aren’t the owner ot the lot')

        elif 'btn_owner_closed_auction' in self.data and \
                self.instance.highest_bid is None:
            raise ValidationError('ERROR: there is no bids')

        elif 'btn_owner_withdrew' in self.data and \
                self.instance.owner.username != username:
            raise ValidationError('ERROR: you aren’t the owner ot the lot')

        elif 'btn_user_bid' in self.data and \
                not isinstance(self.cleaned_data['bid_value'], (int, float)):
            raise ValidationError('enter the value of the bid')

        elif 'btn_user_bid' in self.data and \
                self.instance.no_bid_option(username=username):
            raise ValidationError('ERROR: bid is prohibited')

        elif 'btn_user_watching' in self.data and \
                self.instance.in_watchlist.filter(username=username).exists():
            raise ValidationError('ERROR: already watching')

        elif 'btn_user_unwatched' in self.data and \
                self.instance.can_unwatch(username=username) is False:
            raise ValidationError('ERROR: can’t unwatch')

        return super().clean()

    def save(self, commit=True):
        username = self.fields['auctioneer'].initial
        if 'btn_owner_closed_auction' in self.data:
            self.instance.change_the_owner()
        elif 'btn_owner_withdrew' in self.data:
            self.instance.withdraw()
        elif 'btn_user_bid' in self.data:
            bid_value = self.cleaned_data['bid_value']
            profile = Profile.manager.filter(username=username).first()
            self.instance.make_a_bid(profile, bid_value)
        elif 'btn_user_watching' in self.data:
            profile = Profile.manager.filter(username=username).first()
            profile.items_watched.add(self.instance)
        elif 'btn_user_unwatched' in self.data:
            self.instance.unwatch(username=username)

        self.instance.refresh_from_db()
        return self.instance


class CommentForm(ModelForm):
    author_hidden = CharField(
        required=True,
        disabled=True,
        max_length=USERNAME_MAX_LEN,
        widget=HiddenInput()
    )
    text_field = CharField(
        label='',
        min_length=5,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 5})
    )
    class Meta:
        model = Listing
        fields = ['text_field', 'author_hidden']

    def save(self, commit=True):
        username = self.cleaned_data['author_hidden']
        self.instance.comment_set.create(
            text=self.cleaned_data['text_field'],
            author=Profile.manager.filter(username=username).first()
        )
        return self.instance


class CreateListingForm(ModelForm):
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
        required=True,
        widget=TextInput(
            attrs={'class': 'form-control', 'autocomplete': 'off',
                   'placeholder': f'{LOT_TITLE_MAX_LEN} characters max'}
        )
    )
    category = ModelChoiceField(
        label='Category',
        required=True,
        queryset=ListingCategory.manager.all(),
        widget=Select(attrs={'class': 'form-control'})
    )
    starting_price = FloatField(
        label='Starting 🪙 price',
        required=True,
        min_value=MONEY_MIN_VALUE,
        initial=DEFAULT_STARTING_PRICE,
        widget=NumberInput(attrs={'class': 'form-control'})
    )
    description = CharField(
        label='Description',
        required=True,
        min_length=10,
        widget=Textarea(attrs={'class': 'form-control'})
    )
    image = ImageField(
        label='Item image',
        required=True,
        widget=ClearableFileInput(attrs={'class': 'form-control'})
    )
    owner = ModelChoiceField(
        required=True,
        disabled=True,
        queryset=None,
        widget=HiddenInput()
    )
    class Meta:
        model = Listing
        fields = ['slug', 'title', 'category', 'starting_price',
                  'description', 'image', 'owner']


class EditListingForm(ModelForm):
    title = CharField(
        label='Listing title',
        help_text=f'{LOT_TITLE_MAX_LEN} characters max',
        widget=TextInput(attrs={'class': 'form-control', 'autocomplete': 'off'})
    )
    category = ModelChoiceField(
        label='Category',
        queryset=ListingCategory.manager.all(),
        widget=Select(attrs={'class': 'form-control'})
    )
    starting_price = FloatField(
        label='Starting 🪙 price',
        min_value=MONEY_MIN_VALUE,
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

    def save(self, commit=True):
        instance = super().save(commit)
        if 'button_publish' in self.data:
            instance.publish_the_lot()
        instance.refresh_from_db()
        return instance
