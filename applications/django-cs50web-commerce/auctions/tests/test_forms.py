import tempfile
import datetime
from pathlib import Path

from django.test import TestCase, SimpleTestCase, override_settings
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse, reverse_lazy
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile
from django.forms import HiddenInput


from django.contrib.auth.models import User
from accounts.models import ProxyUser
from auctions.models import (
    Profile, ListingCategory, Comment,
    Listing, Watchlist, Bid, Log,
    user_media_path
)
from auctions.forms import (
    TransferMoneyForm, PublishListingForm,
    AuctionLotForm, CommentForm,
    CreateListingForm, EditListingForm,
    MONEY_MIN_VALUE, MONEY_MAX_VALUE,
    USERNAME_MAX_LEN
)
from .tests import (
    DATABASES, TEST_IMAGE,
    TMP_IMAGE, IMGNAME,
    get_category, get_profile,
    get_listing, get_comment
)

""" TODO
+ TransferMoneyForm
+ PublishListingForm
- AuctionLotForm
+ CommentForm
- CreateListingForm
- EditListingForm
"""


class TransferMoneyFormTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.profile = get_profile('Capybara', money=10)

    def test_add_money_normal_case(self):
        data = {'transfer_money': 10}
        form = TransferMoneyForm(instance=self.profile, data=data)
        self.assertTrue(form.is_valid())
        self.profile.refresh_from_db()
        self.assertEqual(self.profile.display_money(), (20, 0))

    def test_add_money_boundary_values(self):
        form = TransferMoneyForm()
        self.assertTrue(form.fields['transfer_money'].required is True)
        self.assertTrue(form.fields['transfer_money'].min_value == MONEY_MIN_VALUE)
        self.assertTrue(form.fields['transfer_money'].max_value == MONEY_MAX_VALUE)


class PublishListingFormTests(TestCase):
    databases = DATABASES

    def test_publish_normal_case(self):
        listing = get_listing()
        form = PublishListingForm(instance=listing, data={'ghost_field': ''})
        self.assertTrue(form.is_valid(), 'normal')
        listing.refresh_from_db()
        self.assertTrue(listing.is_active)

        form2 = PublishListingForm(instance=listing, data={'ghost_field': ''})
        self.assertFalse(form2.is_valid(), 'already published')
        error_message = form2.errors['__all__'].as_data()[0].message
        self.assertTrue('already published' in error_message)


class AuctionLotFormTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_profile('LuckyBeast')
        cls.category = get_category(label='Buns')
        cls.listing = get_listing(
            category=cls.category,
            profile=cls.user1,
            title='White Japari Bun',
            description='An ultra rare valuable item.'
        )
        cls.listing.publish_the_lot()

    def setUp(self):
        self.form = AuctionLotForm(instance=self.listing)

    def test_owner_closed_auction(self):
        pass

    def test_owner_withdrew(self):
        pass

    def test_user_bid(self):
        pass

    def test_user_watching_and_unwatched(self):
        profile = get_profile('Rhinoceros')

        form1 = AuctionLotForm({'btn_user_watching': ['']}, instance=self.listing)
        form1.fields['auctioneer'].initial = profile.username
        self.assertTrue(form1.is_valid(), 'watching ok')
        profile.refresh_from_db()
        self.assertTrue(profile.items_watched.contains(self.listing))

        form2 = AuctionLotForm({'btn_user_watching': ['']}, instance=self.listing)
        form2.fields['auctioneer'].initial = profile.username
        self.assertFalse(form2.is_valid(), 'already watching')
        error_message = form2.errors['__all__'].as_data()[0].message
        self.assertTrue('already watching' in error_message)

        form3 = AuctionLotForm({'btn_user_unwatched': ['']}, instance=self.listing)
        form3.fields['auctioneer'].initial = profile.username
        self.assertTrue(form3.is_valid(), 'unwatched ok')
        profile.refresh_from_db()
        self.assertFalse(profile.items_watched.contains(self.listing))

        form4 = AuctionLotForm({'btn_user_unwatched': ['']}, instance=self.listing)
        form4.fields['auctioneer'].initial = self.user1.username
        self.assertFalse(form4.is_valid(), 'can’t unwatch')
        error_message = form4.errors['__all__'].as_data()[0].message
        self.assertTrue('can’t unwatch' in error_message)

    def test_lot_boundary_values(self):
        form = self.form
        highest_price = self.listing.get_highest_price(percent=True)
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

    def test_comment_normal_case(self):
        listing = get_listing()
        user = get_profile('Lizard')

        form = CommentForm(
            instance=listing,
            initial={'author_hidden': user.username},
            data={'text_field': 'Nic~se'}
        )
        self.assertTrue(form.is_valid())
        self.assertTrue(user.comment_set.filter(text='Nic~se').exists())
        self.assertTrue(listing.comment_set.filter(text='Nic~se').exists())

    def test_comment_boundary_values(self):
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
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_profile('LuckyBeast')
        cls.category = get_category(label='Buns')
        cls.slug = 'japari-pie'

        date = timezone.localdate().strftime('%Y.%m.%d')
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

    def test_create_normal_case(self):
        data = {
            'slug': 'japari-pie',
            'title': 'Japari Pie',
            'category': self.category.id,
            'starting_price': 9,
            'description': 'Restores your powers instantly!',
        }
        file_data = {'image': TEST_IMAGE}
        form = CreateListingForm(
            data=data,
            files=file_data,
            initial={'owner': self.user}
        )
        form.fields['owner'].queryset = Profile.manager.all()

        self.assertTrue(form.is_valid())
        listing = form.save()
        self.assertTrue(listing.category == self.category)
        self.assertTrue(listing.owner == self.user)
        self.assertTrue(self.image_path.exists())

    def test_create_boundary_values(self):
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
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_profile('Kaban-chan')
        cls.category = get_category(label='Gear')
        cls.listing = get_listing(
            cls.category, cls.user, title='Bakpack',
            description='Reliable and handy backpack for '
                        'long hikes in search of adventures and friends.'
        )

    def tearDown(self):
        if self.listing.is_active:
            self.listing.withdraw()

    def test_edit_normal_case(self):
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
        form.save()
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.title == 'Backpack')
        self.assertTrue(self.listing.starting_price == 6)
        self.assertTrue(self.listing.description == updated_descr)

    def test_edit_and_publish(self):
        data = {
            'title': 'Foo',
            'starting_price': 9,
            'category': self.category.id,
            'description': 'bar baz qux quux',
            'button_publish': ['']
        }
        form = EditListingForm(instance=self.listing, data=data)

        self.assertTrue(form.is_valid())
        form.save()
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active is True)

    def test_edit_boundary_values(self):
        form = EditListingForm()
        self.assertTrue(form.fields['title'].required is True)
        self.assertTrue(form.fields['category'].required is True)
        self.assertTrue(form.fields['starting_price'].required is True)
        self.assertTrue(form.fields['starting_price'].min_value == MONEY_MIN_VALUE)
        self.assertTrue(form.fields['description'].required is True)
        self.assertTrue(form.fields['description'].min_length == 10)
        self.assertTrue(form.fields['image'].required is True)






















#
