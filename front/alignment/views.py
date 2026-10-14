import json

from django.views.generic import View
from django.http import FileResponse, Http404, HttpResponse

from .forms import AlignmentForm
from .models import Alignment
from tasking.views import task_view_set


@task_view_set
class AlignmentMixin:
    """
    Mixin for Alignment views
    """

    model = Alignment
    form_class = AlignmentForm
    task_name = "Alignment"
    app_name = "alignment"
    task_data = "dataset"


class AlignmentStart(AlignmentMixin.Start):
    template_name = "alignment/start.html"


class AlignmentStartFrom(AlignmentMixin.StartFrom, AlignmentStart):
    pass


class AlignmentDownloadJson(View):
    def get(self, request, pk):
        try:
            alignment = Alignment.objects.get(pk=pk)
            alignment_results = alignment.get_alignment_results_for_display()
            return FileResponse(
                json.dumps(alignment_results, indent=4),
                as_attachment=True,
                content_type="application/json",
                filename=f"alignment_{alignment.pk}.json",
            )

        except Alignment.DoesNotExist:
            raise Http404("Alignment not found")
