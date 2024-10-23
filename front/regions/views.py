from typing import Any

from django.views.generic import (
    DetailView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
    TemplateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .forms import RegionsForm
from .models import Regions
from tasking.views import (
    TaskStartView,
    TaskStatusView,
    TaskProgressView,
    TaskCancelView,
    TaskWatcherView,
    TaskDeleteView,
    TaskListView,
)


class RegionsMixin:
    """
    Mixin for Regions extractions views
    """

    model = Regions
    form_class = RegionsForm
    task_name = "Regions Extraction"
    app_name = "regions"


class RegionsStart(RegionsMixin, TaskStartView):
    pass


class RegionsList(RegionsMixin, TaskListView):
    # permission_see_all = "dticlustering.monitor_dticlustering"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("dataset")


class RegionsMonitor(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    """
    Monitoring view
    """

    template_name = "tasking/monitoring.html"
    permission_required = "regions.monitor_regions"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["app_name"] = "regions"
        context["task_name"] = "Regions extraction"
        # context["api"] = Regions.get_api_monitoring()
        # context["frontend"] = Regions.get_frontend_monitoring()
        return context
