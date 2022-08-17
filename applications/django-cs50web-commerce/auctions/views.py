import logging

from django.urls import reverse, reverse_lazy
from django.views import generic
from django.http import HttpResponseRedirect

from .models import Profile, Listing, ListingCategory, Log, Watchlist
from .forms import TransferMoneyForm, CreateListingForm, PublishListingForm

logger = logging.getLogger(__name__)


class NavbarMixin:
    @staticmethod
    def _get_default_nav() -> list:
        category_list = []
        for category in ListingCategory.manager.iterator():
            url = reverse('auctions:category', args=[category.pk])
            category_list.append({'label': category.label, 'url': url})
        return [
            {'url': reverse_lazy('auctions:index'), 'text': 'Active Listings'},
            {'text': 'Category', 'category_list': category_list, 'category': True},
        ]

    @staticmethod
    def _get_auth_user_nav(pk: int) -> list:
        return [
            {'url': reverse_lazy('auctions:watchlist', args=[pk]), 'text': 'Watchlist'},
            {'url': reverse_lazy('auctions:create_listing', args=[pk]), 'text': 'Create Listing'},
            {'url': reverse_lazy('auctions:profile', args=[pk]), 'text': 'Wallet'},
            {'url': reverse_lazy('auctions:user_history', args=[pk]), 'text': 'History'},
        ]

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['expand_navbar'] = True
        context['navbar_list'] = self._get_default_nav()
        if self.request.user.is_authenticated:
            profile = Profile.manager.filter(
                username=self.request.user.username
            ).first()
            if profile:
                context['navbar_list'] += self._get_auth_user_nav(profile.pk)

        return context


class AuctionsAuthMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return HttpResponseRedirect(reverse('accounts:login_and_next', args=['auctions']))
        else:
            return super().dispatch(request, *args, **kwargs)


class AuctionsIndexView(NavbarMixin, generic.ListView):
    template_name = 'auctions/index.html'
    model = Listing
    context_object_name = 'published_listings'

    def get_queryset(self):
        if self.kwargs.get('category_pk'):
            return Listing.manager.filter(category__pk=self.kwargs['category_pk'],
                                          is_active=True)
        else:
            return Listing.manager.filter(is_active=True)


class ProfileView(NavbarMixin, AuctionsAuthMixin, generic.UpdateView):
    template_name = 'auctions/profile.html'
    model = Profile
    form_class = TransferMoneyForm

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        profile = context['object']
        money, bets_total = profile.display_money()
        context['user_money'] = money
        context['bets_total'] = bets_total
        return context


class UserHistoryView(NavbarMixin, AuctionsAuthMixin, generic.ListView):
    template_name = 'auctions/profile_history.html'
    model = Log
    context_object_name = 'profile_logs'

    def get_queryset(self):
        return Log.manager.filter(profile__pk=self.kwargs.get('pk'))


class WatchlistView(NavbarMixin, AuctionsAuthMixin, generic.TemplateView):
    template_name = 'auctions/watchlist.html'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        watchlist = Watchlist.manager.filter(profile__pk=self.kwargs.get('pk')).first()
        items_owned, owned_and_published, just_watched = watchlist.generate_watchlist()
        context['listing_owned'] = items_owned
        context['owned_and_published'] = owned_and_published
        context['listing_watched'] = just_watched
        return context


class CreateListingView(NavbarMixin, AuctionsAuthMixin, generic.CreateView):
    template_name = 'auctions/listing_create.html'
    model = Listing
    form_class = CreateListingForm

    def get_form(self, *args, **kwargs):
        form = super().get_form(*args, **kwargs)
        profile = Profile.manager.filter(pk=self.kwargs['pk'])
        form.fields['owner'].queryset = profile
        form.fields['owner'].initial = profile[0]
        return form


class ListingView(NavbarMixin, AuctionsAuthMixin, generic.UpdateView):
    template_name = 'auctions/listing.html'
    model = Listing
    form_class = PublishListingForm
    context_object_name = 'listing'

    def get_object(self, queryset=None):
        """ Not published listing only. """
        instance = super().get_object(queryset)
        if instance.is_active:
            return HttpResponseRedirect(reverse('accounts:auction_lot', args=[instance.slug]))
        else:
            return instance


class EditListingView(NavbarMixin, AuctionsAuthMixin, generic.TemplateView):
    template_name = 'auctions/listing_edit.html'

    def get_object(self, queryset=None):
        """ Not published listing only. """
        instance = super().get_object(queryset)
        if instance.is_active:
            return HttpResponseRedirect(reverse('accounts:auction_lot', args=[instance.slug]))
        else:
            return instance


class AuctionLotView(NavbarMixin, generic.TemplateView):
    template_name = 'auctions/listing_published.html'

    def get_object(self, queryset=None):
        """ Published listing only. """
        instance = super().get_object(queryset)
        if instance.is_active:
            return HttpResponseRedirect(reverse('accounts:listing', args=[instance.slug]))
        else:
            return instance


class CommentsView(NavbarMixin, generic.TemplateView):
    template_name = 'auctions/comments.html'


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
