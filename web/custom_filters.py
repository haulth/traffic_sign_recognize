from django import template

register = template.Library()

@register.filter
def has_items(lst):
    return any(lst)