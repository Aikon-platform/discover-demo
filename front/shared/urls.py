from django.urls import path

from .views import *

urlpatterns = [
    path('', HomeView.as_view(), name='home'),

    path('accounts/request/', AccountRequestView.as_view(),
        name="account_request"),
    path('accounts/created/', AccountCreatedView.as_view(),
        name="account_created"),
    path('accounts/profile/', AccountView.as_view(),
        name="account"),
    path('accounts/edit/', AccountEditView.as_view(),
        name="account_edit"),
    path('accounts/admin/', AccountsAdminView.as_view(),
        name="accounts_admin"),
    path('accounts/<int:pk>/validate/', AccountsValidateView.as_view(),
        name="accounts_validate"),
    path('accounts/<int:pk>/reject/', AccountsRequestDeleteView.as_view(),
        name="accounts_reject"),
    path('accounts/<int:pk>/delete/', AccountsDeleteView.as_view(),
        name="accounts_delete"),
]