from django import template

register = template.Library()


@register.simple_tag
def in_watchlist(listing, profile):
    return listing.in_watchlist.contains(profile)


@register.simple_tag
def can_unwatch(listing, profile):
    return listing.can_unwatch(profile)
