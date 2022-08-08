from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.db import models
from django.db.models import (
    Model, CharField, TextField,
    SlugField, FloatField, ImageField,
    DateTimeField, BooleanField,
    ForeignKey, ManyToManyField, OneToOneField
)
from core.utils import unique_slugify

# TODO
# get_absolute_url
# user history
# admin model
# deletion mechanism with signal

SLUG_MAX_LEN = 16


def user_media_path(listing, filename):
    """ Files will be uploaded to MEDIA_ROOT/auctions/2022.08.08_<listing_slug>/ """
    return f'auctions/%Y.%m.%d_{listing.slug}/{filename}'


class Profile(Model):
    manager = models.Manager()

    username = CharField('category label', db_index=True, max_length=30)
    money = FloatField('money on account', default=0)

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

    def save(self, date_joined=None, log=False, *args, **kwargs):
        if not self.pk:
            log = True
        super().save(*args, **kwargs)
        if log is True:
            date = date_joined if date_joined else timezone.localtime()
            self.logs.create(entry='Date of your registration.', date=date)

    def add_money(self, amount):
        self.money += amount
        self.save()
        self.logs.create(entry=f'Wallet topped up with {amount} coins.')

    def __str__(self): return self.username


class Log(Model):
    manager = models.Manager()

    entry = CharField(max_length=100)
    date = DateTimeField(default=timezone.localtime)
    profile = ForeignKey(Profile, on_delete=models.CASCADE, related_name='logs')

    class Meta:
        """
        0. YYYY.MM.DD Date of your registration.
        1. YYYY.MM.DD Wallet topped up with <money> coins.
        2. YYYY.MM.DD The item <listing> has been added to your listings.
        3. YYYY.MM.DD The <listing> has been taken into possession.
        4. YYYY.MM.DD You have created an auction — <listing>.
        5. YYYY.MM.DD You have withdrawn <listing> from the auction.
        6. YYYY.MM.DD Made a bet on <listing>. Value — <bid_value>.
        7. YYYY.MM.DD You lost the auction — <listing>.
        8. YYYY.MM.DD You closed the auction — <listing>. The winner is <user>.
        """
        db_table = 'auctions_logs'
        verbose_name = 'auctioneer log'
        verbose_name_plural = 'auctioneer logs'
        ordering = ['-date']

    def __str__(self): return f'log-entry #{self.pk}'


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
    owner = ForeignKey(Profile, on_delete=models.RESTRICT, related_name='lots_owned')
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

    def save(self, *args, **kwargs):
        """ Auto get a unique slug and
            add a new listing to owner's watchlist. """
        if not self.pk:
            if self.slug: s = str(self.slug)
            else: s = slugify(self.title)
            unique_slugify(self, s)

        super().save(*args, **kwargs)
        if self.in_watchlist.contains(self.owner) is False:
            self.in_watchlist.add(self.owner)
        entry = f'The item [{self.title}] has been added to your listings.'
        self.owner.logs.create(entry=entry)

    def publish_the_lot(self) -> bool:
        """ Make the listing available on the auction. """
        if self.starting_price < 1 or self.is_active is True:
            return False
        else:
            self.date_published = timezone.localtime()
            self.is_active = True
            self.save()
            entry = f'You have created an auction — [{self.title}].'
            self.owner.logs.create(entry=entry)
            return True

    def withdraw(self, item_sold=False) -> bool:
        """ Get the listing back from the auction. """
        if self.is_active is False:
            return False
        else:
            self.date_published = None
            self.is_active = False
            self.save()

            if item_sold is False:
                entry = f'You have withdrawn [{self.title}] from the auction.'
                self.owner.logs.create(entry=entry)
            elif self.potential_buyers.count() > 0:
                for profile in self.potential_buyers.all():
                    profile.logs.create(entry=f'You lost the auction — [{self.title}].')

            self.potential_buyers.clear()
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

    def bid_possibility(self, auctioneer, return_highest_bid=None) -> bool:
        if not self.is_active:
            return False
        elif self.owner == auctioneer:
            return False
        elif self.potential_buyers.count() > 0:
            highest_bid = self.bid_set.latest()
            if highest_bid.auctioneer == auctioneer:
                return False
            elif return_highest_bid:
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

        if not self.in_watchlist.contains(auctioneer):
            self.in_watchlist.add(auctioneer)
        auctioneer.placed_bets.add(self, through_defaults={'bid_value': bid_value})

        entry = f'Made a bet on [{self.title}]. Value — {bid_value}.'
        auctioneer.logs.create(entry=entry)
        return True

    def change_the_owner(self) -> bool:
        """ Sell the lot to the auctioneer that offers the highest bid and
            withdraw the lot from the auction. """
        if self.is_active is False or self.potential_buyers.count() == 0:
            return False
        else:
            highest_bid = self.bid_set.latest()
            new_owner = highest_bid.auctioneer
            entry = f'You closed the auction — [{self.title}]. ' \
                    f'The winner is {new_owner.username}.'
            self.owner.logs.create(entry=entry)

            self.owner = new_owner
            self.starting_price = highest_bid.bid_value
            if not self.in_watchlist.contains(new_owner):
                # don't really need that, but just in case...
                self.in_watchlist.add(new_owner)
            self.withdraw()

            entry = f'The listing [{self.title}] has been taken into possession.'
            self.owner.logs.create(entry=entry)
            return True


    def delete(self, **kwargs):
        self.image.delete()
        return super().delete(**kwargs)

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
