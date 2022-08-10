from django.contrib import admin

from .models import ListingCategory, Profile, Listing, Comment, Bid, Watchlist, Log


@admin.register(ListingCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['label', 'items_in_category']
    list_filter = ['label']

    fields = ['label']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['username', 'money', 'items_owned_count',
                    'placed_bets_count', 'comments_written_count']
    list_filter = ['username', 'money']

    fields = ['username', 'money']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['slug', 'owner', 'category', 'date_created', 'is_active', 'date_published']
    list_filter = ['slug', 'category', 'owner', 'date_created', 'is_active']
    list_select_related = ['category', 'owner']

    search_fields = ['title']
    search_help_text = 'search listing title'

    fields = ['slug', 'title', 'category', 'owner',
              'starting_price', 'description', 'image',
              'date_created', 'date_published', 'is_active']
    prepopulated_fields = {'slug': ['title']}


@admin.register(Comment)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'pub_date', 'listing', 'author']
    list_filter = ['pub_date', 'listing', 'author']
    list_select_related = ['listing', 'author']

    search_fields = ['text']
    search_help_text = 'search in comments text'

    fields = ['pub_date', 'listing', 'author', 'text']
    readonly_fields = ['pub_date']


@admin.register(Bid)
class BidsAdmin(admin.ModelAdmin):
    list_display = ['bid_date', '__str__', 'bid_value', 'auctioneer', 'lot']
    list_display_links = ['__str__']
    list_filter = ['bid_date', 'auctioneer', 'lot']
    list_select_related = ['auctioneer', 'lot']

    fields = ['auctioneer', 'lot', 'bid_value', 'bid_date']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'profile', 'listing']
    list_filter = ['profile', 'listing']
    list_select_related = ['profile', 'listing']

    fields = ['profile', 'listing']


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['date', 'profile']
    list_display_links = ['profile']
    list_filter = ['date']
    list_select_related = ['profile']

    fields = ['date', 'profile', 'entry']
