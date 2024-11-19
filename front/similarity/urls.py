from django.urls import path
from .views import *

app_name = "similarity"

urlpatterns = [
    path("", SimilarityMixin.List.as_view(), name="list"),
    path("start", SimilarityMixin.Start.as_view(), name="start"),
    path("<uuid:pk>", SimilarityMixin.Status.as_view(), name="status"),
    path("<uuid:pk>/progress", SimilarityMixin.Progress.as_view(), name="progress"),
    path("<uuid:pk>/cancel", SimilarityMixin.Cancel.as_view(), name="cancel"),
    path("<uuid:pk>/watch", SimilarityMixin.Watcher.as_view(), name="notify"),
    path("<uuid:pk>/restart", SimilarityMixin.StartFrom.as_view(), name="restart"),
    # path("<uuid:pk>/download", SimilarityDownload.as_view(), name="download"),
    path("<uuid:pk>/delete", SimilarityMixin.Delete.as_view(), name="delete"),
    # Admin views
    path(
        "dataset/<uuid:dataset_pk>",
        SimilarityMixin.ByDatasetList.as_view(),
        name="list_perdataset",
    ),
    path("monitor", SimilarityMixin.Monitor.as_view(), name="monitor"),
    path(
        "monitor/clear/front",
        SimilarityMixin.ClearOld.as_view(),
        name="monitor_clear_front",
    ),
    path(
        "monitor/clear/api",
        SimilarityMixin.ClearAPIOld.as_view(),
        name="monitor_clear_api",
    ),
]
