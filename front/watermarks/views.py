from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView
from django.contrib.auth.mixins import LoginRequiredMixin
from typing import Any

from .models import SingleWatermarkDetection
from .forms import SingleWatermarkDetectionForm

class WatermarkQueryView(LoginRequiredMixin, CreateView):
    model = SingleWatermarkDetection
    form_class = SingleWatermarkDetectionForm
    template_name = 'watermarks/detect.html'

    def get_form_kwargs(self) -> dict[str, Any]:
        return super().get_form_kwargs() | {'user': self.request.user}
    
    def get_success_url(self) -> str:
        self.object.fetch_annotations()
        self.object.compress_image()
        return self.object.get_absolute_url()
    
class WatermarkResultView(LoginRequiredMixin, DetailView):
    model = SingleWatermarkDetection
    template_name = 'watermarks/detect.html'
    context_object_name = "detection"

    def get_queryset(self):
        return super().get_queryset().filter(requested_by=self.request.user)
    
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["form"] = SingleWatermarkDetectionForm(user=self.request.user)
        return context