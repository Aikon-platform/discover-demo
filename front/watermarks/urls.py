from django.urls import path
from .views import WatermarkQueryView, WatermarkResultView

app_name = "watermarks"

urlpatterns = [
    path("", WatermarkQueryView.as_view(), name="start"),
    path("detect/<uuid:pk>/", WatermarkResultView.as_view(), name="detect-result"),
]
