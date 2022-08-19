import re
from django import template

register = template.Library()

@register.simple_tag
def active(pattern, path):
    if re.fullmatch(str(pattern), path): return 'active'
    else: return ''
