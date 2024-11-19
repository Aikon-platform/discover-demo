from django.views.generic import View
from django.http import FileResponse, Http404

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


class RegionsList(RegionsMixin.List):
    def get_queryset(self):
        return super().get_queryset().prefetch_related("dataset")


class RegionsDownload(View):
    def get(self, request, pk):
        try:
            region = Regions.objects.get(pk=pk)
            zip_path = region.zip_crops()

            if zip_path and zip_path.exists():
                response = FileResponse(
                    open(zip_path, "rb"), content_type="application/zip"
                )
                response[
                    "Content-Disposition"
                ] = f'attachment; filename="crops_{region.pk}.zip"'
                return response

        except Regions.DoesNotExist:
            pass

        raise Http404("Crops not found")
