from django.urls import path
from .views import *

app_name = "pipelines"

urlpatterns = [
    path("", PipelineList.as_view(), name="list"),
    path("start", PipelineMixin.Start.as_view(), name="start"),
    path("<uuid:pk>", PipelineMixin.Status.as_view(), name="status"),
    path("<uuid:pk>/progress", PipelineMixin.Progress.as_view(), name="progress"),
    path("<uuid:pk>/cancel", PipelineMixin.Cancel.as_view(), name="cancel"),
    path("<uuid:pk>/watch", PipelineMixin.Watcher.as_view(), name="notify"),
    path("<uuid:pk>/restart", PipelineMixin.StartFrom.as_view(), name="restart"),
    path("<uuid:pk>/delete", PipelineMixin.Delete.as_view(), name="delete"),
    # Admin views
    path(
        "dataset/<uuid:dataset_pk>",
        PipelineMixin.ByDatasetList.as_view(),
        name="list_perdataset",
    ),
    path("monitor", PipelineMixin.Monitor.as_view(), name="monitor"),
    path(
        "monitor/clear/front",
        PipelineMixin.ClearOld.as_view(),
        name="monitor_clear_front",
    ),
]
