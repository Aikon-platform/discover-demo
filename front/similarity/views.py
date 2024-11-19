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
