from django.urls import path
from . import views

app_name = "watermarks"

urlpatterns = [
    path("", views.WatermarkProcessingList.as_view(), name="list"),
    path("start", views.WatermarkProcessingStart.as_view(), name="start"),
    path("<uuid:pk>", views.WatermarkProcessingResult.as_view(), name="status"),
    path(
        "<uuid:pk>/progress",
        views.WatermarkProcessingProgress.as_view(),
        name="progress",
    ),
    path("<uuid:pk>/cancel", views.WatermarkProcessingCancel.as_view(), name="cancel"),
    path("<uuid:pk>/watch", views.WatermarkProcessingWatcher.as_view(), name="notify"),
    path("<uuid:pk>/delete", views.WatermarkProcessingDelete.as_view(), name="delete"),
    path("sources/", views.SourcesManageView.as_view(), name="monitor"),
    path("sources/", views.SourcesManageView.as_view(), name="source-manage"),
    path("sources/add/", views.SourcesAddView.as_view(), name="source-add"),
    path("sources/<int:pk>/sim", views.SourcesSimView.as_view(), name="source-sim"),
    path(
        "sources/<int:pk>/change",
        views.SourcesActionView.as_view(),
        name="source-action",
    ),
]
