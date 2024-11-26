from django import template
from django.utils.safestring import mark_safe

register = template.Library()


@register.filter("field_type")
def field_type(obj):
    return obj.field.widget.__class__.__name__


@register.filter("field_classes")
def field_classes(obj):
    classes = obj.field.widget.attrs.get("classes", "")
    if type(classes) is list:
        return " ".join(classes)
    return classes


@register.filter
def add_class(field, class_name):
    attrs = field.field.widget.attrs
    attrs["class"] = attrs.get("class", "") + " " + class_name
    return field.as_widget(attrs=attrs)


@register.filter
def add_str(arg1, arg2):
    return str(arg1) + str(arg2)


@register.filter
def startswith(text, starts):
    if not isinstance(text, str):
        return False
    if isinstance(starts, str):
        return text.startswith(starts)

    if isinstance(starts, dict):
        starts = starts.keys()
    starts = list(starts)

    for start in starts:
        if text.startswith(start):
            return True
    return False


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
