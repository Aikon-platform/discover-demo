from django import forms

from datasets.fields import ContentRestrictedFileField, URLListField
from datasets.models import Dataset
from datasets.forms import DatasetForm


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


class AbstractTaskOnDatasetForm(AbstractTaskForm, DatasetForm):
    class Meta(AbstractTaskForm.Meta, DatasetForm.Meta):
        # model = AbstractAPITaskOnDataset
        abstract = True
        fields = AbstractTaskForm.Meta.fields + DatasetForm.Meta.fields

    # TODO add "use existing dataset"

    def __init__(self, *args, **kwargs):
        self._dataset = kwargs.pop("dataset", None)
        super().__init__(*args, **kwargs)

        # If the instance has a dataset, initialize the DatasetForm with its instance
        if self.instance and self.instance.dataset:
            self.dataset_form = DatasetForm(instance=self.instance.dataset)
        else:
            self.dataset_form = DatasetForm()  # Empty form if no dataset exists

    def check_dataset(self):
        """
        Check if the dataset was provided
        TODO use field_format_map
        """
        data_format = self.cleaned_data.get("format", None)
        if not data_format:
            self.add_error("format", "A dataset format is required.")
            return False

        if data_format == "img":
            if not self.cleaned_data.get("img_files"):
                self.add_error("img_files", "An image file is required.")
                return False
        elif data_format == "zip":
            if not self.cleaned_data.get("zip_file"):
                self.add_error("zip_file", "A zip file is required.")
                return False
        elif data_format == "iiif":
            if not self.cleaned_data.get("iiif_manifests"):
                self.add_error(
                    "iiif_manifests", "At least one IIIF manifest is required."
                )
                return False
        elif data_format == "pdf":
            if not self.cleaned_data.get("pdf_file"):
                self.add_error("pdf_file", "A PDF file is required.")
                return False
        else:
            self.add_error("format", "Invalid dataset format.")
            return False

        return True

    def is_valid(self) -> bool:
        return super().is_valid() and self.check_dataset()

    def _populate_instance(self, instance):
        super()._populate_instance(instance)
        #
        # if self._dataset:
        #     # instance.dataset = self._dataset
        #     return
        #
        # dataset_fields = {
        #     "name": self.cleaned_data.get("dataset_name", None)
        # }
        # data_format = self.cleaned_data.get("format", None)
        # if data_format in field_format_map:
        #     field_name = field_format_map[data_format]
        #     dataset_fields[field_name] = self.cleaned_data[field_name]
        #
        # dataset = Dataset(**dataset_fields)
        # self._dataset = dataset

    def _populate_dataset(self):
        if self._dataset:
            return

        dataset_fields = {"name": self.cleaned_data.get("dataset_name", None)}
        data_format = self.cleaned_data.get("format", None)
        if data_format in field_format_map:
            field_name = field_format_map[data_format]
            dataset_fields[field_name] = self.cleaned_data[field_name]

        dataset = Dataset(**dataset_fields)
        self._dataset = dataset

    def save(self, commit=True):
        self._populate_dataset()
        if commit:
            if self._dataset and self._dataset.pk is None:
                self._dataset.save()

        instance = super().save(commit=False)
        self._populate_instance(instance)

        if commit:
            instance.dataset = self._dataset
            instance.save()

        return instance


class AbstractTaskOnCropsForm(AbstractTaskOnDatasetForm):
    class Meta:
        # model = AbstractAPITaskOnCrops
        fields = AbstractTaskOnDatasetForm.Meta.fields + ("crops",)

    # crops = forms.ModelField(
    #     queryset=None,  # We'll set this in __init__
    #     required=False,  # Adjust as needed
    #     help_text="If using crops from a previous task, also set the dataset to be the same (and ignore the dataset upload fields)."
    # )

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
