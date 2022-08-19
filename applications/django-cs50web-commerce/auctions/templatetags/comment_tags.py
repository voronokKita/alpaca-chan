from django import template

register = template.Library()


@register.simple_tag
def comment_slice(comment_set, view=None, slice_=10):
    if view: return comment_set
    else: return comment_set[:slice_]
