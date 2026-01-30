# templatetags.custom_filters.py
from django import template
from django.utils.html import conditional_escape
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter(name='truncate_title')
def truncate_title(value, max_length=70):
    if not value:
        return ""
    if len(value) <= max_length:
        return conditional_escape(value)
    return mark_safe(f"{conditional_escape(value[:max_length-3])}...")
