from pathlib import Path

from django.test import TestCase
from django.conf import settings
from django.forms import HiddenInput
from django.core.files.uploadedfile import SimpleUploadedFile

from auctions.models import Profile, user_media_path
from auctions.forms import (
    TransferMoneyForm, PublishListingForm,
    AuctionLotForm, CommentForm,
    CreateListingForm, EditListingForm,
    MONEY_MIN_VALUE, MONEY_MAX_VALUE, USERNAME_MAX_LEN
)
from .tests import (
    DATABASES, SMALL_GIF, IMGNAME,
    get_category, get_profile, get_listing
)
from auctions.utils import format_bid_value

""" TODO
+ TransferMoneyForm
+ PublishListingForm
+ AuctionLotForm
+ CommentForm
+ CreateListingForm
+ EditListingForm
"""


def form_error_msg(form, sub):
    msg = form.errors['__all__'].as_data()[0].message
    return sub in msg if msg else False


class TransferMoneyFormTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.profile = get_profile('Capybara', money=10)

    def test_add_money_normal_case(self):
        form = TransferMoneyForm({'transfer_money': 10}, instance=self.profile)
        self.assertTrue(form.is_valid())
        profile = form.save()
        self.assertEqual(profile.display_money(), (20.0, 0.0))

    def test_add_money_form_boundary_values(self):
        form = TransferMoneyForm()
        self.assertTrue(form.fields['transfer_money'].required is True)
        self.assertTrue(form.fields['transfer_money'].min_value == MONEY_MIN_VALUE)
        self.assertTrue(form.fields['transfer_money'].max_value == MONEY_MAX_VALUE)


class PublishListingFormTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.listing = get_listing()

    def test_publish_form(self):
        self._normal_case()
        self._already_published()

    def _normal_case(self):
        form = PublishListingForm({'ghost_field': ''}, instance=self.listing)
        self.assertTrue(form.is_valid(), 'ok')
        listing = form.save()
        self.assertTrue(listing.is_active)

    def _already_published(self):
        form = PublishListingForm({'ghost_field': ''}, instance=self.listing)
        self.assertFalse(form.is_valid(), 'already published')
        self.assertTrue(form_error_msg(form, 'already published'))


class AuctionLotFormTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.owner = get_profile('LuckyBeast')
        cls.profile = get_profile('Jaguar')
        cls.category = get_category(label='Buns')
        cls.listing = get_listing(
            category=cls.category,
            profile=cls.owner,
            title='White Japari Bun',
            description='An ultra rare valuable item.'
        )

    def setUp(self):
        self.listing.refresh_from_db()
        if self.listing.highest_bid is not None:
            self.listing.withdraw()
        if self.listing.owner != self.owner:
            self.listing.save_new_owner(self.owner)

        self.listing.refresh_from_db()
        if self.listing.is_active is False:
            self.listing.publish_the_lot()
            self.listing.refresh_from_db()

    def test_owner_closed_the_auction(self):
        self._not_the_owner_closing_error()
        self._no_bids_placed_closing_error()
        self.assertTrue(self.listing.make_a_bid(self.profile, 5))
        self._closed_successfully()

    def _not_the_owner_closing_error(self):
        form = AuctionLotForm({'btn_owner_closed_auction': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.profile.username
        self.assertFalse(form.is_valid(), 'not the owner')
        self.assertTrue(form_error_msg(form, 'aren’t the owner'))

    def _no_bids_placed_closing_error(self):
        form = AuctionLotForm({'btn_owner_closed_auction': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.owner.username
        self.assertFalse(form.is_valid(), 'no bid')
        self.assertTrue(form_error_msg(form, 'no bids'))

    def _closed_successfully(self):
        form = AuctionLotForm({'btn_owner_closed_auction': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.owner.username
        self.assertTrue(form.is_valid(), 'ok')
        listing = form.save()
        self.assertTrue(listing.owner == self.profile, 'ok')

    def test_owner_withdrew_from_the_auction(self):
        self._not_the_owner_withdrew_error()
        self._withdrew_successfully()

    def _not_the_owner_withdrew_error(self):
        form = AuctionLotForm({'btn_owner_withdrew': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.profile.username
        self.assertFalse(form.is_valid(), 'not the owner')
        self.assertTrue(form_error_msg(form, 'aren’t the owner'))

    def _withdrew_successfully(self):
        form = AuctionLotForm({'btn_owner_withdrew': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.owner.username
        self.assertTrue(form.is_valid(), 'ok')
        listing = form.save()
        self.assertFalse(listing.is_active)

    def test_user_bid_on_the_auction(self):
        self._blank_value_bid_error()
        self._bid_successfully()
        self._already_on_the_top_bid_error()

    def _blank_value_bid_error(self):
        form = AuctionLotForm({'btn_user_bid': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.profile.username
        self.assertFalse(form.is_valid(), 'no bid')
        self.assertTrue(form_error_msg(form, 'enter the value'))

    def _bid_successfully(self):
        form = AuctionLotForm({'bid_value': 5, 'btn_user_bid': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.profile.username
        self.assertTrue(form.is_valid(), 'ok')
        listing = form.save()
        self.assertTrue(listing.potential_buyers.contains(self.profile))

    def _already_on_the_top_bid_error(self):
        form = AuctionLotForm({'bid_value': 5, 'btn_user_bid': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.profile.username
        self.assertFalse(form.is_valid(), 'already on the top')
        self.assertTrue(form_error_msg(form, 'bid is prohibited'))

    def test_user_watching_and_unwatched_the_auction(self):
        self._watching_successfully()
        self._already_watching_error()
        self._unwatched_successfully()
        self._not_watching_error()

    def _watching_successfully(self):
        form = AuctionLotForm({'btn_user_watching': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.profile.username
        self.assertTrue(form.is_valid(), 'watching ok')
        listing = form.save()
        self.assertTrue(self.listing.in_watchlist.contains(self.profile))

    def _already_watching_error(self):
        form = AuctionLotForm({'btn_user_watching': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.profile.username
        self.assertFalse(form.is_valid(), 'already watching')
        self.assertTrue(form_error_msg(form, 'already watching'))

    def _unwatched_successfully(self):
        form = AuctionLotForm({'btn_user_unwatched': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.profile.username
        self.assertTrue(form.is_valid(), 'unwatched ok')
        listing = form.save()
        self.assertFalse(self.listing.in_watchlist.contains(self.profile))

    def _not_watching_error(self):
        form = AuctionLotForm({'btn_user_unwatched': ['']}, instance=self.listing)
        form.fields['auctioneer'].initial = self.owner.username
        self.assertFalse(form.is_valid(), 'can’t unwatch')
        self.assertTrue(form_error_msg(form, 'can’t unwatch'))

    def test_lot_form_boundary_values(self):
        form = AuctionLotForm(instance=self.listing)
        n = self.listing.get_highest_price(percent=True)
        highest_price = format_bid_value(n)

        self.assertTrue(form.fields['ghost_field'].required is False)
        self.assertTrue(form.fields['ghost_field'].disabled is True)
        self.assertIsInstance(form.fields['ghost_field'].widget, HiddenInput)
        self.assertTrue(form.fields['auctioneer'].required is False)
        self.assertTrue(form.fields['auctioneer'].disabled is True)
        self.assertTrue(form.fields['auctioneer'].max_length == USERNAME_MAX_LEN)
        self.assertIsInstance(form.fields['auctioneer'].widget, HiddenInput)
        self.assertTrue(form.fields['bid_value'].required is False)
        self.assertTrue(form.fields['bid_value'].min_value == highest_price)
        self.assertTrue(form.fields['bid_value'].initial == highest_price)


class CommentFormTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.listing = get_listing()
        cls.user = get_profile('Lizard')

    def test_comment_form_normal_case(self):
        form = CommentForm(
            data={'text_field': 'Nic~se'},
            instance=self.listing,
            initial={'author_hidden': self.user.username},
        )
        self.assertTrue(form.is_valid())
        form.save()
        self.assertTrue(self.user.comment_set.filter(text='Nic~se').exists())
        self.assertTrue(self.listing.comment_set.filter(text='Nic~se').exists())

    def test_comment_form_boundary_values(self):
        form = CommentForm()
        self.assertTrue(form.fields['author_hidden'].required is True)
        self.assertTrue(form.fields['author_hidden'].disabled is True)
        self.assertTrue(form.fields['author_hidden'].max_length == USERNAME_MAX_LEN)
        self.assertIsInstance(form.fields['author_hidden'].widget, HiddenInput)
        self.assertTrue(form.fields['text_field'].required is True)
        self.assertTrue(form.fields['text_field'].min_length == 5)


class CreateListingFormTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user = get_profile('LuckyBeast')
        cls.category = get_category(label='Buns')
        cls.slug = 'japari-pie'

        cls.test_image = SimpleUploadedFile(IMGNAME, SMALL_GIF, content_type='image/gif')
        cls.image_path = Path(
            settings.MEDIA_ROOT / user_media_path(slug=cls.slug, filename=IMGNAME)
        ).resolve()

    @classmethod
    def tearDownClass(cls):
        if cls.image_path.exists():
            cls.image_path.unlink()
        if cls.image_path.parent.exists() and \
                not [f for f in cls.image_path.parent.iterdir()]:
            cls.image_path.parent.rmdir()
        super().tearDownClass()

    def test_create_form_normal_case(self):
        """ May crash if other tests are using TEST_IMAGE. """
        form = CreateListingForm(
            data={
                'slug': self.slug,
                'title': 'Japari Pie',
                'category': self.category.id,
                'starting_price': 9,
                'description': 'Restores your powers instantly!',
            },
            files={'image': self.test_image},
            initial={'owner': self.user}
        )
        form.fields['owner'].queryset = Profile.manager.all()

        self.assertTrue(form.is_valid())
        listing = form.save()
        self.assertTrue(listing.category == self.category)
        self.assertTrue(listing.owner == self.user)
        self.assertTrue(self.image_path.exists())

    def test_create_form_boundary_values(self):
        form = CreateListingForm()
        self.assertTrue(form.fields['slug'].required is False)
        self.assertTrue(form.fields['title'].required is True)
        self.assertTrue(form.fields['category'].required is True)
        self.assertTrue(form.fields['starting_price'].required is True)
        self.assertTrue(form.fields['starting_price'].min_value == MONEY_MIN_VALUE)
        self.assertTrue(form.fields['description'].required is True)
        self.assertTrue(form.fields['description'].min_length == 10)
        self.assertTrue(form.fields['image'].required is True)
        self.assertTrue(form.fields['owner'].required is True)
        self.assertTrue(form.fields['owner'].disabled is True)
        self.assertIsInstance(form.fields['owner'].widget, HiddenInput)


class EditListingFormTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user = get_profile('Kaban-chan')
        cls.category = get_category(label='Gear')
        cls.listing = get_listing(
            cls.category, cls.user, title='bakpck',
            description='Reliable and handy backpack.'
        )

    def test_edit_form_normal_case(self):
        updated_descr = 'Reliable & handy backpack for ' \
                        'long hikes in search of adventures and friends!'
        data = {
            'title': 'Backpack',
            'starting_price': 6,
            'category': self.category.id,
            'description': updated_descr,
        }
        form = EditListingForm(instance=self.listing, data=data)

        self.assertTrue(form.is_valid())
        listing = form.save()
        self.assertTrue(self.listing.title == 'Backpack')
        self.assertTrue(self.listing.starting_price == 6)
        self.assertTrue(self.listing.description == updated_descr)

    def test_edit_form_and_publish(self):
        data = {
            'title': 'Foo',
            'starting_price': 9,
            'category': self.category.id,
            'description': 'bar baz qux quux',
            'button_publish': ['']
        }
        form = EditListingForm(instance=self.listing, data=data)

        self.assertTrue(form.is_valid())
        listing = form.save()
        self.assertTrue(self.listing.is_active is True)

        # clear
        self.listing.withdraw()

    def test_edit_form_boundary_values(self):
        form = EditListingForm()
        self.assertTrue(form.fields['title'].required is True)
        self.assertTrue(form.fields['category'].required is True)
        self.assertTrue(form.fields['starting_price'].required is True)
        self.assertTrue(form.fields['starting_price'].min_value == MONEY_MIN_VALUE)
        self.assertTrue(form.fields['description'].required is True)
        self.assertTrue(form.fields['description'].min_length == 10)
        self.assertTrue(form.fields['image'].required is True)
