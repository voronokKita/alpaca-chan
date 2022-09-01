from pathlib import Path

from django.test import TestCase, override_settings
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.hashers import make_password
from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth.models import User
from auctions.models import (
    Profile, user_media_path,
    LOG_REGISTRATION, NO_BID_NO_MONEY_SP,
    NO_BID_ON_TOP, NO_BID_NO_MONEY
)
from .tests import (
    DATABASES, SMALL_GIF, IMGNAME, FAST_HASHER,
    get_category, get_listing
)
from auctions.utils import format_bid_value

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
+ Lot View
    + btn owner_closed
    + btn owner_withdrew
    + btn user_bid
    + btn watch & unwatch
    + comments & comments page link
    + comment form
    + bids page link
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
def login_user(self_, username) -> None:
    self_.assertTrue(self_.client.login(username=username, password='qwerty'))


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
        login_user(self, self.second_profile.username)
        response = self.client.get(self.test_url)
        self.assertRedirects(response, reverse('auctions:index'), 302, 200)


class TestRedirectMixin(AbstractTestMixin):
    """ Logic form ListingRedirectMixin.
        Request of a published auction lot by
        url of an unpublished listing, and vice versa. """

    def test_wrong_listing_url(self):
        login_user(self, self.owner_profile)
        slug = self.listing.slug
        if self.listing.is_active:
            wrong_url = reverse('auctions:listing', args=[slug])
            correct_url = reverse('auctions:auction_lot', args=[slug])
            response = self.client.get(wrong_url)
            self.assertRedirects(response, correct_url, 302, 200)
        else:
            wrong_url = reverse('auctions:auction_lot', args=[slug])
            correct_url = reverse('auctions:listing', args=[slug])
            response = self.client.get(wrong_url)
            self.assertRedirects(response, correct_url, 302, 200)


class TestSessionMixin(AbstractTestMixin):
    """ Checks that the profile's pk has been written to the session through the ProfileMixin. """

    def test_page_session_loads(self):
        login_user(self, self.owner_profile.username)
        self.client.get(self.test_url)
        self.assertTrue(self.client.session['auctioneer_pk'] == self.owner_profile.pk)


class TestNavbarMixin(AbstractTestMixin):
    """
    Checks the work of the NavbarMixin.

    Active pages are: 'Active Listings', 'Watchlist', 'Create Listing', 'Wallet', 'History'.
    """
    def test_page_navbar(self):
        self._navbar_for_anonymous()
        self._navbar_for_user()

    def _navbar_for_anonymous(self):
        response = self.client.get(self.test_url)
        self.assertIn(response.status_code, (200, 302))
        if response.status_code != 200:
            # access for an anonymous is forbidden
            return

        self._navbar_active_class(response)
        self._navbar_items_on_both_pages(response)

        self.assertNotContains(response, 'Watchlist')
        self.assertNotContains(response, 'Create Listing')
        self.assertNotContains(response, 'Wallet')
        self.assertNotContains(response, 'History')
        self.assertContains(response, 'Register')
        self.assertContains(response, 'Login')
        register_url = f'href=\"{reverse("accounts:register_and_next", args=["auctions"])}\"'
        login_url = f'href=\"{reverse("accounts:login_and_next", args=["auctions"])}\"'
        self.assertContains(response, register_url)
        self.assertContains(response, login_url)

    def _navbar_for_user(self):
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self._navbar_active_class(response)
        self._navbar_items_on_both_pages(response)

        self.assertContains(response, 'Watchlist')
        self.assertContains(response, 'Create Listing')
        self.assertContains(response, 'Wallet')
        self.assertContains(response, 'History')
        self.assertContains(response, 'Logout')
        self.assertContains(response, self.owner_profile.username)
        pk = self.owner_profile.pk
        watchlist_url = f'href=\"{reverse("auctions:watchlist", args=[pk])}\"'
        create_url = f'href=\"{reverse("auctions:create_listing", args=[pk])}\"'
        profile_url = f'href=\"{reverse("auctions:profile", args=[pk])}\"'
        history_url = f'href=\"{reverse("auctions:user_history", args=[pk])}\"'
        logout_url = f'href=\"{reverse("accounts:logout_and_next", args=["auctions"])}\"'
        self.assertContains(response, watchlist_url)
        self.assertContains(response, create_url)
        self.assertContains(response, profile_url)
        self.assertContains(response, history_url)
        self.assertContains(response, logout_url)

    def _navbar_active_class(self, response):
        if self.active_page:
            active_ell = '<a class="nav-link active" href="%s">%s</a>' \
                         % (self.test_url, self.active_page)
            self.assertContains(response, active_ell, html=True)

    def _navbar_items_on_both_pages(self, response):
        self.assertContains(response, 'Active Listings')
        self.assertContains(response, 'Alpaca’s Cafe')
        self.assertContains(response, 'Category')
        self.assertContains(response, f'href=\"{reverse("auctions:index")}\"')
        self.assertContains(response, f'href=\"{reverse("core:index")}\"')
        for category in self.test_categories:
            self.assertContains(response, category.label)
            category_url = f'href=\"{reverse("auctions:category", args=[category.pk])}\"'
            self.assertContains(response, category_url)


