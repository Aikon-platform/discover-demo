from typing import Any
from django.views.generic import CreateView, DetailView, View, ListView
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin
from django.http import JsonResponse
from django.shortcuts import redirect
from django.urls import reverse
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import json


class TaskStartView(LoginRequiredMixin, CreateView):
    template_name = "tasking/start.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["user"] = self.request.user
        return kwargs

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        context["task_name"] = getattr(self, "task_name", self.model._meta.verbose_name)
        return context

    def get_success_url(self):
        # Start task
        self.object.start_task()

        return self.object.get_absolute_url()


class TaskStatusView(LoginRequiredMixin, DetailView):
    """
    Clustering status and results
    """

    template_name = "tasking/status.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_name"] = self.model.django_app_name
        context["task_name"] = getattr(self, "task_name", self.model._meta.verbose_name)
        return context


class TaskProgressView(LoginRequiredMixin, SingleObjectMixin, View):
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


class TaskCancelView(LoginRequiredMixin, DetailView):
    """
    Cancel a task
    """

    template_name = "tasking/cancel.html"
    context_object_name = "task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task_name"] = getattr(self, "task_name", self.model._meta.verbose_name)
        return context

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

    def post(self, *args, **kwargs):
        object = self.get_object()

        # check token
        token = self.request.GET.get("token")
        if token != object.get_token():
            return JsonResponse({"success": False, "error": "Invalid token"})

        data = self.request.body.decode("utf-8")
        data = json.loads(data)

        assert data is not None

        object.receive_notification(data)

        return JsonResponse(
            {
                "success": True,
            }
        )


class TaskDeleteView(LoginRequiredMixin, DetailView):
    """
    Delete a clustering
    """

    template_name = "tasking/delete.html"
    context_object_name = "task"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["task_name"] = getattr(self, "task_name", self.model._meta.verbose_name)
        return context

    def post(self, *args, **kwargs):
        if not hasattr(self, "object"):
            self.object = self.get_object()

        self.object.delete()
        return redirect(self.get_success_url())

    def get_success_url(self):
        if hasattr(self, "success_url"):
            return self.success_url
        return reverse(f"{self.model.django_app_name}:list")


class TaskListView(LoginRequiredMixin, ListView):
    """
    List of all clusterings
    """

    template_name = "tasking/list.html"
    paginate_by = 40
    permission_see_all = "notimplemented"

    def get_queryset(self):
        # if user doesn't have dticlustering.monitor right, only show their own clusterings
        qset = (
            super()
            .get_queryset()
            .order_by("-requested_on")
            .prefetch_related("requested_by")
        )
        if not self.request.user.has_perm(self.permission_see_all):
            qset = qset.filter(requested_by=self.request.user)
        return qset

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_name"] = self.model.django_app_name
        context["task_name"] = getattr(self, "task_name", self.model._meta.verbose_name)
        return context
