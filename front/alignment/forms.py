from django import forms

from .models import Alignment
from tasking.forms import AbstractTaskOnCropsForm

# Available alignment methods - will be fetched from API if available
AVAILABLE_ALIGNMENT_METHODS = [
    ("sift+ransac", "Alignment using SIFT feature matching with RANSAC refinement")
]

AVAILABLE_TRANSFORMS = [
    ("scale", "Scale"),
    ("scalexy", "Scale (non-uniform)"),
    ("scale+rotate", "Scale and Rotate"),
    ("scalexy+rotate", "Scale (non-uniform) and Rotate"),
    ("affine", "Affine"),
    ("homographic", "Homographic"),
]


class AlignmentForm(AbstractTaskOnCropsForm):
    """Form for creating alignment analysis tasks."""

    class Meta(AbstractTaskOnCropsForm.Meta):
        model = Alignment
        fields = AbstractTaskOnCropsForm.Meta.fields + ("method",)

    method = forms.ChoiceField(
        label="Alignment Method",
        help_text="Select the method to use for image alignment",
        widget=forms.Select(attrs={"extra-class": "preprocessing-field"}),
        choices=AVAILABLE_ALIGNMENT_METHODS,
        initial=AVAILABLE_ALIGNMENT_METHODS[0][0],
    )

    target_transform = forms.ChoiceField(
        label="Target Transform",
        help_text="Select the target transform to use for image alignment",
        widget=forms.Select(attrs={"extra-class": "preprocessing-field"}),
        choices=Alignment.TARGET_TRANSFORMS,
        initial=Alignment.TARGET_TRANSFORMS[0][0],
    )

    def save(self, commit=True):
        instance = super().save(commit=False)
        
        parameters = {
            "method": self.cleaned_data.get("method", "sift+ransac"),
            "target_transform": self.cleaned_data.get("target_transform", "homographic"),
        }
        
        instance.parameters = parameters

        if commit:
            instance.save()

        return instance