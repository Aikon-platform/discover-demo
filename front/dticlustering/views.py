from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView, View
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse, Http404
import json
from typing import Any

from .models import DTIClustering, SavedClustering
from .forms import DTIClusteringForm, SavedClusteringForm

class DTIClusteringStart(CreateView):
    """
    Request a clustering
    """
    model = DTIClustering
    template_name = 'dticlustering/start.html'
    form_class = DTIClusteringForm
    
    def get_success_url(self):
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
    

class DTIClusteringStatus(DetailView):
    """
    Clustering status and results
    """
    model = DTIClustering
    template_name = 'dticlustering/status.html'
    context_object_name = 'clustering'


class DTIClusteringProgress(SingleObjectMixin, View):
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


class DTIClusteringCancel(DetailView):
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


class DTIClusteringList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """
    List of all clusterings [for admins]
    """
    model = DTIClustering
    template_name = 'dticlustering/list.html'
    permission_required = 'dticlustering.view_dticlustering'


class SavedClusteringFromDTI(CreateView):
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


class SavedClusteringEdit(UpdateView):
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
    