from dataclasses import dataclass
from typing import Type

from django import forms
from django.conf import settings
from django.contrib.auth import get_user_model

from .mails import (
    send_activation_email,
    send_application_email,
    send_newaccount_notification,
)

User = get_user_model()


@dataclass
class FormConfig:
    display_name: str
    description: str
    form_class: Type[forms.Form]


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
