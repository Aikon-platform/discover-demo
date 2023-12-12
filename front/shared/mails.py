from django.conf import settings
from django.core.mail import send_mail
from django.contrib.auth import get_user_model
from django.db.models import Q
from django.urls import reverse
from django.contrib.auth.forms import PasswordResetForm
from django.template import loader

User = get_user_model()

def send_activation_email(user: User):
    form = PasswordResetForm({"email": user.email})
    form.is_valid()
    form.save(
        subject_template_name="registration/mails/activation_subject.txt",
        email_template_name="registration/mails/activation_body.txt",
        domain_override=settings.BASE_URL,
        use_https=True,
    )

def send_application_email(user: User):
    context = {
        "email": user.email,
        "user": user
    }
    subject = loader.render_to_string("registration/mails/activation_subject.txt", context)
    # Email subject *must not* contain newlines
    subject = "".join(subject.splitlines())
    body = loader.render_to_string("registration/mails/application_body.txt", context)

    send_mail(
        subject,
        body,
        settings.DEFAULT_FROM_EMAIL,
        [user.email],
        fail_silently=False
    )

def send_newaccount_notification(user):
    # send mails to users with perm auth.add_user to notify them that someone requested an account
    for admin_user in User.objects.filter(Q(groups__permissions__codename="add_user")|Q(user_permissions__codename="add_user")).distinct():
        send_mail(
            "[Discover Demo] User Account requested",
            ("Dear {nom},\n\n"
            "A new account request was submitted by {username}.\n"
            "Please review it on the admin page at {url}.\n\n"
            "Best regards,\n"
            "The Discover team").format(
                nom=admin_user.first_name,
                username=user.username,
                url=settings.BASE_URL + reverse("accounts_admin")
            ),
            settings.DEFAULT_FROM_EMAIL,
            [admin_user.email],
            fail_silently=True
        )