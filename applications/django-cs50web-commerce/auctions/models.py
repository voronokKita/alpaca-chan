import logging
from pathlib import Path

from django.contrib import admin
from django.utils import timezone
from django.urls import reverse, reverse_lazy
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.db import models, transaction
from django.db.models import (
    Model, CharField, TextField,
    SlugField, FloatField, ImageField,
    DateTimeField, BooleanField,
    ForeignKey, ManyToManyField,
    IntegerField, Sum, F
)
from core.utils import unique_slugify

logger = logging.getLogger(__name__)


class LowOnMoney(Exception): pass

NEW_BID_PERCENT = 1+5/100

SLUG_MAX_LEN = 16
USERNAME_MAX_LEN = 150
LOT_TITLE_MAX_LEN = 300
DEFAULT_STARTING_PRICE = 1

NO_BID_NOT_PUBLISHED = 'Listing is not published'
NO_BID_THE_OWNER = 'You are the owner'
NO_BID_NO_MONEY = 'Insufficient funds'
NO_BID_NO_MONEY_SP = 'Your money is less than the starting price'
NO_BID_ON_TOP = 'Your bid is on the top'

LOG_REGISTRATION = 'Date of your registration.'
LOG_MONEY_ADDED = 'Wallet topped up with %0.2f coins.'
LOG_NEW_LISTING = 'The item [%s] has been added to your listings.'
LOG_YOU_WON = 'The listing [%s] has been taken into possession. Price — %0.2f.'
LOG_LOT_PUBLISHED = 'You have created an auction — [%s].'
LOG_NEW_BID = 'Made a bid on [%s]. Value — %0.2f.'
LOG_WITHDRAWN = 'You have withdrawn [%s] from the auction.'
LOG_YOU_LOSE = 'You lost the auction — [%s]. Refund %0.2f coins.'
LOG_OWNER_REMOVED = 'The owner removed the lot [%s] from the auction. Refund %0.2f coins.'
LOG_ITEM_SOLD = 'You closed the auction — [%s]. The winner is %s.'


def log_entry(profile, msg, listing='None', user='None', coins=0):
    case = {
        'money_added': LOG_MONEY_ADDED % coins,
        'new_item': LOG_NEW_LISTING % listing,
        'published': LOG_LOT_PUBLISHED % listing,
        'withdrawn': LOG_WITHDRAWN % listing,
        'removed': LOG_OWNER_REMOVED % (listing, coins),
        'sold': LOG_ITEM_SOLD % (listing, user),
        'you_won': LOG_YOU_WON % (listing, coins),
        'you_lose': LOG_YOU_LOSE % (listing, coins),
        'bid': LOG_NEW_BID % (listing, coins),
    }[msg]
    profile.logs.create(entry=case)


def user_media_path(listing=None, filename=None, slug=None) -> Path:
    """ Files will be uploaded to
        MEDIA_ROOT/auctions/listings/2022.08.08__<listing.slug>/<filename> """
    date = timezone.localdate().strftime('%Y.%m.%d')
    slug = listing.slug if listing else slug
    return Path('auctions', 'listings', f'{date}__{slug}', f'{filename}')


