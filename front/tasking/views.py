from typing import Any
from django.views.generic import CreateView, DetailView, View, ListView, TemplateView
from django.views.generic.detail import SingleObjectMixin
from django.conf import settings
from django.contrib import messages
from django.contrib.auth.mixins import AccessMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json

LOGIN_REQUIRED = getattr(settings, "LOGIN_REQUIRED", True)


class LoginRequiredIfConfProtectedMixin(AccessMixin):
    """
    Mixin for views that require login if LOGIN_REQUIRED is True
    """

    def dispatch(self, request, *args, **kwargs):
        if self.request.user.is_authenticated or not LOGIN_REQUIRED:
            return super().dispatch(request, *args, **kwargs)
        return self.handle_no_permission()


class TaskMixin:
    app_name = None
    task_name = None
    model = None
    form_class = None

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["task_name"] = getattr(self, "task_name", self.model._meta.verbose_name)
        context["app_name"] = self.model.django_app_name
        return context


class TaskStartView(LoginRequiredIfConfProtectedMixin, TaskMixin, CreateView):
    template_name = "tasking/start.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = (
            self.request.user if self.request.user.is_authenticated else None
        )
        return kwargs

    def get_success_url(self):
        # Start task
        self.object.start_task()

        return self.object.get_absolute_url()


class TaskStartFromView(TaskStartView):
    """
    Request a task using same dataset as a previous one
    """

    # def __init__(self):
    #     self.from_task = None

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        self.from_task = self.model.objects.get(id=self.kwargs["pk"])
        kwargs["dataset"] = self.from_task.dataset
        kwargs["initial"] = {"name": self.from_task.name}
        return kwargs

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # context["task_name"] = self.task_name
        context["from_task"] = self.from_task
        return context


class TaskStatusView(LoginRequiredIfConfProtectedMixin, TaskMixin, DetailView):
    """
    Clustering status and results
    """

    template_name = "tasking/status.html"


class TaskProgressView(
    LoginRequiredIfConfProtectedMixin, TaskMixin, SingleObjectMixin, View
):
    """
    Task progress (AJAX)
    """

    def get(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        return JsonResponse(
            {
                "is_finished": self.object.is_finished,
                **self.object.get_progress(),
            }
        )


class TaskCancelView(LoginRequiredIfConfProtectedMixin, TaskMixin, DetailView):
    """
    Cancel a task
    """

    template_name = "tasking/cancel.html"
    context_object_name = "task"

    def post(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        self.object.cancel_task()
        return redirect(self.object.get_absolute_url())


@method_decorator(csrf_exempt, name="dispatch")
class TaskWatcherView(SingleObjectMixin, View):
    """
    Receive notifications (start, success, error) from an API task

    Expects data in the request JSON body
    """

    def get(self, *args, **kwargs):
        # TODO test task
        return JsonResponse({"success": False, "error": "GET not allowed"})

    def post(self, *args, **kwargs):
        object = self.get_object()

        # check token
        token = self.request.GET.get("token")
        if token != object.get_token():
            return JsonResponse({"success": False, "error": "Invalid token"})

        data = self.request.body.decode("utf-8")
        data = json.loads(data)

        assert data is not None
        assert "event" in data
        # assert "output" in data

        object.receive_notification(data)

        return JsonResponse(
            {
                "success": True,
            }
        )


class TaskDeleteView(LoginRequiredIfConfProtectedMixin, TaskMixin, DetailView):
    """
    Delete a clustering
    """

    template_name = "tasking/delete.html"
    context_object_name = "task"

    def post(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        self.object.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        if hasattr(self, "success_url"):
            return self.success_url
        # return reverse(f"{self.app_name}:list")
        return reverse(f"{self.model.django_app_name}:list")


class TaskListView(LoginRequiredIfConfProtectedMixin, TaskMixin, ListView):
    """
    List of all tasks
    """

    template_name = "tasking/list.html"
    paginate_by = 40
    permission_see_all = "notimplemented"

    def get_queryset(self):
        # if user doesn't have task.monitor right, only show their own experiments
        qset = (
            super()
            .get_queryset()
            .order_by("-requested_on")
            .prefetch_related("requested_by")
        )
        if not self.request.user.is_authenticated:
            return qset.none()
        if not self.request.user.has_perm(self.permission_see_all):
            qset = qset.filter(requested_by=self.request.user)
        return qset


class TaskByDatasetList(TaskListView):
    """
    List of all task results for a given dataset
    """

    def get_queryset(self):
        return super().get_queryset().filter(dataset__id=self.kwargs["dataset_pk"])

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context[
            "filter"
        ] = f"{context['task_name']} results on dataset {self.kwargs['dataset_pk']}"
        return context


class TaskMonitoringView(LoginRequiredIfConfProtectedMixin, TaskMixin, TemplateView):
    """
    PermissionRequiredMixin, LoginRequiredMixin, TemplateView
    """

    template_name = "tasking/monitoring.html"
    permission_required = None

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        # context["api"] = self.model.get_api_monitoring()
        # context["frontend"] = self.model.get_frontend_monitoring()
        return context


class ClearOldResultsView(LoginRequiredIfConfProtectedMixin, TaskMixin, View):
    # permission_required = f"{self.app_name}.monitor_{self.app_name}"
    permission_required = None

    def post(self, *args, **kwargs):
        messages.error(
            self.request,
            "Front task clearing not implemented",
        )
        return redirect(f"{self.app_name}:monitor")


class ClearAPIOldResultsView(LoginRequiredIfConfProtectedMixin, TaskMixin, View):
    # permission_required = f"{self.app_name}.monitor_{self.app_name}"
    permission_required = None

    def post(self, *args, **kwargs):
        messages.error(
            self.request,
            "API clearing not implemented",
        )
        return redirect(f"{self.app_name}:monitor")
