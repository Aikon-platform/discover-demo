from typing import Any

from django.contrib.auth import get_user_model
from django.views.generic import ListView

from tasking.views import LoginRequiredIfConfProtectedMixin, TaskMixin
from .forms import DatasetForm
from .models import Dataset

User = get_user_model()


class DatasetMixin:
    """
    Mixin for Dataset views
    """

    model = Dataset
    form_class = DatasetForm
    task_name = "Dataset"
    app_name = "datasets"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # context["foo"] = "bar"
        return context


class DatasetListView(DatasetMixin, LoginRequiredIfConfProtectedMixin, ListView):
    """
    List of all tasks
    """

    template_name = "datasets/list.html"
    paginate_by = 40
    permission_see_all = "datasets.monitor_datasets"

    def get_queryset(self):
        # if user doesn't have task.monitor right, only show their own experiments
        qset = (
            super()
            .get_queryset()
            .order_by("-created_on")
            .prefetch_related("created_by")
        )
        if not self.request.user.is_authenticated:
            return qset.none()
        if not self.request.user.has_perm(self.permission_see_all):
            qset = qset.filter(requested_by=self.request.user)
        return qset
