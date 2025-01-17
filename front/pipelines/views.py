from django.views.generic import View
from django.http import FileResponse, Http404, HttpResponse

from .forms import PipelineForm
from .models import Pipeline
from tasking.views import task_view_set


# instanciate all views from tasking.views, override to add custom behavior
@task_view_set
class PipelineMixin:
    """
    Mixin for Pipeline extractions views
    """

    model = Pipeline
    form_class = PipelineForm
    task_name = "Watermark Pipeline"
    app_name = "Pipeline"
    # NOTE: set task_data to "dataset" in order to use dataset form template
    task_data = "dataset"


class PipelineList(PipelineMixin.List):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("dataset")
