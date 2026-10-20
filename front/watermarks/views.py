from django.views.generic import View
from django.http import FileResponse, Http404, HttpResponse

from .forms import WatermarksPipelineForm
from .models import WatermarksPipeline
from tasking.views import task_view_set


# instanciate all views from tasking.views, override to add custom behavior
@task_view_set
class WatermarksMixin:
    """
    Mixin for Watermark Pipeline extractions views
    """

    model = WatermarksPipeline
    form_class = WatermarksPipelineForm
    task_name = "Watermark Pipeline"
    app_name = "Watermarks"
    task_data = "dataset"


class WatermarksList(WatermarksMixin.List):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("dataset")


class WatermarksStatusView(WatermarksMixin.Status):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        if (
            self.object.analysis_type == "indexing"
            and self.object.indexing_task
            and hasattr(self.object.indexing_task, "index")
        ):
            context["editable"] = (
                self.object.indexing_task.index.owner == self.request.user
            ) or self.request.user.is_superuser
        return context


class WatermarksStartMixin:
    template_name = "watermarks/start.html"

    def get_form_kwargs(self):
        kwargs = super().get_form_kwargs()
        kwargs["query_target_index"] = self.request.GET.get("index")
        kwargs["analysis_type"] = self.request.GET.get("analysis_type")
        return kwargs


class WatermarksStartView(WatermarksStartMixin, WatermarksMixin.Start):
    pass


class WatermarksStartFromView(WatermarksStartMixin, WatermarksMixin.StartFrom):
    pass
