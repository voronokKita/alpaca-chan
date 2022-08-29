import tempfile
import datetime
from pathlib import Path

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
    Listing, Watchlist, Bid, Log,
    LOG_REGISTRATION, user_media_path
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
+ AuctionsAuthMixin
+ ProfileMixin
+ RestrictPkMixin
+ NavbarMixin
+ PresetMixin
+ ListingRedirectMixin
+ Index View
    + filter by category
    + listing page links
+ Profile View
    + add money form
+ History View
+ Watchlist View
    + listing owned list
    + owned & published list
    + listing watched list
    + listing & lot links
+ Create View
    + create listing form
+ Listing View
    + publish form
    + edit link
    + comments & comment page link
+ Edit View
    + save form
    + save & publish from
    + the listing's go back link
- Lot View
    - btn owner_closed
    - btn owner_withdrew
    - btn user_bid
    - btn watch & unwatch
    - comments & comments page link
    - comment form
    - bids page link
+ Comments View
    + comment form
    + the listing's go back link
+ Bid View
    + the listing's go back link
"""


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
def get_user(username) -> User:
    return User.objects.create(username=username, password=make_password('qwerty'))


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
def login_user(self_, username) -> bool:
    return self_.client.login(username=username, password='qwerty')


class AbstractTestMixin:
    active_page = None
    test_url = None
    test_categories = []
    owner_profile = None
    second_profile = None
    listing = None


class TestAccessMixin(AbstractTestMixin):
    """ A page is only available to the profile's owner.
        AuctionsAuthMixin & RestrictPkMixin & ListingRedirectMixin. """

    def test_page_access(self):
        self.assertTrue(login_user(self, self.second_profile.username))
        response = self.client.get(self.test_url)
        self.assertRedirects(response, reverse('auctions:index'), 302, 200)


class TestRedirectMixin(AbstractTestMixin):
    """ Logic form ListingRedirectMixin.
        Request of a published auction lot by
        url of an unpublished listing, and vice versa. """

    def test_wrong_listing_url(self):
        slug = self.listing.slug
        self.assertTrue(login_user(self, self.owner_profile))
        if self.listing.is_active:
            response = self.client.get(reverse('auctions:listing', args=[slug]))
            self.assertRedirects(response, reverse('auctions:auction_lot', args=[slug]), 302, 200)
        else:
            response = self.client.get(reverse('auctions:auction_lot', args=[slug]))
            self.assertRedirects(response, reverse('auctions:listing', args=[slug]), 302, 200)


class TestSessionMixin(AbstractTestMixin):
    """ Checks that the profile's pk has been written to the session through the ProfileMixin. """

    @override_settings(PASSWORD_HASHERS=FAST_HASHER)
    def test_page_session_loads(self):
        self.assertTrue(self.client.login(username=self.owner_profile.username,
                                          password='qwerty'))
        self.client.get(self.test_url)
        self.assertTrue(self.client.session['auctioneer_pk'] == self.owner_profile.pk)


