from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView, View
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse
import json
from typing import Any

from .models import DTIClustering
from .forms import DTIClusteringForm

# Request a clustering
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
    
# Start new clustering from previous one
class DTIClusteringStartFrom(DTIClusteringStart):
    """
    Request a clustering from a previous one
    """
    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.fromdti = DTIClustering.objects.get(id=self.kwargs["pk"])
        kwargs["dataset"] = self.fromdti.dataset
        return kwargs
    
    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["fromdti"] = self.fromdti
        return context
    

# Clustering status
class DTIClusteringStatus(DetailView):
    """
    Clustering status
    """
    model = DTIClustering
    template_name = 'dticlustering/status.html'
    context_object_name = 'clustering'

class DTIClusteringProgress(SingleObjectMixin, View):
    """
    Clustering progress
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


# Cancel a clustering
class DTIClusteringCancel(DetailView):
    """
    Generic page to cancel a task
    """
    model = DTIClustering
    template_name = "dticlustering/cancel.html"
    context_object_name = "task"

    def post(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()
        self.object.cancel_clustering()
        return redirect(self.object.get_absolute_url())
    
# Clustering callback
@method_decorator(csrf_exempt, name='dispatch')
class DTIClusteringWatcher(SingleObjectMixin, View):
    """
    Generic page to handle a notification from a clustering task

    Expects data in the JSON body
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

# Admin: List all clusterings
class DTIClusteringList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = DTIClustering
    template_name = 'dticlustering/list.html'
    permission_required = 'dticlustering.view_dticlustering'
