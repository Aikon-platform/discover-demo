from django import forms
from django.conf import settings

from datasets.models import ZippedDataset, path_datasets
from datasets.fields import ContentRestrictedFileField

from .models import DTIClustering, SavedClustering


class IntegerListField(forms.CharField):
    def clean(self, value):
        # First, let the CharField do its normal validation.
        super().clean(value)

        # Split the input value by commas and strip any whitespace.
        values = [v.strip() for v in value.split(",")]

        # Validate that each value is an integer.
        for item in values:
            try:
                int(item)
            except (TypeError, ValueError):
                raise forms.ValidationError("All items must be integers.")

        return values


DTI_TRANSFORM_OPTIONS = [
    ("0_identity", "Identity"),
    ("1_color", "Color shift"),
    ("2_affine", "Affine deformation"),
    ("3_projective", "Projective deformation"),
    ("4_tps", "Thin plate spline"),
]

DTI_BACKGROUND_OPTIONS = [
    ("0_dti", "No background model"),
    ("1_learn_bg", "Learned background model"),
    ("2_const_bg", "Constant background model"),
    ("3_learn_fg", "Learned foreground model (transparency mask)"),
]


class DTIClusteringForm(forms.ModelForm):
    dataset_zip = ContentRestrictedFileField(
        label="Dataset",
        help_text="A .zip file containing the dataset to be clustered",
        accepted_types=["application/zip"],
        max_size=settings.MAX_UPLOAD_SIZE,
    )
    dataset_name = forms.CharField(
        label="Dataset name",
        help_text="An optional name to identify this dataset",
        max_length=64,
        required=False,
    )

    p_n_clusters = forms.IntegerField(
        label="Number of clusters",
        help_text="The number of clusters to be generated",
        min_value=2,
        max_value=50,
        initial=10,
        required=True,
    )
    p_background = forms.ChoiceField(
        label="Background",
        choices=DTI_BACKGROUND_OPTIONS,
        widget=forms.RadioSelect,
        required=True,
        initial="0_dti",
    )
    p_transforms = forms.MultipleChoiceField(
        label="Transforms",
        help_text="The transforms to be used for clustering",
        choices=DTI_TRANSFORM_OPTIONS,
        widget=forms.CheckboxSelectMultiple,
        required=True,
        initial=["0_identity", "1_color"],
    )
    p_n_epochs = forms.IntegerField(
        label="Number of epochs",
        help_text="Number of times the whole dataset is passed through the network",
        min_value=10,
        max_value=1000,
        initial=400,
        required=True,
    )
    p_batch_size = forms.IntegerField(
        label="Batch size",
        help_text="Number of samples used per iteration",
        min_value=10,
        max_value=40,
        initial=16,
        required=True,
    )
    p_milestones = IntegerListField(
        label="Milestones",
        help_text="List of epoch indices (integers separated by a comma) where learning rate is reduced",
        initial=350,
        required=True,
    )
    p_curriculum = IntegerListField(
        label="Learning curriculum",
        help_text="List of epoch indices (integers separated by a comma) to unlock/unfreeze/learn transformations",
        initial=0,
        required=True,
    )

    class Meta:
        model = DTIClustering
        fields = ("name", "dataset_zip", "dataset_name", "notify_email")

        fieldsets = (
            (
                "Dataset",
                {
                    "fields": ["name", "dataset_zip", "dataset_name", "notify_email"],
                },
            ),
            (
                "Clustering Options",
                {"fields": ["p_n_clusters", "p_background", "p_transforms"]},
            ),
            # (
            #     "Extra Options",
            #     {
            #         "fields": [("p_n_epochs", "p_batch_size"), ("p_milestones", "p_curriculum")],
            #         "classes": ("collapse",),
            #     },
            # ),
        )

    def __init__(self, *args, **kwargs):
        self.__dataset = kwargs.pop("dataset", None)
        self.__user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

        if self.__dataset:
            self.fields.pop("dataset_zip")
            self.fields.pop("dataset_name")

    def save(self, commit=True):
        instance = super().save(commit=False)

        p_transforms = "_".join(
            [t.split("_")[1] for t in sorted(self.cleaned_data["p_transforms"])]
        )

        instance.parameters = {
            "n_prototypes": self.cleaned_data["p_n_clusters"],
            "background_option": self.cleaned_data["p_background"],
            "transformation_sequence": p_transforms,
        }

        if self.__dataset:
            instance.dataset = self.__dataset
        else:
            instance.dataset = ZippedDataset.objects.create(
                zip_file=self.cleaned_data["dataset_zip"],
                name=self.cleaned_data["dataset_name"],
            )

        instance.requested_by = self.__user

        if commit:
            instance.save()

        return instance


class SavedClusteringForm(forms.ModelForm):
    class Meta:
        model = SavedClustering
        fields = (
            "name",
            "clustering_data",
        )
        widgets = {"clustering_data": forms.HiddenInput()}

    def __init__(self, *args, **kwargs):
        self.__from_dti = kwargs.pop("from_dti", None)

        super().__init__(*args, **kwargs)

        if self.__from_dti:
            self.fields["name"].initial = self.__from_dti.name

    def save(self, commit=True):
        instance = super().save(commit=False)

        if self.__from_dti:
            instance.from_dti = self.__from_dti

        if commit:
            instance.save()

        return instance
