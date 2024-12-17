import json

from django.views.generic import View
from django.http import FileResponse, Http404, HttpResponse

from .forms import SimilarityForm, AVAILABLE_SIMILARITY_ALGORITHMS
from .models import Similarity
from tasking.views import task_view_set


@task_view_set
class SimilarityMixin:
    """
    Mixin for Similarity views
    """

    model = Similarity
    form_class = SimilarityForm
    task_name = "Similarity"
    app_name = "similarity"
    # NOTE: set task_data to "dataset" in order to use dataset form template
    task_data = "dataset"


class SimilarityStart(SimilarityMixin.Start):
    template_name = "similarity/start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_algorithms"] = AVAILABLE_SIMILARITY_ALGORITHMS
        return context


class SimilarityStartFrom(SimilarityMixin.StartFrom, SimilarityStart):
    pass


class SimilarityDownloadJson(View):
    def get(self, request, pk):
        try:
            similarity = Similarity.objects.get(pk=pk)
            similarity_matrix_dict = similarity.get_similarity_matrix_for_display(
                as_list=False
            )
            return FileResponse(
                json.dumps(similarity_matrix_dict, indent=4),
                as_attachment=True,
                content_type="application/json",
                filename=f"similarity_{similarity.pk}.json",
            )

        except Similarity.DoesNotExist:
            raise Http404("Similarity not found")
