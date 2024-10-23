from django.urls import path
from .views import *

app_name = "regions"

urlpatterns = [
    path("new", RegionsStart.as_view(), name="start"),
    path("", RegionsList.as_view(), name="list"),
    # path("<uuid:pk>", RegionsStatus.as_view(), name="status"),
    path("monitor", RegionsMonitor.as_view(), name="monitor"),
]
