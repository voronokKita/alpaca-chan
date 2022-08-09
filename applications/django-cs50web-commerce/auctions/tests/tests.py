from django.test import TestCase, SimpleTestCase
from django.utils import timezone
from django.urls import reverse
from django.conf import settings
from django.contrib.auth.hashers import make_password


from django.contrib.auth.models import User
from auctions.models import (
    Profile, ListingCategory, Comment,
    Listing, Watchlist, Bid, Log
)
from .test_models import get_category, get_profile, get_listing, get_comment


DB = settings.PROJECT_MAIN_APPS['auctions']['db']['name']
PASSWORD_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']


class IndexViewTests(TestCase):
    databases = [DB]

    def test_index_loads(self):
        response = self.client.get(reverse('auctions:index'))
        self.assertEqual(response.status_code, 200)


class ProfileTests(TestCase):
    databases = ['default', DB]

    def test_profile_loads(self):
        User.objects.create(username='Serval')
        response = self.client.get(reverse('auctions:profile', args=[1]))
        self.assertEqual(response.status_code, 200)


class UserHistoryViewTests(TestCase):
    databases = [DB]

    def test_history_loads(self):
        profile = get_profile(username='Nana')
        response = self.client.get(reverse('auctions:user_history', args=[profile.pk]))
        self.assertEqual(response.status_code, 200)


class WatchlistViewTests(TestCase):
    databases = [DB]

    def test_watchlist_loads(self):
        profile = get_profile(username='Kitakitsune')
        response = self.client.get(reverse('auctions:watchlist', args=[profile.pk]))
        self.assertEqual(response.status_code, 200)


class CreateListingViewTests(TestCase):
    databases = [DB]

    def test_create_loads(self):
        response = self.client.get(reverse('auctions:create_listing'))
        self.assertEqual(response.status_code, 200)


class ListingViewTests(TestCase):
    databases = [DB]

    def test_listing_loads(self):
        listing = get_listing()
        response = self.client.get(reverse('auctions:listing', args=[listing.slug]))
        self.assertEqual(response.status_code, 200)


class CommentsViewTests(TestCase):
    databases = [DB]

    def test_comments_loads(self):
        listing = get_listing()
        response = self.client.get(reverse('auctions:comments', args=[listing.slug]))
        self.assertEqual(response.status_code, 200)


class AuctionLotViewTests(TestCase):
    databases = [DB]

    def test_published_loads(self):
        listing = get_listing()
        response = self.client.get(reverse('auctions:auction_lot', args=[listing.slug]))
        self.assertEqual(response.status_code, 200)
