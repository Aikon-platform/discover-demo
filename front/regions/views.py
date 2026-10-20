from django.views.generic import View
from django.http import FileResponse, Http404, HttpResponse
from django.core.paginator import Paginator, EmptyPage, PageNotAnInteger

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


class RegionsStatus(RegionsMixin.Status):
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        if self.object.is_finished and self.object.status == "SUCCESS":
            bboxes = self.object.get_bounding_boxes_for_display()

            paginator = Paginator(bboxes, 10)
            page = self.request.GET.get("page", 1)

            try:
                bboxes_page = paginator.page(page)
            except PageNotAnInteger:
                bboxes_page = paginator.page(1)
            except EmptyPage:
                bboxes_page = paginator.page(paginator.num_pages)

            context["bboxes_page"] = bboxes_page

        return context


class RegionsDownloadZip(View):
    def get(self, request, pk):
        try:
            region = Regions.objects.get(pk=pk)
            zip_content = region.zip_crops()
            if zip_content is None:
                raise Http404(f"Crops not found for regions {pk}")
            response = FileResponse(
                zip_content,
                content_type="application/zip",
                filename=f"crops_{region.pk}.zip",
                as_attachment=True,
            )
            # disable nginx buffering for this route. this avoids timeouts
            # when sending a large amount of data, which can happen here
            # since we zip images.
            response["X-Accel-Buffering"] = "no"
            response["Cache-Control"] = "no-cache"
            return response

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
