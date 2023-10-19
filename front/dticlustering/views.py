from django.views.generic import DetailView, ListView, CreateView, UpdateView, DeleteView
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import DTIClustering
from .forms import DTIClusteringForm

# Request a clustering
class DTIClusteringStart(CreateView):
    """
    Request a clustering
    """
    model = DTIClustering
    template_name = 'dticlustering/start.html'
    
    def get_success_url(self):
        return self.object.get_absolute_url()
    
# Cancel a clustering
class DTIClusteringCancel(DetailView):
    """
    Generic page to cancel a task
    """
    template_name = "vcontagions/tasking/task_cancel.html"
    context_object_name = "task"

    def post(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()
        self.object.cancel_celery_jobs()
        return redirect(self.object.get_absolute_url())

# Admin: List all clusterings
class DTIClusteringList(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    model = DTIClustering
    template_name = 'dticlustering/list.html'
    permission_required = 'dticlustering.view_dticlustering'
