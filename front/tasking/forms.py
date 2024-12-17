from django import forms

from datasets.fields import ContentRestrictedFileField
from datasets.models import Dataset
from datasets.forms import AbstractDatasetForm, MAP_FIELD_FORMAT


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


class AbstractTaskOnDatasetForm(AbstractTaskForm, AbstractDatasetForm):
    class Meta(AbstractTaskForm.Meta, AbstractDatasetForm.Meta):
        # model = AbstractAPITaskOnDataset
        abstract = True
        fields = (
            AbstractTaskForm.Meta.fields
            + AbstractDatasetForm.Meta.fields
            + ("dataset",)
        )

    dataset = forms.ModelChoiceField(
        queryset=Dataset.objects.all(),
        label="Use dataset from...",
        required=False,
        widget=forms.Select(attrs={"extra-class": "old-dataset-field"}),
    )
    reuse_dataset = forms.BooleanField(
        required=False,
        initial=False,
        label="Reuse existing dataset 🔄",
        widget=forms.CheckboxInput(attrs={"class": "use-dataset mb-3"}),
    )

    def __init__(self, *args, **kwargs):
        self.dataset = kwargs.pop("dataset", None)
        if self.dataset:
            kwargs["initial"] = {
                **kwargs.get("initial", {}),
                "dataset": self.dataset,
                "reuse_dataset": True,
            }

        super().__init__(*args, **kwargs)

        self.fields["dataset"].queryset = self.fields["dataset"].queryset.filter(
            created_by=self._user,
        )

    def check_dataset(self):
        """
        Check if the dataset was provided
        """
        reuse_dataset = self.cleaned_data.get("reuse_dataset", False)
        if reuse_dataset:
            is_dataset = self.cleaned_data.get("dataset", None)

            if not is_dataset:
                self.add_error("dataset", "A dataset is required.")
                return False
        else:
            data_format = self.cleaned_data.get("format", None)
            if not data_format:
                self.add_error("format", "A dataset format is required.")
                return False

            if data_format in MAP_FIELD_FORMAT:
                field_name = MAP_FIELD_FORMAT[data_format]
                if not self.cleaned_data.get(field_name):
                    self.add_error(field_name, "A file is required.")
                    return False
            else:
                self.add_error("format", "Invalid dataset format.")
                return False

        return True

    def is_valid(self) -> bool:
        # print("SUPER VALID", super().is_valid())
        # print("DATA VALID", self.check_dataset())
        return super().is_valid() and self.check_dataset()

    def _populate_dataset(self):
        if dataset := self.cleaned_data["dataset"]:
            self._dataset = dataset
            return

        dataset_fields = {
            "name": self.cleaned_data.get("dataset_name", None),
            "created_by": self._user,
        }

        data_format = self.cleaned_data.get("format", None)
        if data_format in MAP_FIELD_FORMAT:
            field_name = MAP_FIELD_FORMAT[data_format]
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
        widgets = {
            "crops": forms.Select(attrs={"extra-class": "old-dataset-field"}),
        }

    def __init__(self, *args, **kwargs):
        self.crops = kwargs.pop("crops", None)
        if self.crops:
            kwargs["initial"] = {
                **kwargs.get("initial", {}),
                "crops": self.crops,
                "reuse_dataset": True,
            }

        super().__init__(*args, **kwargs)
        self.fields["crops"].queryset = self.fields["crops"].queryset.filter(
            regions__isnull=False,
            requested_by=self._user,
            status="SUCCESS",
        )

        self.order_fields(list(AbstractTaskOnDatasetForm.Meta.fields) + ["crops"])

    def check_dataset(self):
        """
        Check if the dataset was provided
        """
        if self.cleaned_data.get("reuse_dataset", False):
            has_crops = bool(self.cleaned_data.get("crops", None))
            has_dataset = bool(self.cleaned_data.get("dataset", None))

            if not (has_crops or has_dataset):
                self.add_error("dataset", "Either a dataset or crops must be provided.")
                return False
            return True

        # If not reusing dataset, fallback to parent class validation
        return super().check_dataset()

    def _populate_dataset(self):
        if crops := self.cleaned_data.get("crops", None):
            self._crops = crops
            self._dataset = crops.dataset
            return
        super()._populate_dataset()

    def save(self, commit=True):
        # TODO check if this works correctly
        instance = super().save(commit=False)
        instance.crops = self._crops

        if commit:
            instance.save()

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
