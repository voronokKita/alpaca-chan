import tempfile
import datetime

from django.test import TestCase, SimpleTestCase, Client, override_settings
from django.utils import timezone
from django.utils.text import slugify
from django.urls import reverse, reverse_lazy
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile


from django.contrib.auth.models import User
from accounts.models import ProxyUser
from auctions.models import (
    Profile, ListingCategory, Comment,
    Listing, Watchlist, Bid, Log
)
from auctions.forms import (
    TransferMoneyForm, PublishListingForm,
    AuctionLotForm, CommentForm,
    CreateListingForm, EditListingForm,
    MONEY_MIN_VALUE, MONEY_MAX_VALUE, USERNAME_MAX_LEN
)
from auctions.views import (
    AuctionsIndexView, ProfileView, UserHistoryView,
    WatchlistView, CreateListingView, ListingView,
    EditListingView, AuctionLotView, CommentsView, BidView
)
from auctions.mixins import (
    AuctionsAuthMixin, ProfileMixin, RestrictPkMixin,
    NavbarMixin, PresetMixin, ListingRedirectMixin
)
from .tests import (
    DATABASES, TEST_IMAGE, IMGNAME, FAST_HASHER,
    get_category, get_profile, get_listing
)

""" TODO
- AuctionsAuthMixin
- ProfileMixin
- RestrictPkMixin
- NavbarMixin
- PresetMixin
- ListingRedirectMixin
+ Index View
    + filter by category
    + listing page link
    + navbar
    + session
- Profile View
    - add_money func
    - restrictions
    - navbar
    - session
- History View
    - restrictions
    - navbar
    - session
- Watchlist View
    - listing_owned
    - owned_and_published
    - listing_watched
    - listing & lot link
    - restrictions
    - navbar
    - session
- Create View
    - create listing form
    - restrictions
    - navbar
    - session
- Listing View
    - publish
    - edit
    - comments & page link
    - restrictions
    - navbar
    - session
- Edit View
    - go back
    - save
    - save & publish
    - restrictions
    - navbar
    - session
- Lot View
    - btn owner_closed
    - btn owner_withdrew
    - btn user_bid
    - btn watch & unwatch
    - bid page link
    - comments & page link
    - comment form
    - restrictions
    - navbar
    - session
- Comments View
    - form
    - go back
    - restrictions
    - navbar
    - session
- Bid View
    - go back
    - restrictions
    - navbar
    - session
"""


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
def get_user(username):
    return User.objects.create(username=username, password=make_password('qwerty'))


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
def check_session(self_, url, username:str, pk:int = None):
    """
    Checks that the profile's pk has been written to the session through the ProfileMixin.
    :username: the username that is contained in both User & Profile models.
    """
    if not pk:
        profile = Profile.manager.get(username=username)
        pk = profile.pk

    self_.assertTrue(self_.client.login(username=username, password='qwerty'))
    self_.client.get(url)
    self_.assertTrue(self_.client.session['auctioneer_pk'] == pk)


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
def test_navbar(self_, url, user:str, categories:list = None, active:str = None):
    """
    Checks the work of the NavbarMixin.
    :user: the username that is contained in both User & Profile models.
    Active pages are:
        'Active Listings', 'Watchlist',
        'Create Listing', 'Wallet', 'History'
    """
    def check_active_page(rsp):
        if active:
            self_.assertContains(
                rsp, html=True,
                text='<a class="nav-link active" href="%s">%s</a>' % (url, active),
            )

    # anonymous
    response = self_.client.get(url)
    self_.assertEqual(response.status_code, 200)
    self_.assertContains(response, 'Active Listings')
    self_.assertContains(response, 'Category')
    [self_.assertContains(response, category) for category in categories]
    self_.assertNotContains(response, 'Watchlist')
    self_.assertNotContains(response, 'Create Listing')
    self_.assertNotContains(response, 'Wallet')
    self_.assertNotContains(response, 'History')
    self_.assertContains(response, 'Alpaca’s Cafe')
    self_.assertContains(response, 'Register')
    self_.assertContains(response, 'Login')
    check_active_page(response)

    # user
    self_.assertTrue(self_.client.login(username=user, password='qwerty'))
    response = self_.client.get(url)
    self_.assertEqual(response.status_code, 200)
    self_.assertContains(response, 'Active Listings')
    self_.assertContains(response, 'Category')
    [self_.assertContains(response, category) for category in categories]
    self_.assertContains(response, 'Watchlist')
    self_.assertContains(response, 'Create Listing')
    self_.assertContains(response, 'Wallet')
    self_.assertContains(response, 'History')
    self_.assertContains(response, 'Alpaca’s Cafe')
    self_.assertContains(response, 'Hippo')
    self_.assertContains(response, 'Logout')
    check_active_page(response)


class AuctionsIndexViewTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.url = reverse('auctions:index')
        cls.category1 = get_category('BUNS')
        cls.category2 = get_category('PIES')
        cls.user = get_user('Hippo')
        cls.hippo = Profile.manager.get(username='Hippo')
        cls.hippo.add_money(100)
        cls.hippo.refresh_from_db()
        cls.item1 = get_listing(
            cls.category1,
            profile=cls.hippo,
            title='ghost item one',
            description='lorem ipsum dolor sit amet.'
        )
        cls.item2 = get_listing(
            cls.category2,
            username='Monkey',
            title='ghost item two',
            description='sed ut perspiciatis unde omnis.'
        )
        cls.item1.starting_price = 20
        cls.item1.save()
        cls.item1.publish_the_lot()
        cls.item2.publish_the_lot()
        cls.item2.make_a_bid(cls.hippo, 15)

    def test_index_loads(self):
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ghost item one', msg_prefix='capfirst')
        self.assertContains(response, 'Ghost item two', msg_prefix='capfirst')
        self.assertContains(response, 'buns', msg_prefix='lower')
        self.assertContains(response, 'pies', msg_prefix='lower')
        self.assertContains(response, 'Price: 🪙20')
        self.assertContains(response, 'Price: 🪙15')
        self.assertContains(response, 'Lorem ipsum dolor sit amet.', msg_prefix='capfirst')
        self.assertContains(response, 'Sed ut perspiciatis unde omnis.', msg_prefix='capfirst')
        self.assertContains(response, 'Published:', 2)
        self.assertContains(response, f'href=\'{self.item1.get_absolute_url()}\'')
        self.assertContains(response, f'href=\'{self.item2.get_absolute_url()}\'')

        # by category
        response = self.client.get(reverse('auctions:category', args=[self.category1.pk]))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Ghost item one', msg_prefix='does have buns')
        self.assertNotContains(response, 'Ghost item two', msg_prefix='does not have pies')

        # no items
        self.item1.withdraw()
        self.item2.withdraw()
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'There are currently no auctions.')

    def test_index_navbar(self):
        test_navbar(
            self,
            url=self.url,
            user='Hippo',
            categories=['BUNS', 'PIES'],
            active='Active Listings',
        )

    def test_index_session_loads(self):
        check_session(
            self,
            url=self.url,
            username='Hippo',
            pk=self.hippo.pk,
        )





























#
