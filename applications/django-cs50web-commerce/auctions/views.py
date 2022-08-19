import logging

from django.views import generic
from django.shortcuts import redirect

from .forms import (
    TransferMoneyForm, CreateListingForm,
    EditListingForm, PublishListingForm,
    AuctionLotForm, CommentForm
)
from .models import Profile, Listing, Log
from .mixins import ProfileMixin, NavbarMixin, AuctionsAuthMixin, ListingRedirectMixin

logger = logging.getLogger(__name__)

# TODO bets placed view


class AuctionsIndexView(ProfileMixin, NavbarMixin, generic.ListView):
    template_name = 'auctions/index.html'
    model = Listing
    context_object_name = 'published_listings'

    def get_queryset(self):
        if self.kwargs.get('category_pk'):
            return Listing.manager\
                .select_related('category')\
                .filter(
                    category__pk=self.kwargs.get('category_pk'),
                    is_active=True
                ).all()
        else:
            return Listing.manager\
                .select_related('category')\
                .filter(is_active=True).all()


# TODO access & redirect
class ProfileView(AuctionsAuthMixin, ProfileMixin,
                  NavbarMixin, generic.UpdateView):
    template_name = 'auctions/profile.html'
    model = Profile
    context_object_name = 'profile'
    form_class = TransferMoneyForm

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        logger.debug(kwargs.get('pk'))
        logger.debug(self.auctioneer_pk)
        return result

    def get_queryset(self):
        return Profile.manager.filter(pk=self.auctioneer_pk)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        money, bets_total = context['profile'].display_money()
        context['user_money'] = money
        context['bets_total'] = bets_total
        return context


# TODO access & redirect
class UserHistoryView(AuctionsAuthMixin, ProfileMixin,
                      NavbarMixin, generic.ListView):
    template_name = 'auctions/profile_history.html'
    model = Log
    context_object_name = 'profile_logs'

    def get_queryset(self):
        return Log.manager.filter(
            profile__pk=self.auctioneer_pk
        ).all()


# TODO access & redirect
class WatchlistView(AuctionsAuthMixin, ProfileMixin,
                    NavbarMixin, generic.DetailView):
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


# TODO access & redirect
class CreateListingView(AuctionsAuthMixin, ProfileMixin,
                        NavbarMixin, generic.CreateView):
    template_name = 'auctions/listing_create.html'
    model = Listing
    form_class = CreateListingForm

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        profile_set = Profile.manager.filter(pk=self.auctioneer_pk)
        form.fields['owner'].queryset = profile_set
        form.fields['owner'].initial = profile_set[0]
        return form


# TODO access
class ListingView(AuctionsAuthMixin, ProfileMixin, NavbarMixin,
                  ListingRedirectMixin, generic.UpdateView):
    template_name = 'auctions/listing.html'
    model = Listing
    context_object_name = 'listing'
    form_class = PublishListingForm

    def get_queryset(self):
        return Listing.manager\
                .select_related('category')\
                .filter(slug=self.kwargs.get('slug'))


# TODO access
class EditListingView(AuctionsAuthMixin, ProfileMixin, NavbarMixin,
                      ListingRedirectMixin, generic.UpdateView):
    template_name = 'auctions/listing_edit.html'
    model = Listing
    context_object_name = 'listing'
    form_class = EditListingForm


# TODO access
class AuctionLotView(ProfileMixin, NavbarMixin,
                     ListingRedirectMixin, generic.UpdateView):
    template_name = 'auctions/listing_published.html'
    model = Listing
    context_object_name = 'listing'
    form_class = AuctionLotForm
    second_form_class = CommentForm

    def get_queryset(self):
        return Listing.manager.select_related('category', 'owner')

    def get_form(self, *args, **kwargs):
        """ Main form class. """
        form = super().get_form(*args, **kwargs)
        initial = self.auctioneer if self.auctioneer else 'none'
        form.fields['auctioneer'].initial = initial
        return form

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        """ Secondary CommentForm class. """
        if self.auctioneer:
            context['form2'] = self.second_form_class(instance=context['listing'])
            context['form2'].fields['author_hidden'].initial = self.auctioneer

        if self.auctioneer and not self.object.bid_possibility(username=self.auctioneer):
            context['form'].fields['bid_value'].disabled = True
            context['bid_forbidden'] = True
        return context


class CommentsView(ProfileMixin, NavbarMixin, generic.UpdateView):
    template_name = 'auctions/comments.html'
    model = Listing
    context_object_name = 'listing'
    form_class = CommentForm
    extra_context = {'comment_view': True}

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        if self.auctioneer:
            form.fields['author_hidden'].initial = self.auctioneer
        return form


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
