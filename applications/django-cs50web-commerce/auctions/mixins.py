from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect

from .models import Profile, ListingCategory, Listing


class AuctionsAuthMixin:
    """ Filter not authenticated requests. """
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('accounts:login_and_next', args=['auctions']))
        else:
            return super().dispatch(request, *args, **kwargs)


class ProfileMixin:
    """ Loads profile's username & pk of authenticated users. """
    auctioneer = None
    auctioneer_pk = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.auctioneer = request.user.username

            # request.session.clear_expired()
            auctioneer_pk = request.session.get('auctioneer_pk')
            if auctioneer_pk:
                self.auctioneer_pk = auctioneer_pk
            else:
                profile = Profile.manager.filter(
                    username=self.auctioneer
                ).first()
                request.session['auctioneer_pk'] = profile.pk
                self.auctioneer_pk = profile.pk

        return super().dispatch(request, *args, **kwargs)


class RestrictPkMixin:
    """ Restricts access to a view with <pk> in path by profile's pk.
        Relies on ProfileMixin to get profile's pk first. """
    def dispatch(self, request, *args, **kwargs):
        pk = kwargs.get('pk')
        if pk and self.auctioneer_pk != pk:
            return redirect(reverse('auctions:index'))
        else:
            return super().dispatch(request, *args, **kwargs)


class NavbarMixin:
    """ Will generate navbar dynamically.
        Relies on ProfileMixin to get profile's pk first. """
    @staticmethod
    def _get_default_nav() -> list:
        """ Navbar elements for any user. """
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
        """ Navbar elements for authenticated users only. """
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
        if self.auctioneer_pk:
            context['navbar_list'] += self._get_auth_user_nav(self.auctioneer_pk)
        return context


class PresetMixin(ProfileMixin, RestrictPkMixin, NavbarMixin):
    """
    Combines ProfileMixin & RestrictPkMixin & NavbarMixin.
    :ProfileMixin: loads profile's username & pk of authenticated users.
    :RestrictPkMixin: restricts access to a view with <pk> in path by profile's pk.
    :NavbarMixin: generates navbar dynamically.
    """


class ListingRedirectMixin:
    """ Will redirect the user if tries to request an incorrect listing view.
        Loads queryset and overrides get_queryset() method. """

    def dispatch(self, request, *args, **kwargs):
        slug = kwargs.get('slug')
        listing = self._get_listing_obj(slug)

        is_active_flag = self._must_bee_active(request, slug)
        if listing.is_active is False and \
                listing.owner.username != request.user.username:
            # only the listing owner can see & edit an unpublished item
            return redirect(reverse('auctions:index'))

        elif listing.is_active != is_active_flag:
            # request of a published auction lot by url of an unpublished listing, and vice versa
            return redirect(listing.get_absolute_url())

        else:
            return super().dispatch(request, *args, **kwargs)

    def get_queryset(self):
        if self.queryset:
            return self.queryset
        else:
            return Listing.manager\
                .select_related('category', 'owner')\
                .filter(slug=self.kwargs.get('slug'))

    def _get_listing_obj(self, slug):
        """
        The conditions depend on the state of a view.
        May add the listing object to the view if called first.
        Note: If a View has an object, then the get_queryset() method isn't called.
        """
        if self.queryset:
            listing_set = self.queryset
        else:
            listing_set = Listing.manager\
                .select_related('category', 'owner')\
                .filter(slug=slug)
            self.queryset = listing_set
        return listing_set.get()

    @staticmethod
    def _must_bee_active(request, slug):
        """ Is this listing's path — the published auction's lot path? """
        if 'lots' in request.path:
            return True
        else:
            return False
