from django.urls import path
from .views import *

app_name = "similarity"

urlpatterns = [
    path("", SimilarityList.as_view(), name="list"),
]
