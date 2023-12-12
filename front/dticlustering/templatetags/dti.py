from django import template

register = template.Library()

@register.simple_tag
def can_monitor_dti(user):
    return user.has_perm("dticlustering.monitor_dticlustering")