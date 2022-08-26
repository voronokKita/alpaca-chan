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
- AuctionsAuthMixin
- ProfileMixin
- RestrictPkMixin
- NavbarMixin
- PresetMixin
- ListingRedirectMixin
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
def get_user(username) -> User:
    return User.objects.create(username=username, password=make_password('qwerty'))


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
def login_user(self_, username) -> bool:
    return self_.client.login(username=username, password='qwerty')


def prohibited_profile_access(self_, username, forbidden_url):
    self_.assertTrue(login_user(self_, username))
    response = self_.client.get(forbidden_url)
    self_.assertRedirects(response, reverse('auctions:index'), 302, 200)
    return True


def wrong_listing_url(self_, username, slug, published):
    """ Request of a published auction lot by
        url of an unpublished listing, and vice versa. """
    self_.assertTrue(login_user(self_, username))
    if published:
        response = self_.client.get(reverse('auctions:listing', args=[slug]))
        self_.assertRedirects(response, reverse('auctions:auction_lot', args=[slug]), 302, 200)
    else:
        response = self_.client.get(reverse('auctions:auction_lot', args=[slug]))
        self_.assertRedirects(response, reverse('auctions:listing', args=[slug]), 302, 200)
    return True


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
def check_session(self_, url, profile:Profile):
    """
    Checks that the profile's pk has been written to the session through the ProfileMixin.
    :profile: the profile that is bound to User model.
    """
    self_.assertTrue(self_.client.login(username=profile.username, password='qwerty'))
    self_.client.get(url)
    self_.assertTrue(self_.client.session['auctioneer_pk'] == profile.pk)


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
def test_navbar(self_, url, profile:Profile, categories:list = None, active:str = None):
    """
    Checks the work of the NavbarMixin.
    :user: the username that is contained in both User & Profile models.
    Active pages are:
        'Active Listings', 'Watchlist',
        'Create Listing', 'Wallet', 'History'
    """
    def check_active_page_class(rsp):
        if active:
            self_.assertContains(
                rsp, html=True,
                text='<a class="nav-link active" href="%s">%s</a>' % (url, active),
            )

    def items_on_both_pages(rsp):
        self_.assertContains(response, 'Active Listings')
        self_.assertContains(response, f'href=\"{reverse("auctions:index")}\"')
        self_.assertContains(response, 'Alpaca’s Cafe')
        self_.assertContains(response, f'href=\"{reverse("core:index")}\"')
        self_.assertContains(response, 'Category')
        [self_.assertContains(response, category.label) for category in categories]
        for category in categories:
            self_.assertContains(response, f'href=\"{reverse("auctions:category", args=[category.pk])}\"')

    # anonymous
    response = self_.client.get(url)
    self_.assertIn(response.status_code, (200, 302))
    if response.status_code == 200:
        check_active_page_class(response)
        items_on_both_pages(response)
        self_.assertNotContains(response, 'Watchlist')
        self_.assertNotContains(response, 'Create Listing')
        self_.assertNotContains(response, 'Wallet')
        self_.assertNotContains(response, 'History')
        self_.assertContains(response, 'Register')
        self_.assertContains(response, f'href=\"{reverse("accounts:register_and_next", args=["auctions"])}\"')
        self_.assertContains(response, 'Login')
        self_.assertContains(response, f'href=\"{reverse("accounts:login_and_next", args=["auctions"])}\"')

    # user
    self_.assertTrue(self_.client.login(username=profile.username, password='qwerty'))
    response = self_.client.get(url)
    self_.assertEqual(response.status_code, 200)
    check_active_page_class(response)
    items_on_both_pages(response)
    self_.assertContains(response, 'Watchlist')
    self_.assertContains(response, f'href=\"{reverse("auctions:watchlist", args=[profile.pk])}\"')
    self_.assertContains(response, 'Create Listing')
    self_.assertContains(response, f'href=\"{reverse("auctions:create_listing", args=[profile.pk])}\"')
    self_.assertContains(response, 'Wallet')
    self_.assertContains(response, f'href=\"{reverse("auctions:profile", args=[profile.pk])}\"')
    self_.assertContains(response, 'History')
    self_.assertContains(response, f'href=\"{reverse("auctions:user_history", args=[profile.pk])}\"')
    self_.assertContains(response, profile.username)
    self_.assertContains(response, 'Logout')
    self_.assertContains(response, f'href=\"{reverse("accounts:logout_and_next", args=["auctions"])}\"')


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
            profile=self.hippo,
            categories=[self.category1, self.category2],
            active='Active Listings',
        )

    def test_index_session_loads(self):
        check_session(self, url=self.url, profile=self.hippo)


class ProfileViewTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Rhino')
        cls.profile = Profile.manager.get(username='Rhino')
        cls.profile.add_money(115)
        cls.profile.refresh_from_db()
        cls.url = reverse('auctions:profile', args=[cls.profile.pk])
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
        cls.item.make_a_bid(cls.profile, 15)

    def test_profile_loads(self):
        if self.profile.money != 100:
            self.profile.money = 100
            self.profile.save()

        self.assertTrue(login_user(self, self.profile.username))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Available money:')
        self.assertContains(response, '🪙100')
        self.assertContains(response, 'Total bids:')
        self.assertContains(response, '🪙15')
        form_input = '<input type="number" name="transfer_money" placeholder="0.01" ' \
                     'class="form-control" autocomplete="off" min="0.01" max="9999.99" ' \
                     'step="any" required="" id="id_transfer_money">'
        self.assertContains(response, form_input, html=True)
        button_input = '<button type="submit" class="btn btn-primary">Transfer</button>'
        self.assertContains(response, button_input, html=True)

    def test_profile_add_money_form(self):
        self.assertTrue(login_user(self, self.profile.username))
        response_post = self.client.post(self.url, {'transfer_money': 20.05})
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(self.url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, '🪙120.05')

    def test_profile_access(self):
        self.assertTrue(prohibited_profile_access(self, self.second_profile.username, self.url))

    def test_profile_navbar(self):
        test_navbar(self, self.url, self.profile, [self.category], 'Wallet')

    def test_profile_session_loads(self):
        check_session(self, self.url, self.profile)


class UserHistoryViewTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Tamandua')
        cls.profile = Profile.manager.get(username='Tamandua')
        cls.url = reverse('auctions:user_history', args=[cls.profile.pk])
        cls.user2 = get_user('Peafowl')
        cls.second_profile = Profile.manager.get(username='Peafowl')
        cls.category = get_category('Buns')

    def test_history_loads(self):
        self.assertTrue(login_user(self, self.profile.username))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, LOG_REGISTRATION)

    def test_history_access(self):
        self.assertTrue(prohibited_profile_access(self, self.second_profile.username, self.url))

    def test_history_navbar(self):
        test_navbar(self, self.url, self.profile, [self.category], 'History')

    def test_history_session_loads(self):
        check_session(self, self.url, self.profile)


class WatchlistViewTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Aurochs')
        cls.profile = Profile.manager.get(username='Aurochs')
        cls.profile.add_money(100)
        cls.profile.refresh_from_db()

        cls.user2 = get_user('Oryx')
        cls.second_profile = Profile.manager.get(username='Oryx')
        cls.second_profile.add_money(100)
        cls.second_profile.refresh_from_db()

        cls.category1 = get_category('PIES')
        cls.category2 = get_category('BUNS')
        cls.category3 = get_category('CAKES')

        cls.item_owned = get_listing(
            cls.category1,
            cls.profile,
            title='apple pie',
            description='lorem ipsum dolor sit amet',
        )

        cls.item_owned_and_published = get_listing(
            cls.category2,
            cls.profile,
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
        cls.item_watched.make_a_bid(cls.profile, 20)

        cls.url = reverse('auctions:watchlist', args=[cls.profile.pk])

    def test_watchlist_loads(self):
        self.assertTrue(login_user(self, self.profile.username))
        response = self.client.get(self.url)
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

    def test_watchlist_access(self):
        self.assertTrue(prohibited_profile_access(self, self.second_profile.username, self.url))

    def test_watchlist_navbar(self):
        test_navbar(self, self.url, self.profile, [self.category1, self.category2, self.category3], 'Watchlist')

    def test_watchlist_session_loads(self):
        check_session(self, self.url, self.profile)


class CreateListingViewTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('Beaver')
        cls.profile = Profile.manager.get(username='Beaver')
        cls.user2 = get_user('Porcupine')
        cls.second_profile = Profile.manager.get(username='Porcupine')
        cls.category1 = get_category('Buns')
        cls.category2 = get_category('Pies')
        cls.url = reverse('auctions:create_listing', args=[cls.profile.pk])

        cls.slug = 'japari-bun'
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

    def test_create_loads(self):
        self.assertTrue(login_user(self, self.profile.username))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)
        slug_input = '<input type="text" name="slug"'
        self.assertContains(response, slug_input)
        title_input = '<input type="text" name="title"'
        self.assertContains(response, title_input)
        category_input = '<select name="category" class="form-control" required="" id="id_category">' \
                         '<option value="" selected="">---------</option>' \
                         '<option value="%d">%s</option><option value="%d">%s</option></select>' \
                         % (self.category1.id, self.category1.label, self.category2.id, self.category2.label)
        self.assertContains(response, category_input, html=True)
        price_input = '<input type="number" name="starting_price"'
        self.assertContains(response, price_input)
        descr_input = '<textarea name="description"'
        self.assertContains(response, descr_input)
        img_input = '<input type="file" name="image" class="form-control" accept="image/*" required="" id="id_image">'
        self.assertContains(response, img_input, html=True)
        hidden_profile = '<input type="hidden" name="owner" value="%d" disabled="" id="id_owner">' % self.profile.id
        self.assertContains(response, hidden_profile, html=True)
        button_input = '<button type="submit" class="btn btn-success">Create</button>'
        self.assertContains(response, img_input, html=True)

    def test_create_form(self):
        self.assertTrue(login_user(self, self.profile.username))
        data = {
            'slug': 'japari-bun',
            'title': 'Japari Bun',
            'category': self.category1.id,
            'starting_price': 5,
            'description': 'Lorem ipsum dolor sit amet',
            'image': TEST_IMAGE,
            'owner': self.profile.id,
        }
        response_post = self.client.post(self.url, data)
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Japari Bun')
        self.assertTrue(self.image_path.exists())

    def test_create_access(self):
        self.assertTrue(prohibited_profile_access(self, self.second_profile.username, self.url))

    def test_create_navbar(self):
        test_navbar(self, self.url, self.profile, [self.category1, self.category2], 'Create Listing')

    def test_create_session_loads(self):
        check_session(self, self.url, self.profile)


class ListingViewTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('CampoFlicker')
        cls.profile = Profile.manager.get(username='CampoFlicker')
        cls.user2 = get_user('Capybara')
        cls.second_profile = Profile.manager.get(username='Capybara')

        cls.category = get_category('BUNS')
        cls.listing = get_listing(
            cls.category,
            cls.profile,
            title='japari bun',
            description='lorem ipsum dolor sit amet',
        )
        cls.listing.comment_set.create(author=cls.second_profile, text='first comment')
        cls.listing.comment_set.create(author=cls.second_profile, text='second comment')

        cls.url = reverse('auctions:listing', args=[cls.listing.slug])

    def test_listing_loads(self):
        self.assertTrue(login_user(self, self.profile.username))
        response = self.client.get(self.url)
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
        self.assertContains(response, f'href=\'{edit_url}\'')
        comments_url = reverse('auctions:comments', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{comments_url}\'')

        ghost_field = '<input type="hidden" name="ghost_field" disabled="" id="id_ghost_field">'
        self.assertContains(response, ghost_field, html=True)
        button_input = '<button type="submit" class="btn btn-warning">Publish and start the auction</button>'
        self.assertContains(response, button_input, html=True)

    def test_publish_listing_form(self):
        self.assertTrue(login_user(self, self.profile.username))
        response_post = self.client.post(self.url, {'ghost_field': True})
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)

        # clean
        self.assertTrue(self.listing.withdraw())

    def test_listing_access(self):
        self.assertTrue(prohibited_profile_access(self, self.second_profile.username, self.url))

    def test_listing_redirects(self):
        self.assertTrue(wrong_listing_url(self, self.profile, self.listing.slug, published=False))

    def test_listing_navbar(self):
        test_navbar(self, self.url, self.profile, [self.category])

    def test_listing_session_loads(self):
        check_session(self, self.url, self.profile)


class EditListingViewTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.user1 = get_user('PrairieDog')
        cls.profile = Profile.manager.get(username='PrairieDog')
        cls.user2 = get_user('Giraffe')
        cls.second_profile = Profile.manager.get(username='Giraffe')

        cls.category = get_category('Buns')
        cls.listing = get_listing(
            cls.category,
            cls.profile,
            title='Japari Bun',
            description='Lorem ipsum dolor sit amet',
        )
        cls.url = reverse('auctions:edit_listing', args=[cls.listing.slug])

    def test_edit_loads(self):
        self.assertTrue(login_user(self, self.profile.username))
        response = self.client.get(self.url)
        self.assertEqual(response.status_code, 200)

        go_back_url = reverse('auctions:listing', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{go_back_url}\'')

        title_input = '<input type="text" name="title"'
        self.assertContains(response, title_input)
        category_input = '<select name="category"'
        self.assertContains(response, category_input)
        price_input = '<input type="number" name="starting_price"'
        self.assertContains(response, price_input)
        descr_input = '<textarea name="description"'
        self.assertContains(response, descr_input)
        image_input = '<input type="file" name="image" class="form-control" accept="image/*" id="id_image">'
        self.assertContains(response, image_input, html=True)
        button_save = '<button type="submit" name="button_save" class="btn btn-success">Save changes</button>'
        self.assertContains(response, button_save, html=True)
        button_save_and_publish = '<button type="submit" name="button_publish" ' \
                                  'class="btn btn-warning">Save and start the auction</button>'
        self.assertContains(response, button_save_and_publish, html=True)

    def test_edit_form_save(self):
        form_data = {
            'title': 'Big Japari Bun',
            'category': self.category.id,
            'starting_price': 10,
            'description': 'Sed ut perspiciatis unde omnis.',
            'button_save': [''],
        }
        self.assertTrue(login_user(self, self.profile.username))
        response_post = self.client.post(self.url, form_data)
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
        self.assertTrue(login_user(self, self.profile.username))
        response_post = self.client.post(self.url, form_data)
        self.assertEqual(response_post.status_code, 302)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, 'Grand Japari Bun')
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)

        # clean
        self.assertTrue(self.listing.withdraw())

    def test_edit_access(self):
        self.assertTrue(prohibited_profile_access(self, self.second_profile.username, self.url))

    def test_edit_redirects(self):
        self.assertTrue(wrong_listing_url(self, self.profile, self.listing.slug, published=False))

    def test_edit_navbar(self):
        test_navbar(self, self.url, self.profile, [self.category])

    def test_edit_session_loads(self):
        check_session(self, self.url, self.profile)



























#
