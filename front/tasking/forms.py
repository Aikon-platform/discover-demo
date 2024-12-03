from django import forms

from datasets.fields import ContentRestrictedFileField, URLListField
from datasets.models import Dataset
from datasets.forms import AbstractDatasetForm


class AbstractTaskForm(forms.ModelForm):
    class Meta:
        model = None
        abstract = True
        fields = ("name", "notify_email")

    def __init__(self, *args, **kwargs):
        self._user = kwargs.pop("user", None)

        super().__init__(*args, **kwargs)

    def _populate_instance(self, instance):
        instance.requested_by = self._user

    def save(self, commit=True):
        instance = super().save(commit=False)
        self._populate_instance(instance)

        if commit:
            instance.save()

        return instance


field_format_map = {
    "img": "img_files",
    "zip": "zip_file",
    "iiif": "iiif_manifests",
    "pdf": "pdf_file",
}


class AbstractTaskOnDatasetForm(AbstractTaskForm, AbstractDatasetForm):
    class Meta(AbstractTaskForm.Meta, AbstractDatasetForm.Meta):
        # model = AbstractAPITaskOnDataset
        abstract = True
        fields = AbstractTaskForm.Meta.fields + AbstractDatasetForm.Meta.fields

    _dataset = None

    # TODO use following to add "use existing dataset"
    # dataset = forms.ModelField(
    #     queryset=Dataset.objects.all(),
    #     required=False,
    #
    # )
    # dataset = models.ForeignKey(
    #     Regions,
    #     verbose_name="Existing dataset",
    #     help_text="Use an existing dataset",
    #     null=True,
    #     blank=True,
    #     on_delete=models.SET_NULL,
    #     related_name="task_crops",
    # )

    def check_dataset(self):
        """
        Check if the dataset was provided
        """
        data_format = self.cleaned_data.get("format", None)
        if not data_format:
            self.add_error("format", "A dataset format is required.")
            return False

        if data_format in field_format_map:
            field_name = field_format_map[data_format]
            if not self.cleaned_data.get(field_name):
                self.add_error(field_name, "A file is required.")
                return False
        else:
            self.add_error("format", "Invalid dataset format.")
            return False

        return True

    def is_valid(self) -> bool:
        return super().is_valid() and self.check_dataset()

    def _populate_dataset(self):
        if self._dataset:
            return

        dataset_fields = {
            "name": self.cleaned_data.get("dataset_name", None),
            "created_by": self._user,
        }

        data_format = self.cleaned_data.get("format", None)
        if data_format in field_format_map:
            field_name = field_format_map[data_format]
            dataset_fields[field_name] = self.cleaned_data[field_name]

        self._dataset = Dataset.objects.create(**dataset_fields)

    def save(self, commit=True):
        self._populate_dataset()
        instance = super().save(commit=False)
        instance.dataset = self._dataset
        super()._populate_instance(instance)

        if commit:
            instance.save()

        return instance


class AbstractTaskOnCropsForm(AbstractTaskOnDatasetForm):
    class Meta:
        model = None
        abstract = True
        fields = AbstractTaskOnDatasetForm.Meta.fields + ("crops",)

    # crops = forms.ModelField(
    #     queryset=None,  # We'll set this in __init__
    #     required=False,  # Adjust as needed
    #     help_text="If using crops from a previous task, also set the dataset to be the same (and ignore the dataset upload fields)."
    # )
    # TODO replace dataset by crops field

    def __init__(self, *args, **kwargs):
        self._crops = kwargs.pop("crops", None)
        super().__init__(*args, **kwargs)

        # self.fields["crops"].queryset = (
        #     Regions.objects.filter(
        #         regions__isnull=False,
        #         requested_by=self._user,
        #     )
        # )
        self.fields["crops"].queryset = self.fields["crops"].queryset.filter(
            regions__isnull=False,
            requested_by=self._user,
        )
        self.fields[
            "crops"
        ].help_text = "If using crops from a previous task, also set the dataset to be the same (and ignore the dataset upload fields)."

    def check_dataset(self):
        # Hook to set the dataset from the crops
        # TODO change here
        # if self.cleaned_data.get("crops", None):
        #     self._dataset = self.cleaned_data["crops"].dataset
        return super().check_dataset()

    def save(self, commit=True):
        # TODO check if crops were provided, if so set the dataset from the crops
        instance = super().save(commit=False)

        # self._populate_instance(instance)
        # instance.crops = self.cleaned_data.get("crops", None)
        #
        # if commit:
        #     instance.save()

        return instance


class AbstractTaskOnImageForm(AbstractTaskForm):
    class Meta:
        model = None
        abstract = True
        fields = ("name", "image", "notify_email")

    image = ContentRestrictedFileField(
        label="Upload an image",
        help_text="An image to be processed",
        accepted_types=["image/jpeg", "image/png"],
        max_size=1024 * 1024 * 10,
    )

    def _populate_instance(self, instance):
        super()._populate_instance(instance)
        instance.name = self.cleaned_data["image"].name
