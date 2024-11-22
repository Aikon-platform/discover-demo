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


class SimilarityStart(SimilarityMixin.Start):
    template_name = "similarity/start.html"

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context["available_algorithms"] = AVAILABLE_SIMILARITY_ALGORITHMS
        return context
