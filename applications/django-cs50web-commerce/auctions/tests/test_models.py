from django.conf import settings
from django.test import TestCase
from django.utils import timezone

from django.contrib.auth.models import User
from auctions.models import Profile, ListingCategory, Comment, Listing, Watchlist, Bid


SECOND_DB = settings.PROJECT_MAIN_APPS['auctions']['db']['name']


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

    def test_unique_slug_works(self):
        expected = 3
        for i in range(expected):
            get_listing(title='Test slug')
        self.assertEqual(Listing.manager.count(), expected)

        from auctions.models import SLUG_MAX_LEN
        title = 's' * SLUG_MAX_LEN
        get_listing(title=title + 'appendix')
        self.assertTrue(Listing.manager.get(slug=title))


class UserProfileTests(TestCase):
    databases = ['default', SECOND_DB]

    def test_new_user_gets_new_profile_in_correct_db(self):
        User.objects.create(username='user1')
        self.assertFalse(
            User.objects.db_manager(SECOND_DB).filter(username='user1').exists()
        )
        self.assertTrue(
            User.objects.db_manager('default').filter(username='user1').exists()
        )

        self.assertTrue(
            Profile.manager.db_manager(SECOND_DB).filter(username='user1').exists()
        )
        try: Profile.manager.db_manager('default').get(username='user1')
        except Exception: pass
        else: raise Exception('found auctions_profile table and a profile on defaults db')

    def test_profile_backref(self):
        profile = get_profile()
        listing = get_listing(profile=profile)
        comment = Comment.manager.create(listing=listing, author=profile,
                                         text='Japari bun is the best bun!')
        profile.refresh_from_db()
        self.assertTrue(profile.lots_owned.contains(listing))
        self.assertTrue(profile.comment_set.contains(comment))


