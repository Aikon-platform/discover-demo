from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView, View
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from django.shortcuts import redirect
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
from django.http import JsonResponse

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
            "status": self.object.status,
            "is_finished": self.object.is_finished,
            "log": self.object.get_progress(),
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
class DTIClusteringCallback(SingleObjectMixin, View):
    """
    Generic page to handle a callback from a terminated clustering task
    """
    model = DTIClustering
    context_object_name = "task"

    def post(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        self.object.terminate_clustering(self.request.POST)

        return JsonResponse({
            "success": True,
        })

# Admin: List all clusterings
class DTIClusteringList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = DTIClustering
    template_name = 'dticlustering/list.html'
    permission_required = 'dticlustering.view_dticlustering'