class Profile(Model):
    manager = models.Manager()

    user_model_pk = IntegerField('user.pk', unique=True, blank=True, null=True)
    username = CharField(max_length=USERNAME_MAX_LEN, unique=True, db_index=True)
    money = FloatField('money on account', default=0.0)

    class Meta:
        """
        profile >-- bid --< placed_bids (listing)
        profile >-- watchlist --< items_watched (listing)
        profile --< lots_owned (listing)
        profile --< comment_set
        profile --< logs
        """
        db_table = 'auctions_profile'
        verbose_name = 'auctioneer'
        verbose_name_plural = 'auctioneers'

    def get_absolute_url(self):
        return reverse('auctions:profile', args=[self.pk])

    def save(self, date_joined=None, log=False, update_fields=None, *args, **kwargs):
        if not self.pk:
            log = True
        with transaction.atomic('auctions_db', savepoint=False):
            super().save(*args, update_fields=update_fields, **kwargs)
            if log is True:
                date = date_joined if date_joined else timezone.localtime()
                self.logs.create(entry=LOG_REGISTRATION, date=date)

    def add_money(self, amount:float, silent=False):
        with transaction.atomic('auctions_db', savepoint=False):
            self.money = F('money') + amount
            self.save(update_fields=['money'])
            if silent is False:
                log_entry(self, 'money_added', coins=amount)

    def get_money(self, value:float) -> (float, LowOnMoney):
        if self.money >= value:
            self.money = F('money') - value
            self.save(update_fields=['money'])
            return value
        else:
            raise LowOnMoney

    def display_money(self) -> (float, float):
        """ Returns current money + in all the bids. """
        bids_total = 0
        if self.bid_set.count() > 0:
            result = self.bid_set.aggregate(Sum('bid_value'))
            bids_total = result['bid_value__sum']
        return self.money, bids_total

    @admin.display(description='items owned')
    def items_owned_count(self):
        return self.lots_owned.count()

    @admin.display(description='comments')
    def comments_written_count(self):
        return self.comment_set.count()

    @admin.display(description='placed bids')
    def placed_bids_count(self):
        return self.bid_set.count()

    def __str__(self): return self.username


class Log(Model):
    manager = models.Manager()

    entry = CharField(max_length=100)
    date = DateTimeField(auto_now=True)
    profile = ForeignKey(Profile, on_delete=models.CASCADE, related_name='logs')

    class Meta:
        db_table = 'auctions_logs'
        verbose_name = 'auctioneer log'
        verbose_name_plural = 'auctioneer logs'
        ordering = ['-date']

    def __str__(self): return self.entry


class ListingCategory(Model):
    manager = models.Manager()

    label = CharField('category label', db_index=True, max_length=100)

    class Meta:
        """ category --< listing_set """
        db_table = 'auctions_category'
        verbose_name = 'category'
        verbose_name_plural = 'categories'
        ordering = ['label']

    @admin.display(description='items in category')
    def items_in_category(self):
        return self.listing_set.count()

    def __str__(self): return self.label


class Bid(Model):
    manager = models.Manager()

    bid_value = FloatField('value', db_index=True)
    bid_date = DateTimeField('date', default=timezone.localtime)

    auctioneer = ForeignKey(Profile, on_delete=models.CASCADE)
    lot = ForeignKey('Listing', on_delete=models.CASCADE)

    def delete(self, refund=False, item_sold=False, **kwargs):
        if refund:
            self._refund(item_sold)
        return super().delete(**kwargs)

    def _refund(self, item_sold):
        """ Returns the money back to the profile if
            the auction was lost or
            the owner withdrew the lot from the auction. """
        with transaction.atomic('auctions_db', savepoint=False):
            if item_sold is True:
                log_entry(self.auctioneer, 'you_lose',
                          self.lot.title, coins=self.bid_value)
            else:
                log_entry(self.auctioneer, 'removed',
                          self.lot.title, coins=self.bid_value)

            self.auctioneer.add_money(self.bid_value, silent=True)

    class Meta:
        """ profiles >-- bid --< listings """
        db_table = 'auctions_bids'
        verbose_name = 'placed bid'
        verbose_name_plural = 'placed bids'
        ordering = ['-bid_date']
        get_latest_by = ['bid_value']

    def __str__(self):
        return f'{self.auctioneer} >-- bid --< {self.lot}'


class Watchlist(Model):
    manager = models.Manager()

    profile = ForeignKey(Profile, on_delete=models.CASCADE)
    listing = ForeignKey('Listing', on_delete=models.CASCADE)

    class Meta:
        """ profiles >-- watchlist --< listings """
        db_table = 'auctions_watchlists'
        verbose_name = 'watchlist'
        verbose_name_plural = 'watchlists'
        ordering = ['listing']

    def __str__(self):
        return f'{self.profile} >-- watchlist --< {self.listing}'


