from django import template

register = template.Library()


@register.simple_tag
def in_watchlist(listing, username):
    return listing.check_name_in_watchlist(username)


@register.simple_tag
def can_unwatch(listing, username):
    return listing.can_unwatch(username=username)


@register.simple_tag
def can_bid(listing, username):
    return listing.bid_possibility(username=username)
