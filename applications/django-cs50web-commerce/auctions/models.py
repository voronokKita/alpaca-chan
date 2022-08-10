from django.utils import timezone
from django.urls import reverse
from django.utils.text import slugify
from django.db import models
from django.db.models import (
    Model, CharField, TextField,
    SlugField, FloatField, ImageField,
    DateTimeField, BooleanField,
    ForeignKey, ManyToManyField
)
from core.utils import unique_slugify

# TODO
# admin model
# Query Expressions

class LowOnMoney(Exception): pass

SLUG_MAX_LEN = 16

LOG_REGISTRATION = 'Date of your registration.'
LOG_MONEY_ADDED = 'Wallet topped up with %d coins.'
LOG_NEW_LISTING = 'The item [%s] has been added to your listings.'
LOG_YOU_WON = 'The listing [%s] has been taken into possession. Price — %d.'
LOG_LOT_PUBLISHED = 'You have created an auction — [%s].'
LOG_NEW_BID = 'Made a bet on [%s]. Value — %d.'
LOG_WITHDRAWN = 'You have withdrawn [%s] from the auction.'
LOG_YOU_LOSE = 'You lost the auction — [%s]. Refund %d coins.'
LOG_OWNER_REMOVED = 'The owner removed the lot [%s] from the auction. Refund %d coins.'
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


def user_media_path(listing, filename):
    """ Files will be uploaded to MEDIA_ROOT/auctions/listings/2022.08.08__<listing_slug>/ """
    date = timezone.localdate().strftime('%Y.%m.%d')
    return f'auctions/listings/{date}__{listing.slug}/{filename}'


