from enum import Enum
from typing import Type
import requests
from django import forms
from django.conf import settings
from dataclasses import dataclass
from .models import Similarity
from tasking.forms import AbstractTaskOnDatasetForm

SIMILARITY_API_URL = (
    f"{getattr(settings, 'API_URL', 'http://localhost:5001')}/similarity"
)


class BaseFeatureExtractionForm(forms.Form):
    """Base form for feature extraction settings."""

    feat_net = forms.ChoiceField(
        label="Feature Extraction Model",
        help_text="Select the model to use for feature extraction",
    )
    feat_set = forms.ChoiceField(
        label="Image dataset on which the model was trained",
        choices=[("imagenet", "ImageNet")],
    )
    feat_layer = forms.ChoiceField(
        label="Feature Extraction Layer", choices=[("conv4", "Convolutional Layer 4")]
    )

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields["feat_net"].choices = self.get_available_models()

    @staticmethod
    def get_available_models():
        try:
            response = requests.get(f"{SIMILARITY_API_URL}/models")
            response.raise_for_status()
            models = response.json()
            if not models:
                return [("", "No models available")]
            # models = { "ref": { "name": "Display Name", "model": "filename", "desc": "Description" }, ... }
            return [
                (info["model"], f"{info['name']} ({info['desc']})")
                for info in models.values()
            ]
        except Exception as e:
            return [("", f"Error fetching models: {e}")]


class CosinePreprocessing(BaseFeatureExtractionForm):
    """Form for SegSwap-specific settings."""

    cosine_preprocessing = forms.BooleanField(
        required=False,
        initial=True,
        label="Use Preprocessing",
        help_text="Filter less similar images before running SegSwap",
    )
    cosine_threshold = forms.FloatField(
        min_value=0.0, max_value=1.0, initial=0.6, label="Cosine Threshold"
    )
    cosine_n_filter = forms.IntegerField(
        min_value=2, initial=10, label="Number of images to keep"
    )


class CosineSimilarityForm(BaseFeatureExtractionForm):
    """Form for cosine similarity-specific settings."""


class SegSwapForm(CosinePreprocessing):
    """Form for SegSwap-specific settings."""


@dataclass
class AlgorithmConfig:
    name: str
    display_name: str
    description: str
    form_class: Type[forms.Form]


class SimilarityAlgorithm(Enum):
    COSINE = "cosine"
    SEGSWAP = "segswap"

    @property
    def config(self) -> AlgorithmConfig:
        return ALGORITHM_CONFIGS[self]

    @classmethod
    def choices(cls):
        return [(algo.value, algo.config.display_name) for algo in cls]


ALGORITHM_CONFIGS = {
    SimilarityAlgorithm.COSINE: AlgorithmConfig(
        name="cosine",
        display_name="Cosine Similarity",
        description="Compute similarity using cosine distance",
        form_class=CosineSimilarityForm,
    ),
    SimilarityAlgorithm.SEGSWAP: AlgorithmConfig(
        name="segswap",
        display_name="SegSwap",
        description="Use segmentation and matching",
        form_class=SegSwapForm,
    ),
}


class SimilarityForm(AbstractTaskOnDatasetForm):
    """Form for creating similarity analysis tasks."""

    algorithm = forms.ChoiceField(
        choices=SimilarityAlgorithm.choices(),
        initial=SimilarityAlgorithm.COSINE.value,
        label="Similarity Algorithm",
        widget=forms.Select(attrs={"class": "algorithm-selector"}),
    )

    class Meta(AbstractTaskOnDatasetForm.Meta):
        model = Similarity
        fields = AbstractTaskOnDatasetForm.Meta.fields + ("algorithm",)

    def __init__(self, *args, **kwargs):
        print(kwargs)
        form_kwargs = kwargs.copy()
        form_kwargs.pop("prefix", None)
        form_kwargs.pop("instance", None)
        form_kwargs.pop("user", None)

        super().__init__(*args, **form_kwargs)
        self.algorithm_forms = {}

        for algo in SimilarityAlgorithm:
            name = algo.value
            config = algo.config
            self.algorithm_forms.update(
                {name: config.form_class(prefix=f"{name}_", *args, **form_kwargs)}
            )
            for field_name, field in self.algorithm_forms[name].fields.items():
                full_field_name = f"{name}_{field_name}"
                self.fields[full_field_name] = field
                field.widget.attrs.update({"data-algorithm": name})

    def clean(self):
        cleaned_data = super().clean()
        algorithm = cleaned_data.get("algorithm")
        if algorithm and algorithm in self.algorithm_forms:
            algo_form = self.algorithm_forms[algorithm]
            if not algo_form.is_valid():
                for field, error in algo_form.errors.items():
                    self.add_error(f"{algorithm}_{field}", error)
        return cleaned_data

    def save(self, commit=True):
        instance = super().save(commit=False)
        algorithm = self.cleaned_data["algorithm"]
        instance.algorithm = algorithm
        instance.parameters = {
            name: self.cleaned_data[f"{algorithm}_{name}"]
            for name in self.algorithm_forms[algorithm].fields
        }
        if commit:
            instance.save()
        return instance
