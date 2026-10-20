from django.urls import path
from .views import *

app_name = "search"

urlpatterns = [
    path("", SearchHomeView.as_view(), name="home"),
    path("indexing", IndexingMixin.List.as_view(), name="indexing_list"),
    path("indexing/start", IndexingMixin.Start.as_view(), name="indexing_start"),
    path("indexing/<uuid:pk>", IndexingStatusView.as_view(), name="indexing_status"),
    path(
        "indexing/<uuid:pk>/progress",
        IndexingMixin.Progress.as_view(),
        name="indexing_progress",
    ),
    path(
        "indexing/<uuid:pk>/cancel",
        IndexingMixin.Cancel.as_view(),
        name="indexing_cancel",
    ),
    path(
        "indexing/<uuid:pk>/watch",
        IndexingMixin.Watcher.as_view(),
        name="indexing_notify",
    ),
    path(
        "indexing/<uuid:pk>/restart",
        IndexingMixin.StartFrom.as_view(),
        name="indexing_restart",
    ),
    path(
        "indexing/<uuid:pk>/delete",
        IndexingMixin.Delete.as_view(),
        name="indexing_delete",
    ),
    path("index/<uuid:pk>/edit", IndexEditView.as_view(), name="index_edit"),
    path("query", QueryMixin.List.as_view(), name="query_list"),
    path("query/start", QueryStartView.as_view(), name="query_start"),
    path("query/<uuid:pk>", QueryMixin.Status.as_view(), name="query_status"),
    path(
        "query/<uuid:pk>/progress", QueryMixin.Progress.as_view(), name="query_progress"
    ),
    path("query/<uuid:pk>/cancel", QueryMixin.Cancel.as_view(), name="query_cancel"),
    path("query/<uuid:pk>/watch", QueryMixin.Watcher.as_view(), name="query_notify"),
    path("query/<uuid:pk>/restart", QueryStartFromView.as_view(), name="query_restart"),
    path("query/<uuid:pk>/delete", QueryMixin.Delete.as_view(), name="query_delete"),
    # Admin views
    path(
        "indexing/dataset/<uuid:dataset_pk>",
        IndexingMixin.ByDatasetList.as_view(),
        name="indexing_list_perdataset",
    ),
    path("indexing/monitor", IndexingMixin.Monitor.as_view(), name="indexing_monitor"),
    path(
        "indexing/monitor/clear",
        IndexingMixin.ClearOld.as_view(),
        name="indexing_monitor_clear",
    ),
    path(
        "indexing/monitor/clear/api",
        IndexingMixin.ClearAPIOld.as_view(),
        name="indexing_monitor_clear_api",
    ),
    path(
        "indexing/dataset/<uuid:dataset_pk>",
        QueryMixin.ByDatasetList.as_view(),
        name="query_list_perdataset",
    ),
    path("query/monitor", QueryMixin.Monitor.as_view(), name="query_monitor"),
    path(
        "query/monitor/clear",
        QueryMixin.ClearOld.as_view(),
        name="query_monitor_clear",
    ),
    path(
        "query/monitor/clear/api",
        QueryMixin.ClearAPIOld.as_view(),
        name="query_monitor_clear_api",
    ),
]
