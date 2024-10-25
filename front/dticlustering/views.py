from django.views.generic import (
    DetailView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
    TemplateView,
)
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.http import JsonResponse, Http404, HttpResponse
from typing import Any

from tasking.views import *

from .models import DTIClustering, SavedClustering
from .forms import DTIClusteringForm, SavedClusteringForm


class DTIClusteringMixin:
    """
    Mixin for DTI clustering views
    """

    model = DTIClustering
    form_class = DTIClusteringForm
    task_name = "DTI Clustering"
    app_name = "dticlustering"


class DTIClusteringStart(DTIClusteringMixin, TaskStartView):
    pass


class DTIClusteringStartFrom(TaskStartFromView):
    # """
    # Request a clustering from a previous one
    # """
    #
    # def get_form_kwargs(self):
    #     kwargs = super().get_form_kwargs()
    #     self.from_task = DTIClustering.objects.get(id=self.kwargs["pk"])
    #     kwargs["dataset"] = self.from_task.dataset
    #     kwargs["initial"] = {"name": self.from_task.name}
    #
    #     return kwargs
    #
    # def get_context_data(self, **kwargs) -> dict[str, Any]:
    #     context = super().get_context_data(**kwargs)
    #     context["task_name"] = self.task_name
    #     context["from_task"] = self.from_task
    #     return context
    pass


class DTIClusteringStatus(DTIClusteringMixin, TaskStatusView):
    pass


class DTIClusteringProgress(DTIClusteringMixin, TaskProgressView):
    pass


class DTIClusteringCancel(DTIClusteringMixin, TaskCancelView):
    pass


class DTIClusteringWatcher(DTIClusteringMixin, TaskWatcherView):
    pass


class DTIClusteringDelete(DTIClusteringMixin, TaskDeleteView):
    pass


class DTIClusteringList(DTIClusteringMixin, TaskListView):
    permission_see_all = "dticlustering.monitor_dticlustering"

    def get_queryset(self):
        return super().get_queryset().prefetch_related("dataset")


class DTIClusteringByDatasetList(TaskByDatasetList):
    permission_see_all = "dticlustering.monitor_dticlustering"

    # """
    # DTIClusteringList
    # List of all clusterings for a given dataset [for admins]
    # """
    #
    # def get_queryset(self):
    #     return super().get_queryset().filter(dataset__id=self.kwargs["dataset_pk"])
    #
    # def get_context_data(self, **kwargs) -> dict[str, Any]:
    #     context = super().get_context_data(**kwargs)
    #
    #     context["filter"] = f"DTI clustering of dataset {self.kwargs['dataset_pk']}"
    #
    #     return context
    pass


class SavedClusteringFromDTI(LoginRequiredMixin, CreateView):
    """
    Create a saved clustering from a DTI
    """

    model = DTIClustering
    form_class = SavedClusteringForm
    template_name = "dticlustering/saved.html"

    def get_form_kwargs(self) -> dict[str, Any]:
        kwargs = super().get_form_kwargs()

        try:
            self.from_task = DTIClustering.objects.get(id=self.kwargs["from_pk"])
        except DTIClustering.DoesNotExist:
            raise Http404()

        initial = kwargs.get("initial", {})
        initial["clustering_data"] = self.from_task.expanded_results
        kwargs["from_task"] = self.from_task

        return kwargs

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["from_task"] = self.from_task
        context["editing"] = True

        return context


class SavedClusteringEdit(LoginRequiredMixin, UpdateView):
    """
    Show/edit a clustering
    """

    model = SavedClustering
    template_name = "dticlustering/saved.html"
    form_class = SavedClusteringForm

    def get_queryset(self):
        return super().get_queryset().filter(from_task=self.kwargs["from_pk"])

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["from_task"] = self.object.from_task

        return context


class SavedClusteringDelete(LoginRequiredMixin, DeleteView):
    """
    Delete a saved clustering
    TODO make abstract class out of it
    """

    model = SavedClustering
    template_name = "tasking/delete.html"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["task_name"] = "DTI Clustering"
        return context

    def get_queryset(self):
        return super().get_queryset().filter(from_task=self.kwargs["from_pk"])

    def get_success_url(self):
        return self.object.from_task.get_absolute_url()


class SavedClusteringCSVExport(LoginRequiredMixin, SingleObjectMixin, View):
    """
    Export a clustering as CSV
    """

    model = SavedClustering
    template_name = "dticlustering/export.html"
    context_object_name = "clustering"

    def get_queryset(self):
        return super().get_queryset().filter(from_task=self.kwargs["from_pk"])

    def get(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        # create CSV response
        response = HttpResponse(content_type="text/csv")
        response["Content-Disposition"] = 'attachment; filename="clustering.csv"'
        data = self.object.format_as_csv()
        response.write(data)

        return response


# SuperUser views


class MonitoringView(DTIClusteringMixin, TaskMonitoringView):
    # template_name = "tasking/monitoring.html"
    permission_required = "dticlustering.monitor_dticlustering"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["api"] = DTIClustering.get_api_monitoring()
        context["frontend"] = DTIClustering.get_frontend_monitoring()
        return context


class ClearOldClusterings(PermissionRequiredMixin, LoginRequiredMixin, View):
    """
    Clear old clusterings
    TODO make abstract class out of it
    """

    permission_required = "dticlustering.monitor_dticlustering"

    def post(self, *args, **kwargs):
        output = DTIClustering.clear_old_clusterings()

        if output is None or output.get("error"):
            messages.error(
                self.request,
                output["error"]
                if output
                else "Unknown error when clearing old clusterings",
            )
        else:
            messages.success(
                self.request,
                f"Deleted {output.get('cleared_clusterings', 0)} clustering results and {output.get('cleared_datasets', 0)} datasets",
            )

        return redirect("dticlustering:monitor")


class ClearAPIOldClusterings(PermissionRequiredMixin, LoginRequiredMixin, View):
    """
    Clear old clusterings from the API server
    TODO make abstract class out of it
    """

    permission_required = "dticlustering.monitor_dticlustering"

    def post(self, *args, **kwargs):
        output = DTIClustering.clear_api_old_tasks()

        if output is None or output.get("error"):
            messages.error(
                self.request,
                output["error"]
                if output
                else "Unknown error when clearing old clusterings",
            )
        else:
            messages.success(
                self.request,
                f"Deleted {output.get('cleared_runs', 0)} clustering runs, {output.get('cleared_results', 0)} results and {output.get('cleared_datasets', 0)} datasets",
            )

        return redirect("dticlustering:monitor")
