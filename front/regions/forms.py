from django import forms
from django.db.models import Q
from django.core.exceptions import ValidationError

from .models import Regions
from tasking.forms import AbstractTaskOnDatasetForm


class RegionsForm(AbstractTaskOnDatasetForm):
    class Meta(AbstractTaskOnDatasetForm.Meta):
        model = Regions
        fields = AbstractTaskOnDatasetForm.Meta.fields + ("model",)

    # TODO implement `clean` to check if dataset field (inherited from `AbstractTaskOnDatasetForm` aldready has a line extraction, if we're doing char extraction)
    model = forms.ChoiceField(
        label="Model",
        help_text="Model used to extract image regions in the dataset",
        choices=[],  # dynamically set in __init__
        widget=forms.Select,
        required=True,
    )
    squarify = forms.BooleanField(
        label="Squarify",
        help_text="Squarify extracted regions",
        required=False,
        initial=False,
    )
    h_margin = forms.IntegerField(
        label="Horizontal Margin (%)",
        help_text="Percentage of horizontal margin to add to the regions.",
        min_value=0,
        max_value=100,
        required=False,
        initial=0,
    )
    v_margin = forms.IntegerField(
        label="Vertical Margin (%)",
        help_text="Percentage of vertical margin to add to the regions.",
        min_value=0,
        max_value=100,
        required=False,
        initial=0,
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["model"].choices = Regions.get_available_models()

    def save(self, commit=True):
        instance = super().save(commit=False)
        instance.parameters = {
            "model": self.cleaned_data["model"],
            "postprocess": {
                "squarify": self.cleaned_data.get("squarify", False),
                "h_margin": self.cleaned_data.get("h_margin", 0) / 100.0,
                "v_margin": self.cleaned_data.get("v_margin", 0) / 100.0,
            },
        }
        if commit:
            instance.save()
        return instance
