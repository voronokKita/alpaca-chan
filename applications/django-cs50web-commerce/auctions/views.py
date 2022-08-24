import logging

from django.urls import reverse
from django.shortcuts import redirect
from django.views import generic

from .forms import (
    TransferMoneyForm, CreateListingForm,
    EditListingForm, PublishListingForm,
    AuctionLotForm, CommentForm
)
from .models import Profile, Listing, Log
from .mixins import AuctionsAuthMixin, PresetMixin, ListingRedirectMixin

logger = logging.getLogger(__name__)


class AuctionsIndexView(PresetMixin, generic.ListView):
    template_name = 'auctions/index.html'
    model = Listing
    context_object_name = 'published_listings'

    def get_queryset(self):
        filter_by_category = self.kwargs.get('category_pk')
        if filter_by_category:
            return Listing.manager\
                .select_related('category')\
                .filter(
                    category__pk=filter_by_category,
                    is_active=True
                ).all()
        else:
            return Listing.manager\
                .select_related('category')\
                .filter(is_active=True).all()


class ProfileView(AuctionsAuthMixin, PresetMixin, generic.UpdateView):
    template_name = 'auctions/profile.html'
    model = Profile
    context_object_name = 'profile'
    form_class = TransferMoneyForm

    def get_queryset(self):
        return Profile.manager.filter(pk=self.auctioneer_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        money, bids_total = context['profile'].display_money()
        context['user_money'] = money
        context['bids_total'] = bids_total
        return context


class UserHistoryView(AuctionsAuthMixin, PresetMixin, generic.ListView):
    template_name = 'auctions/profile_history.html'
    model = Log
    context_object_name = 'profile_logs'

    def get_queryset(self):
        return Log.manager.filter(
            profile__pk=self.auctioneer_pk
        ).all()


class WatchlistView(AuctionsAuthMixin, PresetMixin, generic.DetailView):
    template_name = 'auctions/watchlist.html'
    model = Profile
    context_object_name = 'profile'

    def get_queryset(self):
        return Profile.manager.filter(pk=self.auctioneer_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = context['profile']
        context['listing_owned'] = profile\
            .items_watched\
            .select_related('category')\
            .filter(owner=profile, is_active=False)

        context['owned_and_published'] = profile\
            .items_watched\
            .select_related('category')\
            .filter(owner=profile, is_active=True)

        context['listing_watched'] = profile\
            .items_watched\
            .select_related('category')\
            .exclude(owner=profile)
        return context


class CreateListingView(AuctionsAuthMixin, PresetMixin, generic.CreateView):
    template_name = 'auctions/listing_create.html'
    model = Listing
    form_class = CreateListingForm

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        profile_set = Profile.manager.filter(pk=self.auctioneer_pk)
        form.fields['owner'].queryset = profile_set
        form.fields['owner'].initial = profile_set[0]
        return form


class ListingView(AuctionsAuthMixin, PresetMixin,
                  ListingRedirectMixin, generic.UpdateView):
    template_name = 'auctions/listing.html'
    model = Listing
    context_object_name = 'listing'
    form_class = PublishListingForm


class EditListingView(AuctionsAuthMixin, PresetMixin,
                      ListingRedirectMixin, generic.UpdateView):
    template_name = 'auctions/listing_edit.html'
    model = Listing
    context_object_name = 'listing'
    form_class = EditListingForm


class AuctionLotView(PresetMixin, ListingRedirectMixin, generic.UpdateView):
    template_name = 'auctions/listing_published.html'
    model = Listing
    context_object_name = 'listing'
    form_class = AuctionLotForm
    second_form_class = CommentForm

    def get_form(self, *args, **kwargs):
        """ Main form class. """
        form = super().get_form(*args, **kwargs)
        initial = self.auctioneer if self.auctioneer else 'none'
        form.fields['auctioneer'].initial = initial
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if self.auctioneer:
            """ Secondary CommentForm class. """
            context['form2'] = self.second_form_class(instance=context['listing'])
            context['form2'].fields['author_hidden'].initial = self.auctioneer

            context['profile'] = Profile.manager.filter(username=self.auctioneer).first()

            result = self.object.no_bid_option(context['profile'])
            if result:
                context['form'].fields['bid_value'].disabled = True
                context['bid_forbidden'] = result

        return context


class CommentsView(PresetMixin, generic.UpdateView):
    template_name = 'auctions/comments.html'
    model = Listing
    context_object_name = 'listing'
    form_class = CommentForm
    extra_context = {'comment_view': True}

    def dispatch(self, request, *args, **kwargs):
        """ Comment page of a listing that not published is available only to the owner. """
        result = super().dispatch(request, *args, **kwargs)
        if (not self.object.is_active and not request.user.is_authenticated) or \
                (not self.object.is_active and self.object.owner.username != self.auctioneer):
            return redirect(reverse('auctions:index'))
        else:
            return result

    def get_queryset(self):
        return Listing.manager\
                .select_related('owner')\
                .prefetch_related('comment_set', 'comment_set__author')\
                .filter(slug=self.kwargs.get('slug'))

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if self.auctioneer:
            form.fields['author_hidden'].initial = self.auctioneer
        return form


class BidView(PresetMixin, generic.DetailView):
    template_name = 'auctions/bids_list.html'
    model = Listing
    context_object_name = 'listing'

    def dispatch(self, request, *args, **kwargs):
        """ Only for the published auction lots. """
        result = super().dispatch(request, *args, **kwargs)
        if self.object.is_active is False:
            return redirect(reverse('auctions:index'))
        else:
            return result

    def get_queryset(self):
        return Listing.manager\
                .prefetch_related('bid_set')\
                .filter(slug=self.kwargs.get('slug'))


""" TODO
https://cs50.harvard.edu/web/2020/projects/2/commerce/

# MODELS
* Your application should have at least three models in addition to the User model: 
  one for auction listings, one for bids, and one for comments made on auction listings.

# ACTIVE LISTINGS PAGE
* The default route of your web application should let users view all of the currently active auction listings. 
  For each active listing, this page should display the title, description, current price, and photo.  
* The page should display a list of categories, clicking on any of which will display the items in that category.

# USER PAGE
* A user must be able to register and then log in with his username and password.

# CREATE LISTING
* Users should be able to visit a page to create a new listing. 
  They should be able to specify a title for the listing, a text-based description, and what the starting bid should be, 
  provide an image for the listing and  a category - e.g. Fashion, Toys, Electronics, Home, etc.

# LISTING PAGE
* On that page, users should be able to view all details about the listing, including the current price for the listing.

* If the user is signed in, the user should be able to add the item to their “Watchlist.” 
  If the item is already on the watchlist, the user should be able to remove it.
    
* If the user is signed in, the user should be able to bid on the item. 
  The bid must be at least as large as the starting bid, and must be greater than any other bids 
  that have been placed. If the bid doesn’t meet those criteria, the user should be presented with an error.
    
* If the user is signed in and is the one who created the listing, 
  the user should have the ability to “close” the auction from this page, 
  which makes the highest bidder the winner of the auction and makes the listing no longer active.
    
* If a user is signed in on a closed listing page, and the user has won that auction, the page should say so.
  Users who are signed in should be able to add comments to the listing page. 
  The listing page should display all comments that have been made on the listing.

# WATCHLIST
* Users who are signed in should be able to visit a Watchlist page, 
  which should display all of the listings that a user has added to their watchlist. 
  Clicking on any of those listings should take the user to that listing’s page.
* The page should display all of the listings that are owned by the user: created and purchased.

# MY :: NOTIFICATION PAGE
* A registered user can go to the page and read notifications about closed auctions.
  
# MY :: DJANGO ADMIN INTERFACE
* Via the Django admin interface, a site administrator should be able to view, 
  add, edit, and delete any listings, comments, and bids made on the site.
"""
