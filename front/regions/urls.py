from django.urls import path
from .views import *

app_name = "regions"

urlpatterns = [
    path("", RegionsStart.as_view(), name="start"),
]
