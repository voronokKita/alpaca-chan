from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.utils import timezone
from django.core.files.uploadedfile import SimpleUploadedFile

from django.contrib.auth.models import User
from auctions.models import (
    Profile, ListingCategory, Comment,
    Listing, Watchlist, Bid, Log,
    user_media_path,

    NO_BID_NO_MONEY_SP, NO_BID_THE_OWNER,
    NO_BID_NO_MONEY, NO_BID_ON_TOP, NEW_BID_PERCENT,
    DEFAULT_STARTING_PRICE,

    LOG_REGISTRATION, LOG_NEW_LISTING, LOG_YOU_WON,
    LOG_LOT_PUBLISHED, LOG_NEW_BID, LOG_WITHDRAWN,
    LOG_YOU_LOSE, LOG_OWNER_REMOVED, LOG_ITEM_SOLD,
    LOG_MONEY_ADDED
)
from .tests import (
    DB, DATABASES,
    SMALL_GIF, IMGNAME,
    get_category, get_profile,
    get_listing, get_comment
)

""" TODO
+ unique slug func
+ profile model
    + User & Profile models sync
    + save()
    + add_money()
    + get_money()
    + display_money()
+ category model
+ listing model
    + image upload
    + save()
    + can_be_published()
    + publish_the_lot()
    + withdraw()
    + can_unwatch()
    + unwatch()
    + no_bid_option()
    + make_a_bid()
    + change_the_owner()
    + save_new_owner()
    + get_highest_price()
    + get_highest_bid_entry()
+ watchlist model
+ bid model
    + refund()
+ comment model
+ profile log model
"""


class UniqueSlugTests(TestCase):
    databases = DATABASES

    def test_unique_slug_works(self):
        expected = 3
        get_listing(title='Test slug', username='Eagle-owl')
        get_listing(title='Test slug', username='White-faced-owl')
        get_listing(title='Test slug', username='Fossa')
        self.assertEqual(Listing.manager.count(), expected)

        from auctions.models import SLUG_MAX_LEN
        title = 's' * SLUG_MAX_LEN
        get_listing(title=title + 'appendix')
        self.assertTrue(Listing.manager.get(slug=title))


class UserProfileTests(TestCase):
    databases = DATABASES

    def test_new_user_gets_new_profile_in_correct_db(self):
        user = User.objects.create(username='Serval')
        self.assertFalse(User.objects.db_manager(DB).filter(username='Serval').exists())
        self.assertTrue(User.objects.db_manager('default').filter(username='Serval').exists())

        self.assertTrue(Profile.manager.db_manager(DB).filter(username='Serval').exists())
        self.assertTrue(Profile.manager.filter(user_model_pk=user.pk).exists())
        self.assertTrue(Log.manager.filter(profile__username='Serval').exists())

        try: Profile.manager.db_manager('default').get(username='Serval')
        except Exception: pass
        else: raise Exception('found auctions_profile TABLE ON DEFAULTS db')

    def test_profile_username_updated_with_user_username(self):
        user = User.objects.create(username='Manul')
        self.assertTrue(Profile.manager.filter(username='Manul').exists())
        user.username = 'Manul Cat'
        user.save()
        self.assertTrue(Profile.manager.filter(username='Manul Cat').exists())
        self.assertFalse(Profile.manager.filter(username='Manul').exists())

    def test_profile_backref(self):
        profile = get_profile()
        listing = get_listing(profile=profile)
        comment = get_comment(listing, profile)
        self.assertTrue(profile.lots_owned.contains(listing))
        self.assertTrue(profile.comment_set.contains(comment))
        self.assertTrue(profile.logs.filter(entry='Date of your registration.').exists())

    def test_profile_method_money(self):
        profile = get_profile(money=0)
        self._add_money(profile)

        listing = get_listing()
        listing.publish_the_lot()
        listing.make_a_bid(profile, 10)
        profile.refresh_from_db()
        self._display_money(profile)

        self._get_money(profile)

    def _add_money(self, profile):
        profile.add_money(10)
        profile.refresh_from_db()
        self.assertTrue(profile.money == 10)
        profile.add_money(10)
        profile.refresh_from_db()
        self.assertTrue(profile.money == 20)

    def _display_money(self, profile):
        self.assertEqual(profile.display_money(), (10.0, 10.0))

    def _get_money(self, profile):
        self.assertEqual(profile.get_money(10.0), 10.0)
        profile.refresh_from_db()
        self.assertTrue(profile.money == 0)

    def test_profile_integrity_cascade_deletion(self):
        user = User.objects.create(username='Pallas')
        profile_one = Profile.manager.get(username='Pallas')
        profile_two = get_profile('Manul')
        category = get_category()

        listing_one = get_listing(category, profile_one)
        listing_one.publish_the_lot()
        listing_two = get_listing(category, profile_two)
        listing_two.publish_the_lot()

        comment_one = get_comment(listing_one, profile_two)
        comment_two = get_comment(listing_two, profile_one)

        profile_one.add_money(100)
        profile_one.refresh_from_db()
        listing_one.make_a_bid(profile_two, 10)
        listing_two.make_a_bid(profile_one, 20)
        self.assertTrue(Bid.manager.count() == 2)
        self.assertTrue(Watchlist.manager.count() == 4)

        user.delete()
        self.assertFalse(Profile.manager.filter(username='Pallas').exists(), 'user’s profile deleted')
        self.assertTrue(Profile.manager.filter(username='Manul').exists(), 'profile2 not touched')
        self.assertTrue(ListingCategory.manager.contains(category), 'category not touched')
        self.assertFalse(Listing.manager.contains(listing_one), 'user’s listing1 deleted')
        self.assertTrue(Listing.manager.contains(listing_two), 'profile2’s listing2 not touched')
        self.assertTrue(Bid.manager.count() == 0, 'two bids vanished')
        self.assertTrue(Watchlist.manager.count() == 1, 'profile2’s watchlist not touched')
        self.assertFalse(Comment.manager.contains(comment_one),
                         'comment under user’s listing1 deleted along with')
        self.assertTrue(Comment.manager.contains(comment_two),
                        'comment of the user under profile2’s listing2 not touched')
        comment_two.refresh_from_db()
        self.assertIsNone(comment_two.author, 'user’s comment now without author')


