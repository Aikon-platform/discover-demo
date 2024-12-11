import os

from django.views.generic import View
from django.http import FileResponse, Http404, HttpResponse

from .forms import RegionsForm
from .models import Regions
from tasking.views import task_view_set


# instanciate all views from tasking.views, override to add custom behavior
@task_view_set
class RegionsMixin:
    """
    Mixin for Regions extractions views
    """

    model = Regions
    form_class = RegionsForm
    task_name = "Regions Extraction"
    app_name = "regions"
    # NOTE: set task_data to "dataset" in order to use dataset form template
    task_data = "dataset"


class RegionsList(RegionsMixin.List):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("dataset")


class RegionsDownloadZip(View):
    def get(self, request, pk):
        try:
            region = Regions.objects.get(pk=pk)
            zip_content = region.zip_crops()
            return FileResponse(
                zip_content,
                content_type="application/zip",
                filename=f"crops_{region.pk}.zip",
                as_attachment=True,
            )

        except Regions.DoesNotExist:
            pass

        raise Http404("Crops not found")


class RegionsDownloadJson(View):
    def get(self, request, pk):
        try:
            region = Regions.objects.get(pk=pk)

            # Return the file as a downloadable response
            return FileResponse(
                open(region.task_full_path / f"{region.dataset.id}.json", "rb"),
                as_attachment=True,
                content_type="application/json",
                filename=f"crops_{region.pk}.json",
            )

        except Regions.DoesNotExist:
            pass

        raise Http404("Crops not found")
