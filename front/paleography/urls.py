from django.urls import path
from .views import *

app_name = "paleography"

urlpatterns = [
    path("", PaleographyMixin.List.as_view(), name="list"),
    path("start", PaleographyMixin.Start.as_view(), name="start"),
    path("<uuid:pk>", PaleographyStatus.as_view(), name="status"),
    path("<uuid:pk>/progress", PaleographyMixin.Progress.as_view(), name="progress"),
    path("<uuid:pk>/cancel", PaleographyMixin.Cancel.as_view(), name="cancel"),
    path("<uuid:pk>/watch", PaleographyMixin.Watcher.as_view(), name="notify"),
    path("<uuid:pk>/restart", PaleographyMixin.StartFrom.as_view(), name="restart"),
    path("<uuid:pk>/delete", PaleographyMixin.Delete.as_view(), name="delete"),
    path(
        "dataset/<uuid:dataset_pk>",
        PaleographyMixin.ByDatasetList.as_view(),
        name="list_perdataset",
    ),
    path("monitor", PaleographyMixin.Monitor.as_view(), name="monitor"),
    path(
        "monitor/clear/front",
        PaleographyMixin.ClearOld.as_view(),
        name="monitor_clear_front",
    ),
    # NB: pas de route "monitor/clear/api" ni "download_*" : spécifiques aux tâches
    # API / à regions, hors périmètre paléographie.
]