class ListingCategoryTests(TestCase):
    databases = DATABASES

    def test_category_normal_case(self):
        ListingCategory.manager.create(label='items')
        self.assertTrue(ListingCategory.manager.filter(label='items').exists())

    def test_category_backref(self):
        category = get_category()
        listing = get_listing(category)
        self.assertTrue(category.listing_set.contains(listing))


class ListingTests(TestCase):
    """ May crash if other tests are using TEST_IMAGE. """
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.time_now = timezone.localtime()
        cls.category = get_category()
        cls.profile = get_profile('Serval')
        test_image = SimpleUploadedFile(IMGNAME, SMALL_GIF, content_type='image/gif')
        cls.listing = get_listing(category=cls.category, title='Japari bun',
                                  profile=cls.profile, image=test_image)

        cls.image_path = Path(
            settings.MEDIA_ROOT / user_media_path(cls.listing, IMGNAME)
        ).resolve()

    @classmethod
    def tearDownClass(cls):
        if cls.image_path.exists():
            cls.image_path.unlink()
        if cls.image_path.parent.exists() and \
                not [f for f in cls.image_path.parent.iterdir()]:
            cls.image_path.parent.rmdir()
        super().tearDownClass()

    def test_listing_normal_case(self):
        listing = self.listing
        self.assertEqual(listing.slug, 'japari-bun')
        self.assertEqual(listing.starting_price, 1)
        self.assertTrue(listing.date_created >= self.time_now <= timezone.localtime())
        self.assertIsNone(listing.date_published)
        self.assertFalse(listing.is_active)
        self.assertEqual(listing.potential_buyers.count(), 0)
        self.assertTrue(listing.in_watchlist.contains(self.profile))
        self.assertTrue(self.image_path.exists())

        listing.delete()
        self.assertFalse(self.image_path.exists(), 'image deleted along with the listing')


    def test_listing_backref(self):
        listing = get_listing()
        comment = get_comment(listing)
        self.assertTrue(listing.comment_set.contains(comment))

    def test_listing_method_publish_the_lot(self):
        listing = get_listing(username='Okapi')
        time_now = timezone.localtime()
        self._publish_successfully(listing, time_now)

        self._listing_already_published(listing)

        listing.withdraw()
        listing.starting_price = 0
        listing.save()
        self._too_low_starting_price_to_publish(listing)

    def _publish_successfully(self, listing, time_now):
        self.assertTrue(listing.publish_the_lot(), 'ok')
        self.assertTrue(listing.is_active, 'ok')
        self.assertTrue(listing.date_published >= time_now <= timezone.localtime(), 'ok')

    def _listing_already_published(self, listing):
        self.assertFalse(listing.publish_the_lot(),'already published')

    def _too_low_starting_price_to_publish(self, listing):
        self.assertFalse(listing.publish_the_lot(), 'too low starting price')

    def test_listing_method_withdraw(self):
        listing = get_listing()
        listing.publish_the_lot()
        potential_buyer = get_profile()
        listing.make_a_bid(potential_buyer, 2)

        # ok
        self.assertTrue(potential_buyer.items_watched.contains(listing))
        self.assertTrue(listing.withdraw())
        self.assertFalse(listing.is_active)
        self.assertIsNone(listing.date_published)
        self.assertIsNone(listing.highest_bid)
        self.assertTrue(listing.potential_buyers.count() == 0)
        self.assertFalse(potential_buyer.items_watched.contains(listing))
        self.assertTrue(listing.in_watchlist.count() == 1)

        # not published
        self.assertFalse(listing.withdraw(), 'not published')

    def test_listing_method_unwatch(self):
        owner = get_profile()
        listing = get_listing(profile=owner)
        listing.publish_the_lot()
        self._unwatch_owner(listing, owner)

        auctioneer = get_profile('Tsuchinoko')
        listing.make_a_bid(auctioneer, 2)
        self._unwatch_potential_buyer(listing, auctioneer)

        watcher = get_profile('Tasmanian-Devil')
        listing.in_watchlist.add(watcher)
        self._unwatch_successfully(listing, watcher)

    def _unwatch_owner(self, listing, profile):
        self.assertFalse(listing.unwatch(profile), 'owner can’t unwatch')

    def _unwatch_potential_buyer(self, listing, profile):
        self.assertFalse(listing.unwatch(profile), 'potential buyer can’t unwatch')

    def _unwatch_successfully(self, listing, profile):
        self.assertTrue(listing.unwatch(profile), 'ok')
        self.assertFalse(listing.in_watchlist.contains(profile), 'ok')

    def test_listing_method_no_bid_option(self):
        owner = get_profile()
        listing = get_listing(profile=owner)
        listing.publish_the_lot()
        self._no_bid_owner(listing, owner)

        profile_one = get_profile('Shirosai', money=0.99)
        self._no_bid_low_than_starting_price(listing, profile_one)

        profile_one.add_money(10)
        profile_one.refresh_from_db()
        self._can_place_a_bid(listing, profile_one)

        self.assertTrue(listing.make_a_bid(profile_one, 10), 'ok first bid')
        self._no_bid_already_on_the_top(listing, profile_one)

        profile_two = get_profile('Sunaneko', money=10)
        self._no_bid_low_on_money(listing, profile_two)

        profile_two.add_money(10 * NEW_BID_PERCENT - 10)
        profile_two.refresh_from_db()
        self._can_place_a_bid(listing, profile_two)

    def _no_bid_owner(self, listing, profile):
        self.assertEqual(listing.no_bid_option(profile), NO_BID_THE_OWNER, 'owner can’t bid')

    def _can_place_a_bid(self, listing, profile):
        self.assertIsNone(listing.no_bid_option(profile), 'can place a bid')

    def _no_bid_low_than_starting_price(self, listing, profile):
        self.assertEqual(listing.no_bid_option(profile), NO_BID_NO_MONEY_SP, 'starting price')

    def _no_bid_already_on_the_top(self, listing, profile):
        self.assertEqual(listing.no_bid_option(profile), NO_BID_ON_TOP, 'already on the top')

    def _no_bid_low_on_money(self, listing, profile):
        self.assertEqual(listing.no_bid_option(profile), NO_BID_NO_MONEY, 'low on money')

    def test_listing_method_make_a_bid(self):
        listing = get_listing()
        listing.publish_the_lot()

        profile_one = get_profile('Owl')
        self._bid_successful(listing, profile_one, bid_value=1)

        profile_two = get_profile('Chameleon')
        bid_value = 1 * NEW_BID_PERCENT - 0.01
        self._bid_too_low(listing, profile_one, bid_value)

        bid_value = 1 * NEW_BID_PERCENT
        self._bid_successful(listing, profile_two, bid_value)

    def _bid_successful(self, listing, profile, bid_value):
        self.assertTrue(listing.make_a_bid(profile, bid_value), 'ok')
        self.assertTrue(listing.in_watchlist.contains(profile), 'ok')
        self.assertTrue(listing.potential_buyers.contains(profile), 'ok')

    def _bid_too_low(self, listing, profile, bid_value):
        self.assertFalse(listing.make_a_bid(profile, bid_value),
                         'lower than listing’s highest bid')

    def test_listing_method_change_the_owner(self):
        seller = get_profile()
        listing = get_listing(profile=seller)
        listing.starting_price = 1.5
        listing.save()
        self._change_the_owner_error(listing)

        bid_value = 2
        buyer = get_profile('Rikaon')
        listing.make_a_bid(buyer, bid_value)
        listing.refresh_from_db()
        self.assertTrue(listing.highest_bid == bid_value)
        self._change_the_owner_successfully(listing, seller, buyer)

    def _change_the_owner_error(self, listing):
        self.assertFalse(listing.change_the_owner(), 'not published')
        listing.publish_the_lot()
        self.assertFalse(listing.change_the_owner(), 'without potential buyers')

    def _change_the_owner_successfully(self, listing, seller, buyer):
        self.assertTrue(listing.change_the_owner())
        self.assertFalse(listing.is_active)
        self.assertIsNone(listing.date_published)
        self.assertTrue(listing.starting_price == DEFAULT_STARTING_PRICE)
        self.assertTrue(listing.potential_buyers.count() == 0)
        self.assertFalse(seller.lots_owned.contains(listing))
        self.assertTrue(buyer.lots_owned.contains(listing))
        self.assertFalse(seller.items_watched.contains(listing))
        self.assertTrue(buyer.items_watched.contains(listing))

    def test_listing_method_highest_bid(self):
        profile1 = get_profile('Dog')
        profile2 = get_profile('Bear')
        listing = get_listing()
        listing.publish_the_lot()

        self.assertEqual(listing.get_highest_price(), 1)
        self.assertEqual(listing.get_highest_price(with_starting_price=False), 0)
        self.assertIsNone(listing.get_highest_bid_entry())

        listing.make_a_bid(profile1, 10)
        listing.make_a_bid(profile2, 20)
        listing.refresh_from_db()

        self.assertEqual(listing.get_highest_price(), 20)
        self.assertEqual(listing.get_highest_price(percent=True), 20 * NEW_BID_PERCENT)

        entry = listing.get_highest_bid_entry()
        self.assertTrue(entry.auctioneer.username == 'Bear')


class WatchlistTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.profile1 = get_profile('Toki')
        cls.profile2 = get_profile('Shoujoutoki')
        cls.listing1 = get_listing(profile=cls.profile2, title='friends')
        cls.listing2 = get_listing(profile=cls.profile2, title='buns')
        cls.profile1.items_watched.add(cls.listing1)
        cls.profile1.items_watched.add(cls.listing2)

    def test_watchlist_normal_case(self):
        self.assertEqual(Watchlist.manager.count(), 4)
        self.assertTrue(self.profile1.items_watched.filter(slug='friends').exists())
        self.assertTrue(
            Profile.manager.filter(username='Toki',
                                   items_watched__slug='buns').exists()
        )
        self.assertTrue(self.listing1.in_watchlist.contains(self.profile1))
        self.assertTrue(self.listing1.in_watchlist.contains(self.profile2))


class BidTests(TestCase):
    databases = DATABASES

    def test_bids_normal_case(self):
        time_now = timezone.localtime()
        listing1 = get_listing(title='friends', username='Fossa')
        listing1.publish_the_lot()
        listing2 = get_listing(title='buns', username='Gazelle')
        listing2.publish_the_lot()

        profile = get_profile('Shoujoutoki')
        listing1.make_a_bid(profile, 2)
        profile.refresh_from_db()
        listing2.make_a_bid(profile, 3)

        self.assertEqual(Bid.manager.count(), 2)
        self.assertTrue(profile.placed_bids.filter(slug='friends').exists())
        self.assertTrue(listing1.potential_buyers.filter(username='Shoujoutoki').exists())
        self.assertTrue(
            Profile.manager.filter(username='Shoujoutoki',
                                   placed_bids__slug='buns').exists()
        )
        bid = profile.bid_set.latest()
        self.assertTrue(bid.bid_value == 3)
        self.assertTrue(bid.bid_date >= time_now <= timezone.localtime())

    def test_bids_method_refund(self):
        listing = get_listing()
        listing.publish_the_lot()

        profile1 = get_profile('Aardwolf', money=10)
        profile2 = get_profile('Graywolf', money=20)
        listing.make_a_bid(profile1, 10)
        listing.make_a_bid(profile2, 20)

        profile1.refresh_from_db()
        profile2.refresh_from_db()
        self.assertTrue(profile1.money == 0)
        self.assertTrue(profile2.money == 0)

        listing.withdraw()
        profile1.refresh_from_db()
        profile2.refresh_from_db()
        self.assertTrue(profile1.money == 10)
        self.assertTrue(profile2.money == 20)


