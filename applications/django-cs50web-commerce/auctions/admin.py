from django.contrib import admin

from .models import ListingCategory, Profile, Listing, Comment, Bid, Watchlist, Log


class ListingInline(admin.TabularInline):
    model = Listing
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['slug', 'category', 'owner', 'starting_price',
              'date_created', 'date_published', 'is_active']
    readonly_fields = fields


class CommentInline(admin.TabularInline):
    model = Comment
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['pub_date', '__str__', 'author']
    readonly_fields = fields


class LogInline(admin.TabularInline):
    model = Log
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['date', 'entry']
    readonly_fields = fields


class WatchlistInline(admin.TabularInline):
    model = Watchlist
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['__str__', 'profile', 'listing']
    readonly_fields = fields


class BidInline(admin.TabularInline):
    model = Bid
    extra = 0
    can_delete = False
    show_change_link = True
    fields = ['__str__', 'bid_date', 'bid_value', 'auctioneer', 'lot']
    readonly_fields = fields


@admin.register(ListingCategory)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ['pk', 'label', 'items_in_category']
    list_display_links = ['pk', 'label']
    list_filter = ['label']

    fields = ['pk', 'label']
    readonly_fields = ['pk']

    inlines = [ListingInline]


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    list_display = ['pk', 'username', 'money', 'items_owned_count',
                    'placed_bets_count', 'comments_written_count']
    list_display_links = ['pk', 'username']
    list_filter = ['username', 'money']

    fields = ['pk', 'username', 'money']
    readonly_fields = ['pk']

    inlines = [ListingInline, BidInline, WatchlistInline, CommentInline, LogInline]


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    list_display = ['pk', 'slug', 'owner', 'category', 'date_created', 'is_active', 'date_published']
    list_display_links = ['pk', 'slug']
    list_filter = ['slug', 'category', 'owner', 'date_created', 'is_active']
    list_select_related = ['category', 'owner']

    search_fields = ['title']
    search_help_text = 'search listing title'

    fields = ['pk', 'slug', 'title', 'category', 'owner',
              'starting_price', 'description', 'image',
              'date_created', 'date_published', 'is_active']

    inlines = [BidInline, WatchlistInline, CommentInline]

    def get_readonly_fields(self, request, obj=None):
        if obj: return ['pk', 'slug']
        else: return ['pk']

    def get_prepopulated_fields(self, request, obj=None):
        if obj: return super().get_prepopulated_fields(request, obj)
        else: return {'slug': ['title']}


@admin.register(Comment)
class CommentsAdmin(admin.ModelAdmin):
    list_display = ['pk', '__str__', 'pub_date', 'listing', 'author']
    list_display_links = ['pk', '__str__']
    list_filter = ['pub_date', 'listing', 'author']
    list_select_related = ['listing', 'author']

    search_fields = ['text']
    search_help_text = 'search in comments text'

    fields = ['pk', 'pub_date', 'listing', 'author', 'text']
    readonly_fields = ['pk', 'pub_date']


@admin.register(Bid)
class BidsAdmin(admin.ModelAdmin):
    list_display = ['pk', 'bid_date', '__str__', 'bid_value', 'auctioneer', 'lot']
    list_display_links = ['pk', '__str__']
    list_filter = ['bid_date', 'auctioneer', 'lot']
    list_select_related = ['auctioneer', 'lot']

    fields = ['pk', 'auctioneer', 'lot', 'bid_value', 'bid_date']
    readonly_fields = ['pk']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    list_display = ['pk', '__str__', 'profile', 'listing']
    list_display_links = ['pk', '__str__']
    list_filter = ['profile', 'listing']
    list_select_related = ['profile', 'listing']

    fields = ['pk', 'profile', 'listing']
    readonly_fields = ['pk']


@admin.register(Log)
class LogAdmin(admin.ModelAdmin):
    list_display = ['pk', 'date', 'profile']
    list_display_links = ['pk', 'profile']
    list_filter = ['date']
    list_select_related = ['profile']

    fields = ['pk', 'date', 'profile', 'entry']
    readonly_fields = ['pk', 'date']
