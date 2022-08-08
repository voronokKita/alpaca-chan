import datetime
from unittest.mock import patch, PropertyMock

from django.conf import settings
from django.test import TestCase, SimpleTestCase, override_settings
from django.urls import reverse
from django.utils import timezone
from django.utils.text import slugify
from django.contrib.auth.hashers import make_password

from django.contrib.auth.models import User
from auctions.models import Profile, ListingCategory, Comment, Listing, Watchlist, Bid

""" 
ⓘ The application folder must be added to the "sources" 
for PyCharm to stop swearing on the models import.
"""
SECOND_DB = settings.PROJECT_MAIN_APPS['auctions']['db']['name']
PASSWORD_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']


def get_category(label='precious') -> ListingCategory:
    return ListingCategory.manager.create(label=label)


def get_profile(username='Toki') -> Profile:
    return Profile.manager.create(username=username)


def get_listing(category=None, profile=None,
                title='Japari bun', image='photo.jpg',
                description='An endless source of energy!') -> Listing:
    if category is None:
        category = get_category()
    if profile is None:
        profile = get_profile()
    listing = Listing.manager.create(
        title=title,
        description=description,
        image=image,
        category=category,
        owner=profile,
    )
    return listing


class UniqueSlugTests(TestCase):
    databases = [SECOND_DB]

    @patch('auctions.models.SLUG_MAX_ATTEMPTS', 3)
    def test_get_unique_slug_or_none(self):
        from auctions.models import SLUG_MAX_ATTEMPTS, SLUG_MAX_LEN

        expected = SLUG_MAX_ATTEMPTS
        attempts = SLUG_MAX_ATTEMPTS + 2
        for i in range(attempts):
            get_listing(title='Test slug')

        self.assertEqual(len(Listing.manager.all()), expected)

        title = 's' * SLUG_MAX_LEN
        get_listing(title=title + 'appendix')
        self.assertTrue(Listing.manager.get(slug=title))


class UserProfileTests(TestCase):
    databases = ['default', SECOND_DB]

    def test_new_user_gets_new_profile_in_correct_db(self):
        User.objects.create(username='user1')
        self.assertQuerysetEqual(
            User.objects.db_manager(SECOND_DB).filter(username='user1'), []
        )
        self.assertTrue(
            User.objects.db_manager('default').get(username='user1')
        )

        self.assertTrue(
            Profile.manager.db_manager(SECOND_DB).get(username='user1')
        )
        try: Profile.manager.db_manager('default').get(username='user1')
        except Exception: pass
        else: raise Exception('found profile on defaults db')

    def test_profile_backref(self):
        profile = get_profile()
        listing = get_listing(profile=profile)
        comment = Comment.manager.create(listing=listing, author=profile,
                                         text='Japari bun is the best bun!')
        profile.refresh_from_db()
        self.assertQuerysetEqual(profile.lots_owned.all(), [listing])
        self.assertQuerysetEqual(profile.comment_set.all(), [comment])


class ListingCategoryTests(TestCase):
    databases = [SECOND_DB]

    def test_category_normal_case(self):
        ListingCategory.manager.create(label='items')
        self.assertTrue(ListingCategory.manager.get(label='items'))

    def test_category_backref(self):
        category = get_category()
        listing = get_listing(category)
        category.refresh_from_db()
        self.assertQuerysetEqual(category.listing_set.all(), [listing])


class ListingTests(TestCase):
    databases = [SECOND_DB]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.time_now = timezone.localtime()
        cls.category = get_category()
        cls.profile = get_profile('Toki')
        cls.listing = get_listing(category=cls.category, profile=cls.profile)

    def test_listing_normal_case(self):
        listing = self.listing
        self.assertEqual(listing.slug, 'japari-bun')
        self.assertEqual(listing.starting_price, 1)
        self.assertTrue(listing.date_created >= self.time_now)
        self.assertIsNone(listing.date_published)
        self.assertFalse(listing.is_active)
        self.assertQuerysetEqual(listing.potential_buyers.all(), [])
        self.assertQuerysetEqual(listing.in_watchlist.all(), [self.profile])

    def test_listing_methods(self):
        listing = get_listing()

        listing.publish_the_lot()
        listing.refresh_from_db()
        self.assertTrue(listing.is_active)

        # change_the_owner

    def test_listing_backref(self):
        listing = self.listing
        comment = Comment.manager.create(text='Japari bun is the best bun!', listing=listing)
        listing.refresh_from_db()
        self.assertQuerysetEqual(listing.comment_set.all(), [comment])


class WatchlistTests(TestCase):
    databases = [SECOND_DB]

    def test_watchlist_normal_case(self):
        profile1 = get_profile('Toki')
        profile2 = get_profile('Shoujoutoki')
        listing1 = get_listing(profile=profile2, title='friends')
        listing2 = get_listing(profile=profile2, title='buns')
        profile1.items_watched.add(listing1)
        profile1.items_watched.add(listing2)

        self.assertEqual(len(Watchlist.manager.all()), 4)
        self.assertTrue(profile1.items_watched.get(slug='friends'))
        self.assertIn(profile1, listing1.in_watchlist.all())
        self.assertIn(profile2, listing1.in_watchlist.all())
        self.assertTrue(Profile.manager.
                        filter(username='Toki', items_watched__slug='buns').exists())


class BidTests(TestCase):
    databases = [SECOND_DB]

    def test_bets_normal_case(self):
        time_now = timezone.localtime()
        listing1 = get_listing(title='friends')
        listing2 = get_listing(title='buns')

        profile = get_profile('Shoujoutoki')
        profile.placed_bets.add(listing1, through_defaults={'bid_value': 1})
        profile.placed_bets.add(listing2, through_defaults={'bid_value': 2})

        profile1 = get_profile('Toki')
        profile1.placed_bets.add(listing2, through_defaults={'bid_value': 3})
        l = listing2.bid_set.latest()
        print('A', l.bid_value)

        self.assertEqual(len(Bid.manager.all()), 2)
        self.assertTrue(profile.placed_bets.get(slug='friends'))
        self.assertTrue(listing1.potential_buyers.get(username='Shoujoutoki'))
        self.assertTrue(
            Profile.manager.filter(username='Shoujoutoki',
                                   placed_bets__slug='buns').exists()
        )
        bid = profile.bid_set.get(lot=listing2)
        self.assertEqual(bid.bid_value, 2)
        self.assertTrue(bid.bid_date >= time_now <= timezone.localtime())


class CommentTests(TestCase):
    databases = [SECOND_DB]

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.time_now = timezone.localtime()
        cls.profile = get_profile('Rikaon')
        cls.listing = get_listing(profile=cls.profile)

    def test_comment_normal_case(self):
        Comment.manager.create(text='japari bun is the best bun', listing=self.listing)
        comment = Comment.manager.get(pk=1)
        self.assertTrue(comment.pub_date >= self.time_now)

    def test_comment_backref(self):
        text = 'japari bun is the best bun'
        Comment.manager.create(text=text, listing=self.listing, author=self.profile)
        self.assertTrue(self.listing.comment_set.get(text=text))
        self.assertTrue(self.profile.comment_set.get(text=text))