class CommentTests(TestCase):
    databases = DATABASES

    @classmethod
    def setUpTestData(cls):
        cls.time_now = timezone.localtime()
        cls.profile = get_profile('Rikaon')
        cls.listing = get_listing(profile=cls.profile)
        cls.comment_text = 'japari bun is the best bun'

    def test_comment_normal_case(self):
        comment = Comment.manager.create(
            listing=self.listing,
            author=self.profile,
            text=self.comment_text
        )
        self.assertTrue(comment.pub_date >= self.time_now <= timezone.localtime())

    def test_comment_backref(self):
        get_comment(self.listing, self.profile, self.comment_text)
        self.assertTrue(self.listing.comment_set.filter(text=self.comment_text).exists())
        self.assertTrue(self.profile.comment_set.filter(text=self.comment_text).exists())


class LogTests(TestCase):
    databases = DATABASES

    def test_auctions_logs(self):
        user = User.objects.create(username='LuckyBeast')
        self._log_registration()

        profile = Profile.manager.get(username='LuckyBeast')
        money = 10
        self._log_money_added(profile, money)

        title = 'Japari Bun'
        listing = get_listing(profile=profile, title=title)
        self._log_new_listing(listing)

        self._log_auction_created(listing)

        loser = get_profile(username='Moose')
        lowest_bid = money
        self._logs_new_bid(listing, loser, lowest_bid)
        loser.refresh_from_db()

        self._logs_auction_closed(listing, lowest_bid)

        self._logs_withdrawn(listing, loser)

        self.assertTrue(Log.manager.count() == 16, 'total log entries')

    def _log_registration(self):
        self.assertTrue(Log.manager.filter(entry=LOG_REGISTRATION).exists())

    def _log_money_added(self, profile, money):
        profile.add_money(money)
        self.assertTrue(Log.manager.filter(entry=LOG_MONEY_ADDED % money).exists())

    def _log_new_listing(self, listing):
        self.assertTrue(Log.manager.filter(entry=LOG_NEW_LISTING % listing.title).exists())

    def _log_auction_created(self, listing):
        listing.publish_the_lot()
        self.assertTrue(Log.manager.filter(entry=LOG_LOT_PUBLISHED % listing.title).exists())

    def _logs_new_bid(self, listing, profile, bid_value):
        listing.make_a_bid(profile, bid_value)
        self.assertTrue(Log.manager.filter(entry=LOG_NEW_BID % (listing.title, bid_value)).exists())

    def _logs_auction_closed(self, listing, lowest_bid):
        winner = get_profile(username='Lion')
        highest_bid = 20
        listing.make_a_bid(winner, highest_bid)
        winner.refresh_from_db()
        listing.change_the_owner()

        self.assertTrue(Log.manager.filter(entry=LOG_ITEM_SOLD % (listing.title, 'Lion')).exists())
        self.assertTrue(Log.manager.filter(entry=LOG_MONEY_ADDED % highest_bid,
                                           profile__username='LuckyBeast').exists())
        self.assertTrue(Log.manager.filter(entry=LOG_YOU_LOSE % (listing.title, lowest_bid),
                                           profile__username='Moose').exists())
        self.assertTrue(Log.manager.filter(entry=LOG_YOU_WON % (listing.title, highest_bid),
                                           profile__username='Lion').exists())

    def _logs_withdrawn(self, listing, profile):
        listing.publish_the_lot()
        bid_value = 30
        listing.make_a_bid(profile, bid_value)
        listing.withdraw()
        self.assertTrue(Log.manager.filter(entry=LOG_WITHDRAWN % listing.title).exists())
        self.assertTrue(Log.manager.filter(entry=LOG_OWNER_REMOVED % (listing.title, bid_value)).exists())
