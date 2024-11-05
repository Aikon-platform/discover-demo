from django.urls import path
from .views import *

app_name = "watermarks"

urlpatterns = [
    path("", WatermarkProcessingList.as_view(), name="list"),
    path("start", WatermarkProcessingStart.as_view(), name="start"),
    path("<uuid:pk>", WatermarkProcessingResult.as_view(), name="status"),
    path(
        "<uuid:pk>/progress",
        WatermarkProcessingProgress.as_view(),
        name="progress",
    ),
    path("<uuid:pk>/cancel", WatermarkProcessingCancel.as_view(), name="cancel"),
    path("<uuid:pk>/watch", WatermarkProcessingWatcher.as_view(), name="notify"),
    path("<uuid:pk>/delete", WatermarkProcessingDelete.as_view(), name="delete"),
    path("sources/", SourcesManageView.as_view(), name="monitor"),
    path("sources/", SourcesManageView.as_view(), name="source-manage"),
    path("sources/add/", SourcesAddView.as_view(), name="source-add"),
    path("sources/<int:pk>/sim", SourcesSimView.as_view(), name="source-sim"),
    path(
        "sources/<int:pk>/change",
        SourcesActionView.as_view(),
        name="source-action",
    ),
]
