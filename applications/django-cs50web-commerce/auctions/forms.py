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
    USERNAME_MAX_LEN, Profile, Listing, ListingCategory, Comment
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
    ghost_field = BooleanField(required=False, disabled=True, widget=HiddenInput())

    class Meta:
        model = Listing
        fields = ['ghost_field']

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
    ghost_field = BooleanField(required=False, disabled=True, widget=HiddenInput())
    auctioneer = CharField(required=False, disabled=True,
                           max_length=USERNAME_MAX_LEN, widget=HiddenInput())
    bid_value = FloatField(
        label='',
        min_value=0.01,
        initial=0.01,
        required=False,
        widget=NumberInput(attrs={'class': 'form-control d-inline', 'style': 'width: 100px;'})
    )
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        highest_price = kwargs['instance'].get_highest_price() + 0.01  # TODO each new bid must bee higher on %
        self.fields['bid_value'].initial = highest_price
        self.fields['bid_value'].min_value = highest_price
        self.fields['bid_value'].widget.attrs['min'] = highest_price

    class Meta:
        model = Listing
        fields = ['ghost_field', 'bid_value']

    def clean(self):
        username = self.fields['auctioneer'].initial
        if 'btn_owner_closed_auction' in self.data and \
                self.instance.owner.username != username:
            raise ValidationError('ERROR: you aren’t the owner ot the lot')

        elif 'btn_owner_withdrew' in self.data and \
                self.instance.owner.username != username:
            raise ValidationError('ERROR: you aren’t the owner ot the lot')

        elif 'btn_user_bid' in self.data and \
                self.instance.bid_possibility(username=username) is False:
            raise ValidationError('ERROR: bid is prohibited')

        elif 'btn_user_watching' in self.data and \
                self.instance.check_name_in_watchlist(username) is True:
            raise ValidationError('ERROR: already watching')

        elif 'btn_user_unwatched' in self.data and \
                self.instance.can_unwatch(username=username) is False:
            raise ValidationError('ERROR: can’t unwatch')

        return super().clean()

    def is_valid(self):
        username = self.fields['auctioneer'].initial
        if super().is_valid() is False:
            return False
        elif 'btn_owner_closed_auction' in self.data:
            return self.instance.change_the_owner()
        elif 'btn_owner_withdrew' in self.data:
            return self.instance.withdraw()
        elif 'btn_user_bid' in self.data:
            bid_value = self.cleaned_data['bid_value']
            profile = Profile.manager.filter(username=username).first()
            return self.instance.make_a_bid(profile, bid_value)
        elif 'btn_user_watching' in self.data:
            profile = Profile.manager.filter(username=username).first()
            profile.items_watched.add(self.instance)
            return True
        elif 'btn_user_unwatched' in self.data:
            return self.instance.unwatch(username=username)
        else:
            return True


class CommentForm(ModelForm):
    author_hidden = CharField(required=False, disabled=True,
                              max_length=USERNAME_MAX_LEN, widget=HiddenInput())
    text_field = CharField(
        label='',
        min_length=5,
        widget=Textarea(attrs={'class': 'form-control', 'rows': 5})
    )
    class Meta:
        model = Listing
        fields = ['text_field', 'author_hidden']

    def is_valid(self):
        if super().is_valid() is False:
            return False
        else:
            username = self.cleaned_data['author_hidden']
            self.instance.comment_set.create(
                text=self.cleaned_data['text_field'],
                author=Profile.manager.filter(username=username).first()
            )
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
