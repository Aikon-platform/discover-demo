from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from typing import Any
import traceback
from django.shortcuts import redirect

from tasking.views import (
    TaskStartView,
    TaskStatusView,
    TaskProgressView,
    TaskCancelView,
    TaskWatcherView,
    TaskDeleteView,
    TaskListView,
)

from .models import WatermarkProcessing, WatermarksSource
from .forms import WatermarkProcessingForm


class WatermarkProcessingMixin:
    """
    Mixin for DTI clustering views
    """

    model = WatermarkProcessing
    form_class = WatermarkProcessingForm
    task_name = "Watermark Analysis"


class WatermarkProcessingStart(WatermarkProcessingMixin, TaskStartView):
    pass


class WatermarkProcessingResult(WatermarkProcessingMixin, TaskStatusView):
    model = WatermarkProcessing
    template_name = "watermarks/detection.html"
    context_object_name = "detection"

    def get_queryset(self):
        return super().get_queryset().filter(requested_by=self.request.user)

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = WatermarkProcessingForm(user=self.request.user)
        return context


class WatermarkProcessingProgress(WatermarkProcessingMixin, TaskProgressView):
    pass


class WatermarkProcessingCancel(WatermarkProcessingMixin, TaskCancelView):
    pass


class WatermarkProcessingWatcher(WatermarkProcessingMixin, TaskWatcherView):
    pass


class WatermarkProcessingDelete(WatermarkProcessingMixin, TaskDeleteView):
    pass


class WatermarkProcessingList(WatermarkProcessingMixin, TaskListView):
    permission_see_all = "WatermarkProcessing.monitor_WatermarkProcessing"


# ADMIN


class SourcesManageView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """
    Monitoring view
    """

    permission_required = "watermarks.monitor_watermarks"
    template_name = "watermarks/sources.html"
    context_object_name = "sources"
    model = WatermarksSource

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        try:
            known_sources = {source.uid for source in self.object_list}
            context["extra_sources"] = [
                source
                for source in WatermarksSource.get_available_sources()
                if source["uid"] not in known_sources
            ]
        except Exception as e:
            context["api_error"] = traceback.format_exc(1)
        return context


class SourcesAddView(
    PermissionRequiredMixin, LoginRequiredMixin, SingleObjectMixin, View
):
    """
    Add a new source
    """

    permission_required = "watermarks.monitor_watermarks"
    model = WatermarksSource

    def post(self, request, *args, **kwargs):
        source = WatermarksSource.from_api(request.POST["uid"])
        source.download_images()
        return redirect(reverse_lazy("watermarks:source-manage"))
