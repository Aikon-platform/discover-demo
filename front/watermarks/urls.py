from django.urls import path
from .views import WatermarkQueryView, WatermarkResultView, ManageSourcesView, AddSourceView

app_name = "watermarks"

urlpatterns = [
    path("", WatermarkQueryView.as_view(), name="start"),
    path("detect/<uuid:pk>/", WatermarkResultView.as_view(), name="detect-result"),

    path("sources/", ManageSourcesView.as_view(), name="manage-sources"),
    path("sources/add/", AddSourceView.as_view(), name="add-source"),
]
