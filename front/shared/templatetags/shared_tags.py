from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter("field_type")
def field_type(obj):
    print(obj.field.widget.__class__.__name__)
    return obj.field.widget.__class__.__name__


@register.filter
def add_class(field, class_name):
    return field.as_widget(attrs={"class": class_name})


@register.filter
def add_str(arg1, arg2):
    return str(arg1) + str(arg2)


@register.filter
def uuid_prefix(uid: str):
    return str(uid)[:8]


@register.filter
def uuid_suffix(uid):
    return str(uid)[8:]


@register.simple_tag
def url_get_replace(request, field, value):
    dict_ = request.GET.copy()
    dict_[field] = value
    return mark_safe("?" + dict_.urlencode())


@register.simple_tag
def can_admin_accounts(user):
    return user.has_perm("auth.add_user")


@register.simple_tag
def can_monitor(user, app_name):
    return user.has_perm(f"{app_name}.monitor_{app_name}")
