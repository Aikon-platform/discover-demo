from django.urls import path
from .views import *

app_name = "regions"

urlpatterns = [
    path("", RegionsList.as_view(), name="list"),
    path("start", RegionsStart.as_view(), name="start"),
    path("<uuid:pk>", RegionsStatus.as_view(), name="status"),
    path("<uuid:pk>/progress", RegionsProgress.as_view(), name="progress"),
    path("<uuid:pk>/cancel", RegionsCancel.as_view(), name="cancel"),
    path("<uuid:pk>/watch", RegionsWatcher.as_view(), name="notify"),
    path("<uuid:pk>/restart", RegionsStartFrom.as_view(), name="restart"),
    path("<uuid:pk>/delete", RegionsDelete.as_view(), name="delete"),
    # Admin views
    path(
        "dataset/<uuid:dataset_pk>",
        RegionsByDatasetList.as_view(),
        name="list_perdataset",
    ),
    path("monitor", RegionsMonitor.as_view(), name="monitor"),
    path("monitor/clear/front", ClearOldRegions.as_view(), name="monitor_clear_front"),
    path("monitor/clear/api", ClearAPIOldRegions.as_view(), name="monitor_clear_api"),
]
