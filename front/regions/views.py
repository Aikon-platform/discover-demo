from django.views.generic import (
    DetailView,
    ListView,
    CreateView,
    UpdateView,
    DeleteView,
    View,
    TemplateView,
)
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin

from .models import Regions


class RegionsStart(LoginRequiredMixin, CreateView):
    model = Regions
    template_name = "demowebsite/start.html"


class RegionsList(LoginRequiredMixin, ListView):
    model = Regions
    template_name = "demowebsite/list.html"
    paginate_by = 40

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_name"] = "regions"
        context["task_name"] = "Regions"
        return context
