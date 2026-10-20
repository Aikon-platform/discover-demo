from django import forms

from shared.forms import HiddenJsonField
from .models import DTIClustering, SavedClustering
from tasking.forms import AbstractTaskOnCropsForm

LEARNING_RATE_CHOICES = [
    (1e-5, "0.00001 (Minimum)"),
    (5e-5, "0.00005 (Very Slow)"),
    (1e-4, "0.0001 (Slow)"),
    (5e-4, "0.0005 (Default)"),
    (1e-3, "0.001 (Medium)"),
    (5e-3, "0.005 (Fast)"),
    (1e-2, "0.01 (Very Fast)"),
]

LEARNING_SOURCE_CHOICES = [
    ("data", "Direct Pixel Learning"),
    ("mlp", "MLP Generator (Latent Space)"),
    ("unet", "UNet Generator (Latent Space)"),
]


class DTIClusteringForm(AbstractTaskOnCropsForm):
    p_n_clusters = forms.IntegerField(
        label="Number of clusters",
        help_text="The number of different prototypes to generate from the dataset",
        min_value=1,
        max_value=50,
        initial=10,
        required=True,
    )
    # p_batch_size = forms.IntegerField(
    #     label="Batch size",
    #     help_text="Number of samples used per iteration",
    #     min_value=16,
    #     max_value=64,
    #     initial=64,
    #     required=True,
    # )
    empty_cluster_thres = forms.FloatField(
        label="Threshold for empty clusters",
        help_text="When a cluster falls below threshold, its samples are reassigned",
        min_value=0.001,
        max_value=0.6,
        initial=0.025,
        required=True,
    )
    lr = forms.ChoiceField(
        label="Learning Rate",
        help_text="How fast the prototypes adapt: higher values learn faster but may be unstable.",
        choices=LEARNING_RATE_CHOICES,
        initial=5e-4,
        widget=forms.Select(),
    )
    source = forms.ChoiceField(
        label="Sprite Generation Method",
        help_text="How sprites are learned: direct pixel optimization or neural network generation from latent vectors.",
        choices=LEARNING_SOURCE_CHOICES,
        initial="data",
        widget=forms.Select(),
    )
    p_transforms = HiddenJsonField(
        label="Transform Configuration",
        help_text="Image transformations to fit prototype",
        json_structure={
            "transforms": "identity",
            "iterations": 1000,
            "milestones": [1000],
            "grid_size": 4,  # thin plate spline grid size
        },
    )

    p_background = HiddenJsonField(
        label="Learned Prototypes",
        help_text="How parts of the images should be taken into account for prototype learning",
        json_structure={
            "use_sprites": False,  # Default to DTI (no sprites)
            "freeze": [False, False, False],  # foreground, background, masks
            "init": ["gaussian"],  # only one init for DTI
        },
    )

    class Meta(AbstractTaskOnCropsForm.Meta):
        model = DTIClustering

    def clean_lr(self):
        return float(self.cleaned_data["lr"])

    def _populate_instance(self, instance):
        instance.parameters = {
            "n_prototypes": self.cleaned_data["p_n_clusters"],
            # "batch_size": self.cleaned_data["p_batch_size"],
            "empty_cluster_threshold": self.cleaned_data["empty_cluster_thres"],
            "lr": self.cleaned_data["lr"],
            "source": self.cleaned_data["source"],
            "background_option": self.cleaned_data["p_background"],
            "transformation_sequence": self.cleaned_data["p_transforms"],
        }

        super()._populate_instance(instance)


class SavedClusteringForm(forms.ModelForm):
    class Meta:
        model = SavedClustering
        fields = (
            "name",
            "clustering_data",
        )
        widgets = {"clustering_data": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        self.__from_task = kwargs.pop("from_task", None)

        super().__init__(*args, **kwargs)

        if self.__from_task:
            self.fields["name"].initial = self.__from_task.name

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.__from_task:
            instance.from_task = self.__from_task

        if commit:
            instance.save()

        return instance
