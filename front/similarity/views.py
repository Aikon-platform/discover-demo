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

from .models import Similarity


class SimilarityStart(LoginRequiredMixin, CreateView):
    model = Similarity
    template_name = "demowebsite/start.html"


class SimilarityList(LoginRequiredMixin, ListView):
    model = Similarity
    template_name = "demowebsite/list.html"
    paginate_by = 40

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["app_name"] = "similarity"
        context["task_name"] = "Similarity"
        return context