class Listing(Model):
    manager = models.Manager()

    slug = SlugField('slug', unique=True, blank=True, max_length=SLUG_MAX_LEN)
    title = CharField('listing title', max_length=LOT_TITLE_MAX_LEN)
    description = TextField('listing description')
    image = ImageField('visual presentation', upload_to=user_media_path, max_length=300)
    starting_price = FloatField(default=DEFAULT_STARTING_PRICE, blank=True)

    date_created = DateTimeField('created', default=timezone.localtime)
    date_published = DateTimeField('published', null=True, blank=True, default=None)
    is_active = BooleanField('is listing published?', default=False)
    highest_bid = FloatField(null=True, blank=True, default=None)

    category = ForeignKey(ListingCategory, on_delete=models.PROTECT)
    owner = ForeignKey(Profile, on_delete=models.CASCADE, related_name='lots_owned')
    potential_buyers = ManyToManyField(Profile, through=Bid, related_name='placed_bids')
    in_watchlist = ManyToManyField(Profile, through=Watchlist, related_name='items_watched')

    class Meta:
        """ listing --< comment_set """
        db_table = 'auctions_listing'
        verbose_name = 'listing'
        verbose_name_plural = 'listings'
        ordering = ['-date_published', '-date_created', 'slug']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['date_published', 'date_created']),
        ]

    def get_absolute_url(self):
        if self.is_active:
            return reverse_lazy('auctions:auction_lot', args=[self.slug])
        else:
            return reverse_lazy('auctions:listing', args=[self.slug])

    def save(self, *args, **kwargs):
        """ Auto get a unique slug and
            add a new listing to owner's watchlist. """
        with transaction.atomic('auctions_db', savepoint=False):
            if not self.pk:
                if self.slug:
                    s = str(self.slug)
                else:
                    s = slugify(self.title)
                unique_slugify(self, s)

                log_entry(self.owner, 'new_item', self.title)

            super().save(*args, **kwargs)
            if self.in_watchlist.contains(self.owner) is False:
                self.in_watchlist.add(self.owner)

    def delete(self, **kwargs):
        with transaction.atomic('auctions_db', savepoint=False):
            self.image.delete()
            return super().delete(**kwargs)

    def can_be_published(self) -> bool:
        if self.starting_price < 1 or self.is_active is True:
            return False
        else:
            return True

    def publish_the_lot(self) -> bool:
        """ Make the listing available on the auction. """
        if self.can_be_published() is False:
            return False
        else:
            with transaction.atomic('auctions_db', savepoint=False):
                self.date_published = timezone.localtime()
                self.is_active = True
                self.save()
                log_entry(self.owner, 'published', self.title)
            return True

    def withdraw(self, item_sold=False) -> bool:
        """ Get the listing back from the auction.
            Refund money back to the auctioneers and
            clear the item from all the watchlists, except for the owner. """
        if self.is_active is False:
            return False

        with transaction.atomic('auctions_db', savepoint=False):
            self.date_published = None
            self.is_active = False
            self.highest_bid = None

            if item_sold is False:
                log_entry(self.owner, 'withdrawn', self.title)

            if self.potential_buyers.count() > 0:
                for bid in self.bid_set.iterator():
                    bid.delete(refund=True, item_sold=item_sold)

            if self.in_watchlist.count() > 1:
                self.watchlist_set.exclude(profile=self.owner).delete()

            self.save()
            return True

    def can_unwatch(self, profile:Profile = None, username:str = None) -> bool:
        """ Can remove from watchlist if
            the user is not the owner or potential buyer of the lot. """
        if profile:
            username = profile.username
        if username == self.owner.username or \
                self.potential_buyers.filter(username=username).exists():
            return False
        else:
            return True

    def unwatch(self, profile:Profile = None, username:str = None) -> bool:
        """ Remove from watchlist if
            the user is not the owner or potential buyer of the lot. """
        if profile:
            username = profile.username
        if self.can_unwatch(username=username) is False:
            return False
        else:
            self.watchlist_set.filter(profile__username=username).delete()
            return True

    def no_bid_option(self, auctioneer:Profile = None,
                      username:str = None) -> str or None:
        """ Initial check of the possibility to place a bid.
            Returns None if ok or the reason of the limitation. """
        if username:
            auctioneer = Profile.manager.filter(username=username).first()

        if not self.is_active:
            return NO_BID_NOT_PUBLISHED
        elif self.owner == auctioneer:
            return NO_BID_THE_OWNER

        elif self.potential_buyers.count() > 0:
            highest_bid = self.get_highest_bid_entry()
            if highest_bid.auctioneer == auctioneer:
                return NO_BID_ON_TOP
            elif auctioneer.money < highest_bid.bid_value * NEW_BID_PERCENT:
                return NO_BID_NO_MONEY

        elif self.potential_buyers.count() == 0 and \
                auctioneer.money < self.starting_price:
            return NO_BID_NO_MONEY_SP

    def make_a_bid(self, auctioneer:Profile, bid_value:float) -> bool:
        """ Also add the lot to user's watchlist. """
        if not isinstance(bid_value, (int, float)):
            return False
        elif self.no_bid_option(auctioneer):
            return False
        elif auctioneer.money < bid_value:
            return False
        elif self.potential_buyers.count() == 0 and \
                bid_value < self.starting_price:
            return False
        elif self.highest_bid and self.highest_bid * NEW_BID_PERCENT > bid_value:
            return False

        with transaction.atomic('auctions_db', savepoint=False):
            if not self.in_watchlist.contains(auctioneer):
                self.in_watchlist.add(auctioneer)

            money = auctioneer.get_money(bid_value)
            auctioneer.placed_bids.add(self, through_defaults={'bid_value': money})
            self.highest_bid = money
            self.save()

            log_entry(auctioneer, 'bid', self.title, coins=money)
            return True

    def change_the_owner(self) -> bool:
        """ Transfer the money to the owner form the auctioneer that offers the highest bid,
            transfer the lot to its new owner,
            withdraw the lot from the auction. """
        if self.is_active is False or self.potential_buyers.count() == 0:
            return False

        highest_bid = self.get_highest_bid_entry()
        new_owner = highest_bid.auctioneer
        money = highest_bid.bid_value

        with transaction.atomic('auctions_db', savepoint=False):
            log_entry(self.owner, 'sold', self.title, new_owner)
            self.owner.add_money(money)
            highest_bid.delete()

            self.save_new_owner(new_owner)
            self.starting_price = DEFAULT_STARTING_PRICE
            self.withdraw(item_sold=True)

            log_entry(self.owner, 'you_won', self.title, coins=money)
            return True

    def save_new_owner(self, new_owner):
        self.owner = new_owner
        super().save(update_fields=['owner'])

    def get_highest_price(self, with_starting_price=True, percent=False) -> float:
        if self.highest_bid and percent:
            return self.highest_bid * NEW_BID_PERCENT
        elif self.highest_bid:
            return self.highest_bid
        elif self.highest_bid is None and with_starting_price:
            return self.starting_price
        else:
            return 0.0

    def get_highest_bid_entry(self) -> Bid or None:
        try:
            highest_bid = self.bid_set.latest()
        except ObjectDoesNotExist:
            return None
        else:
            return highest_bid

    def __str__(self):
        return self.slug if self.slug else self.title


class Comment(Model):
    manager = models.Manager()

    text = TextField('comment text')
    pub_date = DateTimeField('comment published', auto_now=True, db_index=True)

    author = ForeignKey(Profile, null=True, on_delete=models.SET_NULL)
    listing = ForeignKey(Listing, verbose_name='commentary on', on_delete=models.CASCADE)

    class Meta:
        db_table = 'auctions_comment'
        verbose_name = 'comment'
        verbose_name_plural = 'comments'
        ordering = ['-pub_date']

    def __str__(self): return f'comment #{self.pk}'