class TestNavbarAndSessionMixin(TestSessionMixin, TestNavbarMixin):
    """
    Checks that the profile's pk has been written to the session through the ProfileMixin.
    """


class AuctionsIndexViewTests(TestNavbarAndSessionMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user = get_user('Hippo')
        cls.owner_profile = Profile.manager.get(username='Hippo')

        cls.category1 = get_category('BUNS')
        cls.category2 = get_category('PIES')

        cls.listing1 = get_listing(
            cls.category1,
            profile=cls.owner_profile,
            title='japari bun',
            description='lorem ipsum dolor sit amet.'
        )
        cls.listing1.starting_price = 20
        cls.listing1.save()
        cls.listing1.publish_the_lot()

        cls.listing2 = get_listing(
            cls.category2,
            username='Monkey',
            title='japari pie',
            description='sed ut perspiciatis unde omnis.'
        )
        cls.listing2.publish_the_lot()

        cls.test_url = reverse('auctions:index')
        cls.active_page = 'Active Listings'
        cls.test_categories = [cls.category1, cls.category2]

    def _bid(self):
        self.owner_profile.add_money(15)
        self.owner_profile.refresh_from_db(fields=['money'])
        self.listing2.make_a_bid(self.owner_profile, 15)

    def test_index_loads(self):
        self._bid()
        self._index_normal_case()
        self._index_by_category()
        self._index_no_auctions()

    def _index_normal_case(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Japari bun', msg_prefix='capfirst')
        self.assertContains(response, 'buns', msg_prefix='lower')
        self.assertContains(response, 'Starting price: 🪙%g' % self.listing1.get_highest_price())
        self.assertContains(response, 'Lorem ipsum dolor sit amet.', msg_prefix='capfirst')
        self.assertContains(response, f'href=\'{self.listing1.get_absolute_url()}\'')

        self.assertContains(response, 'Japari pie', msg_prefix='capfirst')
        self.assertContains(response, 'pies', msg_prefix='lower')
        self.assertContains(response, 'Highest bid: 🪙%g' % self.listing2.get_highest_price())
        self.assertContains(response, 'Sed ut perspiciatis unde omnis.', msg_prefix='capfirst')
        self.assertContains(response, f'href=\'{self.listing2.get_absolute_url()}\'')

        self.assertContains(response, 'Published:', 2)

    def _index_by_category(self):
        request = reverse('auctions:category', args=[self.category1.pk])
        response = self.client.get(request)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'Japari bun', msg_prefix='does have buns')
        self.assertNotContains(response, 'Japari pie', msg_prefix='does not have pies')

    def _index_no_auctions(self):
        self.listing1.withdraw()
        self.listing2.withdraw()
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, 'There are currently no auctions.')


class ProfileViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user('Rhino')
        cls.owner_profile = Profile.manager.get(username='Rhino')
        cls.user2 = get_user('Hippo')
        cls.second_profile = Profile.manager.get(username='Hippo')

        cls.category = get_category('Buns')
        cls.listing = get_listing(cls.category, cls.second_profile)
        cls.listing.publish_the_lot()

        cls.test_url = reverse('auctions:profile', args=[cls.owner_profile.pk])
        cls.active_page = 'Wallet'
        cls.test_categories = [cls.category]

    def _preset(self):
        self.owner_profile.add_money(120)
        self.owner_profile.refresh_from_db(fields=['money'])

        self.listing.make_a_bid(self.owner_profile, 20)
        self.owner_profile.refresh_from_db(fields=['money'])

    def test_profile_page(self):
        login_user(self, self.owner_profile.username)
        self._preset()
        self._profile_loads()
        self._profile_add_money_form()

    def _profile_loads(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Available money:')
        self.assertContains(response, '🪙100')
        self.assertContains(response, 'Total bids:')
        self.assertContains(response, '🪙20')
        form_input = '<input type="number" name="transfer_money" placeholder="0.01" ' \
                     'class="form-control" autocomplete="off" min="0.01" max="9999.99" ' \
                     'step="any" required="" id="id_transfer_money">'
        button_input = '<button type="submit" class="btn btn-primary">Transfer</button>'
        self.assertContains(response, form_input, html=True)
        self.assertContains(response, button_input, html=True)

    def _profile_add_money_form(self):
        response_post = self.client.post(self.test_url, {'transfer_money': 20.05})
        self.assertRedirects(response_post, self.test_url, 302, 200)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.assertContains(response_get, '🪙120.05')


class UserHistoryViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user('Tamandua')
        cls.owner_profile = Profile.manager.get(username='Tamandua')
        cls.user2 = get_user('Peafowl')
        cls.second_profile = Profile.manager.get(username='Peafowl')
        cls.category = get_category('Buns')

        cls.test_url = reverse('auctions:user_history', args=[cls.owner_profile.pk])
        cls.active_page = 'History'
        cls.test_categories = [cls.category]

    def test_history_loads(self):
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, LOG_REGISTRATION)


class WatchlistViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user('Aurochs')
        cls.owner_profile = Profile.manager.get(username='Aurochs')
        cls.user2 = get_user('Oryx')
        cls.second_profile = Profile.manager.get(username='Oryx')

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

        cls.item_watched = get_listing(
            cls.category3,
            cls.second_profile,
            title='chocolate cake',
            description='but I must explain to you',
        )
        cls.item_watched.publish_the_lot()

        cls.test_url = reverse('auctions:watchlist', args=[cls.owner_profile.pk])
        cls.active_page = 'Watchlist'
        cls.test_categories = [cls.category1, cls.category2, cls.category3]

    def _bid(self):
        self.owner_profile.add_money(20)
        self.second_profile.add_money(10)
        self.owner_profile.refresh_from_db()
        self.second_profile.refresh_from_db()
        self.item_owned_and_published.make_a_bid(self.second_profile, 10)
        self.item_watched.make_a_bid(self.owner_profile, 20)

    def test_watchlist_page(self):
        self._bid()
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self._items_owned(response)
        self._items_owned_and_published(response)
        self._items_watched(response)

        self.assertContains(response, 'Published:', 2)

    def _items_owned(self, response):
        self.assertContains(response, 'Apple pie', msg_prefix='capfirst')
        self.assertContains(response, 'Category: pies', msg_prefix='lower')
        self.assertContains(response, 'Starting price: 🪙1')
        self.assertContains(response, 'Lorem ipsum dolor sit amet', msg_prefix='capfirst')
        self.assertContains(response, 'Not Published')
        self.assertContains(response, f'href=\'{self.item_owned.get_absolute_url()}\'')

    def _items_owned_and_published(self, response):
        self.assertContains(response, 'White bun', msg_prefix='capfirst')
        self.assertContains(response, 'Category: buns', msg_prefix='lower')
        self.assertContains(response, 'Current price: 🪙10')
        self.assertContains(response, 'Sed ut perspiciatis unde omnis iste', msg_prefix='capfirst')
        self.assertContains(response, f'href=\'{self.item_owned_and_published.get_absolute_url()}\'')

    def _items_watched(self, response):
        self.assertContains(response, 'Chocolate cake', msg_prefix='capfirst')
        self.assertContains(response, 'Category: cakes', msg_prefix='lower')
        self.assertContains(response, 'Current price: 🪙20')
        self.assertContains(response, 'But I must explain to you', msg_prefix='capfirst')
        self.assertContains(response, f'href=\'{self.item_watched.get_absolute_url()}\'')


class CreateListingViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user('Beaver')
        cls.owner_profile = Profile.manager.get(username='Beaver')
        cls.user2 = get_user('Porcupine')
        cls.second_profile = Profile.manager.get(username='Porcupine')

        cls.category1 = get_category('Buns')
        cls.category2 = get_category('Pies')

        cls.test_image = SimpleUploadedFile(IMGNAME, SMALL_GIF, content_type='image/gif')
        cls.slug = 'japari-pie'
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

    def test_create_page_loads(self):
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

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

        self.assertContains(response, slug_input)
        self.assertContains(response, title_input)
        self.assertContains(response, category_input, html=True)
        self.assertContains(response, price_input)
        self.assertContains(response, descr_input)
        self.assertContains(response, img_input, html=True)
        self.assertContains(response, hidden_profile, html=True)
        self.assertContains(response, img_input, html=True)

    def test_create_form(self):
        """ May crash if other tests are using TEST_IMAGE. """
        login_user(self, self.owner_profile.username)
        data = {
            'slug': self.slug,
            'title': 'Japari Pie',
            'category': self.category2.id,
            'starting_price': 5,
            'description': 'Lorem ipsum dolor sit amet',
            'image': self.test_image,
            'owner': self.owner_profile.id,
        }
        response_post = self.client.post(self.test_url, data)
        success_url = reverse('auctions:listing', args=[self.slug])
        self.assertRedirects(response_post, success_url, 302, 200)

        response_get = self.client.get(response_post.url)
        self.assertContains(response_get, 'Japari Pie')
        self.assertTrue(self.image_path.exists())


class ListingViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestRedirectMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
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

    def setUp(self):
        if self.listing.is_active:
            self.listing.withdraw()
            self.listing.refresh_from_db()

    def test_listing_page_loads(self):
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Japari bun', msg_prefix='capfirst')
        self.assertContains(response, 'Category: buns', msg_prefix='lower')
        self.assertContains(response, 'Starting price: 🪙1')
        self.assertContains(response, 'Lorem ipsum dolor sit amet', msg_prefix='capfirst')
        self.assertContains(response, 'Created:')

        edit_url = reverse('auctions:edit_listing', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{edit_url}\'')

        ghost_field = '<input type="hidden" name="ghost_field" disabled="" id="id_ghost_field">'
        button_input = '<button type="submit" class="btn btn-warning">Publish and start the auction</button>'
        self.assertContains(response, ghost_field, html=True)
        self.assertContains(response, button_input, html=True)

        self._comments_block_loads(response)

    def _comments_block_loads(self, response):
        self.assertContains(response, self.second_profile.username)
        self.assertContains(response, 'first comment')
        self.assertContains(response, 'second comment')
        comments_url = reverse('auctions:comments', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{comments_url}\'')

        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden"'
        button_save = '<button type="submit" class="btn btn-primary mb-5">Comment on</button>'

        self.assertNotContains(response, text_input, msg_prefix='no form')
        self.assertNotContains(response, author_hidden, msg_prefix='no form')
        self.assertNotContains(response, button_save, html=True, msg_prefix='no form')

    def test_publish_listing_form(self):
        login_user(self, self.owner_profile.username)
        response_post = self.client.post(self.test_url, {'ghost_field': True})
        success_url = reverse('auctions:auction_lot', args=[self.listing.slug])
        self.assertRedirects(response_post, success_url, 302, 200)

        response_get = self.client.get(response_post.url)
        self.assertContains(response_get, 'Japari bun')
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)


class EditListingViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
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

    def setUp(self):
        if self.listing.is_active:
            self.listing.withdraw()
            self.listing.refresh_from_db()

    def test_edit_page_loads(self):
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

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

        go_back_url = reverse('auctions:listing', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{go_back_url}\'')

    def test_edit_form_save(self):
        login_user(self, self.owner_profile.username)
        form_data = {
            'title': 'Big Japari Bun',
            'category': self.category.id,
            'starting_price': 10,
            'description': 'Sed ut perspiciatis unde omnis.',
            'button_save': [''],
        }
        response_post = self.client.post(self.test_url, form_data)
        success_url = reverse('auctions:listing', args=[self.listing.slug])
        self.assertRedirects(response_post, success_url, 302, 200)

        response_get = self.client.get(response_post.url)
        self.assertContains(response_get, 'Big Japari Bun')

    def test_edit_form_save_and_start(self):
        login_user(self, self.owner_profile.username)
        form_data = {
            'title': 'Grand Japari Bun',
            'category': self.category.id,
            'starting_price': 20,
            'description': 'But I must explain to you',
            'button_publish': [''],
        }
        response_post = self.client.post(self.test_url, form_data)
        success_url = reverse('auctions:auction_lot', args=[self.listing.slug])
        self.assertRedirects(response_post, success_url, 302, 200)

        response_get = self.client.get(response_post.url)
        self.assertContains(response_get, 'Grand Japari Bun')
        self.listing.refresh_from_db()
        self.assertTrue(self.listing.is_active)


