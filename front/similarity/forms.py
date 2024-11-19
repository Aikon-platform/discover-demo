from .models import Similarity
from tasking.forms import AbstractTaskOnDatasetForm


class SimilarityForm(AbstractTaskOnDatasetForm):
    class Meta:
        model = Similarity
        fields = AbstractTaskOnDatasetForm.Meta.fields
