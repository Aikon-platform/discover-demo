from django.urls import path
from .views import *

app_name = "regions"

urlpatterns = [
    path("", RegionsList.as_view(), name="list"),
    path("start", RegionsMixin.Start.as_view(), name="start"),
    path("<uuid:pk>", RegionsMixin.Status.as_view(), name="status"),
    path("<uuid:pk>/progress", RegionsMixin.Progress.as_view(), name="progress"),
    path("<uuid:pk>/cancel", RegionsMixin.Cancel.as_view(), name="cancel"),
    path("<uuid:pk>/watch", RegionsMixin.Watcher.as_view(), name="notify"),
    path("<uuid:pk>/restart", RegionsMixin.StartFrom.as_view(), name="restart"),
    path("<uuid:pk>/download", RegionsDownload.as_view(), name="download"),
    path("<uuid:pk>/delete", RegionsMixin.Delete.as_view(), name="delete"),
    # Admin views
    path(
        "dataset/<uuid:dataset_pk>",
        RegionsMixin.ByDatasetList.as_view(),
        name="list_perdataset",
    ),
    path("monitor", RegionsMixin.Monitor.as_view(), name="monitor"),
    path(
        "monitor/clear/front",
        RegionsMixin.ClearOld.as_view(),
        name="monitor_clear_front",
    ),
    path(
        "monitor/clear/api",
        RegionsMixin.ClearAPIOld.as_view(),
        name="monitor_clear_api",
    ),
]
