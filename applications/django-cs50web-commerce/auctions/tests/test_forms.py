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


from django.contrib.auth.models import User
from accounts.models import ProxyUser
from auctions.models import (
    Profile, ListingCategory, Comment,
    Listing, Watchlist, Bid, Log
)
from .tests import (
    DB, TEST_IMAGE,
    get_category, get_profile,
    get_listing, get_comment
)