class ListingCategoryTests(TestCase):
    databases = [SECOND_DB]

    def test_category_normal_case(self):
        ListingCategory.manager.create(label='items')
        self.assertTrue(ListingCategory.manager.filter(label='items').exists())

    def test_category_backref(self):
        category = get_category()
        listing = get_listing(category)
        category.refresh_from_db()
        self.assertTrue(category.listing_set.contains(listing))


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
        self.assertTrue(listing.date_created >= self.time_now <= timezone.localtime())
        self.assertIsNone(listing.date_published)
        self.assertFalse(listing.is_active)
        self.assertEqual(listing.potential_buyers.count(), 0)
        self.assertTrue(listing.in_watchlist.contains(self.profile))

    def test_listing_backref(self):
        listing = self.listing
        comment = Comment.manager.create(text='Japari bun is the best bun!', listing=listing)
        listing.refresh_from_db()
        self.assertTrue(listing.comment_set.contains(comment))

    def test_listing_method_publish_the_lot(self):
        listing = get_listing()
        time_now = timezone.localtime()
        # ok
        self.assertTrue(listing.publish_the_lot())
        listing.refresh_from_db()
        self.assertTrue(listing.is_active)
        self.assertTrue(listing.date_published >= time_now <= timezone.localtime())
        # already published
        self.assertFalse(listing.publish_the_lot())
        # too low starting price
        listing2 = get_listing()
        listing2.starting_price = 0
        listing2.save()
        self.assertFalse(listing2.publish_the_lot())

    def test_listing_method_withdraw(self):
        listing = get_listing()
        listing.is_active = True
        listing.save()
        listing.potential_buyers.add(get_profile(), through_defaults={'bid_value': 2})
        # ok
        self.assertTrue(listing.withdraw())
        listing.refresh_from_db()
        self.assertFalse(listing.is_active)
        self.assertIsNone(listing.date_published)
        self.assertEqual(listing.potential_buyers.count(), 0)
        # not published
        self.assertFalse(listing.withdraw())

    def test_listing_method_unwatch(self):
        profile = get_profile()
        listing = get_listing(profile=profile)
        listing.is_active = True
        listing.save()
        # owner
        self.assertFalse(listing.unwatch(profile))
        # potential buyer
        profile2 = get_profile()
        listing.potential_buyers.add(profile2, through_defaults={'bid_value': 2})
        self.assertFalse(listing.unwatch(profile2))
        # ok
        profile3 = get_profile()
        listing.in_watchlist.add(profile3)
        self.assertTrue(listing.unwatch(profile3))
        self.assertFalse(listing.in_watchlist.contains(profile3))

    def test_listing_method_bid_possibility(self):
        profile = get_profile()
        listing = get_listing(profile=profile)
        listing.is_active = True
        listing.save()
        # owner
        self.assertFalse(listing.bid_possibility(profile))
        # already on top
        profile2 = get_profile()
        listing.potential_buyers.add(profile2, through_defaults={'bid_value': 2})
        self.assertFalse(listing.bid_possibility(profile2))
        # ok
        profile3 = get_profile()
        self.assertTrue(listing.bid_possibility(profile3))

    def test_listing_method_make_a_bid(self):
        profile = get_profile()
        listing = get_listing(profile=profile)
        listing.is_active = True
        listing.save()
        # owner
        self.assertFalse(listing.make_a_bid(profile, 99))
        # lower or equal than listing's starting price
        listing.save()
        profile2 = get_profile()
        self.assertFalse(listing.make_a_bid(profile2, 0.99))
        self.assertFalse(listing.make_a_bid(profile2, 1))
        # ok
        self.assertTrue(listing.make_a_bid(profile2, 1.1))
        self.assertTrue(listing.in_watchlist.contains(profile2))
        # lower or equal than listing's highest bid
        profile3 = get_profile()
        self.assertFalse(listing.make_a_bid(profile3, 1))
        self.assertFalse(listing.make_a_bid(profile3, 1.1))

    def test_listing_method_change_the_owner(self):
        seller = get_profile()
        listing = get_listing(profile=seller)
        # not published
        self.assertFalse(listing.change_the_owner())
        # without potential buyers
        listing.is_active = True
        listing.save()
        self.assertFalse(listing.change_the_owner())
        # ok
        bid_value = 2
        buyer = get_profile()
        listing.potential_buyers.add(buyer, through_defaults={'bid_value': bid_value})
        self.assertTrue(listing.change_the_owner())
        self.assertFalse(listing.is_active)
        self.assertIsNone(listing.date_published)
        self.assertTrue(listing.starting_price == bid_value)
        self.assertTrue(listing.potential_buyers.count() == 0)
        self.assertFalse(seller.lots_owned.contains(listing))
        self.assertTrue(buyer.lots_owned.contains(listing))
        self.assertTrue(buyer.items_watched.contains(listing))


class WatchlistTests(TestCase):
    databases = [SECOND_DB]

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
            Profile.manager.filter(username='Toki', items_watched__slug='buns').exists()
        )


class BidTests(TestCase):
    databases = [SECOND_DB]

    def test_bets_normal_case(self):
        time_now = timezone.localtime()
        listing1 = get_listing(title='friends')
        listing2 = get_listing(title='buns')

        profile = get_profile('Shoujoutoki')
        profile.placed_bets.add(listing1, through_defaults={'bid_value': 2})
        profile.placed_bets.add(listing2, through_defaults={'bid_value': 3})

        self.assertEqual(Bid.manager.count(), 2)
        self.assertTrue(profile.placed_bets.filter(slug='friends').exists())
        self.assertTrue(listing1.potential_buyers.filter(username='Shoujoutoki').exists())
        self.assertTrue(
            Profile.manager.filter(username='Shoujoutoki',
                                   placed_bets__slug='buns').exists()
        )
        bid = profile.bid_set.get(lot=listing2)
        self.assertEqual(bid.bid_value, 3)
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
        self.assertTrue(comment.pub_date >= self.time_now <= timezone.localtime())

    def test_comment_backref(self):
        text = 'japari bun is the best bun'
        Comment.manager.create(text=text, listing=self.listing, author=self.profile)
        self.assertTrue(self.listing.comment_set.filter(text=text).exists())
        self.assertTrue(self.profile.comment_set.filter(text=text).exists())
