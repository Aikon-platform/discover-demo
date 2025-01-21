from django import forms

from .models import Pipeline
from tasking.forms import AbstractTaskOnDatasetForm


class PipelineForm(AbstractTaskOnDatasetForm):
    class Meta(AbstractTaskOnDatasetForm.Meta):
        model = Pipeline
        fields = AbstractTaskOnDatasetForm.Meta.fields