class CommentsViewTests(TestNavbarAndSessionMixin, TestAccessMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
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
            self.listing.refresh_from_db()

    def test_comments_page_loads(self):
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Japari bun', msg_prefix='capfirst')
        go_back_url = self.listing.get_absolute_url()
        self.assertContains(response, f'href=\'{go_back_url}\'')

        self.assertContains(response, 'first comment')
        self.assertContains(response, 'second comment')

        self._no_form_for_unpublished(response)

    def _no_form_for_unpublished(self, response):
        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden"'
        button_save = '<button type="submit" class="btn btn-primary mb-5">Comment on</button>'
        self.assertNotContains(response, text_input, msg_prefix='no form')
        self.assertNotContains(response, author_hidden, msg_prefix='no form')
        self.assertNotContains(response, button_save, html=True, msg_prefix='no form')

    def test_comment_form_for_published(self):
        self.listing.publish_the_lot()
        self._no_form_for_anonymous()

        login_user(self, self.second_profile.username)
        self._form_for_a_user()

        self._comment_form_post()

    def _no_form_for_anonymous(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden"'
        button_save = '<button type="submit"'

        self.assertNotContains(response, text_input, msg_prefix='no anon comments')
        self.assertNotContains(response, author_hidden, msg_prefix='no anon comments')
        self.assertNotContains(response, button_save, msg_prefix='no anon comments')

    def _form_for_a_user(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden" value="%s" ' \
                        'disabled="" id="id_author_hidden">' \
                        % self.second_profile.username
        button_save = '<button type="submit" class="btn btn-primary mb-5">Comment on</button>'

        self.assertContains(response, text_input)
        self.assertContains(response, author_hidden, html=True)
        self.assertContains(response, button_save, html=True)

    def _comment_form_post(self):
        form_data = {
            'text_field': 'third comment',
            'author_hidden': self.second_profile.username,
        }
        response_post = self.client.post(self.test_url, form_data)
        success_url = reverse('auctions:auction_lot', args=[self.listing.slug])
        self.assertRedirects(response_post, success_url, 302, 200)

        response_get = self.client.get(response_post.url)
        self.assertContains(response_get, 'third comment')


class BidViewTests(TestNavbarAndSessionMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user('Fennec')
        cls.owner_profile = Profile.manager.get(username='Fennec')
        cls.user2 = get_user('Penguin')
        cls.second_profile = Profile.manager.get(username='Penguin')

        cls.category = get_category('Buns')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='japari bun',
        )
        cls.listing.publish_the_lot()
        cls.test_url = reverse('auctions:bid', args=[cls.listing.slug])
        cls.test_categories = [cls.category]

    def _bid(self):
        self.second_profile.add_money(20)
        self.second_profile.refresh_from_db()
        self.listing.make_a_bid(self.second_profile, 20)
        self.listing.refresh_from_db()

    def test_bids_page(self):
        login_user(self, self.owner_profile.username)
        self._no_bids()
        self._bid()
        self._with_bids()
        self._unpublished_redirects()

    def _no_bids(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Japari bun', msg_prefix='capfirst')
        go_back_url = self.listing.get_absolute_url()
        self.assertContains(response, f'href=\'{go_back_url}\'')

        self.assertContains(response, 'No bids yet')

    def _with_bids(self):
        response = self.client.get(self.test_url)
        self.assertContains(response, self.second_profile.username)
        self.assertContains(response, '🪙20.0')

    def _unpublished_redirects(self):
        self.listing.withdraw()
        self.assertRedirects(
            self.client.get(self.test_url),
            reverse('auctions:index'),
            302, 200,
            msg_prefix='forbidden for an unpublished item'
        )
        self.listing.publish_the_lot()
        self.listing.refresh_from_db()


class AuctionLotViewTests(TestNavbarAndSessionMixin, TestRedirectMixin, TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user('TasmanianDevil')
        cls.owner_profile = Profile.manager.get(username='TasmanianDevil')
        cls.user2 = get_user('GrayWolf')
        cls.second_profile = Profile.manager.get(username='GrayWolf')

        cls.category = get_category('BUNS')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='japari bun',
            description='lorem ipsum dolor sit amet',
        )
        cls.listing.publish_the_lot()
        cls.listing.comment_set.create(author=cls.second_profile, text='first comment')
        cls.listing.comment_set.create(author=cls.second_profile, text='second comment')

        cls.test_url = reverse('auctions:auction_lot', args=[cls.listing.slug])
        cls.test_categories = [cls.category]

    def _bid(self):
        self.second_profile.add_money(20)
        self.second_profile.refresh_from_db()
        self.listing.make_a_bid(self.second_profile, 20)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.highest_bid, 20)

    def test_auction_loads_for_anonymous(self):
        self._auction_page_renders()

        self._bid()
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self._auction_page_renders_with_bids(response)
        self._auction_page_comments(response)
        self._anonymous_auction_form(response)
        self._anonymous_auction_comment_form(response)

    def _auction_page_renders(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self.assertContains(response, 'Japari bun', msg_prefix='capfirst')
        self.assertContains(response, 'Category: buns', msg_prefix='lower')
        self.assertContains(response, 'Bids placed</a>: 0')
        self.assertContains(response, 'Starting price: 🪙1')
        self.assertNotContains(response, 'Highest bid')
        self.assertContains(response, 'Lorem ipsum dolor sit amet', msg_prefix='capfirst')
        self.assertContains(response, 'Published:')

        bids_url = reverse('auctions:bid', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{bids_url}\'')

    def _auction_page_renders_with_bids(self, response):
        self.assertContains(response, 'Bids placed</a>: 1')
        self.assertContains(response, 'Highest bid: 🪙20')
        self.assertNotContains(response, 'Starting price')

    def _auction_page_comments(self, response):
        self.assertContains(response, self.second_profile.username)
        self.assertContains(response, 'first comment')
        self.assertContains(response, 'second comment')
        comments_url = reverse('auctions:comments', args=[self.listing.slug])
        self.assertContains(response, f'href=\'{comments_url}\'')

    def _anonymous_auction_form(self, response):
        ghost_field = '<input type="hidden" name="ghost_field"'
        auctioneer_input = '<input type="hidden" name="auctioneer"'
        bid_input = '<input type="number" name="bid_value"'
        any_button = '<button type="submit"'
        self.assertNotContains(response, ghost_field, msg_prefix='no form for anon')
        self.assertNotContains(response, auctioneer_input, msg_prefix='no form for anon')
        self.assertNotContains(response, bid_input, msg_prefix='no form for anon')
        self.assertNotContains(response, any_button, msg_prefix='no form for anon')

    def _anonymous_auction_comment_form(self, response):
        text_input = '<textarea name="text_field"'
        author_hidden = '<input type="hidden" name="author_hidden"'
        self.assertNotContains(response, text_input, msg_prefix='no form for anon')
        self.assertNotContains(response, author_hidden, msg_prefix='no form for anon')


class AuctionLotViewForUsersTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user('Raccoon')
        cls.owner_profile = Profile.manager.get(username='Raccoon')
        cls.user2 = get_user('Aardwolf')
        cls.second_profile = Profile.manager.get(username='Aardwolf')

        cls.category = get_category('cakes')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='Japari Cake',
            description='But I must explain to you...',
        )
        cls.test_url = reverse('auctions:auction_lot', args=[cls.listing.slug])

    def setUp(self):
        def republish():
            self.listing.withdraw()
            self.listing.publish_the_lot()

        if self.listing.owner != self.owner_profile:
            self.listing.save_new_owner(self.owner_profile)

        if self.listing.watchlist_set.count() > 1 or self.listing.highest_bid:
            republish()
        elif self.listing.is_active is False:
            self.listing.publish_the_lot()

        self.listing.refresh_from_db()

        self.second_profile.refresh_from_db(fields=['money'])
        if self.second_profile.money != 0:
            self.second_profile.get_money(self.second_profile.money)
            self.second_profile.refresh_from_db(fields=['money'])

    def test_auction_loads_for_user(self):
        login_user(self, self.second_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self._user_auction_form_exists(response)
        self._user_auction_form_does_not_have_buttons_for_the_owner(response)
        self._user_auction_comment_form_exists(response)

    def _user_auction_form_exists(self, response):
        ghost_field = '<input type="hidden" name="ghost_field"'
        bid_input = '<input type="number" name="bid_value"'
        self.assertContains(response, ghost_field)
        self.assertContains(response, bid_input)

    def _user_auction_form_does_not_have_buttons_for_the_owner(self, response):
        button_close = '<button type="submit" name="btn_owner_closed_auction"'
        button_withdraw = '<button type="submit" name="btn_owner_withdrew"'
        self.assertNotContains(response, button_close, msg_prefix='not for a user')
        self.assertNotContains(response, button_withdraw, msg_prefix='not for a user')

    def _user_auction_comment_form_exists(self, response):
        comments_view_url = reverse('auctions:comments', args=[self.listing.slug])
        form_html = "<form action='%s'" % comments_view_url
        text_input = '<textarea name="text_field"'
        button_save = '<button type="submit" class="btn btn-primary mb-5">Comment on</button>'
        author_hidden = '<input type="hidden" name="author_hidden" ' \
                        'value="%s" disabled="" id="id_author_hidden">' \
                        % self.second_profile.username
        self.assertContains(response, form_html, msg_prefix='form points to the CommentsView')
        self.assertContains(response, text_input)
        self.assertContains(response, button_save, html=True)
        self.assertContains(response, author_hidden, html=True)

    def test_auction_watch_and_unwatch(self):
        login_user(self, self.second_profile.username)

        self._user_not_watching_the_auction()
        self._user_watch_the_auction_form_works()

        self._user_watching_the_auction()
        self._user_unwatch_the_auction_form_works()

    def _user_not_watching_the_auction(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        button_watch = "<button type='submit' name='btn_user_watching'"
        button_unwatch = "<button type='submit' name='btn_user_unwatched'"
        author_hidden = '<input type="hidden" name="author_hidden" ' \
                        'value="%s" disabled="" id="id_author_hidden">' \
                        % self.second_profile.username
        self.assertContains(response, button_watch, msg_prefix='can watch')
        self.assertNotContains(response, button_unwatch, msg_prefix='no unwatch form')
        self.assertContains(response, author_hidden, html=True)

    def _user_watch_the_auction_form_works(self):
        form_data = {'ghost_field': '', 'btn_user_watching': ['']}
        response_post = self.client.post(self.test_url, form_data)
        self.assertRedirects(response_post, self.test_url, 302, 200)
        self.assertTrue(self.listing.in_watchlist.contains(self.second_profile))

    def _user_watching_the_auction(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        button_watch = "<button type='submit' name='btn_user_watching'"
        button_unwatch = "<button type='submit' name='btn_user_unwatched'"
        author_hidden = '<input type="hidden" name="author_hidden" ' \
                        'value="%s" disabled="" id="id_author_hidden">' \
                        % self.second_profile.username
        self.assertNotContains(response, button_watch, msg_prefix='no watch form')
        self.assertContains(response, button_unwatch, msg_prefix='can unwatch')
        self.assertContains(response, author_hidden, html=True)

    def _user_unwatch_the_auction_form_works(self):
        form_data = {'ghost_field': '', 'btn_user_unwatched': ['']}
        response_post = self.client.post(self.test_url, form_data)
        self.assertRedirects(response_post, self.test_url, 302, 200)
        self.assertFalse(self.listing.in_watchlist.contains(self.second_profile))

    def test_auction_bid(self):
        login_user(self, self.second_profile.username)
        self.second_profile.add_money(2)
        self.second_profile.refresh_from_db(fields=['money'])

        self._user_can_bid()
        self._user_place_a_bid_form_works()

    def _user_can_bid(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        n = format_bid_value(self.listing.starting_price)
        ghost_field = '<input type="hidden" name="ghost_field"'
        bid_button = "<button type='submit' name='btn_user_bid'"
        bid_input = '<input type="number" name="bid_value" value="%s" class="form-control d-inline" ' \
                    'style="width: 100px;" min="%s" step="any" id="id_bid_value">' % (n, n)
        auctioneer_input = '<input type="hidden" name="auctioneer" ' \
                           'value="%s" disabled="" id="id_auctioneer">' \
                           % self.second_profile.username
        self.assertContains(response, ghost_field)
        self.assertContains(response, bid_button)
        self.assertContains(response, bid_input)
        self.assertContains(response, auctioneer_input, html=True)

        bid_forbidden = "<span id='bid_forbidden'"
        self.assertNotContains(response, bid_forbidden)

    def _user_place_a_bid_form_works(self):
        form_data = {
            'ghost_field': '',
            'auctioneer': self.second_profile.username,
            'bid_value': 2,
            'btn_user_bid': [''],
        }
        response_post = self.client.post(self.test_url, form_data)
        self.assertRedirects(response_post, self.test_url, 302, 200)

        self.listing.refresh_from_db()
        self.assertEqual(self.listing.highest_bid, 2)
        self.assertTrue(self.listing.potential_buyers.contains(self.second_profile))

    def test_auction_bid_forbidden(self):
        login_user(self, self.second_profile.username)
        self._user_money_is_less_than_the_starting_price()

        self._bid()
        self._user_bid_already_on_the_top()

        self.client.logout()
        user3 = get_user('Gray-wolf')
        login_user(self, user3.username)
        self._user_money_is_less_than_the_highest_bid()

    def _user_money_is_less_than_the_starting_price(self):
        response = self.client.get(self.test_url)
        n = format_bid_value(self.listing.starting_price)
        bid_forbidden = "<span id='bid_forbidden' class='btn btn-warning disabled'>%s</span>" \
                        % NO_BID_NO_MONEY_SP
        bid_input_disabled = '<input type="number" name="bid_value" value="%s" ' \
                             'class="form-control d-inline" style="width: 100px;" ' \
                             'min="%s" step="any" disabled id="id_bid_value">' % (n, n)
        self.assertContains(response, bid_forbidden, status_code=200)
        self.assertContains(response, bid_input_disabled)

    def _bid(self):
        self.second_profile.add_money(2)
        self.second_profile.refresh_from_db(fields=['money'])
        self.listing.make_a_bid(self.second_profile, 2)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.highest_bid, 2)

    def _user_bid_already_on_the_top(self):
        response = self.client.get(self.test_url)

        n = self.listing.get_highest_price(percent=True)
        n = format_bid_value(n)
        bid_forbidden = "<span id='bid_forbidden' class='btn btn-warning disabled'>%s</span>" \
                        % NO_BID_ON_TOP
        bid_input_disabled = '<input type="number" name="bid_value" value="%s" ' \
                             'class="form-control d-inline" style="width: 100px;" ' \
                             'min="%s" step="any" disabled id="id_bid_value">' % (n, n)
        self.assertContains(response, bid_forbidden, status_code=200)
        self.assertContains(response, bid_input_disabled)

    def _user_money_is_less_than_the_highest_bid(self):
        response = self.client.get(self.test_url)
        bid_forbidden = "<span id='bid_forbidden' class='btn btn-warning disabled'>%s</span>" \
                        % NO_BID_NO_MONEY
        self.assertContains(response, bid_forbidden, status_code=200)


class AuctionLotViewForTheOwnerTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.user1 = get_user('White-faced-owl')
        cls.owner_profile = Profile.manager.get(username='White-faced-owl')
        cls.user2 = get_user('Eagle-owl')
        cls.second_profile = Profile.manager.get(username='Eagle-owl')

        cls.category = get_category('pies')
        cls.listing = get_listing(
            cls.category,
            cls.owner_profile,
            title='Japari Pie',
            description='Sed ut perspiciatis unde omnis iste...',
        )
        cls.listing.publish_the_lot()

        cls.test_url = reverse('auctions:auction_lot', args=[cls.listing.slug])

    def setUp(self):
        if self.listing.owner != self.owner_profile:
            self.listing.save_new_owner(self.owner_profile)
        if self.listing.is_active is False:
            self.listing.publish_the_lot()
            self.listing.refresh_from_db()

    def test_auction_loads_for_the_owner(self):
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self._owner_auction_form_exists(response)
        self._owner_auction_comment_form_exists(response)

    def _owner_auction_form_exists(self, response):
        ghost_field = '<input type="hidden" name="ghost_field"'
        self.assertContains(response, ghost_field)

        bid_input = '<input type="number" name="bid_value"'
        auctioneer_input = '<input type="hidden" name="auctioneer"'
        self.assertNotContains(response, bid_input, msg_prefix='not for the owner')
        self.assertNotContains(response, auctioneer_input, msg_prefix='not for the owner')

    def _owner_auction_comment_form_exists(self, response):
        comments_view_url = reverse('auctions:comments', args=[self.listing.slug])
        form_html = "<form action='%s'" % comments_view_url
        text_input = '<textarea name="text_field"'
        button_save = '<button type="submit" class="btn btn-primary mb-5">Comment on</button>'
        author_hidden = '<input type="hidden" name="author_hidden" ' \
                        'value="%s" disabled="" id="id_author_hidden">' \
                        % self.owner_profile.username
        self.assertContains(response, form_html, msg_prefix='form points to the CommentsView')
        self.assertContains(response, text_input)
        self.assertContains(response, button_save, html=True)
        self.assertContains(response, author_hidden, html=True)

    def test_auction_withdrew(self):
        login_user(self, self.owner_profile.username)
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)

        self._auction_withdrew_form_exists(response)
        self._auction_withdrew_form_works()

    def _auction_withdrew_form_exists(self, response):
        button_withdraw = "<button type='submit' name='btn_owner_withdrew'"
        self.assertContains(response, button_withdraw)

    def _auction_withdrew_form_works(self):
        form_data = {'ghost_field': '', 'btn_owner_withdrew': ['']}
        response_post = self.client.post(self.test_url, form_data)
        success_url = reverse('auctions:listing', args=[self.listing.slug])
        self.assertRedirects(response_post, success_url, 302, 200)

        response_get = self.client.get(response_post.url)
        self.assertEqual(response_get.status_code, 200)
        self.listing.refresh_from_db()
        self.assertFalse(self.listing.is_active)

    def test_auction_closed(self):
        login_user(self, self.owner_profile.username)
        self._auction_close_form_not_exists()

        self._bid()
        response = self.client.get(self.test_url)
        self._auction_close_form_exists(response)

        self._auction_close_form_works()

    def _auction_close_form_not_exists(self):
        response = self.client.get(self.test_url)
        self.assertEqual(response.status_code, 200)
        button_close = "<button type='submit' name='btn_owner_closed_auction'"
        self.assertNotContains(response, button_close, msg_prefix='no bid no form')

    def _bid(self):
        self.second_profile.add_money(20)
        self.second_profile.refresh_from_db()
        self.listing.make_a_bid(self.second_profile, 20)
        self.listing.refresh_from_db()
        self.assertEqual(self.listing.highest_bid, 20)

    def _auction_close_form_exists(self, response):
        button_close = "<button type='submit' name='btn_owner_closed_auction'"
        self.assertContains(response, button_close)

    def _auction_close_form_works(self):
        form_data = {'ghost_field': '', 'btn_owner_closed_auction': ['']}
        response_post = self.client.post(self.test_url, form_data)
        success_url = reverse('auctions:user_history', args=[self.owner_profile.pk])
        self.assertRedirects(response_post, success_url, 302, 200)

        self.listing.refresh_from_db()
        self.assertFalse(self.listing.is_active)
        self.assertEqual(self.listing.owner, self.second_profile)
