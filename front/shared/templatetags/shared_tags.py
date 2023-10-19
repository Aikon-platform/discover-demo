from django import template
from django.utils.safestring import mark_safe

register = template.Library()

@register.filter('field_type')
def field_type(obj):
    return obj.field.widget.__class__.__name__

@register.simple_tag
def url_get_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return mark_safe("?"+dict_.urlencode())
