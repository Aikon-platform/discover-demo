import mimetypes

from django import forms
from django.db import models
from django.forms import FileField
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat
from django.core.validators import URLValidator


class ContentRestrictedFileField(FileField):
    """
    A FileField that only accepts files of a certain type, and a maximum size.
    """

    def __init__(self, *args, **kwargs):
        self.__accepted_types = kwargs.pop("accepted_types", None)
        self.__max_size = kwargs.pop("max_size", None)
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)

        if not data:
            return data

        file_type, _ = mimetypes.guess_type(data.name)

        if self.__accepted_types and file_type:
            print(file_type)
            if file_type not in self.__accepted_types:
                raise ValidationError(
                    "File type not supported. "
                    f"Supported types are: {', '.join(self.__accepted_types)}"
                )

        if self.__max_size:
            if data.size > self.__max_size:
                raise ValidationError(
                    "File too large. "
                    f"Maximum size is: {filesizeformat(self.__max_size)}"
                )

        return data


class MultipleFileInput(forms.ClearableFileInput):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

    allow_multiple_selected = True


class ContentRestrictedMultipleFileField(ContentRestrictedFileField):
    def __init__(self, *args, **kwargs):
        kwargs.setdefault("widget", MultipleFileInput(*args, **kwargs))
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        clean_one_file = super().clean
        if isinstance(data, (list, tuple)):
            return [clean_one_file(d, initial) for d in data]
        return clean_one_file(data, initial)


class URLListWidget(forms.Textarea):
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.attrs["class"] = self.attrs.get("class", "") + " urllistfield"

    class Media:
        js = ("js/url_list_field.js",)
        css = {"all": ("css/url_list_field.css",)}


class URLListField(forms.JSONField):
    """
    A Form Field that handles URL list
    """

    widget = URLListWidget

    def __init__(self, *args, **kwargs):
        kwargs.setdefault("help_text", ("List of URLs",))
        super().__init__(*args, **kwargs)

    def prepare_value(self, value):
        if not value:
            value = []
        elif isinstance(value[0], list) or isinstance(value[0], tuple):
            pass
        else:
            if isinstance(value[0], str):
                urls = value
            else:
                raise ValueError(str(value))
            value = [[url] for url in urls]

        return super().prepare_value(value)

    def to_python(self, value, flatten: bool = True):
        value = super().to_python(value)

        if not value:
            return []

        if not isinstance(value, (list, set)):
            raise ValidationError("Value is not a list")

        validator = URLValidator()
        errors = []
        for url, *_ in value:
            try:
                validator(url)
            except ValidationError as e:
                errors.append(e)

        if len(errors) > 0:
            raise ValidationError(errors)

        if not flatten:
            return value

        return [url for (url, *attrs) in value]


class URLListModelField(models.JSONField):
    def formfield(self, **kwargs):
        kwargs["form_class"] = URLListField
        return super().formfield(**kwargs)
