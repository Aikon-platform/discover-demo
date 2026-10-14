from django import forms

from .models import Alignment
from tasking.forms import AbstractTaskOnCropsForm


AVAILABLE_ALIGNMENT_METHODS = [
    ("ransac", "RANSAC based on feature matching")
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
        fields = AbstractTaskOnCropsForm.Meta.fields + ("ransac_feature",)

    method = forms.ChoiceField(
        label="Alignment Method",
        help_text="Select the method to use for image alignment",
        widget=forms.Select(attrs={"extra-class": "preprocessing-field"}),
        choices=AVAILABLE_ALIGNMENT_METHODS,
        initial=AVAILABLE_ALIGNMENT_METHODS[0][0],
    )

    ransac_feature = forms.ChoiceField(
        label="Feature",
        help_text="Features matched by RANSAC: SIFT or a feature extraction model",
        widget=forms.Select(attrs={"extra-class": "preprocessing-field"}),
    )

    target_transform = forms.ChoiceField(
        label="Target Transform",
        help_text="Select the target transform to use for image alignment",
        widget=forms.Select(attrs={"extra-class": "preprocessing-field"}),
        choices=AVAILABLE_TRANSFORMS,
        initial=AVAILABLE_TRANSFORMS[0][0],
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["ransac_feature"].choices = Alignment.get_available_models()

    def save(self, commit=True):
        instance = super().save(commit=False)

        parameters = {
            "method": self.cleaned_data.get("method", "ransac"),
            "ransac_feature": self.cleaned_data.get("ransac_feature", "SIFT"),
            "target_transform": self.cleaned_data.get(
                "target_transform", "homographic"
            ),
        }

        instance.parameters = parameters

        if commit:
            instance.save()

        return instance
