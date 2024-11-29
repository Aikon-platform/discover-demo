from django import forms

from .models import Regions
from tasking.forms import AbstractTaskOnDatasetForm


class RegionsForm(AbstractTaskOnDatasetForm):
    class Meta(AbstractTaskOnDatasetForm.Meta):
        model = Regions
        fields = AbstractTaskOnDatasetForm.Meta.fields + ("model",)

    model = forms.ChoiceField(
        label="Model",
        help_text="Model used to extract image regions in the dataset",
        choices=[],  # dynamically set in __init__
        widget=forms.RadioSelect,
        required=True,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["model"].choices = Regions.get_available_models()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.parameters = {"model": self.cleaned_data["model"]}

        if commit:
            instance.save()
        return instance
