import tempfile

from django.test import SimpleTestCase, TestCase, override_settings
from django.urls import reverse
from django.conf import settings

from django.contrib.auth.models import User
from auctions.models import Profile, ListingCategory, Listing, Comment


DB = settings.PROJECT_MAIN_APPS['auctions']['db']['name']
DATABASES = ['default', DB]
FAST_HASHER = ['django.contrib.auth.hashers.MD5PasswordHasher']

SMALL_GIF = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00'
    b'\x00\x05\x04\x04\x00\x00\x00\x2c\x00\x00\x00\x00'
    b'\x01\x00\x01\x00\x00\x02\x02\x44\x01\x00\x3b'
)
IMGNAME = 'dot.gif'
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


@override_settings(PASSWORD_HASHERS=FAST_HASHER)
class AuctionsIntegrationWithRegistrationTests(TestCase):
    databases = DATABASES

    def test_register_form(self):
        self._register_page_loads()
        self._register_request()
        self._models_created()

    def _register_page_loads(self):
        from accounts.forms import UserRegisterForm
        response = self.client.get(reverse('accounts:register'))
        self.assertTrue(response.status_code == 200)
        self.assertTrue(isinstance(response.context['form'], UserRegisterForm))

    def _register_request(self):
        url = reverse('accounts:register_and_next', args=['auctions'])
        form_data = {
            'username': 'Serval',
            'password1': 'qwerty',
            'password2': 'qwerty',
        }
        response_post = self.client.post(url, form_data)

        self.assertRedirects(response_post, reverse('auctions:index'), 302, 200)

    def _models_created(self):
        self.assertTrue(User.objects.filter(username='Serval').exists())
        self.assertTrue(Profile.manager.filter(username='Serval').exists())

        response = self.client.get(reverse('auctions:index'))
        self.assertTrue(response.status_code == 200)
        self.assertTrue(response.context['user'].is_authenticated)
        self.assertEqual(response.context['user'].username, 'Serval')
