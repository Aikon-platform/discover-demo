from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

from .mails import (
    send_activation_email,
    send_application_email,
    send_newaccount_notification,
)
from datasets.fields import ContentRestrictedFileField

from datasets.models import ZippedDataset

User = get_user_model()


class AccountRequestForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("username", "email", "first_name", "last_name")

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)

        self.fields["email"].required = True

    def clean_email(self):
        email = self.cleaned_data.get("email")
        if User.objects.filter(email=email).exists():
            raise forms.ValidationError("An account with this email already exists.")
        return email

    def save(self, commit=True):
        instance = super().save(commit)

        account_needs_approval = getattr(settings, "ACCOUNT_NEEDS_APPROVAL", False)

        if account_needs_approval:
            instance.is_active = False
            instance.set_unusable_password()
        else:
            instance.is_active = True
            instance.set_password(User.objects.make_random_password(length=24))

        if commit:
            instance.save()
            if account_needs_approval:
                send_application_email(instance)
            else:
                send_activation_email(instance)

            send_newaccount_notification(instance)

        return instance


class AccountEditForm(forms.ModelForm):
    class Meta:
        model = User
        fields = ("first_name", "last_name", "email")


class AbstractTaskForm(forms.ModelForm):
    class Meta:
        model = None
        abstract = True
        fields = ("name", "notify_email")

    def __init__(self, *args, **kwargs):
        self.__user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

    def _populate_instance(self, instance):
        instance.requested_by = self.__user

    def save(self, commit=True):
        instance = super().save(commit=False)
        self._populate_instance(instance)

        if commit:
            instance.save()

        return instance


class AbstractTaskOnDatasetForm(AbstractTaskForm):
    class Meta(AbstractTaskForm.Meta):
        model = None
        abstract = True
        # TODO add format, iiif, pdf
        fields = AbstractTaskForm.Meta.fields + ("dataset_zip", "dataset_name")

    dataset_format = forms.ChoiceField(
        label="Type",
        choices=[("zip", "ZIP"), ("iiif", "IIIF Manifest"), ("pdf", "PDF")],
    )
    dataset_zip = ContentRestrictedFileField(
        label="Zipped Dataset",
        help_text="A .zip file containing the dataset to be clustered",
        accepted_types=["application/zip"],
        max_size=settings.MAX_UPLOAD_SIZE,
    )
    dataset_iiif = forms.URLField(
        label="IIIF Manifest URL",
        help_text="The URL to the IIIF manifest of the dataset",
        max_length=500,
        required=False,
    )
    dataset_pdf = ContentRestrictedFileField(
        label="Dataset",
        help_text="A .zip file containing the dataset to be clustered",
        accepted_types=["application/zip"],
        max_size=settings.MAX_UPLOAD_SIZE,
    )
    dataset_name = forms.CharField(
        label="Dataset name",
        help_text="An optional name to identify this dataset",
        max_length=64,
        required=False,
    )

    def __init__(self, *args, **kwargs):
        self.__dataset = kwargs.pop("dataset", None)
        super().__init__(*args, **kwargs)

        if self.__dataset:
            self.fields.pop("dataset_zip")
            self.fields.pop("dataset_name")

    def _populate_instance(self, instance):
        super()._populate_instance(instance)
        if self.__dataset:
            instance.dataset = self.__dataset
        else:
            instance.dataset = ZippedDataset.objects.create(
                zip_file=self.cleaned_data["dataset_zip"],
                name=self.cleaned_data["dataset_name"],
            )


class AbstractTaskOnImageForm(AbstractTaskForm):
    class Meta:
        model = None
        abstract = True
        fields = ("name", "image", "notify_email")

    image = ContentRestrictedFileField(
        label="Upload an image",
        help_text="An image to be processed",
        accepted_types=["image/jpeg", "image/png"],
        max_size=1024 * 1024 * 10,
    )

    def _populate_instance(self, instance):
        super()._populate_instance(instance)
        instance.name = self.cleaned_data["image"].name
