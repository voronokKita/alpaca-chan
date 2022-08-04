from django.utils import timezone
from django.utils.text import slugify
from django.core.exceptions import ObjectDoesNotExist
from django.contrib.auth.models import User
from django.db import models
from django.db.models import (
    Model, CharField,
    DateTimeField, ForeignKey, SlugField,
    FloatField, TextField, ImageField,
    BooleanField, ManyToManyField, OneToOneField
)

#TODO get_absolute_url
SLUG_MAX_LEN = 16


def user_media_path(listing, filename):
    """ Files will be uploaded to MEDIA_ROOT/auctions/2022.08.08_<listing_slug>/ """
    return f'auctions/%Y.%m.%d_{listing.slug}/{filename}'


def get_unique_slug_or_none(model_, slug):
    attempt = slug[:SLUG_MAX_LEN]
    for i in range(10):
        try:
            model_.manager.get(attempt)
        except ObjectDoesNotExist:
            return attempt
        else:
            attempt = f'{slug}'[:SLUG_MAX_LEN-1] + str(i)
    else:
        return None

class AuctionsUser(User):
    """ Interface to the main User model. """
    manager = models.Manager()

    class Meta:
        """ auctions_user --- user_profile """
        db_table = 'auctions_user'
        verbose_name = 'auctioneer'
        verbose_name_plural = 'auctioneers'
        proxy = True

    def __str__(self): return self.username


class UserProfile(Model):
    manager = models.Manager()

    slug = SlugField('slug', unique=True, primary_key=True, max_length=SLUG_MAX_LEN)
    user = OneToOneField(AuctionsUser, on_delete=models.PROTECT,
                         verbose_name='profile′s owner', related_name='user_profile')
    money = FloatField('money on account', default=0)

    class Meta:
        """
        profile --- auctions_user (proxy for the project user)
        profile >-- bid --< listings
        profile >-- watchlist --< listings
        profile --< listings_owned
        profile --< comment_set
        """
        db_table = 'auctions_profile'
        verbose_name = 'profile'
        verbose_name_plural = 'profiles'
        ordering = ['slug']

    def save(self, *args, **kwargs):
        result = get_unique_slug_or_none(UserProfile, slugify(self.user))
        if result:
            self.slug = result
            return super().save(*args, **kwargs)

    def __str__(self): return self.user


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

    bid_value = FloatField(default=1)
    bid_date = DateTimeField(default=timezone.localtime, db_index=True)
    auctioneer = ForeignKey(UserProfile, on_delete=models.CASCADE)
    lot = ForeignKey('Listing', on_delete=models.CASCADE)

    class Meta:
        """ profiles >-- bid --< listings """
        db_table = 'auctions_bids'
        verbose_name = 'placed bid'
        verbose_name_plural = 'placed bets'
        ordering = ['-bid_date']
        get_latest_by = ['-bid_date']

    def __str__(self): return f'{self.auctioneer} >-- bid --< {self.lot}'


class Watchlist(Model):
    manager = models.Manager()
    profile = ForeignKey(UserProfile, on_delete=models.CASCADE)
    listing = ForeignKey('Listing', on_delete=models.CASCADE)

    class Meta:
        """ profiles >-- watchlist --< listings """
        db_table = 'auctions_watchlists'
        verbose_name = 'watchlist'
        verbose_name_plural = 'watchlists'

    def __str__(self): return f'{self.profile} >-- watchlist --< {self.listing}'


class Listing(Model):
    manager = models.Manager()

    slug = SlugField('slug', unique=True, blank=True,
                     primary_key=True, max_length=SLUG_MAX_LEN)
    title = CharField('listing title', max_length=300)
    description = TextField('listing description')
    image = ImageField('visual presentation', upload_to=user_media_path, max_length=500)
    starting_price = FloatField(default=1)

    date_created = DateTimeField('created', default=timezone.localtime)
    date_published = DateTimeField('published', null=True, default=None)
    is_active = BooleanField('is listing published?', default=False)

    category = ForeignKey(ListingCategory, on_delete=models.PROTECT)
    owner = ForeignKey(
        UserProfile, on_delete=models.RESTRICT,
        related_name='listings_owned', related_query_name='listing'
    )
    potential_buyers = ManyToManyField(
        UserProfile, through=Bid,
        related_name='placed_bets', related_query_name='bid'
    )
    in_watchlist = ManyToManyField(UserProfile, through=Watchlist)

    class Meta:
        """ listing --< comment_set """
        db_table = 'auctions_listing'
        verbose_name = 'listing'
        verbose_name_plural = 'listings'
        ordering = ['-date_published', '-date_created']
        get_latest_by = ['-date_published', '-date_created']
        indexes = [
            models.Index(fields=['slug']),
            models.Index(fields=['date_published', 'date_created']),
        ]

    def save(self, *args, **kwargs):
        if self.slug: s = self.slug
        else: s = slugify(self.title)

        result = get_unique_slug_or_none(Listing, s)
        if not result: return
        else: self.slug = result

        return super().save(*args, **kwargs)

    def delete_file(self):
        self.image.delete()

    def __str__(self): return self.slug


class Comment(Model):
    manager = models.Manager()

    author = ForeignKey(UserProfile, null=True, on_delete=models.SET_NULL)
    listing = ForeignKey(Listing, verbose_name='commentary on', on_delete=models.CASCADE)
    text = TextField('comment text')
    pub_date = DateTimeField('comment published', auto_now=True, db_index=True)

    class Meta:
        db_table = 'auctions_comment'
        verbose_name = 'comment'
        verbose_name_plural = 'comments'
        ordering = ['-pub_date']
        get_latest_by = ['-pub_date']

    def __str__(self): return f'comment #{self.pk}'
