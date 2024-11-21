from .forms import SimilarityForm
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
        context["special_fields"] = [
            "algorithm"
        ]  # Add any fields that need special handling
        return context
