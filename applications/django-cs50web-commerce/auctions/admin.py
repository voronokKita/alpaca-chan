from django.contrib import admin

from .models import ListingCategory, Profile, Listing, Comment, Bid, Watchlist


@admin.register(ListingCategory)
class CategoryAdmin(admin.ModelAdmin):
    fields = ['label']


@admin.register(Profile)
class ProfileAdmin(admin.ModelAdmin):
    fields = ['username', 'money']


@admin.register(Listing)
class ListingAdmin(admin.ModelAdmin):
    fields = ['slug', 'title', 'description', 'image',
              'starting_price', 'date_created', 'date_published',
              'is_active', 'category', 'owner']


@admin.register(Comment)
class CommentsAdmin(admin.ModelAdmin):
    fields = ['listing', 'author', 'text', 'pub_date']


@admin.register(Bid)
class BidsAdmin(admin.ModelAdmin):
    fields = ['auctioneer', 'lot', 'bid_value', 'bid_date']


@admin.register(Watchlist)
class WatchlistAdmin(admin.ModelAdmin):
    fields = ['profile', 'listing']
