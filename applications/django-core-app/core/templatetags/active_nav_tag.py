import re

from django import template

register = template.Library()


@register.simple_tag
def active(pattern, path):
    if re.search(pattern, path): return 'active'
    else: return ''
