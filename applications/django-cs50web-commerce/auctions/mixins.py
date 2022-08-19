from django.urls import reverse, reverse_lazy
from django.shortcuts import redirect

from .models import Profile, ListingCategory, Listing


class ProfileMixin:
    auctioneer = None
    auctioneer_pk = None

    def dispatch(self, request, *args, **kwargs):
        if request.user.is_authenticated:
            self.auctioneer = request.user.username

            request.session.clear_expired()
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
        if self.auctioneer_pk:
            context['navbar_list'] += self._get_auth_user_nav(self.auctioneer_pk)
        return context


class AuctionsAuthMixin:
    def dispatch(self, request, *args, **kwargs):
        if not request.user.is_authenticated:
            return redirect(reverse('accounts:login_and_next', args=['auctions']))
        else:
            return super().dispatch(request, *args, **kwargs)


class ListingRedirectMixin:
    """ Will redirect the user if tries to request an incorrect listing view. """

    def dispatch(self, request, *args, **kwargs):
        result = super().dispatch(request, *args, **kwargs)
        if result.status_code != 200:
            return result

        slug = kwargs.get('slug')
        listing = self._get_listing_obj(slug)

        is_active_flag = self._must_bee_active(request, slug)
        if listing.is_active != is_active_flag:
            return redirect(listing.get_absolute_url())
        else:
            return result

    def _get_listing_obj(self, slug):
        """
        The conditions depend on the state of a view.
        May add the listing object to the view if called first.
        Note: If the view has an object, then the get_queryset() method isn't called.
        """
        if self.object:
            listing = self.object
        else:
            listing = Listing.manager\
                .select_related('category')\
                .filter(slug=slug)\
                .first()
            self.object = listing
        return listing

    @staticmethod
    def _must_bee_active(request, slug):
        """ Is this listing's path — the published object's path? """
        if 'lots' in request.path:
            return True
        else:
            return False
