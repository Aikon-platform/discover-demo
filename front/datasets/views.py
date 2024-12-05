from typing import Any

from django.contrib.auth import get_user_model
from django.views.generic import ListView, DetailView
from django.shortcuts import redirect
from django.urls import reverse

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
        context["task_name"] = "dataset"
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


class DatasetDeleteView(DatasetMixin, LoginRequiredIfConfProtectedMixin, DetailView):
    """
    Delete a task
    """

    template_name = "tasking/delete.html"

    def get_extra_warning(self):
        task_nb = 0
        task_html = "<ul>"
        for status, task_list in self.object.get_tasks_by_prop("status").items():
            task_list = [f"{task} #{task.id}" for task in task_list]
            task_nb += len(task_list)
            task_html += f"<li><span class='tag status status-{status}'>{status}</span> {'<br>'.join(task_list)}</li>"
        task_html += "</ul>"
        return f"This dataset is used in <b>{task_nb} task(s)</b>: {task_html}"

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["extra_warning"] = self.get_extra_warning()
        return context

    def post(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        self.object.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        if hasattr(self, "success_url"):
            return self.success_url
        return reverse(f"datasets:list")
