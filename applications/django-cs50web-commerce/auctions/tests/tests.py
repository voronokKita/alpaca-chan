import tempfile
import datetime

from django.test import TestCase, SimpleTestCase, override_settings
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

# TODO navbar, functions

DB = settings.PROJECT_MAIN_APPS['auctions']['db']['name']
DATABASES = ['default', DB]
FAST_PASSWORD_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']

small_gif = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00'
    b'\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
)
IMGNAME = 'dot.gif'
TEST_IMAGE = SimpleUploadedFile(IMGNAME, small_gif, content_type='image/gif')
TMP_IMAGE = tempfile.NamedTemporaryFile(suffix='.jpg').name


def get_category(label='precious') -> ListingCategory:
    return ListingCategory.manager.create(label=label)


def get_profile(username='Toki', money=100) -> Profile:
    return Profile.manager.create(username=username, money=money)


def get_listing(category=None, profile=None, username='Fennec',
                title='Japari bun', image=TMP_IMAGE,
                description='An endless source of energy!') -> Listing:
    if category is None:
        category = get_category()
    if profile is None:
        profile = get_profile(username)
    return Listing.manager.create(
        title=title,
        description=description,
        image=image,
        category=category,
        owner=profile,
    )


def get_comment(listing=None, profile=None,
                text='Japari bun is the best bun!') -> Comment:
    if profile is None:
        profile = get_profile()
    if listing is None:
        listing = get_listing(profile=profile)
    return Comment.manager.create(listing=listing, author=profile, text=text)


class AuctionsResourcesTests(SimpleTestCase):
    app_dir = settings.ALL_PROJECT_APPS['auctions']['app_dir']
    resources = [
        app_dir / 'readme.md',
        app_dir / 'auctions' / 'logs.py',
        app_dir / 'auctions' / 'db_router.py',
        app_dir / 'auctions' / 'static' / 'auctions' / 'favicon.ico',
        app_dir / 'auctions' / 'static' / 'auctions' / 'logo.jpg',
        app_dir / 'auctions' / 'templates' / 'auctions' / 'base_auctions.html',
    ]
    def test_base_resources_exists(self):
        from auctions.db_router import CommerceRouter
        for item in self.resources:
            self.assertTrue(item.exists(), msg=item)
