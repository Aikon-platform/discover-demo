from django.urls import reverse_lazy
from django.views.generic import CreateView, DetailView, ListView, View
from django.views.generic.detail import SingleObjectMixin
from django.contrib.auth.mixins import LoginRequiredMixin, PermissionRequiredMixin
from typing import Any
import traceback
from django.shortcuts import redirect

from .models import SingleWatermarkDetection, WatermarksSource
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
    

# ADMIN

class ManageSourcesView(PermissionRequiredMixin, LoginRequiredMixin, ListView):
    """
    Monitoring view
    """
    permission_required = "watermarks.monitor_watermarks"
    template_name = 'watermarks/sources.html'
    context_object_name = 'sources'
    model = WatermarksSource

    def get_context_data(self, **kwargs) -> dict[str, Any]:
        context = super().get_context_data(**kwargs)
        try:
            context["available_sources"] = WatermarksSource.get_available_sources()
        except Exception as e:
            context["api_error"] = traceback.format_exc(1)
        return context

class AddSourceView(PermissionRequiredMixin, LoginRequiredMixin, SingleObjectMixin, View):
    """
    Add a new source
    """
    permission_required = "watermarks.monitor_watermarks"
    model = WatermarksSource

    def post(self, request, *args, **kwargs):
        source = WatermarksSource(uid=request.POST["uid"])
        source.download_images()
        return redirect(reverse_lazy("watermarks:sources-manage"))