class TestNavbarMixin(AbstractTestMixin):
    """ Checks the work of the NavbarMixin. """

    @override_settings(PASSWORD_HASHERS=FAST_HASHER)
    def test_page_navbar(self):
        """ Active pages are:
            'Active Listings', 'Watchlist', 'Create Listing', 'Wallet', 'History' """

        def check_active_page_class(rsp):
            if self.active_page:
                self.assertContains(
                    rsp, html=True,
                    text='<a class="nav-link active" href="%s">%s</a>'
                         % (self.test_url, self.active_page),
                )

        def items_on_both_pages(rsp):
            self.assertContains(response, 'Active Listings')
            self.assertContains(response, f'href=\"{reverse("auctions:index")}\"')
            self.assertContains(response, 'Alpaca’s Cafe')
            self.assertContains(response, f'href=\"{reverse("core:index")}\"')
            self.assertContains(response, 'Category')
            [self.assertContains(response, category.label) for category in self.test_categories]
            for category in self.test_categories:
                category_href = f'href=\"{reverse("auctions:category", args=[category.pk])}\"'
                self.assertContains(response, category_href)

        # anonymous
        response = self.client.get(self.test_url)
        self.assertIn(response.status_code, (200, 302))
        if response.status_code == 200:
            check_active_page_class(response)
            items_on_both_pages(response)
            self.assertNotContains(response, 'Watchlist')
            self.assertNotContains(response, 'Create Listing')
            self.assertNotContains(response, 'Wallet')
            self.assertNotContains(response, 'History')
            self.assertContains(response, 'Register')
            href = f'href=\"{reverse("accounts:register_and_next", args=["auctions"])}\"'
            self.assertContains(response, href)
            self.assertContains(response, 'Login')
            href = f'href=\"{reverse("accounts:login_and_next", args=["auctions"])}\"'
            self.assertContains(response, href)

        # user
        self.assertTrue(self.client.login(username=self.owner_profile.username, password='qwerty'))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)
        check_active_page_class(response)
        items_on_both_pages(response)
        self.assertContains(response, 'Watchlist')
        href = f'href=\"{reverse("auctions:watchlist", args=[self.owner_profile.pk])}\"'
        self.assertContains(response, href)
        self.assertContains(response, 'Create Listing')
        href = f'href=\"{reverse("auctions:create_listing", args=[self.owner_profile.pk])}\"'
        self.assertContains(response, href)
        self.assertContains(response, 'Wallet')
        href = f'href=\"{reverse("auctions:profile", args=[self.owner_profile.pk])}\"'
        self.assertContains(response, href)
        self.assertContains(response, 'History')
        href = f'href=\"{reverse("auctions:user_history", args=[self.owner_profile.pk])}\"'
        self.assertContains(response, href)
        self.assertContains(response, self.owner_profile.username)
        self.assertContains(response, 'Logout')
        href = f'href=\"{reverse("accounts:logout_and_next", args=["auctions"])}\"'
        self.assertContains(response, href)


class TestNavbarAndSessionMixin(TestSessionMixin, TestNavbarMixin):
    """
    Checks that the profile's pk has been written to the session through the ProfileMixin.
    """


class AuctionsIndexViewTests(TestNavbarAndSessionMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user = get_user('Hippo')
        cls.owner_profile = Profile.manager.get(username='Hippo')
        cls.owner_profile.add_money(100)
        cls.owner_profile.refresh_from_db()

        cls.category1 = get_category('BUNS')
        cls.category2 = get_category('PIES')

        cls.item1 = get_listing(
            cls.category1,
            profile=cls.owner_profile,
            title='ghost item one',
            description='lorem ipsum dolor sit amet.'
        )
        cls.item1.starting_price = 20
        cls.item1.save()
        cls.item1.publish_the_lot()

        cls.item2 = get_listing(
            cls.category2,
            username='Monkey',
            title='ghost item two',
            description='sed ut perspiciatis unde omnis.'
        )
        cls.item2.publish_the_lot()
        cls.item2.make_a_bid(cls.owner_profile, 15)

        cls.test_url = reverse('auctions:index')
        cls.active_page = 'Active Listings'
        cls.test_categories = [cls.category1, cls.category2]

    def test_index_loads(self):
        response1 = self.client.get(self.test_url)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, 'Ghost item one', msg_prefix='capfirst')
        self.assertContains(response1, 'Ghost item two', msg_prefix='capfirst')
        self.assertContains(response1, 'buns', msg_prefix='lower')
        self.assertContains(response1, 'pies', msg_prefix='lower')
        self.assertContains(response1, 'Price: 🪙20')
        self.assertContains(response1, 'Price: 🪙15')
        self.assertContains(response1, 'Lorem ipsum dolor sit amet.', msg_prefix='capfirst')
        self.assertContains(response1, 'Sed ut perspiciatis unde omnis.', msg_prefix='capfirst')
        self.assertContains(response1, 'Published:', 2)
        self.assertContains(response1, f'href=\'{self.item1.get_absolute_url()}\'')
        self.assertContains(response1, f'href=\'{self.item2.get_absolute_url()}\'')

        # by category
        response2 = self.client.get(reverse('auctions:category', args=[self.category1.pk]))
        self.assertEqual(response2.status_code, 200)
        self.assertContains(response2, 'Ghost item one', msg_prefix='does have buns')
        self.assertNotContains(response2, 'Ghost item two', msg_prefix='does not have pies')

        # no items
        self.item1.withdraw()
        self.item2.withdraw()
        response3 = self.client.get(self.test_url)
        self.assertEqual(response3.status_code, 200)
        self.assertContains(response3, 'There are currently no auctions.')


class ProfileViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Rhino')
        cls.owner_profile = Profile.manager.get(username='Rhino')
        cls.owner_profile.add_money(115)
        cls.owner_profile.refresh_from_db()

        cls.user2 = get_user('Hippo')
        cls.second_profile = Profile.manager.get(username='Hippo')

        cls.category = get_category('Buns')
        cls.item = get_listing(
            cls.category,
            profile=cls.second_profile,
            title='ghost item one',
            description='lorem ipsum dolor sit amet.'
        )
        cls.item.publish_the_lot()
        cls.item.make_a_bid(cls.owner_profile, 15)

        cls.test_url = reverse('auctions:profile', args=[cls.owner_profile.pk])
        cls.active_page = 'Wallet'
        cls.test_categories = [cls.category]

    def test_profile_loads(self):
        form_input = '<input type="number" name="transfer_money" placeholder="0.01" ' \
                     'class="form-control" autocomplete="off" min="0.01" max="9999.99" ' \
                     'step="any" required="" id="id_transfer_money">'
        button_input = '<button type="submit" class="btn btn-primary">Transfer</button>'

        if self.owner_profile.money != 100:
            self.owner_profile.money = 100
            self.owner_profile.save()

        self.assertTrue(login_user(self, self.owner_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Available money:')
        self.assertContains(response, '🪙100')
        self.assertContains(response, 'Total bids:')
        self.assertContains(response, '🪙15')
        self.assertContains(response, form_input, html=True)
        self.assertContains(response, button_input, html=True)

    def test_profile_add_money_form(self):
        self.assertTrue(login_user(self, self.owner_profile.username))
        response_post = self.client.post(self.test_url, {'transfer_money': 20.05})
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(self.test_url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, '🪙120.05')


class UserHistoryViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Tamandua')
        cls.owner_profile = Profile.manager.get(username='Tamandua')
        cls.user2 = get_user('Peafowl')
        cls.second_profile = Profile.manager.get(username='Peafowl')
        cls.category = get_category('Buns')

        cls.test_url = reverse('auctions:user_history', args=[cls.owner_profile.pk])
        cls.active_page = 'History'
        cls.test_categories = [cls.category]

    def test_history_loads(self):
        self.assertTrue(login_user(self, self.owner_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, LOG_REGISTRATION)


class WatchlistViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Aurochs')
        cls.owner_profile = Profile.manager.get(username='Aurochs')
        cls.owner_profile.add_money(100)
        cls.owner_profile.refresh_from_db()

        cls.user2 = get_user('Oryx')
        cls.second_profile = Profile.manager.get(username='Oryx')
        cls.second_profile.add_money(100)
        cls.second_profile.refresh_from_db()

        cls.category1 = get_category('PIES')
        cls.category2 = get_category('BUNS')
        cls.category3 = get_category('CAKES')

        cls.item_owned = get_listing(
            cls.category1,
            cls.owner_profile,
            title='apple pie',
            description='lorem ipsum dolor sit amet',
        )
        cls.item_owned_and_published = get_listing(
            cls.category2,
            cls.owner_profile,
            title='white bun',
            description='sed ut perspiciatis unde omnis iste',
        )
        cls.item_owned_and_published.publish_the_lot()
        cls.item_owned_and_published.make_a_bid(cls.second_profile, 10)

        cls.item_watched = get_listing(
            cls.category3,
            cls.second_profile,
            title='chocolate cake',
            description='but I must explain to you',
        )
        cls.item_watched.publish_the_lot()
        cls.item_watched.make_a_bid(cls.owner_profile, 20)

        cls.test_url = reverse('auctions:watchlist', args=[cls.owner_profile.pk])
        cls.active_page = 'Watchlist'
        cls.test_categories = [cls.category1, cls.category2, cls.category3]

    def test_watchlist_loads(self):
        self.assertTrue(login_user(self, self.owner_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        # owned
        self.assertContains(response, 'Apple pie', msg_prefix='capfirst')
        self.assertContains(response, 'Category: pies', msg_prefix='lower')
        self.assertContains(response, 'Starting price: 🪙1')
        self.assertContains(response, 'Lorem ipsum dolor sit amet', msg_prefix='capfirst')
        self.assertContains(response, 'Not Published')
        self.assertContains(response, f'href=\'{self.item_owned.get_absolute_url()}\'')

        # item owned and published
        self.assertContains(response, 'White bun', msg_prefix='capfirst')
        self.assertContains(response, 'Category: buns', msg_prefix='lower')
        self.assertContains(response, 'Price: 🪙10')
        self.assertContains(response, 'Sed ut perspiciatis unde omnis iste', msg_prefix='capfirst')
        self.assertContains(response, f'href=\'{self.item_owned_and_published.get_absolute_url()}\'')

        # item watched
        self.assertContains(response, 'Chocolate cake', msg_prefix='capfirst')
        self.assertContains(response, 'Category: cakes', msg_prefix='lower')
        self.assertContains(response, 'Price: 🪙20')
        self.assertContains(response, 'But I must explain to you', msg_prefix='capfirst')
        self.assertContains(response, f'href=\'{self.item_watched.get_absolute_url()}\'')

        self.assertContains(response, 'Published:', 2)


class CreateListingViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Beaver')
        cls.owner_profile = Profile.manager.get(username='Beaver')
        cls.user2 = get_user('Porcupine')
        cls.second_profile = Profile.manager.get(username='Porcupine')

        cls.category1 = get_category('Buns')
        cls.category2 = get_category('Pies')

        cls.slug = 'japari-bun'
        cls.image_path = Path(
            settings.MEDIA_ROOT / user_media_path(slug=cls.slug, filename=IMGNAME)
        ).resolve()

        cls.test_url = reverse('auctions:create_listing', args=[cls.owner_profile.pk])
        cls.active_page = 'Create Listing'
        cls.test_categories = [cls.category1, cls.category2]

    @classmethod
    def tearDownClass(cls):
        if cls.image_path.exists():
            cls.image_path.unlink()
        if cls.image_path.parent.exists() and \
                not [f for f in cls.image_path.parent.iterdir()]:
            cls.image_path.parent.rmdir()
        super().tearDownClass()

    def test_create_loads(self):
        slug_input = '<input type="text" name="slug"'
        title_input = '<input type="text" name="title"'
        category_input = '<select name="category" class="form-control" required="" id="id_category">' \
                         '<option value="" selected="">---------</option>' \
                         '<option value="%d">%s</option><option value="%d">%s</option></select>' \
                         % (self.category1.id, self.category1.label, self.category2.id, self.category2.label)
        price_input = '<input type="number" name="starting_price"'
        descr_input = '<textarea name="description"'
        img_input = '<input type="file" name="image" class="form-control" ' \
                    'accept="image/*" required="" id="id_image">'
        hidden_profile = '<input type="hidden" name="owner" value="%d" ' \
                         'disabled="" id="id_owner">' % self.owner_profile.id
        button_input = '<button type="submit" class="btn btn-success">Create</button>'

        self.assertTrue(login_user(self, self.owner_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, slug_input)
        self.assertContains(response, title_input)
        self.assertContains(response, category_input, html=True)
        self.assertContains(response, price_input)
        self.assertContains(response, descr_input)
        self.assertContains(response, img_input, html=True)
        self.assertContains(response, hidden_profile, html=True)
        self.assertContains(response, img_input, html=True)

    def test_create_form(self):
        data = {
            'slug': 'japari-bun',
            'title': 'Japari Bun',
            'category': self.category1.id,
            'starting_price': 5,
            'description': 'Lorem ipsum dolor sit amet',
            'image': TEST_IMAGE,
            'owner': self.owner_profile.id,
        }
        self.assertTrue(login_user(self, self.owner_profile.username))
        response_post = self.client.post(self.test_url, data)
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Japari Bun')
        self.assertTrue(self.image_path.exists())


class ListingViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestRedirectMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('CampoFlicker')
        cls.owner_profile = Profile.manager.get(username='CampoFlicker')
        cls.user2 = get_user('Capybara')
        cls.second_profile = Profile.manager.get(username='Capybara')

        cls.category = get_category('BUNS')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='japari bun',
            description='lorem ipsum dolor sit amet',
        )
        cls.listing.comment_set.create(author=cls.second_profile, text='first comment')
        cls.listing.comment_set.create(author=cls.second_profile, text='second comment')

        cls.test_url = reverse('auctions:listing', args=[cls.listing.slug])
        cls.test_categories = [cls.category]

    def test_listing_loads(self):
        self.assertTrue(login_user(self, self.owner_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Japari bun', msg_prefix='capfirst')
        self.assertContains(response, 'Category: buns', msg_prefix='lower')
        self.assertContains(response, 'Starting price: 🪙1')
        self.assertContains(response, 'Lorem ipsum dolor sit amet', msg_prefix='capfirst')
        self.assertContains(response, 'Created:')

        self.assertContains(response, self.second_profile.username)
        self.assertContains(response, 'first comment')
        self.assertContains(response, 'second comment')

        edit_url = reverse('auctions:edit_listing', args=[self.listing.slug])
        comments_url = reverse('auctions:comments', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{edit_url}\'')
        self.assertContains(response, f'href=\'{comments_url}\'')

        ghost_field = '<input type="hidden" name="ghost_field" disabled="" id="id_ghost_field">'
        button_input = '<button type="submit" class="btn btn-warning">Publish and start the auction</button>'
        self.assertContains(response, ghost_field, html=True)
        self.assertContains(response, button_input, html=True)

    def test_publish_listing_form(self):
        self.assertTrue(login_user(self, self.owner_profile.username))
        response_post = self.client.post(self.test_url, {'ghost_field': True})
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)

        # clean
        self.assertTrue(self.listing.withdraw())


class EditListingViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('PrairieDog')
        cls.owner_profile = Profile.manager.get(username='PrairieDog')
        cls.user2 = get_user('Giraffe')
        cls.second_profile = Profile.manager.get(username='Giraffe')

        cls.category = get_category('Buns')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='Japari Bun',
            description='Lorem ipsum dolor sit amet',
        )
        cls.test_url = reverse('auctions:edit_listing', args=[cls.listing.slug])
        cls.test_categories = [cls.category]

    def test_edit_loads(self):
        self.assertTrue(login_user(self, self.owner_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        go_back_url = reverse('auctions:listing', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{go_back_url}\'')

        title_input = '<input type="text" name="title"'
        category_input = '<select name="category"'
        price_input = '<input type="number" name="starting_price"'
        descr_input = '<textarea name="description"'
        image_input = '<input type="file" name="image" class="form-control" accept="image/*" id="id_image">'
        button_save = '<button type="submit" name="button_save" class="btn btn-success">Save changes</button>'
        button_save_and_publish = '<button type="submit" name="button_publish" ' \
                                  'class="btn btn-warning">Save and start the auction</button>'
        self.assertContains(response, title_input)
        self.assertContains(response, category_input)
        self.assertContains(response, price_input)
        self.assertContains(response, descr_input)
        self.assertContains(response, image_input, html=True)
        self.assertContains(response, button_save, html=True)
        self.assertContains(response, button_save_and_publish, html=True)

    def test_edit_form_save(self):
        form_data = {
            'title': 'Big Japari Bun',
            'category': self.category.id,
            'starting_price': 10,
            'description': 'Sed ut perspiciatis unde omnis.',
            'button_save': [''],
        }
        self.assertTrue(login_user(self, self.owner_profile.username))
        response_post = self.client.post(self.test_url, form_data)
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Big Japari Bun')

    def test_edit_form_save_and_start(self):
        form_data = {
            'title': 'Grand Japari Bun',
            'category': self.category.id,
            'starting_price': 20,
            'description': 'But I must explain to you',
            'button_publish': [''],
        }
        self.assertTrue(login_user(self, self.owner_profile.username))
        response_post = self.client.post(self.test_url, form_data)
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Grand Japari Bun')
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)

        # clean
        self.assertTrue(self.listing.withdraw())


class AuctionLotViewTests(TestNavbarAndSessionMixin, TestRedirectMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('TasmanianDevil')
        cls.owner_profile = Profile.manager.get(username='TasmanianDevil')
        cls.user2 = get_user('GrayWolf')
        cls.second_profile = Profile.manager.get(username='GrayWolf')
        cls.second_profile.add_money(100)
        cls.second_profile.refresh_from_db()

        cls.category = get_category('BUNS')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='japari bun',
            description='lorem ipsum dolor sit amet',
        )
        cls.listing.comment_set.create(author=cls.second_profile, text='first comment')
        cls.listing.comment_set.create(author=cls.second_profile, text='second comment')

        cls.test_url = reverse('auctions:auction_lot', args=[cls.listing.slug])
        cls.test_categories = [cls.category]

    def setUp(self):
        self.listing.refresh_from_db()
        self.listing.publish_the_lot()
        # self.listing.refresh_from_db()

    def tearDown(self):
        if self.listing.highest_bid:
            self.listing.withdraw()
            self.listing.publish_the_lot()
            self.listing.refresh_from_db()
        if self.listing.in_watchlist.contains(self.second_profile):
            self.listing.watchlist_set.filter(profile=self.second_profile).delete()

    def test_lot_loads_for_anonymous(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Japari bun', msg_prefix='capfirst')
        self.assertContains(response, 'Category: buns', msg_prefix='lower')
        self.assertContains(response, 'Bids placed</a>: 0')
        self.assertContains(response, 'Starting price: 🪙1')
        self.assertContains(response, 'Lorem ipsum dolor sit amet', msg_prefix='capfirst')
        self.assertContains(response, 'Published:')

        bids_url = reverse('auctions:bid', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{bids_url}\'')

        self.assertContains(response, self.second_profile.username)
        self.assertContains(response, 'first comment')
        self.assertContains(response, 'second comment')
        comments_url = reverse('auctions:comments', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{comments_url}\'')

        # lot form
        ghost_field = '<input type="hidden" name="ghost_field"'
        auctioneer_input = '<input type="hidden" name="auctioneer"'
        bid_input = '<input type="number" name="bid_value"'
        any_button = '<button type="submit"'
        self.assertNotContains(response, ghost_field, msg_prefix='no form for anon')
        self.assertNotContains(response, auctioneer_input, msg_prefix='no form for anon')
        self.assertNotContains(response, bid_input, msg_prefix='no form for anon')
        self.assertNotContains(response, any_button, msg_prefix='no form for anon')

        # comment form
        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden"'
        self.assertNotContains(response, text_input, msg_prefix='no form for anon')
        self.assertNotContains(response, author_hidden, msg_prefix='no form for anon')

    def test_lot_loads_for_user(self):
        self.assertTrue(login_user(self, self.second_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        # lot form
        n = self.listing.get_highest_price()
        ghost_field = '<input type="hidden" name="ghost_field"'
        auctioneer_input = '<input type="hidden" name="auctioneer" ' \
                           'value="%s" disabled="" id="id_auctioneer">' \
                           % self.second_profile.username
        bid_input = '<input type="number" name="bid_value" value="%d" class="form-control d-inline" ' \
                    'style="width: 100px;" min="%d" step="any" id="id_bid_value">' \
                    % (n, n)
        self.assertContains(response, ghost_field)
        self.assertContains(response, auctioneer_input, html=True)
        self.assertContains(response, bid_input, html=True)

        # buttons for the owner
        button_close = '<button type="submit" name="btn_owner_closed_auction" ' \
                       'class="btn btn-warning">Close the auction</button>'
        button_withdraw = '<button type="submit" name="btn_owner_withdrew" ' \
                          'class="btn btn-danger">Cancel the auction</button>'
        self.assertNotContains(response, button_close, html=True, msg_prefix='not for user')
        self.assertNotContains(response, button_withdraw, html=True, msg_prefix='not for user')

        # comment form
        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden" ' \
                        'value="%s" disabled="" id="id_author_hidden">' \
                        % self.second_profile.username
        button_save = '<button type="submit" class="btn btn-primary mb-5">Comment on</button>'
        self.assertContains(response, text_input)
        self.assertContains(response, author_hidden, html=True)
        self.assertContains(response, button_save, html=True)

    def test_lot_loads_for_user_watch_and_unwatch(self):
        self.assertTrue(login_user(self, self.second_profile.username))
        button_watch = '<button type="submit" name="btn_user_watching" ' \
                       'class="btn btn-info">Add to watchlist</button>'
        button_unwatch = '<button type="submit" name="btn_user_unwatched" ' \
                         'class="btn btn-info">Remove form watchlist</button>'

        # not watching
        response1 = self.client.get(self.test_url)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, button_watch, html=True, msg_prefix='ok')
        self.assertNotContains(response1, button_unwatch, html=True, msg_prefix='not watching')

        # watching
        self.listing.in_watchlist.add(self.second_profile)
        response2 = self.client.get(self.test_url)
        self.assertNotContains(response2, button_watch, html=True, msg_prefix='already watching')
        self.assertContains(response2, button_unwatch, html=True, msg_prefix='ok')

    def test_lot_loads_for_user_bids(self):
        from auctions.models import NO_BID_ON_TOP
        button_bid = '<button type="submit" name="btn_user_bid" ' \
                     'class="btn btn-warning">Make a bid</button>'
        bid_forbidden = '<span class="btn btn-warning disabled">%s</span>' % NO_BID_ON_TOP

        self.assertTrue(login_user(self, self.second_profile.username))

        # can bid
        response1 = self.client.get(self.test_url)
        self.assertEqual(response1.status_code, 200)
        self.assertContains(response1, button_bid, html=True, msg_prefix='ok')
        self.assertNotContains(response1, bid_forbidden, html=True, msg_prefix='can bid')

        # bid on the top, forbidden
        self.listing.make_a_bid(self.second_profile, 10)
        self.listing.refresh_from_db()

        response2 = self.client.get(self.test_url)
        self.assertNotContains(response2, button_bid, html=True, msg_prefix='can’t bid')
        self.assertContains(response2, bid_forbidden, html=True, msg_prefix='ok')

        self.assertContains(response2, 'Bids placed</a>: 1')
        self.assertContains(response2, 'Highest price: 🪙10')

        n = self.listing.get_highest_price(percent=True)
        bid_input = '<input type="number" name="bid_value" value="%s" class="form-control d-inline" ' \
                    'style="width: 100px;" min="%s" step="any" disabled="" id="id_bid_value">' \
                    % (n, n)
        self.assertContains(response2, bid_input, html=True)

    def test_lot_loads_for_owner(self):
        self.assertTrue(login_user(self, self.owner_profile.username))

        response1 = self.client.get(self.test_url)
        self.assertEqual(response1.status_code, 200)

        # no bids
        button_close = '<button type="submit" name="btn_owner_closed_auction" ' \
                       'class="btn btn-warning">Close the auction</button>'
        button_withdraw = '<button type="submit" name="btn_owner_withdrew" ' \
                          'class="btn btn-danger">Cancel the auction</button>'
        self.assertNotContains(response1, button_close, html=True, msg_prefix='no bids')
        self.assertContains(response1, button_withdraw, html=True, msg_prefix='ok')



class CommentsViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Jaguar')
        cls.owner_profile = Profile.manager.get(username='Jaguar')
        cls.user2 = get_user('Tamandua')
        cls.second_profile = Profile.manager.get(username='Tamandua')

        cls.category = get_category('Buns')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='japari bun',
        )
        cls.listing.comment_set.create(author=cls.second_profile, text='first comment')
        cls.listing.comment_set.create(author=cls.second_profile, text='second comment')

        cls.test_url = reverse('auctions:comments', args=[cls.listing.slug])
        cls.test_categories = [cls.category]

    def tearDown(self):
        if self.listing.is_active:
            self.listing.withdraw()

    def test_unpublished_comments_loads(self):
        self.assertTrue(login_user(self, self.owner_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Japari bun', msg_prefix='capfirst')
        go_back_url = self.listing.get_absolute_url()
        self.assertContains(response, f'href=\'{go_back_url}\'')

        self.assertContains(response, 'first comment')
        self.assertContains(response, 'second comment')

        # form
        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden"'
        button_save = '<button type="submit" class="btn btn-primary mb-5">Comment on</button>'
        self.assertNotContains(response, text_input, msg_prefix='no form')
        self.assertNotContains(response, author_hidden, msg_prefix='no form')
        self.assertNotContains(response, button_save, html=True, msg_prefix='no form')

    def test_published_comments_loads(self):
        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden" value="%s" ' \
                        'disabled="" id="id_author_hidden">' \
                        % self.second_profile.username
        button_save = '<button type="submit" class="btn btn-primary mb-5">Comment on</button>'

        self.listing.publish_the_lot()
        self.assertTrue(login_user(self, self.second_profile.username))
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, text_input)
        self.assertContains(response, author_hidden, html=True)
        self.assertContains(response, button_save, html=True)

    def test_comments_form(self):
        form_data = {
            'text_field': 'third comment',
            'author_hidden': self.second_profile.username,
        }
        self.listing.publish_the_lot()
        self.assertTrue(login_user(self, self.second_profile.username))
        response_post = self.client.post(self.test_url, form_data)
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'third comment')


class BidViewTests(TestNavbarAndSessionMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Fennec')
        cls.owner_profile = Profile.manager.get(username='Fennec')
        cls.user2 = get_user('Penguin')
        cls.second_profile = Profile.manager.get(username='Penguin')
        cls.second_profile.add_money(200)
        cls.second_profile.refresh_from_db()

        cls.category = get_category('Buns')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='japari bun',
        )
        cls.listing.publish_the_lot()

        cls.test_url = reverse('auctions:bid', args=[cls.listing.slug])
        cls.test_categories = [cls.category]

    def test_bids_loads(self):
        self.assertTrue(login_user(self, self.owner_profile.username))

        response1 = self.client.get(self.test_url)
        self.assertEqual(response1.status_code, 200)

        self.assertContains(response1, 'Japari bun', msg_prefix='capfirst')
        go_back_url = self.listing.get_absolute_url()
        self.assertContains(response1, f'href=\'{go_back_url}\'')
        self.assertContains(response1, 'No bids yet')

        self.listing.make_a_bid(self.second_profile, 20)
        response2 = self.client.get(self.test_url)
        self.assertContains(response2, self.second_profile.username)
        self.assertContains(response2, '🪙20.0')

        # unpublished
        self.listing.withdraw()
        self.assertRedirects(
            self.client.get(self.test_url),
            reverse('auctions:index'),
            302, 200,
            msg_prefix='forbidden for an unpublished item'
        )
        self.listing.publish_the_lot()
