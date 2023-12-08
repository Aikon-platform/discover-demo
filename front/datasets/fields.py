from django.forms import FileField
from django.core.exceptions import ValidationError
from django.template.defaultfilters import filesizeformat

class ContentRestrictedFileField(FileField):
    """
    A FileField that only accepts files of a certain type, and a maximum size.
    """
    def __init__(self, *args, **kwargs):
        self.__accepted_types = kwargs.pop('accepted_types', None)
        self.__max_size = kwargs.pop('max_size', None)
        super().__init__(*args, **kwargs)

    def clean(self, *args, **kwargs):
        data = super().clean(*args, **kwargs)
        if self.__accepted_types and data:
            if data.content_type not in self.__accepted_types:
                raise ValidationError(
                    'File type not supported. '
                    'Supported types are: {}'.format(
                        ', '.join(self.__accepted_types)
                    )
                )
        if self.__max_size and data:
            if data.size > self.__max_size:
                raise ValidationError(
                    'File too large. '
                    f'Maximum size is: {filesizeformat(self.__max_size)}'
                )

        return data