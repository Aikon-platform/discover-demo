from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView, View, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.contrib import messages
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404, HttpResponse
import json
from typing import Any

from .models import DTIClustering, SavedClustering
from .forms import DTIClusteringForm, SavedClusteringForm

class DTIClusteringStart(LoginRequiredMixin, CreateView):
    """
    Request a clustering
    """
    model = DTIClustering
    template_name = 'dticlustering/start.html'
    form_class = DTIClusteringForm

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        kwargs["user"] = self.request.user

        return kwargs
    
    def get_success_url(self):
        # Start clustering
        self.object.start_clustering()

        return self.object.get_absolute_url()


class DTIClusteringStartFrom(DTIClusteringStart):
    """
    Request a clustering from a previous one
    """
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()

        self.from_dti = DTIClustering.objects.get(id=self.kwargs["pk"])

        kwargs["dataset"] = self.from_dti.dataset
        kwargs["initial"] = {"name": self.from_dti.name}

        return kwargs
    
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["from_dti"] = self.from_dti

        return context
    

class DTIClusteringStatus(LoginRequiredMixin, DetailView):
    """
    Clustering status and results
    """
    model = DTIClustering
    template_name = 'dticlustering/status.html'
    context_object_name = 'clustering'


class DTIClusteringProgress(LoginRequiredMixin, SingleObjectMixin, View):
    """
    Clustering progress (AJAX)
    """
    model = DTIClustering
    context_object_name = 'clustering'

    def get(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        return JsonResponse({
            "is_finished": self.object.is_finished,
            **self.object.get_progress(),
        })


class DTIClusteringCancel(LoginRequiredMixin, DetailView):
    """
    Cancel a clustering
    """
    model = DTIClustering
    template_name = "dticlustering/cancel.html"
    context_object_name = "task"

    def post(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()
        
        self.object.cancel_clustering()

        return redirect(self.object.get_absolute_url())


@method_decorator(csrf_exempt, name='dispatch')
class DTIClusteringWatcher(SingleObjectMixin, View):
    """
    Receive notifications (start, success, error) from a clustering task

    Expects data in the request JSON body
    """
    model = DTIClustering
    context_object_name = "task"

    def post(self, *args, **kwargs):
        object: DTIClustering = self.get_object()

        # check token
        token = self.request.GET.get("token")
        if token != object.get_token():
            return JsonResponse({
                "success": False,
                "error": "Invalid token"
            })

        data = self.request.body.decode("utf-8")
        data = json.loads(data)

        assert data is not None

        object.receive_notification(data)

        return JsonResponse({
            "success": True,
        })

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
            self.from_dti = DTIClustering.objects.get(id=self.kwargs["from_pk"])
        except DTIClustering.DoesNotExist:
            raise Http404()

        initial = kwargs.get("initial", {})
        initial["clustering_data"] = self.from_dti.expanded_results
        kwargs["from_dti"] = self.from_dti

        return kwargs
    
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["from_dti"] = self.from_dti
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
        return super().get_queryset().filter(from_dti=self.kwargs["from_pk"])

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["from_dti"] = self.object.from_dti

        return context
    
class SavedClusteringDelete(LoginRequiredMixin, DeleteView):
    """
    Delete a saved clustering
    """
    model = SavedClustering
    template_name = "dticlustering/delete.html"

    def get_queryset(self):
        return super().get_queryset().filter(from_dti=self.kwargs["from_pk"])

    def get_success_url(self):
        return self.object.from_dti.get_absolute_url()

class SavedClusteringCSVExport(LoginRequiredMixin, SingleObjectMixin, View):
    """
    Export a clustering as CSV
    """
    model = SavedClustering
    template_name = "dticlustering/export.html"
    context_object_name = "clustering"

    def get_queryset(self):
        return super().get_queryset().filter(from_dti=self.kwargs["from_pk"])
    
    def get(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()
        
        # create CSV response
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="clustering.csv"'
        data = self.object.format_as_csv()
        response.write(data)

        return response

class DTIClusteringList(LoginRequiredMixin, ListView):
    """
    List of all clusterings
    """
    model = DTIClustering
    template_name = 'dticlustering/list.html'
    paginate_by = 40

    def get_queryset(self):
        # if user doesn't have dticlustering.monitor right, only show their own clusterings
        qset =  super().get_queryset().order_by("-requested_on").prefetch_related("dataset", "requested_by", "saved_clustering")
        if not self.request.user.has_perm("dticlustering.monitor_dticlustering"):
            qset = qset.filter(requested_by=self.request.user)
        return qset

class DTIClusteringByDatasetList(DTIClusteringList):
    """
    List of all clusterings for a given dataset
    """
    def get_queryset(self):
        return super().get_queryset().filter(dataset__id=self.kwargs["dataset_pk"])
    
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["filter"] = f"DTI clustering of dataset {self.kwargs['dataset_pk']}"

        return context

# SuperUser views
    
class MonitoringView(PermissionRequiredMixin, LoginRequiredMixin, TemplateView):
    """
    Monitoring view
    """
    template_name = "dticlustering/monitoring.html"
    permission_required = 'dticlustering.monitor_dticlustering'

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)

        context["api"] = DTIClustering.get_api_monitoring()
        context["frontend"] = DTIClustering.get_frontend_monitoring()

        return context
    
class ClearOldClusterings(PermissionRequiredMixin, LoginRequiredMixin, View):
    """
    Clear old clusterings
    """
    permission_required = 'dticlustering.monitor_dticlustering'

    def post(self, *args, **kwargs):
        output = DTIClustering.clear_old_clusterings()

        if output is None or output.get("error"):
            messages.error(self.request, output["error"] if output else "Unknown error when clearing old clusterings")
        else:
            messages.success(self.request, f"Deleted {output.get('cleared_clusterings', 0)} clustering results and {output.get('cleared_datasets', 0)} datasets")

        return redirect("dticlustering:monitor")
    
class ClearAPIOldClusterings(PermissionRequiredMixin, LoginRequiredMixin, View):
    """
    Clear old clusterings from the API server
    """
    permission_required = 'dticlustering.monitor_dticlustering'

    def post(self, *args, **kwargs):
        output = DTIClustering.clear_api_old_clusterings()

        if output is None or output.get("error"):
            messages.error(self.request, output["error"] if output else "Unknown error when clearing old clusterings")
        else:
            messages.success(self.request, f"Deleted {output.get('cleared_runs', 0)} clustering runs, {output.get('cleared_results', 0)} results and {output.get('cleared_datasets', 0)} datasets")

        return redirect("dticlustering:monitor")
