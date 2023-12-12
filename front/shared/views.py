from django.views.generic import TemplateView, UpdateView, ListView, View, DeleteView, CreateView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib.auth import get_user_model
from django.contrib.auth.views import PasswordResetView
from django.urls import reverse_lazy
from django.shortcuts import redirect
from django.conf import settings
from django.contrib.admin.utils import NestedObjects

from typing import Any, Dict

from .forms import AccountRequestForm, AccountEditForm
from .mails import send_activation_email

User = get_user_model()

class HomeView(TemplateView):
    template_name = "demowebsite/home.html"


class AccountsAdminMixin(PermissionRequiredMixin, LoginRequiredMixin):
    """
    Mixin for views that required the user special permission to access
    """
    permission_required = "auth.add_user"


class AccountRequestView(CreateView):
    """
    Request an account
    """
    template_name = "registration/request.html"
    form_class = AccountRequestForm
    success_url = reverse_lazy("account_created")

class AccountCreatedView(TemplateView):
    """
    Account created
    """
    template_name = "registration/created.html"

    def get_context_data(self, **kwargs) -> Dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["account_needs_approval"] = getattr(settings, "ACCOUNT_NEEDS_APPROVAL", False)
        return context

class AccountView(LoginRequiredMixin, TemplateView):
    """
    User account page
    """
    template_name = "registration/account.html"

class AccountEditView(LoginRequiredMixin, UpdateView):
    """
    Edit user's own account
    """
    template_name = "registration/edit.html"
    form_class = AccountEditForm
    success_url = reverse_lazy("account")

    def get_object(self, *args, **kwargs):
        return self.request.user

class PasswordResetView(PasswordResetView):
    """
    Password reset view
    """
    email_template_name = "registration/mails/password_reset_body.txt"
    subject_template_name = "registration/mails/password_reset_subject.txt"
    

# ADMIN VIEWS

class AccountsAdminView(AccountsAdminMixin, ListView):
    """
    List accounts and account requests
    """
    template_name = "registration/admin.html"
    model = User

    def get_queryset(self, *args, **kwargs):
        return (
            User.objects
                .filter(is_active=True)
                .order_by("username")
        )
    
    def get_context_data(self, *args, **kwargs):
        context = super().get_context_data(*args, **kwargs)
        context["pending_list"] = (
            User.objects
                .filter(is_active=False)
                .order_by("-date_joined")
                .prefetch_related("request")
        )
        return context

class AccountsValidateView(AccountsAdminMixin, SingleObjectMixin, View):
    """
    Validate an account request
    """
    model = User
    
    def get_queryset(self, *args, **kwargs):
        return User.objects.filter(is_active=False)
    
    def post(self, request, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()
        user = self.object
        user.is_active = True
        user.set_password(User.objects.make_random_password(length=24))
        user.save()

        send_activation_email(user)

        return redirect(reverse_lazy("accounts_admin"))
        
class AccountsRequestDeleteView(AccountsAdminMixin, DeleteView):
    """
    Delete an account request
    """
    model = User
    template_name = "registration/delete_request.html"
    success_url = reverse_lazy("accounts_admin")

    def get_queryset(self, *args, **kwargs):
        return User.objects.filter(is_active=False)

class AccountsDeleteView(AccountsAdminMixin, DeleteView):
    """
    Delete an account
    """
    model = User
    permission_required = "auth.delete_user"
    template_name = "registration/delete.html"
    success_url = reverse_lazy("accounts_admin")

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        nested = NestedObjects("default")
        nested.collect([self.object])

        def pprint(l, prefix=""):
            ret = ""
            for i in l:
                if isinstance(i, list):
                    ret += pprint(i, " "+prefix) + "\n"
                else:
                    ret += prefix + i.__class__.__name__ + " " + str(i) + "\n"
            return ret
        context["deleting"] = pprint(nested.nested())
        
        return context