class Profile(Model):
    manager = models.Manager()

    username = CharField('category label', max_length=30, db_index=True)
    money = FloatField('money on account', default=0.0)

    class Meta:
        """
        profile >-- bid --< placed_bets (listing)
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
        super().save(*args, update_fields=update_fields, **kwargs)
        if log is True:
            date = date_joined if date_joined else timezone.localtime()
            self.logs.create(entry=LOG_REGISTRATION, date=date)

    def delete(self, **kwargs):
        return super().delete(**kwargs)

    def add_money(self, amount, silent=False):
        self.money += amount
        self.save(update_fields=['money'])
        if silent is False:
            log_entry(self, 'money_added', coins=amount)

    def get_money(self, value) -> (int, LowOnMoney):
        if self.money >= value:
            self.money -= value
            self.save(update_fields=['money'])
            return value
        else:
            raise LowOnMoney

    def display_money(self) -> tuple:
        """ Current + in all the bets. """
        bets_total = 0
        if self.bid_set.count() > 0:
            for bid in self.bid_set.all():
                bets_total += bid.bid_value
        return self.money, bets_total

    def __str__(self): return self.username


class Log(Model):
    manager = models.Manager()

    entry = CharField(max_length=100)
    date = DateTimeField(default=timezone.localtime)
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

    def __str__(self): return self.label


class Bid(Model):
    manager = models.Manager()

    bid_value = FloatField('value', db_index=True)
    bid_date = DateTimeField('date', default=timezone.localtime)

    auctioneer = ForeignKey(Profile, on_delete=models.CASCADE)
    lot = ForeignKey('Listing', on_delete=models.CASCADE)

    def delete(self, refund=False, item_sold=False, **kwargs):
        if refund:
            if item_sold is True:
                log_entry(self.auctioneer, 'you_lose',
                          self.lot.title, coins=self.bid_value)
            else:
                log_entry(self.auctioneer, 'removed',
                          self.lot.title, coins=self.bid_value)
            self.auctioneer.add_money(self.bid_value, silent=True)
        return super().delete(**kwargs)

    class Meta:
        """ profiles >-- bid --< listings """
        db_table = 'auctions_bids'
        verbose_name = 'placed bid'
        verbose_name_plural = 'placed bets'
        ordering = ['-bid_date']
        get_latest_by = ['bid_value']

    def __str__(self): return f'{self.auctioneer} >-- bid --< {self.lot}'


class Watchlist(Model):
    manager = models.Manager()

    profile = ForeignKey(Profile, on_delete=models.CASCADE)
    listing = ForeignKey('Listing', on_delete=models.CASCADE)

    class Meta:
        """ profiles >-- watchlist --< listings """
        db_table = 'auctions_watchlists'
        verbose_name = 'watchlist'
        verbose_name_plural = 'watchlists'

    def get_absolute_url(self):
        return reverse('auctions:watchlist', args=[self.profile.pk])

    def __str__(self): return f'{self.profile} >-- watchlist --< {self.listing}'


class Listing(Model):
    manager = models.Manager()

    slug = SlugField('slug', unique=True, blank=True, max_length=SLUG_MAX_LEN)
    title = CharField('listing title', max_length=300)
    description = TextField('listing description')
    image = ImageField('visual presentation', upload_to=user_media_path, max_length=500)
    starting_price = FloatField(default=1)

    date_created = DateTimeField('created', default=timezone.localtime)
    date_published = DateTimeField('published', null=True, default=None)
    is_active = BooleanField('is listing published?', default=False)

    category = ForeignKey(ListingCategory, on_delete=models.PROTECT)
    owner = ForeignKey(Profile, on_delete=models.CASCADE, related_name='lots_owned')
    potential_buyers = ManyToManyField(Profile, through=Bid, related_name='placed_bets')
    in_watchlist = ManyToManyField(Profile, through=Watchlist, related_name='items_watched')

    class Meta:
        """ listing --< comment_set """
        db_table = 'auctions_listing'
        verbose_name = 'listing'
        verbose_name_plural = 'listings'
        ordering = ['-date_published', '-date_created']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['date_published', 'date_created']),
        ]

    def get_absolute_url(self):
        return reverse('auctions:listing', args=[self.slug])

    def save(self, *args, **kwargs):
        """ Auto get a unique slug and
            add a new listing to owner's watchlist. """
        if not self.pk:
            if self.slug: s = str(self.slug)
            else: s = slugify(self.title)
            unique_slugify(self, s)
            log_entry(self.owner, 'new_item', self.title)

        super().save(*args, **kwargs)
        if self.in_watchlist.contains(self.owner) is False:
            self.in_watchlist.add(self.owner)

    def delete(self, **kwargs):
        self.image.delete()
        return super().delete(**kwargs)

    def publish_the_lot(self) -> bool:
        """ Make the listing available on the auction. """
        if self.starting_price < 1 or self.is_active is True:
            return False
        else:
            self.date_published = timezone.localtime()
            self.is_active = True
            self.save()
            log_entry(self.owner, 'published', self.title)
            return True

    def withdraw(self, item_sold=False) -> bool:
        """ Get the listing back from the auction. """
        if self.is_active is False:
            return False
        else:
            self.date_published = None
            self.is_active = False

            if item_sold is False:
                log_entry(self.owner, 'withdrawn', self.title)

            if self.potential_buyers.count() > 0:
                for bid in self.bid_set.all():
                    bid.delete(refund=True, item_sold=item_sold)

            self.save()
            return True

    def unwatch(self, profile) -> bool:
        """ Remove from watchlist if
            the user is not the owner or potential buyer of the lot. """
        if self.is_active is False or \
                profile == self.owner or \
                self.potential_buyers.contains(profile):
            return False
        else:
            self.in_watchlist.remove(profile)
            return True

    def bid_possibility(self, auctioneer, return_highest_bid=False) -> bool:
        if not self.is_active:
            return False
        elif self.owner == auctioneer:
            return False
        elif self.potential_buyers.count() == 0 and \
                auctioneer.money < self.starting_price:
            return False
        elif self.potential_buyers.count() > 0:
            highest_bid = self.bid_set.latest()
            if highest_bid.auctioneer == auctioneer:
                return False
            elif auctioneer.money < highest_bid.bid_value:
                return False
            if return_highest_bid:
                return_highest_bid = highest_bid

        return True if not return_highest_bid else return_highest_bid

    def make_a_bid(self, auctioneer, bid_value) -> bool:
        """ Also add the lot to user's watchlist. """
        highest_bid = self.bid_possibility(auctioneer, return_highest_bid=True)
        if highest_bid is False:
            return False
        elif self.potential_buyers.count() == 0:
            if bid_value <= self.starting_price:
                return False
        elif highest_bid.bid_value >= bid_value:
            return False
        elif auctioneer.money < bid_value:
            return False

        if not self.in_watchlist.contains(auctioneer):
            self.in_watchlist.add(auctioneer)

        money = auctioneer.get_money(bid_value)
        auctioneer.placed_bets.add(self, through_defaults={'bid_value': money})

        log_entry(auctioneer, 'bid', self.title, coins=money)
        return True

    def change_the_owner(self) -> bool:
        """ Sell the lot to the auctioneer that offers the highest bid and
            withdraw the lot from the auction. """
        if self.is_active is False or self.potential_buyers.count() == 0:
            return False
        else:
            highest_bid = self.bid_set.latest()
            new_owner = highest_bid.auctioneer
            money = highest_bid.bid_value
            log_entry(self.owner, 'sold', self.title, new_owner)
            self.owner.add_money(money)
            highest_bid.delete()

            self._save_new_owner(new_owner)
            self.starting_price = money
            self.withdraw(item_sold=True)

            log_entry(self.owner, 'you_won', self.title, coins=money)
            return True

    def _save_new_owner(self, new_owner):
        self.owner = new_owner
        super().save(update_fields=['owner'])

    def __str__(self): return self.slug if self.slug else self.title


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
