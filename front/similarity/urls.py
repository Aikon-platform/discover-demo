from django.urls import path
from .views import *

app_name = "similarity"

urlpatterns = [
    path("", SimilarityStart.as_view(), name="start"),
]
