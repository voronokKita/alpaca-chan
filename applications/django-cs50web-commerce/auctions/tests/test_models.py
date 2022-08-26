from pathlib import Path

from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from django.contrib.auth.models import User
from auctions.models import (
    Profile, ListingCategory, Comment,
    Listing, Watchlist, Bid, Log,
    user_media_path
)
from .tests import (
    DB, DATABASES,
    TEST_IMAGE, IMGNAME,
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
        else: raise Exception('found auctions_profile TABLE and a profile ON DEFAULTS db')

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

        # add money
        profile.add_money(10)
        profile.refresh_from_db()
        self.assertTrue(profile.money == 10)
        profile.add_money(10)
        profile.refresh_from_db()
        self.assertTrue(profile.money == 20)

        # display money
        listing = get_listing()
        listing.publish_the_lot()
        listing.make_a_bid(profile, 10)
        profile.refresh_from_db()
        self.assertEqual(profile.display_money(), (10.0, 10.0))

        # get money
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

        profile_one.add_money(100)
        profile_one.refresh_from_db()
        listing_one.make_a_bid(profile_two, 10)
        listing_two.make_a_bid(profile_one, 20)
        self.assertTrue(Bid.manager.count() == 2)
        self.assertTrue(Watchlist.manager.count() == 4)

        comment_one = get_comment(listing_one, profile_two)
        comment_two = get_comment(listing_two, profile_one)

        user.delete()
        self.assertFalse(Profile.manager.filter(username='Pallas').exists())
        self.assertTrue(Profile.manager.filter(username='Manul').exists())
        self.assertTrue(ListingCategory.manager.contains(category))
        self.assertFalse(Listing.manager.contains(listing_one))
        self.assertTrue(Listing.manager.contains(listing_two))
        self.assertTrue(Bid.manager.count() == 0)
        self.assertTrue(Watchlist.manager.count() == 1)
        self.assertFalse(Comment.manager.contains(comment_one))
        self.assertTrue(Comment.manager.contains(comment_two))
        comment_two.refresh_from_db()
        self.assertIsNone(comment_two.author)


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
    databases = DATABASES

    @classmethod
    def setUpClass(cls):
        super().setUpClass()
        cls.time_now = timezone.localtime()
        cls.category = get_category()
        cls.profile = get_profile('Serval')
        cls.listing = get_listing(category=cls.category, title='Japari bun',
                                  profile=cls.profile, image=TEST_IMAGE)

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

        # delete
        listing.delete()
        self.assertFalse(self.image_path.exists(), 'image deleted with listing')


    def test_listing_backref(self):
        listing = get_listing()
        comment = get_comment(listing)
        self.assertTrue(listing.comment_set.contains(comment))

    def test_listing_method_publish_the_lot(self):
        listing = get_listing()
        time_now = timezone.localtime()

        # ok
        self.assertTrue(listing.publish_the_lot(), 'ok')
        self.assertTrue(listing.is_active, 'ok')
        self.assertTrue(listing.date_published >= time_now <= timezone.localtime(), 'ok')

        # already published
        self.assertFalse(listing.publish_the_lot(),'already published')

        # too low starting price
        listing2 = get_listing(username='Okapi')
        listing2.starting_price = 0
        listing2.save()
        self.assertFalse(listing2.publish_the_lot(), 'too low starting price')

    def test_listing_method_withdraw(self):
        listing = get_listing()
        listing.publish_the_lot()
        potential_buyer = get_profile()
        listing.make_a_bid(potential_buyer, 2)

        # ok
        self.assertTrue(potential_buyer.items_watched.contains(listing), 'ok')
        self.assertTrue(listing.withdraw(), 'ok')
        self.assertFalse(listing.is_active, 'ok')
        self.assertIsNone(listing.date_published, 'ok')
        self.assertIsNone(listing.highest_bid, 'ok')
        self.assertTrue(listing.potential_buyers.count() == 0, 'ok')
        self.assertFalse(potential_buyer.items_watched.contains(listing), 'ok')
        self.assertTrue(listing.in_watchlist.count() == 1, 'ok')

        # not published
        self.assertFalse(listing.withdraw(), 'not published')

    def test_listing_method_unwatch(self):
        profile = get_profile()
        listing = get_listing(profile=profile)
        listing.publish_the_lot()

        # owner
        self.assertFalse(listing.unwatch(profile), 'owner can’t unwatch')

        # potential buyer
        profile2 = get_profile('Tsuchinoko')
        listing.make_a_bid(profile2, 2)
        self.assertFalse(listing.unwatch(profile2), 'potential buyer can’t unwatch')

        # ok
        profile3 = get_profile('Tasmanian-Devil')
        listing.in_watchlist.add(profile3)
        self.assertTrue(listing.unwatch(profile3), 'ok')
        self.assertFalse(listing.in_watchlist.contains(profile3), 'ok')

    def test_listing_method_no_bid_option(self):
        from auctions.models import (
            NO_BID_NO_MONEY_SP, NO_BID_THE_OWNER,
            NO_BID_NO_MONEY, NO_BID_ON_TOP, NEW_BID_PERCENT
        )
        profile1 = get_profile()
        listing = get_listing(profile=profile1)
        listing.publish_the_lot()

        # owner
        self.assertEqual(listing.no_bid_option(profile1), NO_BID_THE_OWNER, 'owner can’t bid')

        # starting price
        profile2 = get_profile('Shirosai', money=0.99)
        self.assertEqual(listing.no_bid_option(profile2), NO_BID_NO_MONEY_SP, 'starting price')

        # already on top
        profile2.add_money(10)
        profile2.refresh_from_db()
        self.assertTrue(listing.make_a_bid(profile2, 10), 'ok first bid')
        self.assertEqual(listing.no_bid_option(profile2), NO_BID_ON_TOP, 'already on top')

        # low on money
        profile3 = get_profile('Sunaneko', money=10)
        self.assertEqual(listing.no_bid_option(profile3), NO_BID_NO_MONEY, 'low on money')

        # ok
        profile3.add_money(10 * NEW_BID_PERCENT - 10)
        profile3.refresh_from_db()
        self.assertIsNone(listing.no_bid_option(profile3), 'ok')

    def test_listing_method_make_a_bid(self):
        from auctions.models import NEW_BID_PERCENT
        profile1 = get_profile()
        listing = get_listing(profile=profile1)
        listing.publish_the_lot()

        # owner
        self.assertFalse(listing.make_a_bid(profile1, 99), 'owner can’t bid')

        # lower than listing's starting price
        profile2 = get_profile('Otter')
        self.assertFalse(listing.make_a_bid(profile2, 0.99), 'starting price')

        # ok
        self.assertTrue(listing.make_a_bid(profile2, 1), 'ok')
        self.assertTrue(listing.in_watchlist.contains(profile2), 'ok')
        self.assertTrue(listing.potential_buyers.contains(profile2), 'ok')

        # lower than listing's highest bid
        profile3 = get_profile('Chameleon')
        self.assertFalse(listing.make_a_bid(profile3, 1 * NEW_BID_PERCENT - 0.01), 'not enough')

        # ok
        self.assertTrue(listing.make_a_bid(profile3, 1 * NEW_BID_PERCENT), 'ok')

    def test_listing_method_change_the_owner(self):
        from auctions.models import DEFAULT_STARTING_PRICE
        seller = get_profile()
        listing = get_listing(profile=seller)
        listing.starting_price = 1.5
        listing.save()

        # not published
        self.assertFalse(listing.change_the_owner(), 'not published')

        # without potential buyers
        listing.publish_the_lot()
        self.assertFalse(listing.change_the_owner(), 'not wanted')

        # ok
        bid_value = 2
        buyer = get_profile('Rikaon')
        listing.make_a_bid(buyer, bid_value)
        self.assertTrue(listing.highest_bid == bid_value)

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
        from auctions.models import NEW_BID_PERCENT
        profile1 = get_profile('Dog')
        profile2 = get_profile('Bear')
        listing = get_listing()
        listing.publish_the_lot()
        self.assertEqual(listing.get_highest_price(), 1)
        self.assertEqual(listing.get_highest_price(with_starting_price=False), 0)
        self.assertIsNone(listing.get_highest_bid_entry())

        listing.make_a_bid(profile1, 10)
        listing.make_a_bid(profile2, 20)
        self.assertEqual(listing.get_highest_price(), 20)
        self.assertEqual(listing.get_highest_price(percent=True), 20 * NEW_BID_PERCENT)

        entry = listing.get_highest_bid_entry()
        self.assertTrue(entry.auctioneer.username == 'Bear')


class WatchlistTests(TestCase):
    databases = DATABASES

    def test_watchlist_normal_case(self):
        profile1 = get_profile('Toki')
        profile2 = get_profile('Shoujoutoki')
        listing1 = get_listing(profile=profile2, title='friends')
        listing2 = get_listing(profile=profile2, title='buns')
        profile1.items_watched.add(listing1)
        profile1.items_watched.add(listing2)

        self.assertEqual(Watchlist.manager.count(), 4)
        self.assertTrue(profile1.items_watched.filter(slug='friends').exists())
        self.assertTrue(listing1.in_watchlist.contains(profile1))
        self.assertTrue(listing1.in_watchlist.contains(profile2))
        self.assertTrue(
            Profile.manager.filter(username='Toki',
                                   items_watched__slug='buns').exists()
        )


class BidTests(TestCase):
    databases = DATABASES

    def test_bids_normal_case(self):
        time_now = timezone.localtime()
        listing1 = get_listing(title='friends')
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
        self.assertEqual(bid.bid_value, 3)
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
    def setUpClass(cls):
        super().setUpClass()
        cls.time_now = timezone.localtime()
        cls.profile = get_profile('Rikaon')
        cls.listing = get_listing(profile=cls.profile)

    def test_comment_normal_case(self):
        comment = get_comment(self.listing)
        self.assertTrue(comment.pub_date >= self.time_now <= timezone.localtime())

    def test_comment_backref(self):
        text = 'japari bun is the best bun'
        get_comment(self.listing, self.profile, text)
        self.assertTrue(self.listing.comment_set.filter(text=text).exists())
        self.assertTrue(self.profile.comment_set.filter(text=text).exists())


class LogTests(TestCase):
    databases = DATABASES

    def test_auctions_logs(self):
        from auctions.models import (
            LOG_REGISTRATION, LOG_NEW_LISTING, LOG_YOU_WON,
            LOG_LOT_PUBLISHED, LOG_NEW_BID, LOG_WITHDRAWN,
            LOG_YOU_LOSE, LOG_OWNER_REMOVED, LOG_ITEM_SOLD,
            LOG_MONEY_ADDED
        )
        user = User.objects.create(username='LuckyBeast')

        # registration
        self.assertTrue(Log.manager.filter(entry=LOG_REGISTRATION).exists())
        profile = Profile.manager.get(username='LuckyBeast')

        # money
        profile.add_money(10)
        self.assertTrue(Log.manager.filter(entry=LOG_MONEY_ADDED % 10).exists())

        # new listing
        title = 'Japari Bun'
        listing = get_listing(profile=profile, title=title)
        self.assertTrue(Log.manager.filter(entry=LOG_NEW_LISTING % title).exists())

        # auction created
        listing.publish_the_lot()
        self.assertTrue(Log.manager.filter(entry=LOG_LOT_PUBLISHED % title).exists())

        # made a bid
        profile_two = get_profile(username='Moose')
        listing.make_a_bid(profile_two, 10)
        profile_two.refresh_from_db()
        self.assertTrue(Log.manager.filter(entry=LOG_NEW_BID % (title, 10)).exists())

        # auction closed - one win, one lose
        profile_three = get_profile(username='Lion')
        listing.make_a_bid(profile_three, 20)
        profile_three.refresh_from_db()
        listing.change_the_owner()
        self.assertTrue(Log.manager.filter(entry=LOG_ITEM_SOLD % (title, 'Lion')).exists())
        self.assertTrue(Log.manager.filter(entry=LOG_MONEY_ADDED % 20.0, profile=profile).exists())
        self.assertTrue(Log.manager.filter(entry=LOG_YOU_LOSE % (title, 10.0), profile=profile_two).exists())
        self.assertTrue(Log.manager.filter(entry=LOG_YOU_WON % (title, 20.0), profile=profile_three).exists())

        # withdrawn
        listing.publish_the_lot()
        listing.make_a_bid(profile_two, 30)
        profile_two.refresh_from_db()
        listing.withdraw()
        self.assertTrue(Log.manager.filter(entry=LOG_WITHDRAWN % title).exists())
        self.assertTrue(Log.manager.filter(entry=LOG_OWNER_REMOVED % (title, 30.0)).exists())

        # count
        self.assertTrue(Log.manager.count() == 16, 'total log entries')
